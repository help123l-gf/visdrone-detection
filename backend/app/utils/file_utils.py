import os
import uuid
from fastapi import UploadFile


def get_file_url(filename: str, subdir: str) -> str:
    return f"/{subdir}/{filename}"


def ensure_directories():
    from app.config import settings
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULT_DIR, exist_ok=True)


async def save_upload_file(file: UploadFile, upload_dir: str) -> str:
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"temp_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return filename
