# app/services/clamav_service.py
# Wrapper around ClamAV scanning. Uses python-clamd to connect to clamd over TCP.

import logging
import asyncio
from typing import Tuple
import clamd
from app.config import settings

logger = logging.getLogger("clamav")


async def scan_buffer(buffer: bytes) -> Tuple[bool, str]:
    """
    Scan a bytes buffer with ClamAV. Returns (ok, reason)
    If CLAMAV_ENABLED is false, skip scan and return OK.
    This function runs blocking clamd client in a ThreadPool since clamd is sync.
    """
    if not settings.clamav_enabled:
        logger.info("ClamAV disabled by configuration")
        return True, ""

    def _scan():
        try:
            cd = clamd.ClamdNetworkSocket(settings.clamav_tcp_host, settings.clamav_tcp_port)
            # clamd scan_stream may return None if no virus
            result = cd.instream(io=buffer_stream())
            # result is a dict mapping stream: (status, virusname)
            # but instream wrapper usage below provides detail.
        except Exception as e:
            raise

    # Use a small helper because clamd's instream expects a file-like object
    import io

    def buffer_stream():
        return io.BytesIO(buffer)

    loop = asyncio.get_running_loop()
    try:
        res = await loop.run_in_executor(None, lambda: _sync_scan(buffer))
        # _sync_scan returns (ok, reason)
        return res
    except Exception as e:
        logger.error("ClamAV scanning error: %s", e)
        # In case of scan failure, be conservative: reject uploads or allow?
        # Here we choose to reject to prioritize safety.
        return False, f"ClamAV error: {e}"


def _sync_scan(buffer: bytes):
    """
    Synchronous worker scanning function used in threadpool.
    """
    import io

    cd = clamd.ClamdNetworkSocket(settings.clamav_tcp_host, settings.clamav_tcp_port)
    # instream returns a dict keyed by 'stream'
    try:
        res = cd.instream(io.BytesIO(buffer))
    except Exception as e:
        # If scanning TCP failed, raise for caller to handle
        raise

    # res looks like {'stream': ('OK', None)} or {'stream': ('FOUND', 'Eicar-Test-Signature')}
    if not res:
        # treat as OK
        return True, ""
    val = res.get("stream")
    if not val:
        return True, ""
    status = val[0]
    if status == "OK":
        return True, ""
    else:
        return False, val[1] or "infected"
