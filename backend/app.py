import os
import time
import uuid
import tempfile
from pathlib import Path
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

# Configure tempfile to use our custom temp directory instead of /tmp
from backend.settings import settings as app_settings
TEMP_DIR = Path(f"{app_settings.DATA_DIR}/temp_uploads")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEMP_DIR)
os.environ["TMPDIR"] = str(TEMP_DIR)

from backend.db import create_tables
from backend.database import init_db
from backend.jobs import start_scheduler, stop_scheduler
from backend.utils.logger import logger, log_request
from backend.routes import auth, messages, publish, listings, offers, orders, health, ws, feedback
from backend.api.v1.routers import (
    ingest, health as health_v1, vinted, bulk, ai, auth as auth_v1, billing,
    analytics, automation, accounts, admin, orders as orders_v1, images, storage,
    payments, webhooks  # MEGA-PROMPT: New premium features (Stripe + Webhooks)
)
from backend.settings import settings

load_dotenv()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting VintedBot Connector Backend...")

    # Register HEIC/HEIF support for PIL
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        logger.info("✅ HEIC/HEIF support registered for PIL")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register HEIC support: {e}")

    # Initialize databases
    create_tables()  # Legacy JSON database
    init_db()  # PostgreSQL database

    # Start scheduler
    start_scheduler()

    logger.info("Backend ready on port 5000")

    yield

    # Shutdown
    logger.info("Shutting down VintedBot Connector...")
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

# CORS middleware - Allow frontend domain
# CRITICAL: Cannot use "*" with credentials=True, must specify exact origin
allowed_origins = os.getenv("ALLOWED_ORIGINS", "https://vintedbot-frontend.fly.dev,https://vintedbot.app,https://www.vintedbot.app,http://localhost:3000,http://localhost:5173")
if allowed_origins == "*":
    # Fallback to specific origin for credentials support
    origins = ["https://vintedbot-frontend.fly.dev", "https://vintedbot.app", "https://www.vintedbot.app", "http://localhost:3000", "http://localhost:5173"]
    allow_origin_regex = None
else:
    origins = [origin.strip() for origin in allowed_origins.split(",")]
    # Add regex pattern for all Lovable domains
    allow_origin_regex = r"https://.*\.lovable(project\.com|\.dev|\.app)"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-request-id"]
)

# GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Handle OPTIONS requests globally (CORS preflight)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600"
        }
    )


# Security: Block direct API access in production (force use of frontend)
# TEMPORARILY DISABLED for debugging - will re-enable once auth works
# @app.middleware("http")
# async def block_direct_api_access(request: Request, call_next):
#     # Middleware disabled for debugging
#     return await call_next(request)


# Request ID and logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    # DEBUG: Log multipart upload details for /bulk/photos/analyze
    if request.url.path == "/bulk/photos/analyze" and request.method == "POST":
        logger.info(f"[DEBUG] Multipart upload detected:")
        logger.info(f"   Content-Type: {request.headers.get('content-type', 'MISSING')}")
        logger.info(f"   Content-Length: {request.headers.get('content-length', 'MISSING')}")
        logger.info(f"   Headers: {dict(request.headers)}")

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
# app.include_router(auth.router)  # Disabled - using new Vinted router with Playwright
app.include_router(messages.router)
app.include_router(publish.router)
app.include_router(listings.router)
app.include_router(offers.router)
app.include_router(orders.router)
app.include_router(ws.router)
app.include_router(feedback.router)

# Include API v1 routers
app.include_router(auth_v1.router, tags=["auth"])  # Auth endpoints (/auth/register, /auth/login, /auth/me)
app.include_router(billing.router, tags=["billing"])  # Billing endpoints (/billing/checkout, /billing/portal, /billing/webhook)
app.include_router(ingest.router, prefix="/api/v1", tags=["api-v1"])
app.include_router(health_v1.router, prefix="/api/v1", tags=["api-v1"])
app.include_router(vinted.router, tags=["vinted"])
app.include_router(bulk.router, tags=["bulk"])
app.include_router(ai.router, tags=["ai"])

