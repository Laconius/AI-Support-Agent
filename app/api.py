"""
FastAPI web entry point for the AI Support Agent.

Plain idea: other systems talk to us over HTTP (browsers, Twilio webhooks,
mobile apps) instead of only through the terminal.

Technical idea: FastAPI app that calls agent_service.handle_question —
same brain as the CLI, different door.

The browser chat UI lives in /web and is served at /.
It POSTs to /v1/support/ask — the same endpoint a Shopify widget can use later.

Run from project root (with venv active):

    .\\.venv\\Scripts\\uvicorn.exe api:app --app-dir app --reload --host 127.0.0.1 --port 8000

Then open:
  - Chat UI:  http://127.0.0.1:8000/
  - API docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent_service import handle_question
from ai_client import describe_ai_client
from schemas import HealthResponse, SupportAskRequest, SupportAskResponse
from tenant import get_tenant

# Project root /web — HTML/CSS/JS for the chat channel.
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

_tenant = get_tenant()

app = FastAPI(
    title=f"AI Support Agent — {_tenant.display_name}",
    description=(
        "HTTP API for the customer support agent. "
        "Same pipeline as the CLI: guardrails → classify → facts → responses → log. "
        f"Active tenant: {_tenant.id}."
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

# CSS/JS at /static/... (index.html references these paths).
if WEB_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


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


@app.get("/api")
def api_info() -> dict[str, str]:
    """Machine-readable pointers (chat UI owns /)."""
    tenant = get_tenant()
    return {
        "service": "ai-support-agent",
        "tenant": tenant.id,
        "display_name": tenant.display_name,
        "docs": "/docs",
        "health": "/health",
        "ask": "POST /v1/support/ask",
        "chat": "/",
    }


@app.get("/")
def chat_ui() -> FileResponse:
    """Browser front door — same agent brain as CLI and /v1/support/ask."""
    index = WEB_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Chat UI not found (web/index.html).")
    return FileResponse(index)
