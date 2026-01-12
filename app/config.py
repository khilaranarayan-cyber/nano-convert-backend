# app/config.py
# Centralized configuration loaded from environment variables.

from typing import List
import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # App
    debug: bool = os.getenv("NODE_ENV", "development") != "production"
    port: int = int(os.getenv("PORT", 8000))

    # Redis (for metadata and RQ)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # S3 / Cloudflare R2 (S3 compatible)
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "")  # e.g. https://<accountid>.r2.cloudflarestorage.com
    s3_region: str = os.getenv("S3_REGION", "auto")
    s3_bucket: str = os.getenv("S3_BUCKET", "nano-convert-temp")
    s3_access_key_id: str = os.getenv("S3_ACCESS_KEY_ID", "")
    s3_secret_access_key: str = os.getenv("S3_SECRET_ACCESS_KEY", "")

    # ClamAV
    clamav_enabled: bool = os.getenv("CLAMAV_ENABLED", "true").lower() == "true"
    clamav_tcp_host: str = os.getenv("CLAMD_HOST", "127.0.0.1")
    clamav_tcp_port: int = int(os.getenv("CLAMD_PORT", 3310))

    # Upload constraints and rate limiting
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", 50 * 1024 * 1024))  # 50MB
    rate_limit_per_min: int = int(os.getenv("RATE_LIMIT_PER_MIN", 60))

    # Job TTL seconds
    job_ttl_seconds: int = int(os.getenv("JOB_TTL_SECONDS", 3600))

    # CORS
    cors_allow_origins: List[str] = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
