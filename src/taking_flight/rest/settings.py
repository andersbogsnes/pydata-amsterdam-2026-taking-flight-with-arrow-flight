from pydantic import SecretStr, HttpUrl, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    access_key: SecretStr = "rustfsadmin"
    secret_key: SecretStr = "rustfsadmin"
    s3_endpoint: HttpUrl = "http://localhost:9000"
    region: str = "eu-north-1"
    db_url: PostgresDsn = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
    )
