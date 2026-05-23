from pydantic import BaseModel
from typing import Optional
import os


class Settings(BaseModel):
    APP_NAME: str = "VisDrone Detection Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "static/uploads"
    RESULT_DIR: str = "static/results"

    YOLO_MODEL_PATH: str = "yolo11m_visdrone.pt"
    COCO_MODEL_PATH: str = "yolo11n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    # PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "visdrone_user"
    DB_PASSWORD: str = "visdrone_password"
    DB_NAME: str = "visdrone_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "visdrone-bucket"
    MINIO_SECURE: bool = False

    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]


def get_settings() -> Settings:
    settings = Settings()

    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if hasattr(settings, key):
                        try:
                            target_type = type(getattr(settings, key))
                            if target_type == bool:
                                setattr(settings, key, value.lower() in ("true", "1", "yes"))
                            else:
                                setattr(settings, key, target_type(value))
                        except (ValueError, TypeError):
                            pass

    return settings


settings = get_settings()

_db_available = None


def is_db_available() -> bool:
    global _db_available
    if _db_available is not None:
        return _db_available
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_available = True
        return True
    except Exception:
        _db_available = False
        return False


def reset_db_status():
    global _db_available
    _db_available = None
