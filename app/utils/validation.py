# app/utils/validation.py
# Functions to validate uploads, check mime types, scan for malware, enforce limits.

import io
import magic
import logging
from fastapi import HTTPException, UploadFile
from typing import List, Tuple
from app.config import settings
from app.constants import TOOLS_META
from app.services import clamav_service

logger = logging.getLogger("validation")


async def read_upload_file_bytes(upload_file: UploadFile) -> bytes:
    """
    Read the UploadFile fully into memory as bytes.
    For production systems consider streaming to S3/temporary disk to avoid OOM for huge files.
    """
    content = await upload_file.read()
    return content


def detect_mime_type(buffer: bytes, filename: str = "") -> str:
    """
    Use libmagic to detect the MIME type of a buffer.
    """
    try:
        mime = magic.from_buffer(buffer, mime=True)
        return mime
    except Exception:
        # fallback based on filename extension
        import mimetypes

        mt, _ = mimetypes.guess_type(filename)
        return mt or "application/octet-stream"


async def validate_tool_and_files(slug: str, files: List[UploadFile]) -> List[Tuple[str, bytes, str]]:
    """
    Validate based on TOOLS_META: count, size, and MIME whitelist, and run clamav scan.
    Returns list of tuples: (filename, bytes, detected_mime)
    """
    if slug not in TOOLS_META:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool = TOOLS_META[slug]

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > tool.maxInputFiles:
        raise HTTPException(status_code=400, detail=f"Too many files. Max allowed: {tool.maxInputFiles}")

    validated = []
    for f in files:
        buffer = await read_upload_file_bytes(f)
        if not buffer:
            raise HTTPException(status_code=400, detail=f"Empty file {f.filename}")

        # size limit per-tool or global
        max_size = tool.maxSizeBytes or settings.max_upload_bytes
        if len(buffer) > max_size:
            raise HTTPException(status_code=413, detail=f"File too large: {f.filename}")

        mime_type = detect_mime_type(buffer, f.filename)
        if mime_type not in tool.allowedMimeTypes:
            raise HTTPException(status_code=415, detail=f"Invalid MIME type for {f.filename}: {mime_type}")

        # Run ClamAV scan
        ok, reason = await clamav_service.scan_buffer(buffer)
        if not ok:
            raise HTTPException(status_code=400, detail=f"Malware detected in {f.filename}: {reason}")

        validated.append((f.filename, buffer, mime_type))

    return validated
