from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AutoInspect"
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    database_url: str
    redis_url: str

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url

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

        return url

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