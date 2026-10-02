"""
Async database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# --- Async Engine (for application runtime) ---
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- Sync Engine (for migrations and seeding) ---
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.app_debug,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(bind=sync_engine)


# --- Declarative Base ---
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# --- Dependency ---
async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
