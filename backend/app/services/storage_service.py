import os
from datetime import timedelta

from minio import Minio

from app.config import settings

_client = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        bucket = settings.MINIO_BUCKET
        if not _client.bucket_exists(bucket):
            _client.make_bucket(bucket)
            _client.set_bucket_policy(bucket, _public_read_policy(bucket))
    return _client


def _public_read_policy(bucket: str) -> str:
    import json
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket}/*"],
        }],
    })


def upload_file(local_path: str, object_name: str, content_type: str = "image/jpeg") -> str:
    client = get_minio()
    client.fput_object(settings.MINIO_BUCKET, object_name, local_path, content_type=content_type)
    # Return direct access URL (bucket is public-read)
    return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"


def delete_file(object_name: str):
    try:
        get_minio().remove_object(settings.MINIO_BUCKET, object_name)
    except Exception:
        pass


def get_presigned_url(object_name: str, expires: int = 86400) -> str:
    client = get_minio()
    return client.presigned_get_object(settings.MINIO_BUCKET, object_name, expires=timedelta(seconds=expires))
