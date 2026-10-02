"""
Analytics API routes.

GET  /dashboard  — Full dashboard data
GET  /revenue    — Revenue analytics
GET  /products   — Product performance
GET  /regions    — Regional performance
POST /query      — Custom analytics query
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.user import User
from app.schemas.analytics import (
    DashboardResponse,
    ProductPerformanceResponse,
    RegionPerformanceResponse,
    RevenueResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete dashboard data (KPIs, charts, recent orders)."""
    service = AnalyticsService(db)
    return await service.get_dashboard_data()


@router.get("/revenue")
async def get_revenue(
    months: int = 12,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get revenue analytics with monthly breakdown."""
    service = AnalyticsService(db)
    growth = await service.get_revenue_growth()
    monthly = await service.get_monthly_revenue(months)
    total = await service.get_total_revenue()

    return {
        "total_revenue": total,
        "previous_period_revenue": growth["previous_revenue"],
        "growth_percent": growth["growth_percent"],
        "monthly_data": monthly,
    }


@router.get("/products")
async def get_products(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get product performance analytics."""
    service = AnalyticsService(db)
    products = await service.get_product_performance()
    return {
        "products": products,
        "total_products": len(products),
    }


@router.get("/regions")
async def get_regions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get regional performance analytics."""
    service = AnalyticsService(db)
    regions = await service.get_revenue_by_region()
    return {"regions": regions}
