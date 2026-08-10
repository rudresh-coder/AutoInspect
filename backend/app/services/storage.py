import os
import tempfile
from pathlib import Path

import boto3

from backend.app.core.config import settings


def r2_is_configured() -> bool:
    return all(
        [
            settings.r2_endpoint_url,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
            settings.r2_bucket_name,
        ]
    )


def get_r2_client():
    if not r2_is_configured():
        raise RuntimeError("Cloudflare R2 is not configured.")

    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def upload_file(
    local_path: str,
    object_key: str,
    content_type: str | None = None,
) -> None:
    client = get_r2_client()

    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    client.upload_file(
        local_path,
        settings.r2_bucket_name,
        object_key,
        ExtraArgs=extra_args or None,
    )


def download_file(
    object_key: str,
    local_path: str,
) -> None:
    client = get_r2_client()

    client.download_file(
        settings.r2_bucket_name,
        object_key,
        local_path,
    )


def delete_file(object_key: str) -> None:
    client = get_r2_client()

    client.delete_object(
        Bucket=settings.r2_bucket_name,
        Key=object_key,
    )