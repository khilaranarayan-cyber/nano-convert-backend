# app/services/storage.py
# S3-compatible Cloudflare R2 / MinIO integration using boto3.
# We wrap synchronous boto3 calls into async-friendly run_in_threadpool to avoid blocking the event loop.

import logging
import boto3
from botocore.config import Config
from fastapi.concurrency import run_in_threadpool
from app.config import settings
from typing import Optional
import time
import urllib.parse

logger = logging.getLogger("storage")

_s3_client = None


async def init_s3_client():
    """
    Initialize boto3 S3 client with given endpoint and credentials.
    boto3 client is synchronous; use run_in_threadpool when calling network ops.
    """
    global _s3_client
    if _s3_client is not None:
        return
    # Configure signature version for R2 compatibility
    boto_config = Config(signature_version="s3v4", region_name=settings.s3_region)
    session = boto3.session.Session()
    _s3_client = session.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
        config=boto_config,
    )
    logger.info("S3 client initialized using endpoint=%s bucket=%s", settings.s3_endpoint, settings.s3_bucket)


async def close_s3_client():
    # boto3 clients do not require explicit close in many cases, but provide a hook
    global _s3_client
    _s3_client = None


async def upload_bytes(buffer: bytes, content_type: str, prefix: str = "temp") -> str:
    """
    Upload a bytes buffer to S3-compatible storage and return object key.
    """
    if _s3_client is None:
        await init_s3_client()

    key = f"{prefix}/{int(time.time())}-{int(time.time() * 1000)}"
    # run boto3 put_object in threadpool
    def _put():
        _s3_client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=buffer,
            ContentType=content_type,
            Metadata={"createdAt": str(int(time.time()))},
        )
        return key

    return await run_in_threadpool(_put)


async def download_bytes(key: str) -> bytes:
    """
    Download an object from S3 and return bytes.
    """
    if _s3_client is None:
        await init_s3_client()

    def _get():
        resp = _s3_client.get_object(Bucket=settings.s3_bucket, Key=key)
        body = resp["Body"].read()
        return body

    return await run_in_threadpool(_get)


async def delete_object(key: str):
    if _s3_client is None:
        await init_s3_client()

    def _delete():
        _s3_client.delete_object(Bucket=settings.s3_bucket, Key=key)

    await run_in_threadpool(_delete)


async def get_presigned_url(key: str, expires_seconds: int = 3600) -> str:
    """
    Return a presigned URL for the given key. For Cloudflare R2, boto3's generate_presigned_url works.
    """
    if _s3_client is None:
        await init_s3_client()

    def _presign():
        return _s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    url = await run_in_threadpool(_presign)
    # Ensure URL is safe: Cloudflare may return special host; encode key if necessary
    return url
