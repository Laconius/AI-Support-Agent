"""
Customer-facing response writer for the sleep-company AI agent.

Plain idea: other modules discover *what is true*.
This module decides *how we say it* — first as a factual draft, then
(optionally) warmed up by the AI into friendlier customer language.

Technical idea: RAG-style generation.
  1) Retrieve / assemble facts (orders.py, knowledge.py)
  2) Generate wording with ai_client (grounded on those facts only)
  3) If the AI call fails, fall back to the clear template wording

Contract:
  facts in  ->  customer message out
Never invent facts. If a fact is missing, say so honestly.
"""

from __future__ import annotations

import os
from typing import Optional

from ai_client import AiClientError, ChatMessage, get_ai_client
from config import load_env
from knowledge import Snippet
from orders import (
    STATUS_CANCELLED,
    STATUS_PLACED,
    STATUS_PROCESSING,
    Order,
    OrderHelpFacts,
)
from support import SLEEP_DISCLAIMER

AI_WARM_REWRITE_ENV = "AI_WARM_REWRITE"  # true/false — default true

_SYSTEM_PROMPT = """
You are a helpful customer support writer for a better-sleep brand.

Your job: rewrite the FACTS below into warm, clear customer-facing language.

Hard rules:
- Use ONLY the provided facts. Do not invent order numbers, tracking, policies, or product claims.
- Do not diagnose medical conditions or recommend changing prescriptions.
- Do not promise or approve refunds. You may explain that a human reviews refunds.
- Do not mention other customers or private account data.
- Keep the reply concise (usually under 120 words).
- If the facts say something is unknown or missing, say that honestly.
- Do not add a medical disclaimer unless the facts already include one.
""".strip()


