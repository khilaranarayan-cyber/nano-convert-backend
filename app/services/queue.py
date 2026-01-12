# app/services/queue.py
# RQ (Redis Queue) integration and job metadata storage in Redis.
# Provides enqueue helper used by API routes.

import logging
import json
import uuid
from typing import Any, Dict
import redis
import redis.asyncio as aioredis
from rq import Queue
from app.config import settings

logger = logging.getLogger("queue")

_rq_redis_conn = None  # sync Redis used by RQ
_async_redis = None  # asyncio Redis used by the app
_rq_queue = None


async def init_redis_connections():
    global _rq_redis_conn, _async_redis, _rq_queue
    # Setup async redis for app metadata
    _async_redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    # Setup sync redis for rq
    _rq_redis_conn = redis.from_url(settings.redis_url)
    _rq_queue = Queue(connection=_rq_redis_conn, name="jobs")
    logger.info("Redis connections for RQ and async operations initialized")
    return _async_redis


def get_rq_queue() -> Queue:
    global _rq_queue
    if _rq_queue is None:
        # fallback lazy init
        global _rq_redis_conn
        _rq_redis_conn = redis.from_url(settings.redis_url)
        _rq_queue = Queue(connection=_rq_redis_conn, name="jobs")
    return _rq_queue


def get_sync_redis():
    global _rq_redis_conn
    if _rq_redis_conn is None:
        _rq_redis_conn = redis.from_url(settings.redis_url)
    return _rq_redis_conn


def get_async_redis():
    global _async_redis
    if _async_redis is None:
        import redis.asyncio as aioredis

        _async_redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _async_redis


async def close_redis_connections():
    global _async_redis
    if _async_redis:
        await _async_redis.close()


def enqueue_job(function_path: str, data: Dict[str, Any], job_timeout: int = 3600) -> str:
    """
    Enqueue a job to RQ. function_path is an import path string like 'app.services.processor.process_job'
    data is any serializable dict.
    Returns job id.
    """
    q = get_rq_queue()
    job = q.enqueue(function_path, data, job_timeout=job_timeout)
    logger.info("Enqueued job %s function=%s", job.get_id(), function_path)
    return job.get_id()


async def store_job_metadata(job_id: str, meta: Dict[str, Any]):
    """
    Store job metadata in Redis (async) with TTL based on settings.job_ttl_seconds.
    """
    r = get_async_redis()
    await r.set(f"job:{job_id}", json.dumps(meta), ex=settings.job_ttl_seconds)


async def fetch_job_metadata(job_id: str):
    r = get_async_redis()
    raw = await r.get(f"job:{job_id}")
    if not raw:
        return None
    import json

    try:
        return json.loads(raw)
    except Exception:
        return None
