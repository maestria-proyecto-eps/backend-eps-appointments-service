from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DB_URL: str | None = None

    # Preferred DB settings aligned with .env/.env.example
    DB_OP_USER: str | None = None
    DB_OP_PASSWORD: str | None = None
    DB_OP_HOST: str | None = None
    DB_OP_PORT: int = 5432
    DB_OP_NAME: str | None = None

    # Legacy aliases kept for backward compatibility
    user: str | None = None
    password: str | None = None
    host: str | None = None
    port: int | None = None
    dbname: str | None = None

    #jwt
    JWT_EXPIRES_MINUTES: int
    JWT_SECRET: str
    JWT_ALGORITHM: str

    @model_validator(mode="after")
    def ensure_db_url(self) -> "Settings":
        if self.DB_URL:
            return self

        db_user = self.DB_OP_USER or self.user
        db_password = self.DB_OP_PASSWORD or self.password
        db_host = self.DB_OP_HOST or self.host
        db_port = self.DB_OP_PORT if self.DB_OP_PORT is not None else (self.port or 5432)
        db_name = self.DB_OP_NAME or self.dbname

        if all([db_user, db_password, db_host, db_name]):
            encoded_user = quote_plus(db_user)
            encoded_password = quote_plus(db_password)
            self.DB_URL = (
                "postgresql+psycopg2://"
                f"{encoded_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
                "?sslmode=require"
            )
            return self

        raise ValueError(
            "Database configuration is incomplete. Set DB_URL or DB_OP_USER/DB_OP_PASSWORD/DB_OP_HOST/DB_OP_NAME in .env"
        )

settings = Settings()
