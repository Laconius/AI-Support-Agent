"""
Support helpers for the sleep-company AI agent.

Phase 1: classify a customer request into one category.
Escalation creates a structured handoff package for humans.

Order *actions* (lookup, status, tracking) live in orders.py.
This file only decides that a request belongs in the Order Help lane.

Reply drafting and real AI come later.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

# Stable labels we use in code (snake_case).
# Human-friendly names are in CATEGORY_LABELS for printing.
ORDER_HELP = "order_help"
PRODUCT_QUESTIONS = "product_questions"
SLEEP_GUIDANCE = "sleep_guidance"
ACCOUNT_HELP = "account_help"
RETURNS_REFUNDS_COMPLAINTS = "returns_refunds_complaints"
ESCALATION = "escalation"

CATEGORY_LABELS = {
    ORDER_HELP: "Order Help",
    PRODUCT_QUESTIONS: "Product Questions",
    SLEEP_GUIDANCE: "General Sleep Guidance",
    ACCOUNT_HELP: "Account Help",
    RETURNS_REFUNDS_COMPLAINTS: "Returns, Refunds, and Complaints",
    ESCALATION: "Escalation",
}

# Priority levels for human operators (lower number = more urgent).
PRIORITY_CRITICAL = "P1_critical"
PRIORITY_HIGH = "P2_high"
PRIORITY_NORMAL = "P3_normal"

# Why we escalated — useful for routing and reporting.
REASON_REQUESTED_HUMAN = "requested_human"
REASON_LEGAL = "legal"
REASON_SAFETY = "safety"
REASON_REFUND_DISPUTE = "refund_dispute"
REASON_NO_MATCH = "no_match"
REASON_EMPTY = "empty_message"
REASON_AGENT_STUCK = "agent_stuck"

# Shown whenever we answer sleep-guidance questions.
SLEEP_DISCLAIMER = (
    "This is general wellness information for better sleep, "
    "not medical advice. If you have a health condition or "
    "ongoing sleep problems, please talk with a qualified clinician."
)


@dataclass
class EscalationPacket:
    """
    The handoff package a human operator receives.

    Plain idea: everything a teammate needs in one place.
    Technical idea: a dataclass — a typed container for related fields.

    Later adapters (email, Slack, Twilio queue) all consume this same shape.
    """

    conversation_id: str
    question: str
    category: str
    reason: str
    priority: str
    created_at: str
    customer_id: Optional[str] = None
    channel: str = "cli"
    transcript: list[str] = field(default_factory=list)
    notes_for_human: str = ""

    def to_dict(self) -> dict:
        """Convert to a plain dictionary (handy for JSON, email, or logging)."""
        return asdict(self)

    def summary(self) -> str:
        """Short human-readable block for the terminal today."""
        lines = [
            f"Escalation ID: {self.conversation_id}",
            f"Priority:      {self.priority}",
            f"Reason:        {self.reason}",
            f"Category:      {category_label(self.category)}",
            f"Channel:       {self.channel}",
            f"Created:       {self.created_at}",
        ]
        if self.customer_id:
            lines.append(f"Customer:      {self.customer_id}")
        lines.append(f"Question:      {self.question}")
        if self.notes_for_human:
            lines.append(f"Notes:         {self.notes_for_human}")
        return "\n".join(lines)


def classify_request(question: str) -> str:
    """
    Decide which support category best fits the customer's question.

    Returns one of the category constants above.
    Uses simple keyword matching for now (rule-based classification).
    """
    text = (question or "").lower().strip()

    if not text:
        return ESCALATION

    # 1) Force escalation when the customer is stuck, angry, or asks for a human.
    escalation_clues = [
        "speak to a human",
        "talk to a person",
        "real person",
        "manager",
        "supervisor",
        "this isn't helping",
        "this is not helping",
        "frustrated",
        "angry",
        "lawsuit",
        "attorney",
        "lawyer",
    ]
    if any(clue in text for clue in escalation_clues):
        return ESCALATION

    # 2) Returns / refunds / complaints (money + dissatisfaction — handle carefully).
    returns_clues = [
        "return",
        "refund",
        "money back",
        "complaint",
        "complain",
        "unhappy",
        "defective",
        "broken",
        "damaged",
        "wrong item",
    ]
    if any(clue in text for clue in returns_clues):
        return RETURNS_REFUNDS_COMPLAINTS

    # 3) Account help (login, password, profile).
    account_clues = [
        "account",
        "password",
        "login",
        "log in",
        "sign in",
        "email address",
        "username",
        "profile",
    ]
    if any(clue in text for clue in account_clues):
        return ACCOUNT_HELP

    # 4) Order help (shipping, tracking, delivery).
    # Classification only — see orders.py for lookup / status / tracking.
    order_clues = [
        "order",
        "shipping",
        "shipped",
        "tracking",
        "track my",
        "delivery",
        "delivered",
        "package",
        "where is my",
    ]
    if any(clue in text for clue in order_clues):
        return ORDER_HELP

    # 5) Product questions (what we sell / how it works).
    product_clues = [
        "product",
        "mattress",
        "pillow",
        "sheets",
        "bedding",
        "firmness",
        "materials",
        "warranty",
        "how does it work",
        "what's included",
        "what is included",
        "size",
        "dimensions",
    ]
    if any(clue in text for clue in product_clues):
        return PRODUCT_QUESTIONS

    # 6) General sleep guidance (tips / habits — not medical care).
    sleep_clues = [
        "sleep",
        "can't sleep",
        "cannot sleep",
        "insomnia",
        "tired",
        "rest",
        "bedtime",
        "wake up",
        "snoring",
        "better sleep",
        "sleep tip",
        "sleep advice",
    ]
    if any(clue in text for clue in sleep_clues):
        return SLEEP_GUIDANCE

    # 7) Nothing matched → escalate rather than guess.
    return ESCALATION


def category_label(category: str) -> str:
    """Turn a category code into a readable name for display."""
    return CATEGORY_LABELS.get(category, CATEGORY_LABELS[ESCALATION])


def _contains_any(text: str, clues: list[str]) -> bool:
    return any(clue in text for clue in clues)


def infer_escalation_reason(question: str) -> str:
    """Decide *why* this should go to a human."""
    text = (question or "").lower().strip()

    if not text:
        return REASON_EMPTY

    legal_clues = ["lawsuit", "attorney", "lawyer", "sue", "legal action"]
    if _contains_any(text, legal_clues):
        return REASON_LEGAL

    safety_clues = [
        "emergency",
        "chest pain",
        "can't breathe",
        "cannot breathe",
        "suicidal",
        "hurt myself",
    ]
    if _contains_any(text, safety_clues):
        return REASON_SAFETY

    human_clues = [
        "speak to a human",
        "talk to a person",
        "real person",
        "manager",
        "supervisor",
    ]
    if _contains_any(text, human_clues):
        return REASON_REQUESTED_HUMAN

    stuck_clues = [
        "this isn't helping",
        "this is not helping",
        "frustrated",
        "angry",
    ]
    if _contains_any(text, stuck_clues):
        return REASON_AGENT_STUCK

    refund_clues = ["refund", "return", "money back", "complaint", "complain"]
    if _contains_any(text, refund_clues):
        return REASON_REFUND_DISPUTE

    return REASON_NO_MATCH


def priority_for_reason(reason: str) -> str:
    """Map escalation reason to an operator priority."""
    if reason in {REASON_LEGAL, REASON_SAFETY}:
        return PRIORITY_CRITICAL
    if reason in {REASON_REQUESTED_HUMAN, REASON_REFUND_DISPUTE, REASON_AGENT_STUCK}:
        return PRIORITY_HIGH
    return PRIORITY_NORMAL


def build_escalation_packet(
    question: str,
    category: str = ESCALATION,
    customer_id: Optional[str] = None,
    channel: str = "cli",
    transcript: Optional[list[str]] = None,
) -> EscalationPacket:
    """
    Build the handoff package for a human operator.

    Today we print it. Later we can email it, post it to Slack,
    or open a ticket — without changing this shape.
    """
    reason = infer_escalation_reason(question)
    priority = priority_for_reason(reason)
    notes = {
        REASON_LEGAL: "Possible legal issue - do not continue automated replies.",
        REASON_SAFETY: "Possible safety concern - prioritize human contact; no medical advice.",
        REASON_REQUESTED_HUMAN: "Customer explicitly asked for a person.",
        REASON_AGENT_STUCK: "Customer indicates the automated path is failing.",
        REASON_REFUND_DISPUTE: "Money or dissatisfaction involved - review carefully.",
        REASON_EMPTY: "Empty message received.",
        REASON_NO_MATCH: "No classifier lane matched - avoid guessing.",
    }.get(reason, "")

    return EscalationPacket(
        conversation_id=str(uuid4()),
        question=(question or "").strip(),
        category=category,
        reason=reason,
        priority=priority,
        created_at=datetime.now(timezone.utc).isoformat(),
        customer_id=customer_id,
        channel=channel,
        transcript=list(transcript or ([question] if question else [])),
        notes_for_human=notes,
    )