"""
Guardrails for the sleep-company AI agent.

Plain idea: hard safety rules the agent must never break —
even after we wire a real AI that writes natural replies.

Technical idea: input checks (before we answer) and output checks
(after a draft reply exists). Rule-based for now; later an AI checker
can sit beside these same functions without changing main.py much.

Rules in this file:
  1) Do not diagnose medical conditions
  2) Do not recommend changing prescriptions
  3) Escalate emergencies
  4) Do not promise refunds
  5) Do not expose another customer's order information
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Actions main.py can take after a guardrail check.
ALLOW = "allow"
BLOCK = "block"
ESCALATE = "escalate"

# Machine-readable reasons (useful for logs and EscalationPacket notes).
REASON_MEDICAL_DIAGNOSIS = "medical_diagnosis"
REASON_PRESCRIPTION = "prescription_change"
REASON_EMERGENCY = "emergency"
REASON_REFUND_PROMISE = "refund_promise"
REASON_OTHER_CUSTOMER_ORDER = "other_customer_order"
REASON_OUTPUT_POLICY = "output_policy_violation"


@dataclass
class GuardrailResult:
    """
    What the guardrail decided.

    Plain idea: a traffic light for the reply pipeline.
    allow  = proceed
    block  = refuse with a safe customer message (do not invent an answer)
    escalate = hand off to a human immediately
    """

    action: str
    reason: Optional[str] = None
    message: str = ""

    @property
    def allowed(self) -> bool:
        return self.action == ALLOW


def _contains_any(text: str, clues: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(clue in lowered for clue in clues)


# --- Input checks (customer message) -----------------------------------------

_EMERGENCY_CLUES = [
    "emergency",
    "chest pain",
    "can't breathe",
    "cannot breathe",
    "suicidal",
    "kill myself",
    "hurt myself",
    "overdose",
    "call 911",
    "call 999",
]

_DIAGNOSIS_CLUES = [
    "do i have",
    "diagnose me",
    "what disease",
    "what condition do i have",
    "is this insomnia disorder",
    "am i depressed",
    "do i have sleep apnea",
    "is this apnea",
    "medical diagnosis",
]

_PRESCRIPTION_CLUES = [
    "change my prescription",
    "stop taking my",
    "stop my medication",
    "increase my dose",
    "decrease my dose",
    "should i stop taking",
    "should i change my medication",
    "replace my prescription",
    "instead of my medication",
]

_OTHER_CUSTOMER_CLUES = [
    "my husband's order",
    "my husbands order",
    "my wife's order",
    "my wifes order",
    "my boyfriend's order",
    "my girlfriend's order",
    "someone else's order",
    "someone elses order",
    "another customer's order",
    "another customers order",
    "look up their order",
    "look up his order",
    "look up her order",
    "friend's order",
    "friends order",
    "neighbor's order",
]


def check_input(question: str) -> GuardrailResult:
    """
    Inspect the customer's message *before* we classify / answer.

    Emergencies escalate first. Other violations block with a safe refusal.
    """
    text = (question or "").strip()
    if not text:
        return GuardrailResult(ALLOW)

    if _contains_any(text, _EMERGENCY_CLUES):
        return GuardrailResult(
            action=ESCALATE,
            reason=REASON_EMERGENCY,
            message=(
                "If you are in immediate danger, please contact local emergency "
                "services right away. I am escalating this so a teammate can help."
            ),
        )

    if _contains_any(text, _PRESCRIPTION_CLUES):
        return GuardrailResult(
            action=BLOCK,
            reason=REASON_PRESCRIPTION,
            message=(
                "I cannot recommend changing, stopping, or adjusting prescriptions "
                "or medication. Please talk with a qualified clinician or pharmacist "
                "about medication decisions. I can still help with product or "
                "general sleep-habit questions."
            ),
        )

    if _contains_any(text, _DIAGNOSIS_CLUES):
        return GuardrailResult(
            action=BLOCK,
            reason=REASON_MEDICAL_DIAGNOSIS,
            message=(
                "I cannot diagnose medical conditions. I can share general "
                "wellness tips from our approved sleep guidance, but anything "
                "about a personal diagnosis needs a qualified clinician."
            ),
        )

    if _contains_any(text, _OTHER_CUSTOMER_CLUES):
        return GuardrailResult(
            action=BLOCK,
            reason=REASON_OTHER_CUSTOMER_ORDER,
            message=(
                "For privacy, I can only discuss orders with the account holder. "
                "Please have that person contact us from their own account or "
                "email, or I can escalate this to a teammate."
            ),
        )

    return GuardrailResult(ALLOW)


# --- Output checks (draft reply, including future AI text) -------------------

_REFUND_PROMISE_PATTERNS = [
    r"\bi (?:will|can|have) (?:issue|process|approve|send) (?:you )?(?:a )?refund\b",
    r"\byour refund (?:is|has been|will be) (?:approved|issued|processed|guaranteed)\b",
    r"\bi(?:'| a)?m (?:issuing|approving|processing) (?:your )?refund\b",
    r"\bguaranteed refund\b",
    r"\bfull refund (?:is|has been) (?:yours|approved)\b",
]

_DIAGNOSIS_OUTPUT_CLUES = [
    "you have sleep apnea",
    "you have insomnia disorder",
    "you are depressed",
    "your diagnosis is",
    "i diagnose",
    "this means you have",
]

_PRESCRIPTION_OUTPUT_CLUES = [
    "stop taking your medication",
    "change your prescription",
    "increase your dose",
    "decrease your dose",
    "replace your medication with",
]


def check_output(draft: str, question: str = "") -> GuardrailResult:
    """
    Inspect a draft reply *after* knowledge / orders / (later) AI wrote it.

    If the draft breaks a rule, block it and return a safe replacement message.
    """
    text = (draft or "").strip()
    if not text:
        return GuardrailResult(ALLOW)

    lowered = text.lower()

    for pattern in _REFUND_PROMISE_PATTERNS:
        if re.search(pattern, lowered):
            return GuardrailResult(
                action=BLOCK,
                reason=REASON_REFUND_PROMISE,
                message=(
                    "I can explain our return and refund policy, but I cannot "
                    "promise or approve a refund myself. A teammate reviews "
                    "refund decisions. Would you like me to escalate this?"
                ),
            )

    if _contains_any(lowered, _DIAGNOSIS_OUTPUT_CLUES):
        return GuardrailResult(
            action=BLOCK,
            reason=REASON_MEDICAL_DIAGNOSIS,
            message=(
                "I almost shared wording that sounded like a medical diagnosis. "
                "I cannot do that. Please speak with a qualified clinician about "
                "personal medical concerns."
            ),
        )

    if _contains_any(lowered, _PRESCRIPTION_OUTPUT_CLUES):
        return GuardrailResult(
            action=BLOCK,
            reason=REASON_PRESCRIPTION,
            message=(
                "I cannot recommend changing prescriptions or medication. "
                "Please consult a qualified clinician or pharmacist."
            ),
        )

    # Rudimentary PII leak check: draft should not dump another customer's email
    # when the customer did not mention that email themselves.
    emails_in_draft = set(re.findall(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", lowered))
    emails_in_question = set(
        re.findall(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", (question or "").lower())
    )
    unexpected = emails_in_draft - emails_in_question
    if unexpected:
        return GuardrailResult(
            action=BLOCK,
            reason=REASON_OTHER_CUSTOMER_ORDER,
            message=(
                "I cannot share another customer's account or order details. "
                "Please sign in with the account that placed the order, or ask "
                "a teammate for help after verifying identity."
            ),
        )

    return GuardrailResult(ALLOW)


def apply_output_guardrails(draft: str, question: str = "") -> str:
    """Convenience: return the draft if safe, otherwise the safe refusal text."""
    result = check_output(draft, question=question)
    if result.allowed:
        return draft
    return result.message


def policy_summary() -> str:
    """Human-readable list of active guardrails (handy for docs / operators)."""
    return "\n".join(
        [
            "Active guardrails:",
            "  - Do not diagnose medical conditions",
            "  - Do not recommend changing prescriptions",
            "  - Escalate emergencies",
            "  - Do not promise refunds",
            "  - Do not expose another customer's order information",
        ]
    )
