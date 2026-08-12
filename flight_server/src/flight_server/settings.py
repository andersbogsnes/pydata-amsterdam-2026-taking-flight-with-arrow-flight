from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    catalog_url: str = "http://lakekeeper:8181/catalog"
    flight_server_url: str = "grpc://0.0.0.0:7001"
    warehouse: str = "default"
    namespace: str = "trips"
    mode: Literal["local", "aws"] = "local"
    token: str = "pydata_amsterdam"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
