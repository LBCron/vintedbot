"""
Async PostgreSQL Database with Connection Pooling
Replaces SQLite for production scalability

All connections managed with proper context managers to prevent leaks.
"""
import os
import asyncpg
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlmodel import SQLModel
from backend.utils.logger import logger

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///backend/data/vbs.db"  # Fallback to SQLite for development
)

# Convert sync postgres:// to async postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Engine configuration
ENGINE_CONFIG = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
    "future": True,
}

# Connection pool configuration for PostgreSQL
if "postgresql" in DATABASE_URL:
    ENGINE_CONFIG.update({
        "poolclass": QueuePool,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,  # Verify connections before using
    })
    logger.info(f"🐘 PostgreSQL pool: size={ENGINE_CONFIG['pool_size']}, max_overflow={ENGINE_CONFIG['max_overflow']}")
else:
    # SQLite doesn't support connection pooling
    ENGINE_CONFIG["poolclass"] = NullPool
    logger.info("💾 Using SQLite (development mode)")

# Create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    **ENGINE_CONFIG
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize database schema"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Database schema initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("✅ Database connections closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session with automatic cleanup

    Usage:
        async with get_db_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with get_db_session() as session:
        yield session


# ============================================================================
# ASYNCPG CONNECTION POOL (for direct PostgreSQL access)
# ============================================================================
_asyncpg_pool: Optional[asyncpg.Pool] = None


async def init_asyncpg_pool():
    """Initialize raw asyncpg connection pool for direct DB access"""
    global _asyncpg_pool

    if _asyncpg_pool is not None:
        return _asyncpg_pool

    # Extract asyncpg-compatible URL from SQLAlchemy URL
    if "postgresql" not in DATABASE_URL:
        logger.warning("asyncpg pool only supported for PostgreSQL")
        return None

    # Convert SQLAlchemy URL to asyncpg format
    asyncpg_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    try:
        _asyncpg_pool = await asyncpg.create_pool(
            asyncpg_url,
            min_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_size=int(os.getenv("DB_POOL_SIZE", "10")) + int(os.getenv("DB_MAX_OVERFLOW", "20")),
            timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            command_timeout=60.0,  # 60s query timeout
            max_inactive_connection_lifetime=int(os.getenv("DB_POOL_RECYCLE", "3600")),
        )
        logger.info(f"✅ asyncpg pool initialized (size={_asyncpg_pool.get_size()}/{_asyncpg_pool.get_max_size()})")
        return _asyncpg_pool
    except Exception as e:
        logger.error(f"❌ Failed to create asyncpg pool: {e}")
        return None


async def get_db_pool():
    """
    FastAPI dependency for raw asyncpg connection pool

    Usage:
        @router.get("/users")
        async def get_users(db = Depends(get_db_pool)):
            async with db.acquire() as conn:
                users = await conn.fetch("SELECT * FROM users")
                return users

    IMPORTANT: Always use `async with db.acquire()` context manager
    to ensure connections are properly released back to the pool.
    """
    global _asyncpg_pool

    if _asyncpg_pool is None:
        _asyncpg_pool = await init_asyncpg_pool()

    if _asyncpg_pool is None:
        raise RuntimeError("Database pool not initialized")

    return _asyncpg_pool


async def close_asyncpg_pool():
    """Close asyncpg connection pool"""
    global _asyncpg_pool
    if _asyncpg_pool:
        await _asyncpg_pool.close()
        _asyncpg_pool = None
        logger.info("✅ asyncpg pool closed")


# Health check query
async def check_db_health() -> dict:
    """Check database connectivity and pool stats"""
    try:
        async with get_db_session() as session:
            await session.execute("SELECT 1")

        stats = {
            "status": "healthy",
            "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "sqlite",
        }

        # Add pool stats for PostgreSQL
        if "postgresql" in DATABASE_URL:
            pool = engine.pool
            stats.update({
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total_connections": pool.size() + pool.overflow(),
            })

            # Add asyncpg pool stats if available
            if _asyncpg_pool:
                stats.update({
                    "asyncpg_pool_size": _asyncpg_pool.get_size(),
                    "asyncpg_pool_max": _asyncpg_pool.get_max_size(),
                })

        return stats
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
