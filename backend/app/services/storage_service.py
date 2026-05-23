"""MinIO 对象存储服务"""
import io
import os
import uuid
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.config import settings


class StorageService:
    """MinIO 对象存储封装"""

    def __init__(self):
        self._client: Minio | None = None
        self._enabled = False
        self._init_client()

    def _init_client(self):
        try:
            self._client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            # 确保 bucket 存在
            bucket = settings.MINIO_BUCKET
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
            self._enabled = True
            print(f"[MinIO] Connected to {settings.MINIO_ENDPOINT}, bucket='{bucket}'")
        except Exception as e:
            print(f"[MinIO] Connection failed ({e}) — falling back to local storage")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def upload_file(self, file_path: str, object_name: str = None, content_type: str = None) -> str | None:
        """上传本地文件到 MinIO，返回 object_name；失败返回 None"""
        if not self._enabled:
            return None
        if object_name is None:
            ext = os.path.splitext(file_path)[1]
            object_name = f"uploads/{uuid.uuid4().hex}{ext}"
        try:
            self._client.fput_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
            )
            return object_name
        except S3Error as e:
            print(f"[MinIO] Upload failed: {e}")
            return None

    def upload_bytes(self, data: bytes, object_name: str = None, content_type: str = "application/octet-stream") -> str | None:
        """上传字节数据到 MinIO"""
        if not self._enabled:
            return None
        if object_name is None:
            object_name = f"uploads/{uuid.uuid4().hex}"
        try:
            self._client.put_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return object_name
        except S3Error as e:
            print(f"[MinIO] Upload bytes failed: {e}")
            return None

    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str | None:
        """生成预签名下载 URL"""
        if not self._enabled or not object_name:
            return None
        try:
            return self._client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                expires=timedelta(seconds=expires),
            )
        except S3Error as e:
            print(f"[MinIO] Presigned URL failed: {e}")
            return None

    def download_file(self, object_name: str, file_path: str) -> bool:
        """从 MinIO 下载文件到本地"""
        if not self._enabled:
            return False
        try:
            self._client.fget_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=object_name,
                file_path=file_path,
            )
            return True
        except S3Error as e:
            print(f"[MinIO] Download failed: {e}")
            return False

    def delete_file(self, object_name: str) -> bool:
        """删除 MinIO 中的文件"""
        if not self._enabled:
            return False
        try:
            self._client.remove_object(settings.MINIO_BUCKET, object_name)
            return True
        except S3Error as e:
            print(f"[MinIO] Delete failed: {e}")
            return False


# 全局单例
storage_service = StorageService()
