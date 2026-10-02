"""
Business glossary — maps business terminology to SQL/schema concepts.

The agent uses this to translate natural language business terms
into correct database column references and aggregation patterns.
"""

BUSINESS_GLOSSARY = {
    "revenue": {
        "description": "Total money earned from orders",
        "sql_expression": "SUM(orders.total_amount)",
        "table": "orders",
        "filter": "orders.status != 'cancelled'",
    },
    "sales": {
        "description": "Same as revenue — total order amounts",
        "sql_expression": "SUM(orders.total_amount)",
        "table": "orders",
        "filter": "orders.status != 'cancelled'",
    },
    "profit": {
        "description": "Revenue minus cost of goods sold",
        "sql_expression": "SUM(order_items.total_price) - SUM(order_items.quantity * products.unit_cost)",
        "tables": ["order_items", "products"],
        "join": "order_items.product_id = products.id",
    },
    "margin": {
        "description": "Profit as a percentage of revenue",
        "sql_expression": "(SUM(order_items.total_price) - SUM(order_items.quantity * products.unit_cost)) / NULLIF(SUM(order_items.total_price), 0) * 100",
        "tables": ["order_items", "products"],
    },
    "orders": {
        "description": "Count of orders placed",
        "sql_expression": "COUNT(orders.id)",
        "table": "orders",
    },
    "order count": {
        "description": "Total number of orders",
        "sql_expression": "COUNT(orders.id)",
        "table": "orders",
    },
    "average order value": {
        "description": "Average amount per order",
        "sql_expression": "AVG(orders.total_amount)",
        "table": "orders",
        "abbreviation": "AOV",
    },
    "aov": {
        "description": "Average Order Value",
        "sql_expression": "AVG(orders.total_amount)",
        "table": "orders",
    },
    "customers": {
        "description": "Number of unique customers",
        "sql_expression": "COUNT(DISTINCT customers.id)",
        "table": "customers",
    },
    "customer count": {
        "description": "Total active customers",
        "sql_expression": "COUNT(customers.id)",
        "table": "customers",
        "filter": "customers.is_active = true",
    },
    "churn": {
        "description": "Customers who became inactive",
        "sql_expression": "COUNT(customers.id)",
        "table": "customers",
        "filter": "customers.is_active = false",
    },
    "growth": {
        "description": "Period-over-period revenue increase percentage",
        "context": "Compare current period revenue with previous period",
    },
    "conversion": {
        "description": "Percentage of marketing clicks that became orders",
        "sql_expression": "CAST(conversions AS FLOAT) / NULLIF(clicks, 0) * 100",
        "table": "marketing_campaigns",
    },
    "expense": {
        "description": "Business expenses / costs",
        "sql_expression": "SUM(expenses.amount)",
        "table": "expenses",
    },
    "expenses": {
        "description": "Business operating expenses",
        "sql_expression": "SUM(expenses.amount)",
        "table": "expenses",
    },
    "top products": {
        "description": "Products ranked by revenue",
        "context": "JOIN order_items with products, SUM total_price, ORDER BY DESC",
    },
    "regions": {
        "description": "Geographic regions: North, South, East, West, Central",
        "column": "orders.region OR customers.region",
    },
    "refund": {
        "description": "Orders with refunded status",
        "filter": "orders.status = 'refunded'",
        "table": "orders",
    },
    "discount": {
        "description": "Discount amount on orders",
        "sql_expression": "SUM(orders.discount_amount)",
        "table": "orders",
    },
}


def get_glossary_context() -> str:
    """Format the business glossary as context for the LLM."""
    lines = ["## Business Glossary\n"]
    for term, info in BUSINESS_GLOSSARY.items():
        desc = info.get("description", "")
        expr = info.get("sql_expression", "")
        table = info.get("table", info.get("tables", ""))
        line = f"- **{term}**: {desc}"
        if expr:
            line += f" → SQL: `{expr}`"
        if table:
            line += f" (table: {table})"
        lines.append(line)
    return "\n".join(lines)


# Database schema description for the LLM
DATABASE_SCHEMA = """
## Database Schema

### customers
- id (PK), name, email, phone, region, city, segment, is_active, created_at
- Segments: premium, regular, enterprise
- Regions: North, South, East, West, Central

### products
- id (PK), name, sku, category, subcategory, unit_price, unit_cost, is_active, created_at
- Categories: Electronics, Software, Office Supplies, Services, Networking

### orders
- id (PK), customer_id (FK→customers), order_date, status, total_amount, discount_amount, region, payment_method, created_at
- Status: completed, processing, shipped, cancelled, refunded
- Payment methods: credit_card, debit_card, upi, bank_transfer, cash

### order_items
- id (PK), order_id (FK→orders), product_id (FK→products), quantity, unit_price, total_price

### employees
- id (PK), name, email, department, role, salary, hire_date, is_active, region, created_at
- Departments: Engineering, Sales, Marketing, Support, Operations, HR, Finance

### expenses
- id (PK), category, description, amount, expense_date, department, region, approved_by, created_at
- Categories: Salaries, Marketing, Infrastructure, Travel, Software Licenses, Office Rent, Utilities, Training

### marketing_campaigns
- id (PK), name, channel, budget, spend, impressions, clicks, conversions, revenue_generated, start_date, end_date, status, region, created_at
- Channels: Google Ads, Facebook, Instagram, LinkedIn, Email, Content, Referral

### support_tickets
- id (PK), customer_id (FK→customers), subject, description, category, priority, status, assigned_to, resolution, created_at, resolved_at
- Categories: Billing, Technical, Product Inquiry, Returns, Account, Shipping, General
- Priority: low, medium, high, critical
- Status: open, in_progress, resolved

## Key Relationships
- orders.customer_id → customers.id
- order_items.order_id → orders.id
- order_items.product_id → products.id
- support_tickets.customer_id → customers.id

## Important Notes
- Revenue = SUM(orders.total_amount) WHERE status != 'cancelled'
- Profit = Revenue - Cost (use order_items.quantity * products.unit_cost for cost)
- All monetary values are in INR (₹)
- Date ranges: Data spans ~18 months from current date
"""


def get_schema_context() -> str:
    """Return the full database schema context for the LLM."""
    return DATABASE_SCHEMA
