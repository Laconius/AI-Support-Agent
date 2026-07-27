"""
FastAPI web entry point for the AI Support Agent.

Plain idea: other systems talk to us over HTTP (browsers, Twilio webhooks,
mobile apps) instead of only through the terminal.

Technical idea: FastAPI app that calls agent_service.handle_question —
same brain as the CLI, different door.

Run from project root (with venv active):

    uvicorn app.api:app --reload --app-dir .

Or from the app folder:

    cd app
    ..\\.venv\\Scripts\\uvicorn.exe api:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_service import handle_question
from ai_client import describe_ai_client
from schemas import HealthResponse, SupportAskRequest, SupportAskResponse

app = FastAPI(
    title="AI Support Agent — Better Sleep",
    description=(
        "HTTP API for the customer support agent. "
        "Same pipeline as the CLI: guardrails → classify → facts → responses → log."
    ),
    version="0.1.0",
)

# CORS: allow browser frontends on other origins during local demos.
# Tighten allow_origins for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check for load balancers and smoke tests."""
    return HealthResponse(
        status="ok",
        service="ai-support-agent",
        ai_client=describe_ai_client(),
    )


@app.post("/v1/support/ask", response_model=SupportAskResponse)
def support_ask(body: SupportAskRequest) -> SupportAskResponse:
    """
    Send one customer question; get a reply plus routing metadata.

    This is the main integration point for web UIs and future services
    (Twilio adapters can POST here or call handle_question directly).
    """
    result = handle_question(body.question, channel=body.channel or "api")
    return SupportAskResponse(**result.to_dict())


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "ai-support-agent",
        "docs": "/docs",
        "health": "/health",
        "ask": "POST /v1/support/ask",
    }
