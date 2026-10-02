"""
Business Anomaly Detection Service using Explainable Statistical Methods.

Detects unusual spikes or drops in revenue, orders, expenses, and support volume
using rolling moving averages, standard deviation, Z-scores, and percentage thresholds.
Generates human-readable narrative explanations without opaque black-box models.
"""

import math
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.business import Expense, Order, SupportTicket
from app.schemas.agent_schemas import AnomalyItem, AnomalyReport

logger = get_logger(__name__)


def compute_z_score_anomalies(
    series: List[Dict[str, Any]],
    val_key: str,
    date_key: str,
    metric_name: str,
    unit_prefix: str = "",
    min_periods: int = 3,
    z_threshold: float = 1.75,
    pct_threshold: float = 0.22,
) -> List[AnomalyItem]:
    """Calculate Z-scores and percentage deviations on a time-series list.
    
    Args:
        series: List of dicts ordered chronologically.
        val_key: Key name for metric value in dict.
        date_key: Key name for time label in dict.
        metric_name: Display name of metric.
        unit_prefix: e.g. '$' for revenue.
        min_periods: Minimum historical data points required.
        z_threshold: Z-score cutoff (default 1.75 standard deviations).
        pct_threshold: Percentage difference cutoff (default 22%).
    """
    anomalies: List[AnomalyItem] = []
    values = [float(item[val_key]) for item in series]

    if len(values) < min_periods:
        return []

    # Calculate overall mean and standard deviation
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = math.sqrt(variance) if variance > 0 else 0.0

    for idx, item in enumerate(series):
        val = float(item[val_key])
        period = str(item[date_key])

        # Rolling trailing window if we have at least 3 prior points
        if idx >= 3:
            window = values[max(0, idx - 6) : idx]
            win_mean = sum(window) / len(window)
            win_var = sum((x - win_mean) ** 2 for x in window) / len(window)
            win_std = math.sqrt(win_var) if win_var > 0 else std_dev
        else:
            win_mean = mean
            win_std = std_dev

        if win_std == 0:
            continue

        z_score = (val - win_mean) / win_std
        pct_diff = (val - win_mean) / win_mean if win_mean > 0 else 0.0

        is_z_anomaly = abs(z_score) >= z_threshold
        is_pct_anomaly = abs(pct_diff) >= pct_threshold

        if is_z_anomaly and is_pct_anomaly:
            abs_z = abs(z_score)
            abs_pct = abs(pct_diff)

            if abs_z >= 2.5 or abs_pct >= 0.40:
                severity = "critical"
            elif abs_z >= 2.0 or abs_pct >= 0.28:
                severity = "high"
            elif abs_z >= 1.7 or abs_pct >= 0.20:
                severity = "medium"
            else:
                severity = "low"

            direction = "spike" if z_score > 0 else "drop"
            direction_adv = "above" if z_score > 0 else "below"

            val_str = f"{unit_prefix}{val:,.0f}" if val >= 100 else f"{unit_prefix}{val:.2f}"
            mean_str = f"{unit_prefix}{win_mean:,.0f}" if win_mean >= 100 else f"{unit_prefix}{win_mean:.2f}"

            explanation = (
                f"{metric_name} exhibited an unusual {direction} in {period} reaching {val_str}, "
                f"which is {abs(pct_diff) * 100:.1f}% {direction_adv} the trailing expected average "
                f"of {mean_str} (statistical Z-score: {z_score:+.2f})."
            )

            anomalies.append(
                AnomalyItem(
                    metric=metric_name,
                    period=period,
                    actual_value=round(val, 2),
                    expected_value=round(win_mean, 2),
                    deviation_percent=round(pct_diff * 100, 1),
                    z_score=round(z_score, 2),
                    severity=severity,
                    explanation=explanation,
                )
            )

    return anomalies


