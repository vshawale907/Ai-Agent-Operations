"""
Analytics Pydantic schemas for dashboard and query endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DashboardKPI(BaseModel):
    """Single KPI metric."""
    label: str
    value: Any
    change_percent: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    prefix: Optional[str] = None  # e.g., "₹"
    suffix: Optional[str] = None  # e.g., "%"


class DashboardResponse(BaseModel):
    """Full dashboard data."""
    kpis: List[DashboardKPI]
    monthly_revenue: List[Dict[str, Any]]
    revenue_by_region: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    revenue_by_category: List[Dict[str, Any]]
    expense_trend: List[Dict[str, Any]]
    recent_orders: List[Dict[str, Any]]


class RevenueResponse(BaseModel):
    """Revenue analytics response."""
    total_revenue: float
    previous_period_revenue: float
    growth_percent: float
    monthly_data: List[Dict[str, Any]]


class ProductPerformanceResponse(BaseModel):
    """Product analytics."""
    products: List[Dict[str, Any]]
    total_products: int


class RegionPerformanceResponse(BaseModel):
    """Regional analytics."""
    regions: List[Dict[str, Any]]


class AnalyticsQueryRequest(BaseModel):
    """Custom analytics query request."""
    query: str = Field(..., min_length=1)
    time_period: Optional[str] = None  # "last_month", "last_quarter", "ytd", "last_year"
