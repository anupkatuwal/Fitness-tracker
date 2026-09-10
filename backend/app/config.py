"""Application settings.

Values are read from environment variables (or a local ``.env`` file).
The production target is Microsoft SQL Server 2022 over ``pyodbc``; a SQLite
fallback keeps the app runnable on machines without the MS ODBC driver.
"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VANGUARD_", extra="ignore")

    # --- App ---
    app_name: str = "Vanguard Fitness API"
    api_v1_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Auth ---
    secret_key: str = "change-me-in-production-please-use-a-long-random-value"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # --- Database (MS SQL Server 2022) ---
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_host: str = "localhost"
    db_port: int = 1433
    db_name: str = "VanguardFitness"
    db_user: str = "sa"
    db_password: str = ""
    db_trust_server_certificate: bool = True
    db_echo: bool = False

    # Escape hatch: when the MS ODBC driver is unavailable (CI, local dev),
    # set VANGUARD_USE_SQLITE=true or provide an explicit DATABASE_URL.
    use_sqlite: bool = False
    sqlite_path: str = "./vanguard_fitness.db"
    database_url: str | None = None

    # --- External API ---
    openfoodfacts_base_url: str = "https://world.openfoodfacts.org"
    openfoodfacts_user_agent: str = (
        "VanguardFitness/1.0 (https://github.com/anupkatuwal/fitness-tracker)"
    )
    openfoodfacts_timeout_seconds: float = 12.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        """Build the SQLAlchemy connection URL."""
        if self.database_url:
            return self.database_url
        if self.use_sqlite:
            return f"sqlite:///{self.sqlite_path}"

        odbc = (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={self.db_host},{self.db_port};"
            f"DATABASE={self.db_name};"
            f"UID={self.db_user};"
            f"PWD={self.db_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate={'yes' if self.db_trust_server_certificate else 'no'};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
