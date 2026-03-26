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

    # Optional discrete DB settings (fallback when DB_URL is not provided)
    user: str | None = None
    password: str | None = None
    host: str | None = None
    port: int = 5432
    dbname: str | None = None

    #jwt
    JWT_EXPIRES_MINUTES: int
    JWT_SECRET: str
    JWT_ALGORITHM: str

    @model_validator(mode="after")
    def ensure_db_url(self) -> "Settings":
        if self.DB_URL:
            return self

        if all([self.user, self.password, self.host, self.dbname]):
            encoded_user = quote_plus(self.user)
            encoded_password = quote_plus(self.password)
            self.DB_URL = (
                "postgresql+psycopg2://"
                f"{encoded_user}:{encoded_password}@{self.host}:{self.port}/{self.dbname}"
                "?sslmode=require"
            )
            return self

        raise ValueError(
            "Database configuration is incomplete. Set DB_URL or user/password/host/dbname in .env"
        )

settings = Settings()
