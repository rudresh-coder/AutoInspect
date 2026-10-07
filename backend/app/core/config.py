from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_postgres_url(url: str, *, require_ssl: bool) -> str:
    if url.startswith("postgres://"):
        url = url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    elif url.startswith("postgresql://"):
        url = url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    if require_ssl and "sslmode=" not in url:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}sslmode=require"

    return url


class Settings(BaseSettings):
    app_name: str = "AutoInspect"
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    database_url: str
    database_url_unpooled: str | None = None
    redis_url: str

    @property
    def sqlalchemy_database_url(self) -> str:
        return _normalize_postgres_url(
            self.database_url,
            require_ssl=self.app_env == "production",
        )

    @property
    def sqlalchemy_database_url_unpooled(self) -> str | None:
        url = self.database_url_unpooled

        if url is None:
            return None

        return _normalize_postgres_url(
            url,
            require_ssl=self.app_env == "production",
        )

    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    r2_endpoint_url: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None

    allowed_image_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()