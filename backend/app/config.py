from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toàn bộ cấu hình/bí mật đọc từ biến môi trường hoặc file .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Chợ đồ cũ sinh viên API"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 5
    max_images_per_listing: int = 5
    max_listings_per_day: int = 5  # chống spam tin đăng

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    log_level: str = "INFO"
    log_json: bool = True

    @field_validator("jwt_secret_key")
    @classmethod
    def _strong_secret(cls, value: str) -> str:
        if len(value) < 32 or value.startswith("replace-with"):
            raise ValueError("JWT_SECRET_KEY phải dài ≥ 32 ký tự và không được dùng giá trị mẫu")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
