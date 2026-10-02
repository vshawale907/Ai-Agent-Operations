"""
Pydantic schemas for structured agent outputs, citations, anomalies, and reports.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Source reference for retrieved information."""

    source_type: Literal["database", "document", "analytics"] = Field(
        ..., description="Data origin (database table, document file, or computed analytics)"
    )
    title: str = Field(..., description="Document filename or database table name")
    page_number: Optional[int] = Field(None, description="Page number if available")
    chunk_index: Optional[int] = Field(None, description="Chunk index if document")
    excerpt: Optional[str] = Field(None, description="Relevant supporting text or SQL expression")
    reference: str = Field(..., description="Human-readable citation tag")


class ChartSpec(BaseModel):
    """Specification for dynamic charting in frontend."""

    chart_type: Literal["bar", "line", "pie", "donut", "table"] = "bar"
    title: str
    data: List[Dict[str, Any]]
    x_key: Optional[str] = None
    y_key: Optional[str] = None
    keys: Optional[List[str]] = None


class AnomalyItem(BaseModel):
    """Individual statistical business anomaly."""

    metric: str
    period: str
    actual_value: float
    expected_value: float
    deviation_percent: float
    z_score: float
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str


class AnomalyReport(BaseModel):
    """Collection of detected anomalies across business metrics."""

    anomalies: List[AnomalyItem]
    detected_count: int
    analyzed_periods: int
    summary: str


class AgentResponse(BaseModel):
    """Unified structured response from the multi-agent system."""

    answer: str
    intent: Literal["BUSINESS_DATA", "DOCUMENT_KNOWLEDGE", "HYBRID", "GENERAL"]
    confidence: float = 0.95
    data_sources: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    chart: Optional[ChartSpec] = None
    table_data: Optional[List[Dict[str, Any]]] = None
    sql_query: Optional[str] = None
    execution_time_ms: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)


class ExecutiveReport(BaseModel):
    """Structured executive monthly/quarterly business intelligence report."""

    title: str
    period: str
    generated_at: str
    executive_summary: str
    revenue_performance: str
    customer_performance: str
    product_performance: str
    expense_performance: str
    anomalies_summary: str
    key_insights: List[str]
    identified_risks: List[str]
    investigation_recommendations: List[str]
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)
