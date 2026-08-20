"""
Order tools for the sleep-company AI agent.

Plain idea: once we know the customer is asking about an order,
this file looks up the *facts* (status, tracking).

Technical idea: a small data/service module. Classification stays in
support.py; customer wording lives in responses.py.

Today we use sample orders from the active tenant pack (orders.json).
Later this can call a real order system (Shopify, ERP, etc.) without
changing how responses.py phrases the reply.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Optional

from tenant import get_tenant

# Status values we allow in sample / future real data.
STATUS_PLACED = "placed"
STATUS_PROCESSING = "processing"
STATUS_SHIPPED = "shipped"
STATUS_DELIVERED = "delivered"
STATUS_CANCELLED = "cancelled"


@dataclass
class Order:
    """
    One customer order.

    Plain idea: the facts about a purchase.
    Technical idea: a dataclass - a typed container for related fields.
    """

    order_id: str
    customer_name: str
    email: str
    status: str
    items: list[str]
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    shipped_at: Optional[str] = None
    estimated_delivery: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def has_shipped(self) -> bool:
        """True when the order is on its way or already delivered."""
        return self.status in {STATUS_SHIPPED, STATUS_DELIVERED} and bool(
            self.tracking_number
        )


@dataclass
class OrderHelpFacts:
    """
    Everything responses.py needs to talk about an order question.

    Plain idea: the truth packet for Order Help.
    order_id is None when the customer did not provide a number.
    order is None when we looked up an id and found nothing.
    """

    order_id: Optional[str]
    order: Optional[Order]
    tracking_number: Optional[str] = None


def _load_orders() -> dict[str, Order]:
    """Read sample orders from disk into Order objects."""
    orders_path = get_tenant().orders_path
    if not orders_path.exists():
        return {}

    raw = json.loads(orders_path.read_text(encoding="utf-8"))
    orders: dict[str, Order] = {}
    for row in raw:
        order = Order(
            order_id=str(row["order_id"]).upper(),
            customer_name=row.get("customer_name", ""),
            email=row.get("email", ""),
            status=str(row.get("status", STATUS_PLACED)).lower(),
            items=list(row.get("items") or []),
            tracking_number=row.get("tracking_number"),
            carrier=row.get("carrier"),
            shipped_at=row.get("shipped_at"),
            estimated_delivery=row.get("estimated_delivery"),
        )
        orders[order.order_id] = order
    return orders


def extract_order_id(text: str) -> Optional[str]:
    """
    Pull an order number out of free-form customer text.

    Accepts patterns like:
      ORD-1001, ord-1001, #1001, order 1001
    """
    if not text:
        return None

    cleaned = text.strip()

    match = re.search(r"\bORD-?\d{3,}\b", cleaned, flags=re.IGNORECASE)
    if match:
        digits = re.sub(r"\D", "", match.group(0))
        return f"ORD-{digits}"

    match = re.search(r"#\s*(\d{3,})", cleaned)
    if match:
        return f"ORD-{match.group(1)}"

    match = re.search(
        r"\border\s*(?:number|#)?\s*(\d{3,})\b", cleaned, flags=re.IGNORECASE
    )
    if match:
        return f"ORD-{match.group(1)}"

    return None


def lookup_order(order_id: str) -> Optional[Order]:
    """Find one order by ID. Returns None if it does not exist."""
    if not order_id:
        return None
    normalized = order_id.strip().upper()
    if normalized.isdigit():
        normalized = f"ORD-{normalized}"
    if normalized.startswith("ORD") and not normalized.startswith("ORD-"):
        digits = re.sub(r"\D", "", normalized)
        normalized = f"ORD-{digits}"
    return _load_orders().get(normalized)


def get_order_status(order_id: str) -> Optional[str]:
    """Return the status string for an order, or None if not found."""
    order = lookup_order(order_id)
    return order.status if order else None


def get_tracking_number(order_id: str) -> Optional[str]:
    """
    Return a tracking number only when the order has shipped.

    If the order exists but has not shipped, returns None.
    If the order does not exist, also returns None - use lookup_order
    first when you need to tell those cases apart.
    """
    order = lookup_order(order_id)
    if not order or not order.has_shipped():
        return None
    return order.tracking_number


def get_order_help_facts(question: str) -> OrderHelpFacts:
    """
    Resolve Order Help into facts for responses.py.

    Does not write customer-facing prose - that is responses.render_order_help.
    """
    order_id = extract_order_id(question)
    if not order_id:
        return OrderHelpFacts(order_id=None, order=None, tracking_number=None)

    order = lookup_order(order_id)
    tracking = get_tracking_number(order_id) if order else None
    return OrderHelpFacts(order_id=order_id, order=order, tracking_number=tracking)
