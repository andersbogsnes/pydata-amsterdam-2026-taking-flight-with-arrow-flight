from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    catalog_url: str = "http://localhost:8181/catalog"
    flight_server_url: str = "grpc://0.0.0.0:7000"
    warehouse: str = "default"
    namespace: str = "events"
    mode: Literal["local", "aws"] = "local"
    token: str = "pydata_amsterdam"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
