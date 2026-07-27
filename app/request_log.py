"""
Simple request log for learning and debugging.

Plain idea: after each customer question, write one line that says
what was asked, how we classified it, what we did, and how it ended.

Technical idea: append-only JSONL (JSON Lines) — one JSON object per line.
Easy to append, easy to open later in an editor or load line-by-line.

This is observability for learning, not a full production audit system.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_PATH = LOG_DIR / "support_requests.jsonl"

# Outcomes — how the request ended from the customer's perspective.
OUTCOME_ANSWERED = "answered"
OUTCOME_ESCALATED = "escalated"
OUTCOME_BLOCKED = "blocked"

# Actions — what the agent did (more specific than outcome).
ACTION_ORDER_LOOKUP = "order_lookup"
ACTION_KNOWLEDGE_REPLY = "knowledge_reply"
ACTION_ACCOUNT_HELP = "account_help"
ACTION_RETURNS_HELP = "returns_help"
ACTION_ESCALATE = "escalate"
ACTION_GUARDRAIL_BLOCK = "guardrail_block"
ACTION_GUARDRAIL_ESCALATE = "guardrail_escalate"


def log_request(
    *,
    question: str,
    classification: Optional[str],
    action: str,
    outcome: str,
    notes: str = "",
) -> Path:
    """
    Append one request record to the log file.

    Returns the path written (handy for a one-line console tip).
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": (question or "").strip(),
        "classification": classification,
        "action": action,
        "outcome": outcome,
        "notes": notes or "",
    }

    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return LOG_PATH
