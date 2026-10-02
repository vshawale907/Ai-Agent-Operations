"""
Structured logging setup.

Logs request IDs, user IDs, agent execution, SQL timing, and errors.
Never logs passwords, API keys, or JWT secrets.
"""

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from app.core.config import settings

# Context variable for request-scoped data
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[int]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that includes request_id and user_id."""

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_ctx.get("--")
        record.user_id = user_id_ctx.get("--")
        return super().format(record)


def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.app_debug else logging.INFO

    formatter = StructuredFormatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "req=%(request_id)s | user=%(user_id)s | "
            "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Suppress noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())[:8]
