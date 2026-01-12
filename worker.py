# worker.py
# RQ worker process entry point for processing enqueued jobs.
# Run this in a separate process ideally: python worker.py
# Render: create a worker service using the same file.

import logging
import os
from rq import Worker, Connection
from app.services import queue
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rq.worker")

if __name__ == "__main__":
    # Ensure Redis connections initialized
    queue.init_redis_connections()
    redis_conn = queue.get_sync_redis()
    with Connection(redis_conn):
        worker = Worker(["jobs"])
        logger.info("Starting RQ worker. Listening on 'jobs' queue...")
        worker.work()