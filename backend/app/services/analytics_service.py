"""
Analytics service.

Provides reusable analytics queries for the dashboard and agent tools.
All queries are read-only SELECTs against the business database.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Reusable business analytics engine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Revenue Metrics
    # =========================================================================

    async def get_total_revenue(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> float:
        """Get total revenue for a date range."""
        query = "SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE status != 'cancelled'"
        params: Dict[str, Any] = {}
        if start_date:
            query += " AND order_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND order_date <= :end_date"
            params["end_date"] = end_date
        result = await self.db.execute(text(query), params)
        return float(result.scalar() or 0)

    async def get_revenue_growth(self) -> Dict[str, Any]:
        """Calculate month-over-month revenue growth."""
        today = date.today()
        current_month_start = today.replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        current_rev = await self.get_total_revenue(current_month_start, today)
        prev_rev = await self.get_total_revenue(prev_month_start, prev_month_end)

        growth = 0.0
        if prev_rev > 0:
            growth = ((current_rev - prev_rev) / prev_rev) * 100

        return {
            "current_revenue": current_rev,
            "previous_revenue": prev_rev,
            "growth_percent": round(growth, 2),
            "trend": "up" if growth > 0 else "down" if growth < 0 else "stable",
        }

    async def get_monthly_revenue(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly revenue for the last N months."""
        query = text("""
            SELECT
                TO_CHAR(order_date, 'YYYY-MM') AS month,
                TO_CHAR(order_date, 'Mon YYYY') AS month_label,
                COALESCE(SUM(total_amount), 0) AS revenue,
                COUNT(*) AS order_count
            FROM orders
            WHERE status != 'cancelled'
              AND order_date >= CURRENT_DATE - make_interval(months => :months)
            GROUP BY TO_CHAR(order_date, 'YYYY-MM'), TO_CHAR(order_date, 'Mon YYYY')
            ORDER BY month
        """)
        result = await self.db.execute(query, {"months": int(months)})
        return [
            {
                "month": row.month,
                "month_label": row.month_label,
                "revenue": float(row.revenue),
                "order_count": row.order_count,
            }
            for row in result.fetchall()
        ]

    # =========================================================================
    # Order Metrics
    # =========================================================================

    async def get_order_count(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> int:
        """Get total order count."""
        query = "SELECT COUNT(*) FROM orders WHERE status != 'cancelled'"
        params: Dict[str, Any] = {}
        if start_date:
            query += " AND order_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND order_date <= :end_date"
            params["end_date"] = end_date
        result = await self.db.execute(text(query), params)
        return int(result.scalar() or 0)

    async def get_average_order_value(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> float:
        """Get average order value."""
        query = "SELECT COALESCE(AVG(total_amount), 0) FROM orders WHERE status != 'cancelled'"
        params: Dict[str, Any] = {}
        if start_date:
            query += " AND order_date >= :start_date"
            params["start_date"] = start_date
        if end_date:
            query += " AND order_date <= :end_date"
            params["end_date"] = end_date
        result = await self.db.execute(text(query), params)
        return round(float(result.scalar() or 0), 2)

    # =========================================================================
    # Customer Metrics
    # =========================================================================

    async def get_customer_count(self) -> int:
        """Get total active customer count."""
        result = await self.db.execute(
            text("SELECT COUNT(*) FROM customers WHERE is_active = true")
        )
        return int(result.scalar() or 0)

    async def get_customer_segments(self) -> List[Dict[str, Any]]:
        """Get customer distribution by segment."""
        result = await self.db.execute(text("""
            SELECT segment, COUNT(*) AS count
            FROM customers
            WHERE is_active = true
            GROUP BY segment
            ORDER BY count DESC
        """))
        return [{"segment": row.segment, "count": row.count} for row in result.fetchall()]

    # =========================================================================
    # Product Performance
    # =========================================================================

    async def get_top_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top products by revenue."""
        result = await self.db.execute(text(f"""
            SELECT
                p.name,
                p.category,
                SUM(oi.total_price) AS revenue,
                SUM(oi.quantity) AS units_sold,
                COUNT(DISTINCT oi.order_id) AS order_count
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status != 'cancelled'
            GROUP BY p.id, p.name, p.category
            ORDER BY revenue DESC
            LIMIT {int(limit)}
        """))
        return [
            {
                "name": row.name,
                "category": row.category,
                "revenue": float(row.revenue),
                "units_sold": int(row.units_sold),
                "order_count": row.order_count,
            }
            for row in result.fetchall()
        ]

    async def get_product_performance(self) -> List[Dict[str, Any]]:
        """Get all products with performance metrics."""
        result = await self.db.execute(text("""
            SELECT
                p.name,
                p.category,
                p.unit_price,
                p.unit_cost,
                COALESCE(SUM(oi.total_price), 0) AS revenue,
                COALESCE(SUM(oi.quantity), 0) AS units_sold,
                COALESCE(SUM(oi.total_price) - SUM(oi.quantity * p.unit_cost), 0) AS profit
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.id AND o.status != 'cancelled'
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.category, p.unit_price, p.unit_cost
            ORDER BY revenue DESC
        """))
        return [
            {
                "name": row.name,
                "category": row.category,
                "unit_price": float(row.unit_price),
                "unit_cost": float(row.unit_cost),
                "revenue": float(row.revenue),
                "units_sold": int(row.units_sold),
                "profit": float(row.profit),
            }
            for row in result.fetchall()
        ]

    # =========================================================================
    # Regional Performance
    # =========================================================================

    async def get_revenue_by_region(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by region."""
        result = await self.db.execute(text("""
            SELECT
                region,
                SUM(total_amount) AS revenue,
                COUNT(*) AS order_count,
                AVG(total_amount) AS avg_order_value
            FROM orders
            WHERE status != 'cancelled'
            GROUP BY region
            ORDER BY revenue DESC
        """))
        return [
            {
                "region": row.region,
                "revenue": float(row.revenue),
                "order_count": row.order_count,
                "avg_order_value": round(float(row.avg_order_value), 2),
            }
            for row in result.fetchall()
        ]

    # =========================================================================
    # Category Performance
    # =========================================================================

    async def get_revenue_by_category(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by product category."""
        result = await self.db.execute(text("""
            SELECT
                p.category,
                SUM(oi.total_price) AS revenue,
                SUM(oi.quantity) AS units_sold,
                COUNT(DISTINCT o.id) AS order_count
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status != 'cancelled'
            GROUP BY p.category
            ORDER BY revenue DESC
        """))
        return [
            {
                "category": row.category,
                "revenue": float(row.revenue),
                "units_sold": int(row.units_sold),
                "order_count": row.order_count,
            }
            for row in result.fetchall()
        ]

    # =========================================================================
    # Expense Analysis
    # =========================================================================

    async def get_expense_trend(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly expense trend."""
        query = text("""
            SELECT
                TO_CHAR(expense_date, 'YYYY-MM') AS month,
                TO_CHAR(expense_date, 'Mon YYYY') AS month_label,
                SUM(amount) AS total_expense
            FROM expenses
            WHERE expense_date >= CURRENT_DATE - make_interval(months => :months)
            GROUP BY TO_CHAR(expense_date, 'YYYY-MM'), TO_CHAR(expense_date, 'Mon YYYY')
            ORDER BY month
        """)
        result = await self.db.execute(query, {"months": int(months)})
        return [
            {
                "month": row.month,
                "month_label": row.month_label,
                "total_expense": float(row.total_expense),
            }
            for row in result.fetchall()
        ]

    async def get_expenses_by_category(self) -> List[Dict[str, Any]]:
        """Get expense breakdown by category."""
        result = await self.db.execute(text("""
            SELECT
                category,
                SUM(amount) AS total,
                COUNT(*) AS entry_count
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        """))
        return [
            {"category": row.category, "total": float(row.total), "count": row.entry_count}
            for row in result.fetchall()
        ]

    # =========================================================================
    # Dashboard Aggregate
    # =========================================================================

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data needed for the dashboard in one call."""
        today = date.today()
        current_month_start = today.replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        # KPIs
        total_revenue = await self.get_total_revenue()
        current_rev = await self.get_total_revenue(current_month_start, today)
        prev_rev = await self.get_total_revenue(prev_month_start, prev_month_end)
        growth = await self.get_revenue_growth()
        total_orders = await self.get_order_count()
        aov = await self.get_average_order_value()
        customer_count = await self.get_customer_count()

        # Previous period comparisons
        prev_orders = await self.get_order_count(prev_month_start, prev_month_end)
        curr_orders = await self.get_order_count(current_month_start, today)
        order_growth = ((curr_orders - prev_orders) / max(prev_orders, 1)) * 100

        # Charts
        monthly_revenue = await self.get_monthly_revenue(12)
        revenue_by_region = await self.get_revenue_by_region()
        top_products = await self.get_top_products(10)
        revenue_by_category = await self.get_revenue_by_category()
        expense_trend = await self.get_expense_trend(12)

        # Recent orders
        result = await self.db.execute(text("""
            SELECT o.id, c.name AS customer, o.total_amount, o.order_date,
                   o.status, o.region
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            ORDER BY o.order_date DESC
            LIMIT 10
        """))
        recent_orders = [
            {
                "id": row.id,
                "customer": row.customer,
                "amount": float(row.total_amount),
                "date": str(row.order_date),
                "status": row.status,
                "region": row.region,
            }
            for row in result.fetchall()
        ]

        return {
            "kpis": [
                {
                    "label": "Total Revenue",
                    "value": round(total_revenue, 2),
                    "change_percent": round(growth["growth_percent"], 2),
                    "trend": growth["trend"],
                    "prefix": "₹",
                },
                {
                    "label": "Total Orders",
                    "value": total_orders,
                    "change_percent": round(order_growth, 2),
                    "trend": "up" if order_growth > 0 else "down",
                },
                {
                    "label": "Customers",
                    "value": customer_count,
                    "trend": "up",
                },
                {
                    "label": "Avg Order Value",
                    "value": aov,
                    "prefix": "₹",
                    "trend": "stable",
                },
                {
                    "label": "Revenue Growth",
                    "value": round(growth["growth_percent"], 2),
                    "suffix": "%",
                    "trend": growth["trend"],
                },
            ],
            "monthly_revenue": monthly_revenue,
            "revenue_by_region": revenue_by_region,
            "top_products": top_products,
            "revenue_by_category": revenue_by_category,
            "expense_trend": expense_trend,
            "recent_orders": recent_orders,
        }


class _AnalyticsServiceProxy:
    """Singleton proxy that enables calling `analytics_service.<method>(db, *args, **kwargs)`."""

    def __getattr__(self, name: str):
        def method(db: AsyncSession, *args, **kwargs):
            service = AnalyticsService(db)
            attr = getattr(service, name)
            return attr(*args, **kwargs)
        return method


analytics_service = _AnalyticsServiceProxy()
