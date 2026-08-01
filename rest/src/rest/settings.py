from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://postgres:postgres@localhost:5432"
    )

    model_config = SettingsConfigDict(env_file=".env")
