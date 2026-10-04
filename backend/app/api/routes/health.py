"""
Health check API route.

Reports connectivity status for Database and Redis cache.
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.database import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health_check():
    """Application health check with database and Redis connectivity tests."""
    # --- Database check ---
    db_status = "healthy"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # --- Redis check ---
    redis_status = "connected"
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
    except Exception as e:
        redis_status = f"fallback_mode (in-memory): {str(e)}"

    overall = "healthy" if db_status == "healthy" and redis_status == "connected" else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "redis": redis_status,
        "service": "AI Business Operations Agent",
        "version": "1.0.0",
    }

