"""
HTTP request/response shapes for the support API.

Plain idea: describe the JSON we accept and return.
Technical idea: Pydantic models — FastAPI validates input automatically.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SupportAskRequest(BaseModel):
    """Body for POST /v1/support/ask"""

    question: str = Field(..., min_length=1, description="Customer message")
    channel: str = Field(
        default="api",
        description="Where the question came from (api, web, twilio, ...)",
    )


class SupportAskResponse(BaseModel):
    """JSON returned to the caller."""

    question: str
    reply: str
    outcome: str
    action: str
    classification: Optional[str] = None
    classification_label: Optional[str] = None
    notes: str = ""
    escalation: Optional[dict[str, Any]] = None
    log_path: str = ""


class HealthResponse(BaseModel):
    status: str
    service: str
    ai_client: str
