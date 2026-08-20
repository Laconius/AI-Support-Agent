"""
API smoke tests.

Plain idea: make sure the web doors open — health, chat page, ask endpoint.
Technical idea: FastAPI TestClient talks to the app in-process (no manual uvicorn).

These do NOT judge answer quality deeply — that is the eval set's job.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from api import app  # noqa: E402


@pytest.fixture(autouse=True)
def _deterministic_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep /ask fast and stable in CI/local smoke runs.
    monkeypatch.setenv("AI_WARM_REWRITE", "false")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "ai-support-agent"
    assert "ai_client" in body


def test_chat_ui_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    text = response.text
    assert "Sopoforix" in text
    assert "/v1/support/ask" in Path(PROJECT_ROOT / "web" / "app.js").read_text(
        encoding="utf-8"
    )


def test_static_assets_served(client: TestClient) -> None:
    css = client.get("/static/styles.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "sea" in css.text or "night" in css.text
    assert "support/ask" in js.text


def test_api_info(client: TestClient) -> None:
    response = client.get("/api")
    assert response.status_code == 200
    body = response.json()
    assert body["ask"] == "POST /v1/support/ask"
    assert body["chat"] == "/"
    assert body["tenant"] == "sopoforix"
    assert body["display_name"] == "Sopoforix"


def test_support_ask_returns_shape(client: TestClient) -> None:
    response = client.post(
        "/v1/support/ask",
        json={"question": "Where is order ORD-1001?", "channel": "web"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "Where is order ORD-1001?"
    assert isinstance(body["reply"], str) and body["reply"].strip()
    assert body["outcome"] in {"answered", "blocked", "escalated"}
    assert body["action"]
    assert "ORD-1001" in body["reply"]
