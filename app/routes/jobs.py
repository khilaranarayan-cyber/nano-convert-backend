# app/routes/jobs.py
# Route: GET /api/jobs/{id}
# Returns job metadata stored in Redis and presigned URL for output file if available.

import logging
from fastapi import APIRouter, HTTPException
from app.services import queue
from app.services import storage

router = APIRouter()
logger = logging.getLogger("routes.jobs")


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    meta = await queue.fetch_job_metadata(job_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")
    result = dict(meta)
    if meta.get("outputFile"):
        # generate presigned url
        url = await storage.get_presigned_url(meta["outputFile"], expires_seconds=3600)
        result["outputUrl"] = url
    return result
