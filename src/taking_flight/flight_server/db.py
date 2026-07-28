import sqlalchemy as sa

meta = sa.MetaData()

dataset_table = sa.Table(
    "datasets",
    meta,
    sa.Column("id", sa.BigInteger, primary_key=True),
    sa.Column("name", sa.String, nullable=False, unique=True),
    sa.Column("description", sa.String, nullable=True),
    sa.Column("bucket", sa.String, nullable=False, default="events"),
    sa.Column("file_type", sa.String, nullable=False, default="parquet"),
    sa.Column("file_name", sa.String, nullable=False),
    sa.Column("num_partitions", sa.Integer, nullable=True),
    sa.Column("num_rows", sa.BigInteger, nullable=True),
    sa.Column("serialized_size", sa.BigInteger, nullable=True),
    sa.Column("deleted_at", sa.DateTime, nullable=True),
    sa.Column("created_at", sa.DateTime, nullable=False, default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime, nullable=False, default=sa.func.now(),
              onupdate=sa.func.now()),
)
