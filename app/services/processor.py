# app/services/processor.py
# Worker-side processing functions. Each job enqueued to RQ will call process_job with data payload.
# The processor will:
#   - Download inputs from storage
#   - Perform a simple operation (pass-through or lightweight transform using Pillow / PyPDF2)
#   - Save result back to storage and update job metadata in Redis
#
# For heavy, production-grade processing (OCR, PDF->Word), workers should be provisioned with native tools
# like tesseract, libreoffice, ghostscript. This template implements safe, simple processors as examples.

import logging
import os
import json
from typing import Dict, Any, List
from app.services import storage, queue
from app.config import settings
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
import io
import base64
import time

logger = logging.getLogger("processor")


def _save_metadata_sync(job_id: str, partial: Dict[str, Any]):
    """
    Save partial metadata to Redis (sync). RQ workers are sync, so use sync Redis connection.
    """
    r = queue.get_sync_redis()
    raw = r.get(f"job:{job_id}")
    meta = {}
    if raw:
        try:
            meta = json.loads(raw)
        except Exception:
            meta = {}
    meta.update(partial)
    meta["updatedAt"] = int(time.time() * 1000)
    r.set(f"job:{job_id}", json.dumps(meta), ex=settings.job_ttl_seconds)


def _download_inputs(input_keys: List[str]) -> List[bytes]:
    """
    Download each input from S3 (synchronously using boto3 wrapped method via storage.download_bytes which is async).
    In RQ worker (sync), we call boto3 client directly for simplicity.
    """
    results = []
    # direct boto3 sync client usage
    import boto3
    from botocore.config import Config

    boto_config = Config(signature_version="s3v4", region_name=settings.s3_region)
    sess = boto3.session.Session()
    s3 = sess.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
        config=boto_config,
    )
    for key in input_keys:
        resp = s3.get_object(Bucket=settings.s3_bucket, Key=key)
        body = resp["Body"].read()
        results.append(body)
    return results


def _upload_output_sync(buffer: bytes, content_type: str, prefix: str = "output") -> str:
    """
    Upload bytes synchronously using boto3 and return key.
    """
    import boto3
    from botocore.config import Config
    import time

    boto_config = Config(signature_version="s3v4", region_name=settings.s3_region)
    sess = boto3.session.Session()
    s3 = sess.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key_id or None,
        aws_secret_access_key=settings.s3_secret_access_key or None,
        config=boto_config,
    )
    key = f"{prefix}/{int(time.time())}-{int(time.time() * 1000)}"
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=buffer, ContentType=content_type)
    return key


def _process_pass_through(job_id: str, input_keys: List[str]):
    """
    Default processing: if single input, copy to output; if multiple, for PDFs merge or for images create a zip-like pass.
    Implemented operations:
      - If single image or PDF, return that file as output (no-op copy)
      - If multiple images and the tool is 'merge-images' we will create a simple vertical merge image using Pillow
      - If multiple PDFs and the tool is merge-pdf, try naive PDF merge using PyPDF2
    """
    # Download inputs
    buffers = _download_inputs(input_keys)
    # If only one input, copy it back as output
    if len(buffers) == 1:
        # detect type naive by magic numbers
        head = buffers[0][:8]
        if head.startswith(b"%PDF-"):
            content_type = "application/pdf"
        else:
            # assume image/jpeg fallback
            content_type = "application/octet-stream"
        key = _upload_output_sync(buffers[0], content_type, prefix="output")
        return key

    # Multiple inputs: try to merge PDFs or images based on content types
    # Check first file for PDF
    if buffers[0][:8].startswith(b"%PDF-"):
        # PDF merge using PyPDF2
        writer = PdfWriter()
        for b in buffers:
            reader = PdfReader(io.BytesIO(b))
            for page in reader.pages:
                writer.add_page(page)
        out_io = io.BytesIO()
        writer.write(out_io)
        out_bytes = out_io.getvalue()
        key = _upload_output_sync(out_bytes, "application/pdf", prefix="output")
        return key
    else:
        # Attempt simple vertical concatenation of images with Pillow
        imgs = [Image.open(io.BytesIO(b)).convert("RGBA") for b in buffers]
        widths = [im.width for im in imgs]
        heights = [im.height for im in imgs]
        max_w = max(widths)
        total_h = sum(heights)
        merged = Image.new("RGBA", (max_w, total_h), (255, 255, 255, 0))
        y = 0
        for im in imgs:
            merged.paste(im, (0, y))
            y += im.height
        out_io = io.BytesIO()
        merged = merged.convert("RGB")
        merged.save(out_io, format="JPEG", quality=85)
        out_bytes = out_io.getvalue()
        key = _upload_output_sync(out_bytes, "image/jpeg", prefix="output")
        return key


def process_job(data: Dict[str, Any]):
    """
    RQ worker entrypoint. Expects data dict with:
      - jobId: str
      - inputKeys: List[str]
      - fields: dict
      - tool: optional metadata
    """
    job_id = data.get("jobId")
    input_keys = data.get("inputKeys", [])
    tool = data.get("tool", {}).get("slug") if isinstance(data.get("tool"), dict) else None

    if not job_id or not input_keys:
        logger.error("Invalid job data, missing jobId or inputKeys")
        return

    _save_metadata_sync(job_id, {"status": "running"})

    try:
        # For production-grade processors, replace this dispatch with specialized functions per slug
        # Some slugs might require external binaries. This template intentionally does a safe pass-through.
        out_key = _process_pass_through(job_id, input_keys)

        # Update metadata
        _save_metadata_sync(job_id, {"status": "completed", "outputFile": out_key})
        logger.info("Job %s completed output=%s", job_id, out_key)
    except Exception as exc:
        logger.exception("Job %s failed: %s", job_id, exc)
        _save_metadata_sync(job_id, {"status": "failed", "error": str(exc)})
        raise
