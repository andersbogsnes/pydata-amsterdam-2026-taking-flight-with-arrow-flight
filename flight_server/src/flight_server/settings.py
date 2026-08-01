from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    catalog_url: str = "http://localhost:8181"
    flight_server_url: str = "grpc://localhost:7000"
    warehouse: str = "default"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
