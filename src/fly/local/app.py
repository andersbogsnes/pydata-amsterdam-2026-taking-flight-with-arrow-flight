import pathlib

import cyclopts
import sqlalchemy as sa
from pyarrow.fs import S3FileSystem

from flight_server.client import Client
from fly.console import console
from fly.local.catalog import _bootstrap_catalog
from fly.local.db import _handle_db_upload
from fly.local.iceberg import _handle_iceberg_upload
from fly.settings import Settings
from rest import db as rest_db

app = cyclopts.App(
    name="local", help="local deployment of project"
)

DATA_DIR = pathlib.Path(__file__).parents[3] / "data"
MESSAGES_URL = "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=messages-demo.csv"
CAMPAIGNS_URL = (
    "https://www.kaggle.com/datasets/mkechinov/direct-messaging?select=campaigns.csv"
)
MESSAGES_FILE = DATA_DIR / "messages-demo.csv"
CAMPAIGNS_FILE = DATA_DIR / "campaigns.csv"


@app.command()
def bootstrap():
    """Configure services and upload initial data"""

    for location, data_file in zip(
            [MESSAGES_URL, CAMPAIGNS_URL], [MESSAGES_FILE, CAMPAIGNS_FILE]
    ):
        if not data_file.exists():
            console.print(
                f"❌ [red]{data_file} doesn't exist. "
                f"Go to {location}, download and extract it to the data folder"
            )
            return

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

    _handle_iceberg_upload(client, "events", "messages", MESSAGES_FILE)
    _handle_db_upload(engine, rest_db.messages_table, MESSAGES_FILE)
    console.print("🔗 Notebook is ready! http://localhost:8080")
