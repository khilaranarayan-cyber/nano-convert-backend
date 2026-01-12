# app/routes/tools.py
# Route: POST /api/tools/{slug}
# Accepts multipart/form-data file uploads, validates files, uploads to S3, enqueues job to RQ, stores metadata in Redis.

import logging
import uuid
import time
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse
from app.constants import TOOLS_META
from app.utils.validation import validate_tool_and_files
from app.services import storage, queue
from app.config import settings

router = APIRouter()
logger = logging.getLogger("routes.tools")


@router.post("/tools/{slug}")
async def run_tool(slug: str, request: Request, files: List[UploadFile] = File(...)):
    """
    Main tool endpoint. Validates files according to TOOLS_META, scans them, uploads to S3,
    stores metadata and enqueues a processing job (RQ). Returns a jobId for frontend polling.
    """
    # Rate limiting per-IP using Redis simple counter
    client_ip = request.client.host if request.client else "unknown"
    redis = queue.get_async_redis()
    key = f"ratelimit:{client_ip}:{int(time.time() // 60)}"
    try:
        # increment in redis
        incr = await redis.incr(key)
        if incr == 1:
            await redis.expire(key, 61)
        if incr > settings.rate_limit_per_min:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    except Exception:
        # don't block if redis is unreachable
        logger.exception("Rate limit check failed, continuing")

    if slug not in TOOLS_META:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Validate the uploaded files
    validated = await validate_tool_and_files(slug, files)

    # Upload inputs to S3
    input_keys = []
    for fname, buffer, mime_type in validated:
        key = await storage.upload_bytes(buffer, mime_type, prefix="temp")
        input_keys.append(key)

    # create job id and metadata
    job_id = str(uuid.uuid4())
    created_at = int(time.time() * 1000)
    job_meta = {
        "id": job_id,
        "slug": slug,
        "status": "queued",
        "createdAt": created_at,
        "updatedAt": created_at,
        "inputFiles": input_keys,
        "expiresAt": created_at + settings.job_ttl_seconds * 1000,
    }

    # persist metadata to redis
    await queue.store_job_metadata(job_id, job_meta)

    # enqueue to RQ worker; provide the import path to the function for RQ worker to call.
    job_data = {"jobId": job_id, "inputKeys": input_keys, "fields": {}, "tool": {"slug": slug}}
    rq_job_id = queue.enqueue_job("app.services.processor.process_job", job_data, job_timeout=settings.job_ttl_seconds + 60)

    # return structured json
    return JSONResponse(status_code=202, content={"jobId": job_id, "rqJobId": rq_job_id, "status": "queued"})
