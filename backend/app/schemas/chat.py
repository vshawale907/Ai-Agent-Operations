"""
Chat and AI agent Pydantic schemas.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """User chat message request."""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, v: str) -> str:
        """Strip whitespace and reject blank/whitespace-only messages."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace-only.")
        return stripped


class ChartData(BaseModel):
    """Structured chart data for frontend rendering."""
    chart_type: str = Field(..., description="line, bar, pie, donut, table")
    title: str
    data: List[Dict[str, Any]]
    x_key: Optional[str] = None
    y_key: Optional[str] = None
    keys: Optional[List[str]] = None


class ChatMetadata(BaseModel):
    """Metadata about the AI response."""
    sql_query: Optional[str] = None
    execution_time_ms: Optional[float] = None
    data_sources: Optional[List[str]] = None
    intent: Optional[str] = None
    row_count: Optional[int] = None


class ChatResponse(BaseModel):
    """AI chat response."""
    message: str
    chart_data: Optional[ChartData] = None
    table_data: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[ChatMetadata] = None
    error: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
