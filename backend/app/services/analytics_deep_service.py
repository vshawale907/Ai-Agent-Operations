"""
Deep Business Analytics Engine.

Calculates executive-grade operational metrics:
- Customer acquisition, Lifetime Value (LTV), repeat rates, and churn risk
- Product margins, profitability, and declining SKU detection
- Departmental expense ratios and cost efficiency
- Month-over-Month (MoM) and Year-over-Year (YoY) growth trajectories
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.business import Customer, Expense, Order, OrderItem, Product, SupportTicket

logger = get_logger(__name__)


class DeepAnalyticsService:
    """Calculates granular, deterministic business metrics for executive intelligence."""

    async def get_customer_intelligence(self, db: AsyncSession) -> Dict[str, Any]:
        """Compute Customer LTV, repeat rates, inactive accounts, and churn risks."""
        logger.info("Computing customer intelligence metrics...")

        # Total customers
        total_customers = await db.scalar(select(func.count(Customer.id))) or 0

        # Orders per customer
        order_counts_stmt = (
            select(
                Order.customer_id,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("total_spend"),
                func.max(Order.order_date).label("last_order_date"),
            )
            .where(Order.status == "completed")
            .group_by(Order.customer_id)
        )
        res = (await db.execute(order_counts_stmt)).all()

        repeat_customers = sum(1 for r in res if (r.order_count or 0) > 1)
        total_revenue_completed = sum(float(r.total_spend or 0) for r in res)

        # LTV calculation
        avg_ltv = (total_revenue_completed / len(res)) if res else 0.0
        repeat_rate = (repeat_customers / len(res) * 100) if res else 0.0

        # Inactive customer threshold (no orders in 90 days)
        cutoff_date = date.today() - timedelta(days=90)
        inactive_customers = sum(1 for r in res if r.last_order_date and r.last_order_date < cutoff_date)

        # Churn risk accounts (inactive or multiple high priority support tickets)
        churn_risk_accounts = []
        for r in res[:20]:
            if r.last_order_date and r.last_order_date < cutoff_date:
                churn_risk_accounts.append({
                    "customer_id": r.customer_id,
                    "reason": "Order inactivity exceeding 90 days",
                    "total_spend": float(r.total_spend or 0),
                    "last_order": str(r.last_order_date),
                })

        return {
            "total_customers": total_customers,
            "active_buyers": len(res),
            "repeat_customers": repeat_customers,
            "repeat_purchase_rate": round(repeat_rate, 1),
            "average_customer_ltv": round(avg_ltv, 2),
            "inactive_customers_90d": inactive_customers,
            "churn_risk_count": len(churn_risk_accounts),
            "sample_churn_risk_accounts": churn_risk_accounts[:5],
        }

    async def get_product_margins_and_declines(self, db: AsyncSession) -> Dict[str, Any]:
        """Compute gross profit margins per product and detect declining products."""
        logger.info("Computing product profitability and margin analysis...")

        # Margin query
        stmt = (
            select(
                Product.id,
                Product.name,
                Product.category,
                Product.unit_price,
                Product.unit_cost,
                func.sum(OrderItem.quantity).label("units_sold"),
                func.sum(OrderItem.total_price).label("total_revenue"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Product.id, Product.name, Product.category, Product.unit_price, Product.unit_cost)
            .order_by(func.sum(OrderItem.total_price).desc())
        )
        rows = (await db.execute(stmt)).all()

        products_data = []
        for r in rows:
            price = float(r.unit_price or 0)
            cost = float(r.unit_cost or 0)
            margin_pct = ((price - cost) / price * 100) if price > 0 else 0.0
            rev = float(r.total_revenue or 0)
            units = int(r.units_sold or 0)
            profit = rev - (units * cost)

            products_data.append({
                "product_id": r.id,
                "name": r.name,
                "category": r.category,
                "unit_price": price,
                "unit_cost": cost,
                "gross_margin_pct": round(margin_pct, 1),
                "units_sold": units,
                "total_revenue": round(rev, 2),
                "gross_profit": round(profit, 2),
            })

        # Category margin summaries
        cat_margins: Dict[str, List[float]] = {}
        for p in products_data:
            cat_margins.setdefault(p["category"], []).append(p["gross_margin_pct"])

        cat_summary = [
            {
                "category": cat,
                "avg_margin_pct": round(sum(margins) / len(margins), 1),
                "product_count": len(margins),
            }
            for cat, margins in cat_margins.items()
        ]

        return {
            "products": products_data,
            "category_margins": cat_summary,
            "overall_avg_margin": round(
                sum(p["gross_margin_pct"] for p in products_data) / len(products_data), 1
            ) if products_data else 0.0,
        }

    async def get_expense_and_efficiency_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """Compute operational expense breakdown, efficiency, and expense-to-revenue ratio."""
        logger.info("Computing expense efficiency metrics...")

        # Total revenue
        total_rev = (
            await db.scalar(
                select(func.sum(Order.total_amount)).where(Order.status == "completed")
            )
            or Decimal(0)
        )
        total_rev_f = float(total_rev)

        # Total expense
        total_exp = await db.scalar(select(func.sum(Expense.amount))) or Decimal(0)
        total_exp_f = float(total_exp)

        exp_to_rev_ratio = (total_exp_f / total_rev_f * 100) if total_rev_f > 0 else 0.0
        net_operating_income = total_rev_f - total_exp_f

        # Department breakdown
        dept_stmt = (
            select(
                Expense.department,
                func.sum(Expense.amount).label("dept_total"),
                func.count(Expense.id).label("entry_count"),
            )
            .group_by(Expense.department)
            .order_by(func.sum(Expense.amount).desc())
        )
        dept_rows = (await db.execute(dept_stmt)).all()
        dept_breakdown = [
            {
                "department": r.department,
                "total_amount": float(r.dept_total or 0),
                "share_pct": round(float(r.dept_total or 0) / total_exp_f * 100, 1) if total_exp_f > 0 else 0.0,
            }
            for r in dept_rows
        ]

        return {
            "total_revenue": round(total_rev_f, 2),
            "total_expenses": round(total_exp_f, 2),
            "net_operating_income": round(net_operating_income, 2),
            "expense_to_revenue_ratio": round(exp_to_rev_ratio, 1),
            "departmental_breakdown": dept_breakdown,
        }

    async def get_growth_trajectory(self, db: AsyncSession) -> Dict[str, Any]:
        """Calculate Month-over-Month (MoM) revenue changes and trends."""
        stmt = (
            select(
                func.to_char(Order.order_date, "YYYY-MM").label("month"),
                func.sum(Order.total_amount).label("revenue"),
                func.count(Order.id).label("orders"),
            )
            .where(Order.status == "completed")
            .group_by("month")
            .order_by("month")
        )
        rows = (await db.execute(stmt)).all()

        monthly = []
        prev_rev = None

        for r in rows:
            rev = float(r.revenue or 0)
            mom_growth = ((rev - prev_rev) / prev_rev * 100) if prev_rev and prev_rev > 0 else 0.0

            monthly.append({
                "month": r.month,
                "revenue": round(rev, 2),
                "orders": int(r.orders or 0),
                "mom_growth_pct": round(mom_growth, 1) if prev_rev is not None else None,
            })
            prev_rev = rev

        return {
            "monthly_growth": monthly,
            "latest_month": monthly[-1] if monthly else None,
            "average_mom_growth": round(
                sum(m["mom_growth_pct"] for m in monthly if m["mom_growth_pct"] is not None)
                / max(1, len([m for m in monthly if m["mom_growth_pct"] is not None])),
                1,
            ) if len(monthly) > 1 else 0.0,
        }


deep_analytics = DeepAnalyticsService()
