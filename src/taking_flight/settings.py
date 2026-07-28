from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    S3_URL: str = "http://localhost:9000"
    CATALOG_URL: str = "http://localhost:8181"
    DB_URL: str = "postgresql+psycopg:///postgres:postgres@localhost:5432"

