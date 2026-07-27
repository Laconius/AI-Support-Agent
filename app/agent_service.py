"""
Shared support agent pipeline.

Plain idea: one function that takes a customer question and returns
what happened — used by the CLI (main.py) and the web API (api.py).

Technical idea: a service layer. Channels (CLI, HTTP, later Twilio)
should not re-implement guardrails / classify / respond / log.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from guardrails import (
    ESCALATE,
    apply_output_guardrails,
    check_input,
)
from knowledge import search_knowledge
from orders import get_order_help_facts
from request_log import (
    ACTION_ACCOUNT_HELP,
    ACTION_ESCALATE,
    ACTION_GUARDRAIL_BLOCK,
    ACTION_GUARDRAIL_ESCALATE,
    ACTION_KNOWLEDGE_REPLY,
    ACTION_ORDER_LOOKUP,
    ACTION_RETURNS_HELP,
    LOG_PATH,
    OUTCOME_ANSWERED,
    OUTCOME_BLOCKED,
    OUTCOME_ESCALATED,
    log_request,
)
from responses import (
    render_account_help,
    render_escalation_customer,
    render_knowledge_help,
    render_order_help,
    render_returns_help,
)
from support import (
    ACCOUNT_HELP,
    ESCALATION,
    ORDER_HELP,
    PRODUCT_QUESTIONS,
    RETURNS_REFUNDS_COMPLAINTS,
    SLEEP_GUIDANCE,
    build_escalation_packet,
    category_label,
    classify_request,
)


@dataclass
class AgentResult:
    """What one support turn produced — channel-agnostic."""

    question: str
    reply: str
    outcome: str
    action: str
    classification: Optional[str] = None
    classification_label: Optional[str] = None
    notes: str = ""
    escalation: Optional[dict[str, Any]] = None
    log_path: str = str(LOG_PATH)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def handle_question(question: str, *, channel: str = "cli") -> AgentResult:
    """
    Run the full support pipeline for one customer question.

    Steps: input guardrails -> classify -> draft reply -> output guardrails -> log.
    """
    text = (question or "").strip()

    safety = check_input(text)
    if safety.action == ESCALATE:
        packet = build_escalation_packet(
            text, category=ESCALATION, channel=channel
        )
        log_request(
            question=text,
            classification=None,
            action=ACTION_GUARDRAIL_ESCALATE,
            outcome=OUTCOME_ESCALATED,
            notes=safety.reason or "guardrail_escalate",
        )
        return AgentResult(
            question=text,
            reply=safety.message,
            outcome=OUTCOME_ESCALATED,
            action=ACTION_GUARDRAIL_ESCALATE,
            notes=safety.reason or "",
            escalation=packet.to_dict(),
        )

    if safety.action != "allow":
        log_request(
            question=text,
            classification=None,
            action=ACTION_GUARDRAIL_BLOCK,
            outcome=OUTCOME_BLOCKED,
            notes=safety.reason or "guardrail_block",
        )
        return AgentResult(
            question=text,
            reply=safety.message,
            outcome=OUTCOME_BLOCKED,
            action=ACTION_GUARDRAIL_BLOCK,
            notes=safety.reason or "",
        )

    category = classify_request(text)
    label = category_label(category)

    if category == SLEEP_GUIDANCE:
        snippets = search_knowledge(text, prefer_file="sleep-tips.md")
        draft = render_knowledge_help(
            snippets,
            include_sleep_disclaimer=True,
            question=text,
        )
        action = ACTION_KNOWLEDGE_REPLY
        notes = "prefer_file=sleep-tips.md"
        reply = apply_output_guardrails(draft, question=text)
        log_request(
            question=text,
            classification=category,
            action=action,
            outcome=OUTCOME_ANSWERED,
            notes=notes,
        )
        return AgentResult(
            question=text,
            reply=reply,
            outcome=OUTCOME_ANSWERED,
            action=action,
            classification=category,
            classification_label=label,
            notes=notes,
        )

    if category == ORDER_HELP:
        draft = render_order_help(get_order_help_facts(text), question=text)
        action = ACTION_ORDER_LOOKUP
        notes = ""
        reply = apply_output_guardrails(draft, question=text)
        log_request(
            question=text,
            classification=category,
            action=action,
            outcome=OUTCOME_ANSWERED,
            notes=notes,
        )
        return AgentResult(
            question=text,
            reply=reply,
            outcome=OUTCOME_ANSWERED,
            action=action,
            classification=category,
            classification_label=label,
            notes=notes,
        )

    if category == PRODUCT_QUESTIONS:
        draft = render_knowledge_help(search_knowledge(text), question=text)
        action = ACTION_KNOWLEDGE_REPLY
        notes = ""
        reply = apply_output_guardrails(draft, question=text)
        log_request(
            question=text,
            classification=category,
            action=action,
            outcome=OUTCOME_ANSWERED,
            notes=notes,
        )
        return AgentResult(
            question=text,
            reply=reply,
            outcome=OUTCOME_ANSWERED,
            action=action,
            classification=category,
            classification_label=label,
            notes=notes,
        )

    if category == ACCOUNT_HELP:
        draft = render_account_help(question=text)
        action = ACTION_ACCOUNT_HELP
        reply = apply_output_guardrails(draft, question=text)
        log_request(
            question=text,
            classification=category,
            action=action,
            outcome=OUTCOME_ANSWERED,
            notes="",
        )
        return AgentResult(
            question=text,
            reply=reply,
            outcome=OUTCOME_ANSWERED,
            action=action,
            classification=category,
            classification_label=label,
        )

    if category == RETURNS_REFUNDS_COMPLAINTS:
        draft = render_returns_help(question=text)
        action = ACTION_RETURNS_HELP
        reply = apply_output_guardrails(draft, question=text)
        log_request(
            question=text,
            classification=category,
            action=action,
            outcome=OUTCOME_ANSWERED,
            notes="",
        )
        return AgentResult(
            question=text,
            reply=reply,
            outcome=OUTCOME_ANSWERED,
            action=action,
            classification=category,
            classification_label=label,
        )

    # Escalation lane (or unknown fallback)
    packet = build_escalation_packet(text, category=category, channel=channel)
    draft = render_escalation_customer(question=text)
    reply = apply_output_guardrails(draft, question=text)
    notes = f"priority={packet.priority}; reason={packet.reason}"
    log_request(
        question=text,
        classification=category,
        action=ACTION_ESCALATE,
        outcome=OUTCOME_ESCALATED,
        notes=notes,
    )
    return AgentResult(
        question=text,
        reply=reply,
        outcome=OUTCOME_ESCALATED,
        action=ACTION_ESCALATE,
        classification=category,
        classification_label=label,
        notes=notes,
        escalation=packet.to_dict(),
    )
