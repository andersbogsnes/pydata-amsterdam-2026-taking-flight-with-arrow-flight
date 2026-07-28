from pydantic import HttpUrl, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    access_key: SecretStr = SecretStr("rustfsadmin")
    secret_key: SecretStr = SecretStr("rustfsadmin")
    s3_endpoint: HttpUrl | None = HttpUrl("http://localhost:9000")
    region: str = "eu-north-1"
    location: str = "grpc://0.0.0.0:7000"
    db_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
    bucket_name: str = "events"
