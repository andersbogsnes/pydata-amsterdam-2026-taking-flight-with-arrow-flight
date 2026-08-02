import pathlib

import cyclopts
import sqlalchemy as sa
from flight_server.client import Client
from pyarrow.fs import S3FileSystem
import pyarrow as pa

from fly.console import console
from fly.local.catalog import _bootstrap_catalog
from fly.local.db import _handle_db_upload
from fly.local.iceberg import _handle_iceberg_upload
from fly.settings import Settings
from rest import db as rest_db

cmd = cyclopts.App(name="local", help="local deployment of project")

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"

TRIP_DATA_FILE = DATA_DIR / "202601-citibike-tripdata_1.csv"


@cmd.command()
def bootstrap():
    """Configure services and upload initial data"""

    if not TRIP_DATA_FILE.exists():
        console.print(
            f"❌ {TRIP_DATA_FILE.name} doesn't exist. Run the `fly data download` command"
            f" to download the initial data."
        )

    settings = Settings()
    s3_fs = S3FileSystem(
        access_key=settings.s3_access_key.get_secret_value(),
        secret_key=settings.s3_secret_key.get_secret_value(),
        endpoint_override=settings.s3_url,
        allow_bucket_creation=True,
        region=settings.s3_region,
    )
    s3_fs.create_dir(settings.bucket_name)

    engine = sa.create_engine(settings.db_url.unicode_string())
    rest_db.meta.create_all(engine)

    _bootstrap_catalog(settings)

    client = Client.for_location(settings.flight_server_url)

    _handle_iceberg_upload(client,
                           "trips",
                           "rides", TRIP_DATA_FILE,
                           dtypes={"started_at": pa.timestamp("ms"),
                                   "ended_at": pa.timestamp("ms")})
    _handle_db_upload(engine, rest_db.rides_table, TRIP_DATA_FILE)
    console.print("🔗 Notebook is ready! http://localhost:8080")
