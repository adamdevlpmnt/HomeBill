from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Conso Maison"
    APP_PASSWORD: str = "admin123"  # À surcharger via variable d'environnement
    SECRET_KEY: str = "secret-key-change-in-production-conso-maison-2026"
    DATA_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "data")
    DATABASE_URL: str = ""
    TZ: str = "Africa/Algiers"
    SEED_DEMO: bool = False
    COOKIE_NAME: str = "conso_session"
    COOKIE_MAX_AGE_DAYS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        data_path = Path(self.DATA_DIR)
        data_path.mkdir(parents=True, exist_ok=True)
        db_file = data_path / "conso_maison.db"
        return f"sqlite:///{db_file.as_posix()}"


settings = Settings()
