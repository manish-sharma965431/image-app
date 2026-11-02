from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Image Vision API"
    debug: bool = False

    # Auth
    jwt_secret: str  # required: app refuses to start without it
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # MongoDB (local)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "image_app"

    # CORS: list of allowed frontend origins (never use "*" with credentials)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Images
    cdn_base_url: str = "http://localhost:8000/cdn"
    storage_dir: Path = Path("storage/images")
    max_upload_mb: int = 10

    # Classification (Hugging Face model id, downloaded on first use)
    #classifier_model: str = "google/mobilenet_v2_1.0_224"
    classifier_model: str = "openai/clip-vit-base-patch32"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
