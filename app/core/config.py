from urllib.parse import quote_plus
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Configuracion Operativa ---
    DB_OPERATIVA_URL: str | None = None
    DB_OP_USER: str | None = None
    DB_OP_PASSWORD: str | None = None
    DB_OP_HOST: str | None = None
    DB_OP_PORT: int = 5432
    DB_OP_NAME: str | None = None

    # Alias heredados para compatibilidad
    user: str | None = None
    password: str | None = None
    host: str | None = None
    port: int | None = None
    dbname: str | None = None

    # --- Configuracion Administrativa ---
    DB_ADMIN_URL: str | None = None
    DB_ADMIN_USER: str | None = None
    DB_ADMIN_PASSWORD: str | None = None
    DB_ADMIN_HOST: str | None = None
    DB_ADMIN_PORT: int = 5432
    DB_ADMIN_NAME: str | None = None

    # --- Configuracion de Seguridad ---
    JWT_EXPIRES_MINUTES: int
    JWT_SECRET: str
    JWT_ALGORITHM: str

    @model_validator(mode="after")
    def ensure_db_urls(self) -> "Settings":
        # Validacion y construccion de URL Operativa
        if not self.DB_OPERATIVA_URL:
            db_op_user = self.DB_OP_USER or self.user
            db_op_password = self.DB_OP_PASSWORD or self.password
            db_op_host = self.DB_OP_HOST or self.host
            db_op_port = self.DB_OP_PORT if self.DB_OP_PORT is not None else (self.port or 5432)
            db_op_name = self.DB_OP_NAME or self.dbname

            if all([db_op_user, db_op_password, db_op_host, db_op_name]):
                self.DB_OPERATIVA_URL = (
                    "postgresql+psycopg2://"
                    f"{quote_plus(db_op_user)}:{quote_plus(db_op_password)}@{db_op_host}:{db_op_port}/{db_op_name}"
                    "?sslmode=require"
                )
            else:
                raise ValueError("Configuracion incompleta para la base de datos Operativa en .env")

        # Validacion y construccion de URL Administrativa
        if not self.DB_ADMIN_URL:
            if all([self.DB_ADMIN_USER, self.DB_ADMIN_PASSWORD, self.DB_ADMIN_HOST, self.DB_ADMIN_NAME]):
                self.DB_ADMIN_URL = (
                    "postgresql+psycopg2://"
                    f"{quote_plus(self.DB_ADMIN_USER)}:{quote_plus(self.DB_ADMIN_PASSWORD)}@{self.DB_ADMIN_HOST}:{self.DB_ADMIN_PORT}/{self.DB_ADMIN_NAME}"
                    "?sslmode=require"
                )
            else:
                raise ValueError("Configuracion incompleta para la base de datos Administrativa en .env")

        return self

settings = Settings()