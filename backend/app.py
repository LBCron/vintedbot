import os
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.db import create_tables
from backend.jobs import start_scheduler, stop_scheduler
from backend.utils.logger import logger, log_request
from backend.routes import auth, messages, publish, listings, offers, orders, health, ws
from backend.api.v1.routers import ingest, health as health_v1, vinted
from backend.settings import settings

load_dotenv()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting VintedBot Connector Backend...")
    
    # Initialize database
    create_tables()
    
    # Start scheduler
    start_scheduler()
    
    logger.info("✅ Backend ready on port 5000")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down VintedBot Connector...")
    stop_scheduler()


# Create FastAPI app
app = FastAPI(
    title="VintedBot Connector API",
    description="Backend connector for Vinted automation with messaging, publishing, and session management",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id"]
)

# GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1024)


# Request ID and logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id
    )
    
    response.headers["x-request-id"] = request_id
    return response


# Include routers (existing routes)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(publish.router)
app.include_router(listings.router)
app.include_router(offers.router)
app.include_router(orders.router)
app.include_router(ws.router)

# Include API v1 routers
app.include_router(ingest.router, prefix="/api/v1", tags=["api-v1"])
app.include_router(health_v1.router, prefix="/api/v1", tags=["api-v1"])
app.include_router(vinted.router, tags=["vinted"])

# Alias for Lovable.dev compatibility (without /api/v1 prefix)
app.include_router(ingest.router, tags=["ingest-alias"])

# Mount static files for uploads and media
try:
    app.mount("/uploads", StaticFiles(directory="backend/data/uploads"), name="uploads")
except:
    pass

if settings.MEDIA_STORAGE == "local":
    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        app.mount(settings.MEDIA_BASE_URL, StaticFiles(directory=settings.MEDIA_ROOT), name="media")
    except Exception as e:
        logger.warning(f"Could not mount media directory: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VintedBot Connector API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "mode": "MOCK" if os.getenv("MOCK_MODE", "true") == "true" else "LIVE"
    }


@app.get("/preview/{job_id}")
async def preview_job(job_id: str):
    """Preview endpoint for manual mode jobs"""
    from backend.db import get_publish_job
    
    job = get_publish_job(job_id)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    
    return {
        "job_id": job.job_id,
        "mode": job.mode,
        "status": job.status,
        "screenshot": job.screenshot_path,
        "logs": job.logs
    }
