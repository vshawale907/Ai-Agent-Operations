"""
Seed the database with realistic business data.

Creates meaningful patterns:
- Some products grow, some decline
- Regions have different performance levels
- Seasonal trends in orders
- High-value customers vs regular ones
- Varied expenses across departments
- Marketing campaigns with different ROI
- Support tickets with resolution patterns

Run: python -m app.db.seed
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import text

from app.core.security import hash_password
from app.db.database import sync_engine, Base, SyncSessionLocal
from app.db.models import (
    Customer, Product, Order, OrderItem,
    Employee, Expense, MarketingCampaign, SupportTicket, User,
)

random.seed(42)  # Reproducible data

# =============================================================================
# Constants
# =============================================================================
REGIONS = ["North", "South", "East", "West", "Central"]
REGION_WEIGHTS = [0.30, 0.22, 0.18, 0.15, 0.15]  # North is strongest

CITIES_BY_REGION = {
    "North": ["Delhi", "Chandigarh", "Lucknow", "Jaipur", "Dehradun"],
    "South": ["Bangalore", "Chennai", "Hyderabad", "Kochi", "Coimbatore"],
    "East": ["Kolkata", "Bhubaneswar", "Patna", "Guwahati", "Ranchi"],
    "West": ["Mumbai", "Pune", "Ahmedabad", "Surat", "Goa"],
    "Central": ["Bhopal", "Nagpur", "Indore", "Raipur", "Jabalpur"],
}

SEGMENTS = ["premium", "regular", "enterprise"]
SEGMENT_WEIGHTS = [0.15, 0.65, 0.20]

CATEGORIES = {
    "Electronics": {
        "subcategories": ["Smartphones", "Laptops", "Tablets", "Accessories", "Wearables"],
        "price_range": (5000, 120000),
        "margin": 0.20,
        "trend": "growing",
    },
    "Software": {
        "subcategories": ["Productivity", "Security", "Analytics", "CRM", "Cloud Services"],
        "price_range": (2000, 50000),
        "margin": 0.65,
        "trend": "growing",
    },
    "Office Supplies": {
        "subcategories": ["Paper", "Furniture", "Printers", "Stationery", "Storage"],
        "price_range": (200, 25000),
        "margin": 0.30,
        "trend": "stable",
    },
    "Services": {
        "subcategories": ["Consulting", "Training", "Support Plans", "Integration", "Maintenance"],
        "price_range": (10000, 200000),
        "margin": 0.50,
        "trend": "growing",
    },
    "Networking": {
        "subcategories": ["Routers", "Switches", "Cables", "Firewalls", "Access Points"],
        "price_range": (1000, 80000),
        "margin": 0.25,
        "trend": "declining",
    },
}

PAYMENT_METHODS = ["credit_card", "debit_card", "upi", "bank_transfer", "cash"]
PAYMENT_WEIGHTS = [0.35, 0.20, 0.25, 0.15, 0.05]

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Support", "Operations", "HR", "Finance"]

EXPENSE_CATEGORIES = [
    "Salaries", "Marketing", "Infrastructure", "Travel",
    "Software Licenses", "Office Rent", "Utilities", "Training",
]

TICKET_CATEGORIES = [
    "Billing", "Technical", "Product Inquiry", "Returns",
    "Account", "Shipping", "General",
]

TICKET_PRIORITIES = ["low", "medium", "high", "critical"]
TICKET_PRIORITY_WEIGHTS = [0.25, 0.40, 0.25, 0.10]

FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Ananya", "Arjun", "Diya", "Gaurav", "Ishaan",
    "Kavya", "Krishna", "Lakshmi", "Meera", "Nikhil", "Pooja", "Rahul",
    "Riya", "Rohan", "Saanvi", "Sanjay", "Shreya", "Suresh", "Tanvi",
    "Varun", "Vikram", "Zara", "Amit", "Bhavna", "Deepak", "Esha", "Farhan",
    "Geeta", "Harsh", "Isha", "Jai", "Kiran", "Lalit", "Manisha", "Neeraj",
    "Om", "Priya", "Rajesh", "Sapna", "Tushar", "Uma", "Vinay",
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Reddy", "Gupta", "Shah",
    "Verma", "Joshi", "Mehta", "Nair", "Iyer", "Rao", "Chopra",
    "Malhotra", "Desai", "Pillai", "Agarwal", "Bhat", "Das",
    "Kapoor", "Mishra", "Banerjee", "Chauhan", "Dutta",
]


# =============================================================================
# Helper Functions
# =============================================================================
def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_email(name: str, idx: int) -> str:
    parts = name.lower().split()
    return f"{parts[0]}.{parts[1]}{idx}@example.com"


def seasonal_multiplier(month: int) -> float:
    """Simulate seasonal business patterns."""
    # Q4 is strongest (festival season), Q1 dip, Q2-Q3 steady growth
    multipliers = {
        1: 0.75, 2: 0.80, 3: 0.90, 4: 0.95,
        5: 1.00, 6: 1.05, 7: 1.00, 8: 0.95,
        9: 1.10, 10: 1.20, 11: 1.35, 12: 1.25,
    }
    return multipliers.get(month, 1.0)


def trend_multiplier(month_offset: int, trend: str) -> float:
    """Apply growth/decline trend over months."""
    if trend == "growing":
        return 1.0 + (month_offset * 0.015)  # ~1.5% monthly growth
    elif trend == "declining":
        return max(0.5, 1.0 - (month_offset * 0.02))  # ~2% monthly decline
    return 1.0  # stable


# =============================================================================
# Seed Functions
# =============================================================================
def seed_customers(session) -> list:
    """Create 1200 customers across regions."""
    customers = []
    for i in range(1200):
        region = random.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0]
        city = random.choice(CITIES_BY_REGION[region])
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
        name = random_name()
        customer = Customer(
            name=name,
            email=random_email(name, i),
            phone=f"+91{random.randint(7000000000, 9999999999)}",
            region=region,
            city=city,
            segment=segment,
            is_active=random.random() > 0.08,  # 92% active
            created_at=date.today() - timedelta(days=random.randint(30, 730)),
        )
        customers.append(customer)
    session.add_all(customers)
    session.flush()
    print(f"  ✓ Created {len(customers)} customers")
    return customers


def seed_products(session) -> list:
    """Create 120 products across categories."""
    products = []
    idx = 0
    for category, info in CATEGORIES.items():
        for subcat in info["subcategories"]:
            for variant in range(4 + random.randint(0, 2)):
                idx += 1
                base_price = random.uniform(*info["price_range"])
                product = Product(
                    name=f"{subcat} {chr(64 + variant + 1)} {category[:3].upper()}",
                    sku=f"SKU-{category[:3].upper()}-{idx:04d}",
                    category=category,
                    subcategory=subcat,
                    unit_price=Decimal(str(round(base_price, 2))),
                    unit_cost=Decimal(str(round(base_price * (1 - info["margin"]), 2))),
                    is_active=random.random() > 0.05,
                )
                products.append(product)
    session.add_all(products)
    session.flush()
    print(f"  ✓ Created {len(products)} products")
    return products


def seed_orders_and_items(session, customers: list, products: list) -> None:
    """Create 12000+ orders with items over 18 months."""
    start_date = date.today() - timedelta(days=540)  # ~18 months ago
    total_orders = 0
    total_items = 0

    # Group products by category for trend-aware selection
    products_by_category = {}
    for p in products:
        products_by_category.setdefault(p.category, []).append(p)

    for day_offset in range(540):
        current_date = start_date + timedelta(days=day_offset)
        month = current_date.month
        month_offset = day_offset // 30  # Approximate month index

        # Base orders per day with seasonal variation
        base_orders = random.randint(15, 30)
        daily_orders = int(base_orders * seasonal_multiplier(month))

        for _ in range(daily_orders):
            customer = random.choice(customers)
            region = customer.region

            # Pick 1-5 items per order
            num_items = random.choices([1, 2, 3, 4, 5], weights=[0.30, 0.35, 0.20, 0.10, 0.05])[0]
            order_total = Decimal("0.00")
            discount = Decimal(str(round(random.uniform(0, 0.10), 2)))

            order = Order(
                customer_id=customer.id,
                order_date=current_date,
                status=random.choices(
                    ["completed", "processing", "shipped", "cancelled", "refunded"],
                    weights=[0.75, 0.08, 0.10, 0.04, 0.03],
                )[0],
                total_amount=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                region=region,
                payment_method=random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0],
                created_at=current_date,
            )
            session.add(order)
            session.flush()

            items = []
            selected_products = random.sample(products, min(num_items, len(products)))
            for product in selected_products:
                cat_info = CATEGORIES[product.category]
                t_mult = trend_multiplier(month_offset, cat_info["trend"])
                quantity = max(1, int(random.randint(1, 5) * t_mult))
                item_price = product.unit_price
                item_total = item_price * quantity

                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=item_price,
                    total_price=item_total,
                )
                items.append(item)
                order_total += item_total
                total_items += 1

            discount_amount = (order_total * discount).quantize(Decimal("0.01"))
            order.total_amount = order_total - discount_amount
            order.discount_amount = discount_amount
            session.add_all(items)
            total_orders += 1

        # Commit in daily batches for efficiency
        if day_offset % 30 == 0:
            session.commit()
            print(f"    ... seeded orders through {current_date}")

    session.commit()
    print(f"  ✓ Created {total_orders} orders with {total_items} items")


def seed_employees(session) -> None:
    """Create 85 employees."""
    employees = []
    for i in range(85):
        dept = random.choice(DEPARTMENTS)
        roles = {
            "Engineering": ["Software Engineer", "Senior Engineer", "Tech Lead", "Architect"],
            "Sales": ["Sales Rep", "Account Manager", "Sales Lead", "VP Sales"],
            "Marketing": ["Marketing Analyst", "Content Manager", "SEO Specialist", "CMO"],
            "Support": ["Support Agent", "Senior Agent", "Support Lead", "Support Manager"],
            "Operations": ["Ops Analyst", "Logistics Coord", "Ops Manager", "COO"],
            "HR": ["HR Executive", "Recruiter", "HR Manager", "CHRO"],
            "Finance": ["Accountant", "Financial Analyst", "Finance Manager", "CFO"],
        }
        role = random.choice(roles.get(dept, ["Associate"]))
        salary_base = {
            "Engineering": 85000, "Sales": 60000, "Marketing": 55000,
            "Support": 40000, "Operations": 50000, "HR": 50000, "Finance": 65000,
        }
        name = random_name()
        employee = Employee(
            name=name,
            email=f"emp.{name.lower().replace(' ', '.')}.{i}@company.com",
            department=dept,
            role=role,
            salary=Decimal(str(salary_base.get(dept, 50000) + random.randint(-10000, 30000))),
            hire_date=date.today() - timedelta(days=random.randint(90, 1800)),
            is_active=random.random() > 0.05,
            region=random.choice(REGIONS),
        )
        employees.append(employee)
    session.add_all(employees)
    session.commit()
    print(f"  ✓ Created {len(employees)} employees")


def seed_expenses(session) -> None:
    """Create monthly expenses over 18 months."""
    expenses = []
    start_date = date.today() - timedelta(days=540)
    for month_offset in range(18):
        current_month = start_date + timedelta(days=month_offset * 30)
        for category in EXPENSE_CATEGORIES:
            base_amounts = {
                "Salaries": 2500000, "Marketing": 450000, "Infrastructure": 350000,
                "Travel": 120000, "Software Licenses": 200000, "Office Rent": 500000,
                "Utilities": 80000, "Training": 60000,
            }
            base = base_amounts.get(category, 100000)
            # Add some variance
            amount = base * (1 + random.uniform(-0.15, 0.15))
            # Growing costs trend
            amount *= (1 + month_offset * 0.005)

            for region in REGIONS:
                region_share = dict(zip(REGIONS, REGION_WEIGHTS))[region]
                expense = Expense(
                    category=category,
                    description=f"{category} expense for {region} region",
                    amount=Decimal(str(round(amount * region_share, 2))),
                    expense_date=current_month,
                    department=random.choice(DEPARTMENTS),
                    region=region,
                    approved_by=random_name(),
                )
                expenses.append(expense)
    session.add_all(expenses)
    session.commit()
    print(f"  ✓ Created {len(expenses)} expenses")


def seed_marketing_campaigns(session) -> None:
    """Create marketing campaigns."""
    campaigns = []
    channels = ["Google Ads", "Facebook", "Instagram", "LinkedIn", "Email", "Content", "Referral"]
    start_date = date.today() - timedelta(days=540)

    for month_offset in range(18):
        month_start = start_date + timedelta(days=month_offset * 30)
        month_end = month_start + timedelta(days=29)
        for i in range(random.randint(3, 6)):
            channel = random.choice(channels)
            budget = Decimal(str(random.randint(50000, 500000)))
            spend = budget * Decimal(str(random.uniform(0.70, 1.05)))
            impressions = random.randint(50000, 500000)
            clicks = int(impressions * random.uniform(0.01, 0.05))
            conversions = int(clicks * random.uniform(0.02, 0.08))
            revenue = Decimal(str(conversions * random.randint(2000, 15000)))

            campaign = MarketingCampaign(
                name=f"{channel} Campaign {month_start.strftime('%b %Y')} #{i + 1}",
                channel=channel,
                budget=budget,
                spend=spend.quantize(Decimal("0.01")),
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                revenue_generated=revenue,
                start_date=month_start,
                end_date=month_end,
                status=random.choice(["completed", "active", "paused"]),
                region=random.choice(REGIONS),
            )
            campaigns.append(campaign)
    session.add_all(campaigns)
    session.commit()
    print(f"  ✓ Created {len(campaigns)} marketing campaigns")


def seed_support_tickets(session, customers: list) -> None:
    """Create support tickets."""
    tickets = []
    start_date = date.today() - timedelta(days=540)

    for day_offset in range(540):
        current_date = start_date + timedelta(days=day_offset)
        daily_tickets = random.randint(2, 8)

        for _ in range(daily_tickets):
            customer = random.choice(customers)
            category = random.choice(TICKET_CATEGORIES)
            priority = random.choices(TICKET_PRIORITIES, weights=TICKET_PRIORITY_WEIGHTS)[0]
            is_resolved = random.random() > 0.15

            subjects = {
                "Billing": [
                    "Invoice discrepancy", "Payment failed", "Refund request",
                    "Billing cycle question", "Overcharge complaint",
                ],
                "Technical": [
                    "Product not working", "Integration issue", "Performance problem",
                    "Setup assistance needed", "API error",
                ],
                "Product Inquiry": [
                    "Product specifications", "Bulk order query", "Compatibility check",
                    "Feature request", "Product comparison",
                ],
                "Returns": [
                    "Return request", "Exchange needed", "Defective product",
                    "Wrong item received", "Return status check",
                ],
                "Account": [
                    "Password reset", "Account access issue", "Profile update",
                    "Account deletion request", "Subscription change",
                ],
                "Shipping": [
                    "Delivery delayed", "Track my order", "Address change",
                    "Shipping damage", "International shipping query",
                ],
                "General": [
                    "General inquiry", "Partnership proposal", "Feedback",
                    "Store hours", "Contact information",
                ],
            }

            subject = random.choice(subjects.get(category, ["General inquiry"]))
            resolved_at = None
            resolution = None
            if is_resolved:
                resolve_days = random.randint(0, 7) if priority in ["critical", "high"] else random.randint(1, 14)
                resolved_at = current_date + timedelta(days=resolve_days)
                resolution = f"Resolved: {subject} - addressed customer concern"

            ticket = SupportTicket(
                customer_id=customer.id,
                subject=subject,
                description=f"Customer reported: {subject.lower()}. Priority: {priority}.",
                category=category,
                priority=priority,
                status="resolved" if is_resolved else random.choice(["open", "in_progress"]),
                assigned_to=random_name(),
                resolution=resolution,
                created_at=current_date,
                resolved_at=resolved_at,
            )
            tickets.append(ticket)

    session.add_all(tickets)
    session.commit()
    print(f"  ✓ Created {len(tickets)} support tickets")


def seed_users(session):
    """Seed initial administrator account for immediate login."""
    admin = User(
        email="admin@example.com",
        full_name="Operations Admin",
        hashed_password=hash_password("admin123"),
        is_active=True,
        is_admin=True,
    )
    session.add(admin)
    session.commit()
    print("  ✓ Admin user created: admin@example.com (Password: admin123)")


# =============================================================================
# Main Seed Runner
# =============================================================================
def run_seed():
    """Execute full database seeding."""
    print("\n" + "=" * 60)
    print("  AI Business Agent — Database Seeding")
    print("=" * 60)

    # Create all tables
    print("\n▶ Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("  ✓ Tables created")

    session = SyncSessionLocal()
    try:
        # Check if data already exists
        existing = session.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if existing and existing > 0:
            print(f"\n⚠ Database already has {existing} customers. Skipping seed.")
            print("  To re-seed, drop the database and run again.")
            return

        print("\n▶ Seeding customers...")
        customers = seed_customers(session)

        print("\n▶ Seeding products...")
        products = seed_products(session)

        print("\n▶ Seeding orders & order items (this may take a minute)...")
        seed_orders_and_items(session, customers, products)

        print("\n▶ Seeding employees...")
        seed_employees(session)

        print("\n▶ Seeding expenses...")
        seed_expenses(session)

        print("\n▶ Seeding marketing campaigns...")
        seed_marketing_campaigns(session)

        print("\n▶ Seeding support tickets...")
        seed_support_tickets(session, customers)

        print("\n▶ Seeding admin user...")
        seed_users(session)

        print("\n" + "=" * 60)
        print("  ✅ Database seeding complete!")
        print("=" * 60 + "\n")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Seeding failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
