from pathlib import Path
from typing import Optional, Any
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo


BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_SERVER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="after")
    def assemble_db_connection(cls, v: Optional[str], info: FieldValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            port=info.data.get("POSTGRES_PORT"),
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )

    class Config:
        env_file = BASE_DIR / "config/.env"


settings = Settings()
