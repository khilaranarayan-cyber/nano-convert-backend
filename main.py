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
    logger.info("Starting app, initializing services...")
    try:
        # 1. Initialize Redis
        await queue_service.init_redis_connections()
        logger.info("Redis connection established.")

        # 2. Cloudinary & MongoDB
        logger.info("MongoDB and Cloudinary services are ready.")
        
        logger.info("All services initialized successfully.")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    await queue_service.close_redis_connections()

# API Routes - PREFIX "/api" REMOVED
app.include_router(health.router)
app.include_router(tools.router)
app.include_router(jobs.router)

# Root path for Health Check
@app.get("/", include_in_schema=False)
async def root():
    return {"ok": True, "service": "nano-convert-backend"}
