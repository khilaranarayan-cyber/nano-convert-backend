# main.py
# Entry point for the FastAPI app. Start with: uvicorn main:app

import logging
import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import tools, jobs, health
from app.config import settings
from app.services import storage, queue as queue_service

# Basic logging
logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("nano-convert")

app = FastAPI(title="Nano Convert - Backend", version="1.0.0")

# CORS is minimal: frontend should be configured in production through a gateway/CDN
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Initialize connections (Redis async, S3 boto3 clients)
    logger.info("Starting app, initializing services...")
    await storage.init_s3_client()
    await queue_service.init_redis_connections()
    logger.info("Services initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    # Clean up
    try:
        await storage.close_s3_client()
    except Exception:
        pass
    await queue_service.close_redis_connections()


# include routers
app.include_router(health.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

# Root
@app.get("/", include_in_schema=False)
async def root():
    return {"ok": True, "service": "nano-convert-backend"}