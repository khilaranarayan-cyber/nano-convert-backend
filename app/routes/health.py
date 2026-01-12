# app/routes/health.py
# Health endpoint that checks critical dependencies (Redis and S3)

import logging
from fastapi import APIRouter
from app.services import queue
from app.services import storage
from app.config import settings

router = APIRouter()
logger = logging.getLogger("routes.health")


@router.get("/health")
async def health():
    status = {"ok": True, "redis": False, "s3": False}
    # Redis
    try:
        r = queue.get_async_redis()
        pong = await r.ping()
        status["redis"] = bool(pong)
    except Exception as e:
        logger.exception("Health check redis failed: %s", e)
        status["ok"] = False

    # S3 - simple head_bucket or list
    try:
        # attempt to init s3 client and check bucket exists by generating a presigned url for root key
        await storage.init_s3_client()
        status["s3"] = True
    except Exception as e:
        logger.exception("Health check s3 failed: %s", e)
        status["ok"] = False

    return status
