import pathlib

import cyclopts
import pyarrow as pa
import sqlalchemy as sa
from flight_server.client import Client
from pyarrow.fs import S3FileSystem

from fly.console import console
from fly.shared.catalog import bootstrap_catalog
from fly.local.compose import _start_services, _stop_services
from fly.settings import Settings
from fly.shared.db import handle_db_upload
from fly.shared.iceberg import handle_iceberg_upload
from rest import db as rest_db

cmd = cyclopts.App(name="local", help="local deployment of project")

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"

TRIP_DATA_FILE = DATA_DIR / "202601-citibike-tripdata_1.csv"


@cmd.command()
def up(services: bool = True):
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

    if services:
        _start_services()

    s3_fs.create_dir(settings.bucket_name)

    engine = sa.create_engine(settings.db_url.unicode_string())
    rest_db.meta.create_all(engine)

    bootstrap_catalog(settings)

    client = Client.for_location(settings.flight_server_url)
    client.ping(5)
    handle_iceberg_upload(client,
                           "trips",
                           "rides", TRIP_DATA_FILE,
                          dtypes={"started_at": pa.timestamp("ms"),
                                   "ended_at": pa.timestamp("ms")})
    handle_db_upload(engine, rest_db.rides_table, TRIP_DATA_FILE)
    console.print("🔗 Notebook is ready! http://localhost:8080")

@cmd.command()
def down():
    """Tear down the local deployment"""
    _stop_services()