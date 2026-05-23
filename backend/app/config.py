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
    DOWNLOAD_DIR: str = "static/downloads"

    YOLO_MODEL_PATH: str = "yolo11m_visdrone.pt"
    COCO_MODEL_PATH: str = "yolo11n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # ── PostgreSQL 数据库 ──
    DATABASE_URL: str = "postgresql://visdrone_user:visdrone_password@localhost:5432/visdrone_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis 缓存 ──
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None

    # ── MinIO 对象存储 ──
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "visdrone"
    MINIO_SECURE: bool = False

    # ── JWT 认证 ──
    JWT_SECRET_KEY: str = "visdrone-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── 告警阈值 ──
    ALERT_THRESHOLD: int = 15


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
                            current_val = getattr(settings, key)
                            if isinstance(current_val, bool):
                                setattr(settings, key, value.lower() in ("true", "1", "yes"))
                            elif isinstance(current_val, int):
                                setattr(settings, key, int(value))
                            elif isinstance(current_val, float):
                                setattr(settings, key, float(value))
                            elif isinstance(current_val, list):
                                setattr(settings, key, [v.strip() for v in value.split(",")])
                            else:
                                setattr(settings, key, value)
                        except (ValueError, TypeError):
                            pass

    return settings


settings = get_settings()