# PREMIUM FEATURES (Nov 2025) - Most sophisticated Vinted bot on market!
app.include_router(analytics.router, tags=["analytics"])  # Analytics dashboard (UNIQUE! Not in any competitor)
app.include_router(automation.router, tags=["automation"])  # Auto-bump, auto-follow, auto-messages
app.include_router(accounts.router, tags=["accounts"])  # Multi-account management
app.include_router(orders_v1.router, tags=["orders"])  # Order management & CSV export (Dotb feature)
app.include_router(images.router, tags=["images"])  # Bulk image editing (Dotb feature)
app.include_router(storage.router, prefix="/api", tags=["storage"])  # Multi-tier photo storage (TEMP/HOT/COLD)

# MEGA-PROMPT PREMIUM FEATURES (Nov 2025) - Market Domination Features!
app.include_router(payments.router, tags=["payments"])  # Stripe payments & subscriptions
app.include_router(webhooks.router, tags=["webhooks"])  # External webhooks (Zapier, Make, etc.)

# SUPER-ADMIN FEATURES - DB-based role system with SQL injection protection
app.include_router(admin.router, tags=["admin"])  # Admin panel (secured - Nov 2025)

# Alias for Lovable.dev compatibility (without /api/v1 prefix)
app.include_router(ingest.router, tags=["ingest-alias"])

# Mount static files for uploads and media
try:
    app.mount("/uploads", StaticFiles(directory="backend/data/uploads"), name="uploads")
except:
    pass

# Mount temp photos for Vinted uploads
try:
    temp_photos_dir = f"{settings.DATA_DIR}/temp_photos"
    os.makedirs(temp_photos_dir, exist_ok=True)
    app.mount("/temp_photos", StaticFiles(directory=temp_photos_dir), name="temp_photos")
except Exception as e:
    logger.warning(f"Could not mount temp_photos directory: {e}")

if settings.MEDIA_STORAGE == "local":
    try:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        app.mount(settings.MEDIA_BASE_URL, StaticFiles(directory=settings.MEDIA_ROOT), name="media")
    except Exception as e:
        logger.warning(f"Could not mount media directory: {e}")


@app.get("/api")
async def api_root():
    """API info endpoint"""
    return {
        "message": "VintedBot Connector API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "mode": "MOCK" if os.getenv("MOCK_MODE", "true") == "true" else "LIVE"
    }


# Mount frontend (SPA - Single Page Application)
try:
    from fastapi.responses import FileResponse
    frontend_dir = Path("frontend/dist")

    if frontend_dir.exists():
        logger.info(f"✅ Frontend found at {frontend_dir}, serving SPA...")

        # Mount static assets
        app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="frontend-assets")

        # Serve index.html for root and all SPA routes
        @app.get("/")
        @app.get("/login")
        @app.get("/register")
        @app.get("/dashboard")
        @app.get("/upload")
        @app.get("/drafts")
        @app.get("/drafts/{draft_id}")
        @app.get("/analytics")
        @app.get("/automation")
        @app.get("/accounts")
        @app.get("/admin")
        @app.get("/settings")
        async def serve_spa():
            """Serve React SPA"""
            return FileResponse(frontend_dir / "index.html")

        logger.info("✅ Frontend successfully mounted")
    else:
        logger.warning(f"⚠️ Frontend not found at {frontend_dir} - only API will be available")

        @app.get("/")
        async def root():
            """Root endpoint (API only mode)"""
            return {
                "message": "VintedBot Connector API (Frontend not built)",
                "version": "1.0.0",
                "docs": "/docs",
                "health": "/health",
                "mode": "MOCK" if os.getenv("MOCK_MODE", "true") == "true" else "LIVE"
            }
except Exception as e:
    logger.error(f"❌ Failed to mount frontend: {e}")

    @app.get("/")
    async def root():
        """Root endpoint (fallback)"""
        return {
            "message": "VintedBot Connector API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "error": f"Frontend failed to load: {str(e)}"
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