class AnomalyService:
    """Detects multi-dimensional statistical anomalies across sales, costs, and support."""

    async def detect_all_anomalies(
        self,
        db: AsyncSession,
        lookback_months: int = 12,
    ) -> AnomalyReport:
        """Run statistical anomaly scanners across revenue, orders, expenses, and tickets."""
        logger.info(f"Running multi-metric anomaly detection across last {lookback_months} months...")
        all_anomalies: List[AnomalyItem] = []

        # 1. Monthly Revenue & Order Volume
        rev_stmt = (
            select(
                func.to_char(Order.order_date, "YYYY-MM").label("month"),
                func.sum(Order.total_amount).label("revenue"),
                func.count(Order.id).label("orders"),
            )
            .where(Order.status == "completed")
            .group_by("month")
            .order_by("month")
        )
        rev_rows = (await db.execute(rev_stmt)).all()
        rev_data = [
            {"month": r.month, "revenue": float(r.revenue or 0), "orders": int(r.orders or 0)}
            for r in rev_rows
        ]

        if rev_data:
            all_anomalies.extend(
                compute_z_score_anomalies(
                    rev_data,
                    val_key="revenue",
                    date_key="month",
                    metric_name="Monthly Revenue",
                    unit_prefix="$",
                )
            )
            all_anomalies.extend(
                compute_z_score_anomalies(
                    rev_data,
                    val_key="orders",
                    date_key="month",
                    metric_name="Order Volume",
                    unit_prefix="",
                )
            )

        # 2. Monthly Expenses
        exp_stmt = (
            select(
                func.to_char(Expense.expense_date, "YYYY-MM").label("month"),
                func.sum(Expense.amount).label("total_expense"),
            )
            .group_by("month")
            .order_by("month")
        )
        exp_rows = (await db.execute(exp_stmt)).all()
        exp_data = [
            {"month": r.month, "total_expense": float(r.total_expense or 0)}
            for r in exp_rows
        ]

        if exp_data:
            all_anomalies.extend(
                compute_z_score_anomalies(
                    exp_data,
                    val_key="total_expense",
                    date_key="month",
                    metric_name="Operating Expenses",
                    unit_prefix="$",
                )
            )

        # 3. Monthly Support Tickets
        try:
            ticket_stmt = (
                select(
                    func.to_char(SupportTicket.created_at, "YYYY-MM").label("month"),
                    func.count(SupportTicket.id).label("ticket_count"),
                )
                .group_by("month")
                .order_by("month")
            )
            ticket_rows = (await db.execute(ticket_stmt)).all()
            ticket_data = [
                {"month": r.month, "ticket_count": int(r.ticket_count or 0)}
                for r in ticket_rows
            ]
            if ticket_data:
                all_anomalies.extend(
                    compute_z_score_anomalies(
                        ticket_data,
                        val_key="ticket_count",
                        date_key="month",
                        metric_name="Support Ticket Volume",
                        unit_prefix="",
                    )
                )
        except Exception as e:
            logger.warning(f"Support ticket anomaly scan skipped: {e}")

        # Summary formulation
        analyzed_periods = max(len(rev_data), len(exp_data))
        if all_anomalies:
            critical_count = sum(1 for a in all_anomalies if a.severity in ("critical", "high"))
            summary = (
                f"Identified {len(all_anomalies)} statistical anomalies across {analyzed_periods} operational periods "
                f"({critical_count} require immediate executive investigation)."
            )
        else:
            summary = (
                f"All business operations, revenues, and operating expenses remain within normal "
                f"expected standard deviation bounds across the analyzed {analyzed_periods} periods."
            )

        # Sort anomalies by severity and deviation
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_anomalies.sort(key=lambda a: (severity_order.get(a.severity, 4), -abs(a.deviation_percent)))

        return AnomalyReport(
            anomalies=all_anomalies,
            detected_count=len(all_anomalies),
            analyzed_periods=analyzed_periods,
            summary=summary,
        )


anomaly_service = AnomalyService()
