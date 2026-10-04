"""
FastAPI application entry point.

Configures middleware, routes, and lifecycle events.
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analytics, auth, chat, documents, health, reports
from app.core.config import settings, startup_security_check
from app.core.logging import (
    generate_request_id,
    get_logger,
    request_id_ctx,
    setup_logging,
    user_id_ctx,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    startup_security_check()  # Warn or halt if default JWT secret is still in use
    logger.info("AI Business Operations Agent starting up...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    yield
    logger.info("AI Business Operations Agent shutting down...")


app = FastAPI(
    title="AI Business Operations Agent",
    description=(
        "AI-powered business analytics platform. Ask natural language questions "
        "about revenue, orders, products, customers, and more."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request ID Middleware ---
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Inject request ID and track response time."""
    req_id = generate_request_id()
    request_id_ctx.set(req_id)

    start_time = time.time()
    response: Response = await call_next(request)
    elapsed_ms = (time.time() - start_time) * 1000

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"

    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({elapsed_ms:.1f}ms)"
    )
    return response


# --- Routes ---
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chat"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(health.router, prefix="/api", tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    """API root — service information."""
    return {
        "service": "AI Business Operations Agent",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
    }
