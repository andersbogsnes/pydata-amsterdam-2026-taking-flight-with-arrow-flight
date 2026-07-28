from types import TracebackType
from typing import Self

import attrs
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from taking_flight.flight_server.db import dataset_table
from taking_flight.flight_server.models import Dataset, UpdateDatasetRequest

get_dataset_sql = sa.select(
    dataset_table.c.name,
    dataset_table.c.description,
    dataset_table.c.bucket,
    dataset_table.c.file_name,
    dataset_table.c.file_type,
    dataset_table.c.num_partitions,
    dataset_table.c.num_rows,
    dataset_table.c.serialized_size,
)


@attrs.define
class DatasetRepo:
    _engine: sa.Engine
    _conn: sa.Connection | None = attrs.field(init=False, default=None)

    @classmethod
    def from_url(cls, db_url: str) -> Self:
        engine = sa.create_engine(db_url)
        return cls(engine=engine)  # ty:ignore[missing-argument, unknown-argument]

    def get_dataset(self, dataset_name: str) -> Dataset | None:
        sql = get_dataset_sql.where(dataset_table.c.name == dataset_name).where(
            dataset_table.c.deleted_at.is_(None)
        )
        data = self.conn.execute(sql).one_or_none()
        if data is None:
            return None
        return Dataset.model_validate(data)

    def get_datasets(self, name_filter: str | None = None) -> list[Dataset]:
        sql = get_dataset_sql.where(dataset_table.c.deleted_at.is_(None))
        if name_filter:
            sql = sql.where(dataset_table.c.name.ilike(f"%{name_filter}%"))
        results = self.conn.execute(sql)
        return [Dataset.model_validate(r) for r in results]

    def update_dataset(self, dataset: UpdateDatasetRequest) -> Dataset | None:
        sql = (
            dataset_table.update()
            .values(description=dataset.description)
            .where(dataset_table.c.name == dataset.name)
        )
        self.conn.execute(sql)
        return self.get_dataset(dataset.name)

    def create_dataset(self, dataset: Dataset) -> Dataset:

        sql = (
            dataset_table.insert()
            .values(
                name=dataset.name,
                description=dataset.description,
                bucket=dataset.bucket,
                file_name=dataset.file_name,
                file_type=dataset.file_type,
                num_partitions=dataset.num_partitions,
                num_rows=dataset.num_rows,
                serialized_size=dataset.serialized_size,
            )
            .returning(dataset_table)
        )
        try:
            result = self.conn.execute(sql).fetchone()
        except IntegrityError:
            raise ValueError(f"Dataset {dataset.name} already exists") from None
        return Dataset.model_validate(result)

    def delete_dataset(self, dataset_name: str) -> None:
        sql = (
            dataset_table.update()
            .where(dataset_table.c.name == dataset_name)
            .values(deleted_at=sa.func.now())
        )
        self.conn.execute(sql)

    def __enter__(self) -> Self:
        if self._conn is None:
            self._conn = self._engine.connect()
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_value: Exception | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._conn is None:
            return

        if exc_type is not None:
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()
        self._conn = None

    @property
    def conn(self) -> sa.Connection:
        if self._conn is None:
            raise RuntimeError("Connection not open")
        return self._conn
