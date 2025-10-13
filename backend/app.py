import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from backend.routes import ingest, listings, pricing, export, stats, bonus, import_route
from backend.jobs.scheduler import start_scheduler, stop_scheduler

load_dotenv()


def ok(data: dict | list, status_code: int = 200):
    """Helper function for standardized JSON responses"""
    return JSONResponse(content=data, status_code=status_code)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting VintedBot Backend...")
    start_scheduler()
    yield
    print("🛑 Shutting down VintedBot Backend...")
    stop_scheduler()


allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://*.lovable.dev",
        "https://*.lovable.app",
    ]

app = FastAPI(
    title=os.getenv("API_TITLE", "VintedBot API"),
    description=os.getenv("API_DESCRIPTION", "AI-powered clothing resale assistant API"),
    version=os.getenv("API_VERSION", "1.0.0"),
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != [""] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(listings.router)
app.include_router(pricing.router)
app.include_router(export.router)
app.include_router(stats.router)
app.include_router(bonus.router)
app.include_router(import_route.router)


@app.get("/")
async def root():
    return {
        "message": "VintedBot API is running!",
        "docs": "/docs",
        "redoc": "/redoc"
    }
