import logging
import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing your specific routes and services
from app.routes import tools, jobs, health
from app.config import settings
from app.services import storage, queue as queue_service

# Logging configuration
logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("nano-convert")

app = FastAPI(title="Nano Convert - Backend", version="1.0.0")

# Proper CORS Setup to allow your frontend link
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://nano-convert-frontend.pages.dev",
        "https://nano-convert-frontend.pages.dev/", # Adding slash for safety
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # English: Initializing all backend services (MongoDB, Redis, Cloudinary)
    logger.info("Starting app, initializing services...")
    try:
        # 1. Initialize Redis (Using your Render Redis link)
        await queue_service.init_redis_connections()
        logger.info("Redis connection established.")

        # 2. Cloudinary & MongoDB are usually handled via Env Variables
        # S3 line removed as requested (using Cloudinary now)
        logger.info("MongoDB and Cloudinary services are ready.")
        
        logger.info("All services initialized successfully.")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    # Clean up connections
    await queue_service.close_redis_connections()

# API Routes with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

# Root path for Health Check
@app.get("/", include_in_schema=False)
async def root():
    return {"ok": True, "service": "nano-convert-backend"}
        
