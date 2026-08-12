import pathlib

import cyclopts
import pyarrow as pa
import sqlalchemy as sa
from flight_server.client import Client

from fly.console import console
from fly.remote.compose import _start_services
from fly.settings import Settings
from fly.shared.db import handle_db_upload
from fly.shared.iceberg import handle_iceberg_upload
from fly.shared.catalog import bootstrap_catalog
from rest import db as rest_db

cmd = cyclopts.App(name="remote", help="remote deployment of project - requires AWS setup")

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"

TRIP_DATA_FILE = DATA_DIR / "202601-citibike-tripdata_1.csv"


@cmd.command()
def bootstrap(services: bool = True):
    """Configure services and upload initial data"""

    if not TRIP_DATA_FILE.exists():
        console.print(
            f"❌ {TRIP_DATA_FILE.name} doesn't exist. Run the `fly data download` command"
            f" to download the initial data."
        )

    settings = Settings(_env_file="aws.env")

    if services:
        _start_services()
    bootstrap_catalog(settings)
    engine = sa.create_engine(settings.db_url.unicode_string())
    rest_db.meta.create_all(engine)

    client = Client.for_location(settings.flight_server_url)

    handle_iceberg_upload(
        client,
        "trips",
        "rides",
        TRIP_DATA_FILE,
        dtypes={"started_at": pa.timestamp("ms"), "ended_at": pa.timestamp("ms")},
    )
    handle_db_upload(engine, rest_db.rides_table, TRIP_DATA_FILE)
    console.print(" 🔗 Notebook is ready! http://localhost:8080")
