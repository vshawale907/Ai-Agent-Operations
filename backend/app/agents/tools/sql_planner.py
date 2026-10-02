"""
Intelligent Schema-Aware SQL Planner and Conversation Resolver.

Translates natural language questions and multi-turn conversation context
into precise, read-only PostgreSQL queries against the actual database schema.
Works independently and as a reliable engine alongside LLM generation.
"""

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

VALID_REGIONS = ["North", "South", "East", "West", "Central"]
VALID_CATEGORIES = ["Electronics", "Software", "Office Supplies", "Services", "Networking"]
VALID_STATUSES = ["completed", "processing", "shipped", "cancelled", "refunded"]
VALID_SEGMENTS = ["regular", "premium", "enterprise"]
MONTH_NAMES = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09", "sept": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12",
}


def resolve_conversation_context(
    current_question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Resolve pronouns and follow-up phrases using conversation history."""
    if not history or not current_question.strip():
        return current_question.strip()

    q_lower = current_question.lower().strip()

    # Find the most recent user turn
    last_user_turn = ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            last_user_turn = msg.get("content", "")
            break

    if not last_user_turn:
        return current_question

    # Check for ellipsis or follow-up patterns
    followup_patterns = [
        r"^(what\s+about|how\s+about|and\s+for|what\s+of|and\s+in|for)\s+(.+)",
        r"^(compare\s+(?:it|this|that)?\s*(?:with|to)\s*)(.+)",
        r"^(which\s+(?:of\s+those|one|product|region)\s+.*)",
        r"^(now\s+show|now\s+for|what\s+is\s+the\s+same\s+for)\s+(.+)",
    ]

    for pat in followup_patterns:
        m = re.match(pat, q_lower)
        if m:
            target = m.group(len(m.groups()))
            # Combine the intent of last_user_turn with target
            # e.g., "What was revenue in North?" + "What about South?" -> "What was revenue in South?"
            last_lower = last_user_turn.lower()
            for r in VALID_REGIONS:
                if r.lower() in last_lower:
                    for new_r in VALID_REGIONS:
                        if new_r.lower() in target:
                            return re.sub(re.escape(r), new_r, last_user_turn, flags=re.IGNORECASE)
            for c in VALID_CATEGORIES:
                if c.lower() in last_lower:
                    for new_c in VALID_CATEGORIES:
                        if new_c.lower() in target:
                            return re.sub(re.escape(c), new_c, last_user_turn, flags=re.IGNORECASE)

            # If comparison follow-up:
            if "compare" in q_lower:
                return f"{last_user_turn} and compare with {target}"

            return f"{last_user_turn} ({current_question})"

    # If it refers to "there", "it", "those"
    if re.search(r"\b(there|it|that|those|them)\b", q_lower):
        for r in VALID_REGIONS:
            if r.lower() in last_user_turn.lower() and r.lower() not in q_lower:
                return f"{current_question} in {r} region"
        for c in VALID_CATEGORIES:
            if c.lower() in last_user_turn.lower() and c.lower() not in q_lower:
                return f"{current_question} in {c} category"

    return current_question


def generate_structured_sql(question: str) -> Tuple[str, str]:
    """Generate exact, schema-accurate PostgreSQL query from question parameters."""
    q = question.strip()
    q_lower = q.lower()

    # Detect requested limit
    limit_match = re.search(r"\b(?:top|first|limit)\s+(\d+)\b", q_lower)
    limit_val = int(limit_match.group(1)) if limit_match else 5

    # Detect specific regions
    found_regions = [r for r in VALID_REGIONS if r.lower() in q_lower]
    # Check for invalid/unknown region query (e.g. "Antarctica", "Europe", "Mars")
    unknown_region_match = re.search(r"\b(?:in|for|from|region)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", q)
    unknown_region = None
    if unknown_region_match:
        cand = unknown_region_match.group(1)
        if cand not in VALID_REGIONS and cand not in VALID_CATEGORIES and cand.lower() not in (
            "the", "our", "all", "total", "last", "this", "each", "every", "q1", "q2", "q3", "q4"
        ):
            unknown_region = cand

    # Detect categories
    found_categories = [c for c in VALID_CATEGORIES if c.lower() in q_lower]

    # Detect statuses
    found_status = None
    for s in VALID_STATUSES:
        if s in q_lower:
            found_status = s
            break

    # Detect years & months
    year_match = re.search(r"\b(202[0-9])\b", q_lower)
    found_year = year_match.group(1) if year_match else None

    found_month_num = None
    for m_name, m_num in MONTH_NAMES.items():
        if re.search(rf"\b{m_name}\b", q_lower):
            found_month_num = m_num
            break

    # Detect relative dates: "last month", "latest month", "past month"
    is_last_month = any(w in q_lower for w in ["last month", "previous month", "latest month", "past month"])
    is_last_6_months = any(w in q_lower for w in ["last 6 months", "past 6 months", "recent months"])

    # Dynamically compute last month (never hardcoded)
    _today = date.today()
    _first_of_this_month = _today.replace(day=1)
    _last_month_date = _first_of_this_month - timedelta(days=1)
    _last_month_str = _last_month_date.strftime("%Y-%m")
    _last_month_label = _last_month_date.strftime("%B %Y")

    # -------------------------------------------------------------------------
    # Case 1: Queries for explicitly non-existent entities (e.g. "Antarctica")
    # -------------------------------------------------------------------------
    if unknown_region and not found_regions and any(w in q_lower for w in ["region", "revenue", "sales", "orders"]):
        sql = (
            f"SELECT region, COUNT(id) AS total_orders, COALESCE(SUM(total_amount), 0) AS total_revenue "
            f"FROM orders WHERE region = '{unknown_region}' GROUP BY region"
        )
        return sql, f"Querying orders filtered by specified region '{unknown_region}'."

    # -------------------------------------------------------------------------
    # Case 2: Regional Comparisons (e.g., "compare revenue between North and South")
    # -------------------------------------------------------------------------
    if "compare" in q_lower and len(found_regions) >= 2:
        reg_list = ", ".join(f"'{r}'" for r in found_regions)
        year_filter = f"AND EXTRACT(YEAR FROM order_date) = {found_year} " if found_year else ""
        sql = (
            f"SELECT region, COUNT(id) AS total_orders, "
            f"ROUND(SUM(total_amount)::numeric, 2) AS total_revenue, "
            f"ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value "
            f"FROM orders WHERE status = 'completed' {year_filter}AND region IN ({reg_list}) "
            f"GROUP BY region ORDER BY total_revenue DESC"
        )
        return sql, f"Comparing revenue and orders across regions: {', '.join(found_regions)}."

    # -------------------------------------------------------------------------
    # Case 3: Category Comparisons (e.g., "compare Electronics vs Software")
    # -------------------------------------------------------------------------
    if "compare" in q_lower and len(found_categories) >= 2:
        cat_list = ", ".join(f"'{c}'" for c in found_categories)
        sql = (
            f"SELECT p.category, COUNT(DISTINCT o.id) AS total_orders, "
            f"SUM(oi.quantity) AS total_units_sold, "
            f"ROUND(SUM(oi.total_price)::numeric, 2) AS total_revenue, "
            f"ROUND(AVG(p.unit_price)::numeric, 2) AS avg_unit_price "
            f"FROM products p "
            f"JOIN order_items oi ON p.id = oi.product_id "
            f"JOIN orders o ON o.id = oi.order_id "
            f"WHERE o.status = 'completed' AND p.category IN ({cat_list}) "
            f"GROUP BY p.category ORDER BY total_revenue DESC"
        )
        return sql, f"Comparing performance across product categories: {', '.join(found_categories)}."

    # -------------------------------------------------------------------------
    # Case 4: Category Breakdown / Breakdown by Category
    # -------------------------------------------------------------------------
    if "category" in q_lower or "categories" in q_lower or (found_categories and "product" not in q_lower):
        where_clauses = ["o.status = 'completed'"]
        if found_categories:
            cat_list = ", ".join(f"'{c}'" for c in found_categories)
            where_clauses.append(f"p.category IN ({cat_list})")
        if found_regions:
            where_clauses.append(f"o.region = '{found_regions[0]}'")
        if found_year:
            where_clauses.append(f"EXTRACT(YEAR FROM o.order_date) = {found_year}")

        where_sql = " AND ".join(where_clauses)
        sql = (
            f"SELECT p.category, COUNT(DISTINCT o.id) AS orders, "
            f"SUM(oi.quantity) AS units_sold, "
            f"ROUND(SUM(oi.total_price)::numeric, 2) AS total_revenue, "
            f"ROUND(((SUM(oi.total_price) - SUM(oi.quantity * p.unit_cost)) / NULLIF(SUM(oi.total_price), 0) * 100)::numeric, 2) AS margin_percent "
            f"FROM products p "
            f"JOIN order_items oi ON p.id = oi.product_id "
            f"JOIN orders o ON o.id = oi.order_id "
            f"WHERE {where_sql} "
            f"GROUP BY p.category ORDER BY total_revenue DESC"
        )
        return sql, "Aggregating sales revenue, units sold, and margins by product category."

    # -------------------------------------------------------------------------
    # Case 5: Top Products by Revenue, Profit, or Units Sold
    # -------------------------------------------------------------------------
    if "product" in q_lower or "item" in q_lower or "sku" in q_lower or "best-selling" in q_lower or "top selling" in q_lower or "sell" in q_lower:
        where_clauses = ["o.status = 'completed'"]
        if found_regions:
            where_clauses.append(f"o.region = '{found_regions[0]}'")
        if found_categories:
            where_clauses.append(f"p.category = '{found_categories[0]}'")
        if found_year:
            where_clauses.append(f"EXTRACT(YEAR FROM o.order_date) = {found_year}")

        if any(w in q_lower for w in ["profit", "margin", "max"]):
            order_by = "total_profit DESC"
        elif "unit" in q_lower or "quantity" in q_lower:
            order_by = "units_sold DESC"
        elif "least" in q_lower or "lowest" in q_lower or "worst" in q_lower or "bottom" in q_lower:
            order_by = "revenue ASC"
        else:
            order_by = "revenue DESC"

        where_sql = " AND ".join(where_clauses)
        sql = (
            f"SELECT p.name AS product_name, p.category, "
            f"SUM(oi.quantity) AS units_sold, "
            f"ROUND(SUM(oi.total_price)::numeric, 2) AS revenue, "
            f"ROUND((SUM(oi.total_price) - SUM(oi.quantity * p.unit_cost))::numeric, 2) AS total_profit, "
            f"ROUND(((SUM(oi.total_price) - SUM(oi.quantity * p.unit_cost)) / NULLIF(SUM(oi.total_price), 0) * 100)::numeric, 2) AS margin_percent "
            f"FROM products p "
            f"JOIN order_items oi ON p.id = oi.product_id "
            f"JOIN orders o ON o.id = oi.order_id "
            f"WHERE {where_sql} "
            f"GROUP BY p.id, p.name, p.category "
            f"ORDER BY {order_by} "
            f"LIMIT {limit_val}"
        )
        return sql, f"Retrieving top {limit_val} products ordered by {order_by.split()[0]}."

    # -------------------------------------------------------------------------
    # Case 6: Profit & Gross Margins
    # -------------------------------------------------------------------------
    if "margin" in q_lower or "profit" in q_lower:
        where_clauses = ["o.status = 'completed'"]
        if found_regions:
            where_clauses.append(f"o.region = '{found_regions[0]}'")
        if found_year:
            where_clauses.append(f"EXTRACT(YEAR FROM o.order_date) = {found_year}")

        where_sql = " AND ".join(where_clauses)
        sql = (
            f"SELECT p.category, "
            f"ROUND(SUM(oi.total_price)::numeric, 2) AS revenue, "
            f"ROUND((SUM(oi.total_price) - SUM(oi.quantity * p.unit_cost))::numeric, 2) AS gross_profit, "
            f"ROUND(((SUM(oi.total_price) - SUM(oi.quantity * p.unit_cost)) / NULLIF(SUM(oi.total_price), 0) * 100)::numeric, 2) AS margin_pct "
            f"FROM products p "
            f"JOIN order_items oi ON p.id = oi.product_id "
            f"JOIN orders o ON o.id = oi.order_id "
            f"WHERE {where_sql} "
            f"GROUP BY p.category ORDER BY margin_pct DESC"
        )
        return sql, "Calculating gross profit and margin percentages by category."

    # -------------------------------------------------------------------------
    # Case 7: Customer Metrics & Accounts
    # -------------------------------------------------------------------------
    if "customer" in q_lower or "churn" in q_lower or "buyer" in q_lower or "client" in q_lower:
        if "segment" in q_lower:
            sql = (
                "SELECT segment, COUNT(id) AS total_customers, "
                "COUNT(CASE WHEN is_active THEN 1 END) AS active_customers, "
                "COUNT(CASE WHEN NOT is_active THEN 1 END) AS inactive_customers "
                "FROM customers GROUP BY segment ORDER BY total_customers DESC"
            )
            return sql, "Aggregating customer accounts by customer tier/segment."

        if "top" in q_lower or "highest" in q_lower or "spend" in q_lower or "best" in q_lower:
            sql = (
                f"SELECT c.name AS customer_name, c.region, c.segment, "
                f"COUNT(o.id) AS total_orders, "
                f"ROUND(SUM(o.total_amount)::numeric, 2) AS total_spent "
                f"FROM customers c "
                f"JOIN orders o ON c.id = o.customer_id "
                f"WHERE o.status = 'completed' "
                f"GROUP BY c.id, c.name, c.region, c.segment "
                f"ORDER BY total_spent DESC LIMIT {limit_val}"
            )
            return sql, f"Retrieving top {limit_val} highest spending customers."

        where_clause = f"WHERE region = '{found_regions[0]}'" if found_regions else ""
        sql = (
            f"SELECT region, COUNT(id) AS total_customers, "
            f"COUNT(CASE WHEN is_active THEN 1 END) AS active_customers, "
            f"COUNT(CASE WHEN NOT is_active THEN 1 END) AS inactive_customers "
            f"FROM customers {where_clause} GROUP BY region ORDER BY total_customers DESC"
        )
        return sql, "Retrieving customer counts and activity status by region."

    # -------------------------------------------------------------------------
    # Case 8: Expenses & OpEx
    # -------------------------------------------------------------------------
    if "expense" in q_lower or "spending" in q_lower or "opex" in q_lower or ("cost" in q_lower and "unit_cost" not in q_lower):
        where_clauses = []
        if found_regions:
            where_clauses.append(f"region = '{found_regions[0]}'")
        if found_year:
            where_clauses.append(f"EXTRACT(YEAR FROM expense_date) = {found_year}")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        group_by = "department" if "dept" in q_lower or "department" in q_lower else "category"

        sql = (
            f"SELECT {group_by}, COUNT(id) AS entries, "
            f"ROUND(SUM(amount)::numeric, 2) AS total_expense, "
            f"ROUND(AVG(amount)::numeric, 2) AS avg_expense "
            f"FROM expenses {where_sql} "
            f"GROUP BY {group_by} ORDER BY total_expense DESC"
        )
        return sql, f"Aggregating operating expenses by {group_by}."

    # -------------------------------------------------------------------------
    # Case 9: Support Tickets
    # -------------------------------------------------------------------------
    if "ticket" in q_lower or "support" in q_lower or "complaint" in q_lower:
        group_col = "priority" if "priority" in q_lower else ("status" if "status" in q_lower else "category")
        sql = (
            f"SELECT {group_col}, COUNT(id) AS ticket_count, "
            f"COUNT(CASE WHEN status = 'resolved' THEN 1 END) AS resolved_count, "
            f"COUNT(CASE WHEN status = 'open' THEN 1 END) AS open_count "
            f"FROM support_tickets GROUP BY {group_col} ORDER BY ticket_count DESC"
        )
        return sql, f"Aggregating customer support tickets by {group_col}."

    # -------------------------------------------------------------------------
    # Case 10: Date / Monthly Revenue Queries (e.g. "revenue last month", "revenue in August 2026")
    # -------------------------------------------------------------------------
    if found_month_num or is_last_month or "month" in q_lower or "trend" in q_lower:
        where_clauses = ["status = 'completed'"]
        if found_regions:
            where_clauses.append(f"region = '{found_regions[0]}'")

        if is_last_month:
            where_clauses.append(f"TO_CHAR(order_date, 'YYYY-MM') = '{_last_month_str}'")
            where_sql = " AND ".join(where_clauses)
            sql = (
                f"SELECT TO_CHAR(order_date, 'YYYY-MM') AS month, "
                f"COUNT(id) AS total_orders, "
                f"ROUND(SUM(total_amount)::numeric, 2) AS total_revenue, "
                f"ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value "
                f"FROM orders WHERE {where_sql} GROUP BY month"
            )
            return sql, f"Retrieving verified revenue and order metrics for last month ({_last_month_label})."

        if found_month_num:
            target_year = found_year or str(date.today().year)
            target_period = f"{target_year}-{found_month_num}"
            where_clauses.append(f"TO_CHAR(order_date, 'YYYY-MM') = '{target_period}'")
            where_sql = " AND ".join(where_clauses)
            sql = (
                f"SELECT TO_CHAR(order_date, 'YYYY-MM') AS month, "
                f"COUNT(id) AS total_orders, "
                f"ROUND(SUM(total_amount)::numeric, 2) AS total_revenue, "
                f"ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value "
                f"FROM orders WHERE {where_sql} GROUP BY month"
            )
            return sql, f"Retrieving performance metrics for {target_period}."

        limit_months = 6 if is_last_6_months else 12
        where_sql = " AND ".join(where_clauses)
        sql = (
            f"SELECT TO_CHAR(order_date, 'YYYY-MM') AS month, "
            f"COUNT(id) AS total_orders, "
            f"ROUND(SUM(total_amount)::numeric, 2) AS revenue, "
            f"ROUND(AVG(total_amount)::numeric, 2) AS aov "
            f"FROM orders WHERE {where_sql} "
            f"GROUP BY month ORDER BY month DESC LIMIT {limit_months}"
        )
        return sql, f"Aggregating monthly sales and order volume over the last {limit_months} months."

    # -------------------------------------------------------------------------
    # Case 11: Regional Performance & Breakdown
    # -------------------------------------------------------------------------
    if "region" in q_lower or "territory" in q_lower or (found_regions and not found_categories):
        where_clauses = ["status = 'completed'"]
        if found_regions:
            where_clauses.append(f"region = '{found_regions[0]}'")
        if found_year:
            where_clauses.append(f"EXTRACT(YEAR FROM order_date) = {found_year}")

        where_sql = " AND ".join(where_clauses)
        sql = (
            f"SELECT region, COUNT(id) AS total_orders, "
            f"ROUND(SUM(total_amount)::numeric, 2) AS revenue, "
            f"ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value "
            f"FROM orders WHERE {where_sql} "
            f"GROUP BY region ORDER BY revenue DESC"
        )
        return sql, "Aggregating revenue and order metrics across regional territories."

    # -------------------------------------------------------------------------
    # Case 12: General Total Revenue & Orders
    # -------------------------------------------------------------------------
    where_clauses = [f"status = '{found_status}'" if found_status else "status = 'completed'"]
    if found_year:
        where_clauses.append(f"EXTRACT(YEAR FROM order_date) = {found_year}")

    where_sql = " AND ".join(where_clauses)
    sql = (
        f"SELECT COUNT(id) AS total_orders, "
        f"ROUND(SUM(total_amount)::numeric, 2) AS total_revenue, "
        f"ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value "
        f"FROM orders WHERE {where_sql}"
    )
    return sql, "Aggregating overall sales revenue, order count, and average order value."
