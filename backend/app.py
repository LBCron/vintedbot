from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routes import ingest, listings, pricing, export, stats, bonus, import_route
from backend.jobs.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting VintedBot Backend...")
    start_scheduler()
    yield
    print("🛑 Shutting down VintedBot Backend...")
    stop_scheduler()


app = FastAPI(
    title="VintedBot API",
    description="AI-powered clothing resale assistant API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
