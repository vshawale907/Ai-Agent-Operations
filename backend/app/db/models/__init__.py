"""
Database models package.

Import all models here so Alembic and Base.metadata can discover them.
"""

from app.db.models.user import User
from app.db.models.business import (
    Customer,
    Product,
    Order,
    OrderItem,
    Employee,
    Expense,
    MarketingCampaign,
    SupportTicket,
)
from app.db.models.document import Document, DocumentChunk
from app.db.models.conversation import Conversation, ChatMessageModel

__all__ = [
    "User",
    "Customer",
    "Product",
    "Order",
    "OrderItem",
    "Employee",
    "Expense",
    "MarketingCampaign",
    "SupportTicket",
    "Document",
    "DocumentChunk",
    "Conversation",
    "ChatMessageModel",
]
