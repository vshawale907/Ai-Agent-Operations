"""
Explicit callable business tools for LLM agent orchestration.

All tools return structured dictionaries and Pydantic-compatible objects,
enabling deterministic mathematical calculation without LLM arithmetic errors.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.database import AsyncSessionLocal
from app.rag.service import rag_service
from app.services.analytics_deep_service import deep_analytics
from app.services.analytics_service import analytics_service
from app.services.anomaly_service import anomaly_service
from app.utils.sql_validator import validate_sql

logger = get_logger(__name__)


async def get_revenue_metrics(months: int = 12) -> Dict[str, Any]:
    """Retrieve monthly revenue trends and MoM growth trajectory."""
    async with AsyncSessionLocal() as session:
        growth = await deep_analytics.get_growth_trajectory(session)
        monthly = await analytics_service.get_monthly_revenue(session, months)
        return {
            "monthly_revenue": monthly,
            "growth_metrics": growth,
        }


async def get_top_products_metrics(limit: int = 5) -> Dict[str, Any]:
    """Retrieve top performing products, units sold, and margin profitability."""
    async with AsyncSessionLocal() as session:
        top_prods = await analytics_service.get_top_products(session, limit)
        margins = await deep_analytics.get_product_margins_and_declines(session)
        return {
            "top_products": top_prods,
            "overall_avg_margin": margins.get("overall_avg_margin"),
            "category_margins": margins.get("category_margins"),
        }


async def get_product_margins_and_declines(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """Retrieve product gross margin and declining product categories."""
    if session is not None:
        return await deep_analytics.get_product_margins_and_declines(session)
    async with AsyncSessionLocal() as s:
        return await deep_analytics.get_product_margins_and_declines(s)


async def get_region_performance_metrics() -> List[Dict[str, Any]]:
    """Retrieve revenue, orders, and average order value broken down by geography."""
    async with AsyncSessionLocal() as session:
        return await analytics_service.get_revenue_by_region(session)


async def get_customer_metrics() -> Dict[str, Any]:
    """Retrieve Customer LTV, repeat rates, inactive accounts, and churn indicators."""
    async with AsyncSessionLocal() as session:
        return await deep_analytics.get_customer_intelligence(session)


async def get_expense_metrics() -> Dict[str, Any]:
    """Retrieve operating expenses, cost efficiency, and expense-to-revenue ratio."""
    async with AsyncSessionLocal() as session:
        return await deep_analytics.get_expense_and_efficiency_metrics(session)


async def detect_anomalies_tool(lookback_months: int = 12) -> Dict[str, Any]:
    """Detect statistical anomalies across revenue, orders, expenses, and support."""
    async with AsyncSessionLocal() as session:
        rep = await anomaly_service.detect_all_anomalies(session, lookback_months)
        return rep.model_dump()


async def search_documents_tool(user_id: int, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """Perform semantic vector retrieval on the user's company documents."""
    async with AsyncSessionLocal() as session:
        return await rag_service.search_documents(
            db=session,
            user_id=user_id,
            query=query,
            top_k=top_k,
        )


from decimal import Decimal

async def execute_safe_sql_tool(sql_query: str) -> Dict[str, Any]:
    """Validate and execute a read-only SQL query against the database."""
    # Strict AST validation
    val = validate_sql(sql_query)
    if not val.is_valid:
        return {
            "success": False,
            "error": f"SQL validation rejected: {', '.join(val.errors) if val.errors else val.error}",
            "rows": [],
            "row_count": 0,
        }

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(sql_query))
            keys = list(result.keys())
            raw_rows = result.fetchmany(500)
            rows = []
            for r in raw_rows:
                d = {}
                for k, v in zip(keys, r):
                    if isinstance(v, Decimal):
                        d[k] = float(v)
                    elif hasattr(v, "isoformat"):
                        d[k] = v.isoformat()
                    else:
                        d[k] = v
                rows.append(d)
            return {
                "success": True,
                "rows": rows,
                "row_count": len(rows),
                "columns": keys,
            }
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "rows": [],
                "row_count": 0,
            }


def generate_chart_data_tool(
    data: List[Dict[str, Any]],
    chart_type: str = "bar",
    title: str = "Analytics Visualization",
    x_key: Optional[str] = None,
    y_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct structured visualization payload for frontend Recharts rendering."""
    if not data:
        return {}

    sample = data[0]
    keys = list(sample.keys())
    x_k = x_key or keys[0]
    y_k = y_key or (keys[1] if len(keys) > 1 else keys[0])

    return {
        "chart_type": chart_type,
        "title": title,
        "data": data,
        "x_key": x_k,
        "y_key": y_k,
    }
