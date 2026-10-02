"""
Health check and documents API routes.
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health_check():
    """Application health check with database connectivity test."""
    db_status = "healthy"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "service": "AI Business Operations Agent",
        "version": "1.0.0",
    }
