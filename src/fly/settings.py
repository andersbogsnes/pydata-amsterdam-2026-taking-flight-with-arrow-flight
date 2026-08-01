from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    s3_url: str | None = "http://localhost:9000"
    s3_catalog_endpoint: str = "http://storage:9000"
    s3_access_key: SecretStr = SecretStr("rustfsadmin")
    s3_secret_key: SecretStr = SecretStr("rustfsadmin")
    s3_region: str = "us-east-1"
    catalog_url: str = "http://localhost:8181"
    db_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://postgres:postgres@localhost:5432"
    )
    flight_server_url: str = "grpc://localhost:7000"
    bucket_name: str = "events"
    namespace: str = "events"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