def _warm_rewrite_enabled() -> bool:
    load_env()
    raw = (os.getenv(AI_WARM_REWRITE_ENV) or "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _warm_rewrite(facts_text: str, *, customer_question: str = "", lane: str = "") -> str:
    """
    Ask the AI to rewrite factual text more warmly.

    On any failure, return facts_text unchanged (safe fallback).
    """
    if not _warm_rewrite_enabled():
        return facts_text

    user_parts = []
    if lane:
        user_parts.append(f"Support lane: {lane}")
    if customer_question.strip():
        user_parts.append(f"Customer question:\n{customer_question.strip()}")
    user_parts.append(f"FACTS (source of truth):\n{facts_text.strip()}")
    user_parts.append("Write the customer-facing reply now.")

    try:
        client = get_ai_client()
        return client.complete(
            [
                ChatMessage(role="system", content=_SYSTEM_PROMPT),
                ChatMessage(role="user", content="\n\n".join(user_parts)),
            ],
            temperature=0.3,
        )
    except AiClientError:
        return facts_text


def _template_order_help(facts: OrderHelpFacts) -> str:
    if not facts.order_id:
        return (
            "I can help with your order. Please share your order number "
            "(for example ORD-1001), and I will look up the status and tracking."
        )

    if facts.order is None:
        return (
            f"I could not find an order named {facts.order_id}. "
            "Please double-check the number, or I can escalate this to a teammate."
        )

    order = facts.order
    lines = [
        f"I found order {order.order_id}.",
        f"Current status: {order.status}.",
    ]

    if facts.tracking_number:
        carrier = order.carrier or "the carrier"
        lines.append(f"Tracking number ({carrier}): {facts.tracking_number}.")
    elif order.status in {STATUS_PLACED, STATUS_PROCESSING}:
        lines.append("A tracking number will appear after the order ships.")
    elif order.status == STATUS_CANCELLED:
        lines.append("This order was cancelled, so there is no tracking number.")

    if order.estimated_delivery and order.status != STATUS_CANCELLED:
        lines.append(f"Estimated delivery: {order.estimated_delivery}.")

    lines.append("")
    lines.append(_order_fact_card(order))
    return "\n".join(lines)


def _order_fact_card(order: Order) -> str:
    """Compact factual card (still customer-safe - no payment / full address)."""
    items = ", ".join(order.items) if order.items else "(no items listed)"
    lines = [
        f"Order:    {order.order_id}",
        f"Status:   {order.status}",
        f"Items:    {items}",
    ]
    if order.estimated_delivery:
        lines.append(f"ETA:      {order.estimated_delivery}")
    if order.has_shipped():
        lines.append(f"Carrier:  {order.carrier or 'n/a'}")
        lines.append(f"Tracking: {order.tracking_number}")
    elif order.status == STATUS_CANCELLED:
        lines.append("Note:     This order was cancelled.")
    else:
        lines.append("Tracking: Not available until the order ships.")
    return "\n".join(lines)


def render_order_help(facts: OrderHelpFacts, *, question: str = "") -> str:
    """Turn order lookup facts into a customer reply (AI-warmed when available)."""
    factual = _template_order_help(facts)
    return _warm_rewrite(factual, customer_question=question, lane="order_help")


def _template_knowledge_help(snippets: list[Snippet]) -> str:
    if not snippets:
        return (
            "I don't have that in my approved knowledge yet. "
            "I can escalate this to a teammate so you get an accurate answer."
        )

    parts: list[str] = ["Here is what our approved materials say:", ""]
    for snippet in snippets:
        parts.append(f"From {snippet.document} - {snippet.section}:")
        parts.append(snippet.content)
        parts.append("")

    sources = ", ".join(sorted({s.source_file for s in snippets}))
    parts.append(f"(Sources: {sources})")
    return "\n".join(parts)


def render_knowledge_help(
    snippets: list[Snippet],
    *,
    include_sleep_disclaimer: bool = False,
    question: str = "",
) -> str:
    """
    Turn retrieved knowledge snippets into a customer reply.

    The sleep disclaimer is attached outside the AI rewrite so it cannot be dropped.
    """
    factual = _template_knowledge_help(snippets)
    warmed = _warm_rewrite(
        factual,
        customer_question=question,
        lane="sleep_guidance" if include_sleep_disclaimer else "product_questions",
    )

    if include_sleep_disclaimer:
        return f"{SLEEP_DISCLAIMER}\n\n{warmed}"
    return warmed


def _template_account_help() -> str:
    return (
        "I can help with account access. Try the password-reset link "
        "if you cannot sign in."
    )


def render_account_help(*, question: str = "") -> str:
    """Placeholder account messaging until account tools exist."""
    return _warm_rewrite(
        _template_account_help(),
        customer_question=question,
        lane="account_help",
    )


def _template_returns_help() -> str:
    return (
        "I can explain our return and refund policy and help start a review. "
        "I cannot approve or promise a refund myself - a teammate makes that decision. "
        "Would you like me to escalate this for a human review?"
    )


def render_returns_help(*, question: str = "") -> str:
    """Returns / refunds messaging without promising a refund."""
    return _warm_rewrite(
        _template_returns_help(),
        customer_question=question,
        lane="returns_refunds_complaints",
    )


def _template_escalation_customer() -> str:
    return (
        "I want to make sure you get the right help.\n"
        "I am escalating this so a teammate can assist you."
    )


def render_escalation_customer(*, question: str = "") -> str:
    """What we say to the customer when handing off to a human."""
    return _warm_rewrite(
        _template_escalation_customer(),
        customer_question=question,
        lane="escalation",
    )


def render_from_facts(
    *,
    kind: str,
    order_facts: Optional[OrderHelpFacts] = None,
    snippets: Optional[list[Snippet]] = None,
    include_sleep_disclaimer: bool = False,
    question: str = "",
) -> str:
    """
    Single entry point for main.py.

    kind is one of: order, knowledge, account, returns, escalation.
    """
    if kind == "order":
        if order_facts is None:
            raise ValueError("order_facts is required when kind='order'")
        return render_order_help(order_facts, question=question)
    if kind == "knowledge":
        return render_knowledge_help(
            snippets or [],
            include_sleep_disclaimer=include_sleep_disclaimer,
            question=question,
        )
    if kind == "account":
        return render_account_help(question=question)
    if kind == "returns":
        return render_returns_help(question=question)
    if kind == "escalation":
        return render_escalation_customer(question=question)
    raise ValueError(f"Unknown response kind: {kind}")
