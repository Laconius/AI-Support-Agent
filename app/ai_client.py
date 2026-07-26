"""
AI provider client for the sleep-company support agent.

Plain idea: one place that knows *how* to talk to an AI service.
The rest of the app asks for a reply; it should not know OpenAI SDK details.

Technical idea: a thin adapter (also called a client wrapper).
Today the default provider is OpenAI. Tomorrow you can add Anthropic
(or another) behind the same functions without rewriting responses.py.

Public surface (stable):
  - get_ai_client() -> AiClient
  - AiClient.complete(messages) -> str

Secrets stay in .env via config.py. This file never hardcodes API keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from config import get_openai_api_key, load_env

# Environment knobs (optional — defaults are fine for learning).
AI_PROVIDER_ENV = "AI_PROVIDER"          # openai (default); later: anthropic, etc.
OPENAI_MODEL_ENV = "OPENAI_MODEL"        # e.g. gpt-4o-mini
DEFAULT_PROVIDER = "openai"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class ChatMessage:
    """
    One turn in a conversation with the model.

    role is usually:
      - "system"    = standing instructions (persona, safety)
      - "user"      = customer / app question
      - "assistant" = prior model reply (for multi-turn later)
    """

    role: str
    content: str


class AiClient(Protocol):
    """
    The shape every provider must implement.

    Plain idea: a promise — “you can complete a chat.”
    Technical idea: a Protocol (structural interface). Any class with
    a matching complete() method can be used as an AiClient.
    """

    provider_name: str
    model_name: str

    def complete(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> str:
        """Return the model's text reply for the given messages."""
        ...


class AiClientError(RuntimeError):
    """Raised when the AI client cannot be created or a call fails."""


class OpenAiClient:
    """OpenAI Chat Completions adapter."""

    def __init__(self, api_key: str, model: str) -> None:
        # Import inside __init__ so other providers do not require this package.
        from openai import OpenAI

        self.provider_name = "openai"
        self.model_name = model
        self._client = OpenAI(api_key=api_key)

    def complete(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> str:
        if not messages:
            raise AiClientError("complete() requires at least one ChatMessage.")

        payload = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=payload,
                temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001 - surface provider errors clearly
            raise AiClientError(f"OpenAI request failed: {exc}") from exc

        choice = response.choices[0].message.content if response.choices else None
        if not choice:
            raise AiClientError("OpenAI returned an empty response.")
        return choice.strip()


def _selected_provider() -> str:
    load_env()
    return (os.getenv(AI_PROVIDER_ENV) or DEFAULT_PROVIDER).strip().lower()


def _selected_openai_model() -> str:
    load_env()
    return (os.getenv(OPENAI_MODEL_ENV) or DEFAULT_OPENAI_MODEL).strip()


def get_ai_client() -> AiClient:
    """
    Build the configured AI client.

    Reads:
      AI_PROVIDER=openai          (default)
      OPENAI_API_KEY=...          (required for openai)
      OPENAI_MODEL=gpt-4o-mini    (optional)
    """
    provider = _selected_provider()

    if provider == "openai":
        api_key = get_openai_api_key()
        if not api_key:
            raise AiClientError(
                "OPENAI_API_KEY is missing. Add it to your project-root .env file."
            )
        return OpenAiClient(api_key=api_key, model=_selected_openai_model())

    # Future: elif provider == "anthropic": ...
    raise AiClientError(
        f"Unsupported AI_PROVIDER '{provider}'. "
        f"Supported today: openai. Set {AI_PROVIDER_ENV}=openai in .env."
    )


def describe_ai_client() -> str:
    """Safe one-line status for startup logs (never includes the API key)."""
    try:
        client = get_ai_client()
    except AiClientError as exc:
        return f"AI client not ready: {exc}"
    return f"AI client ready (provider={client.provider_name}, model={client.model_name})."


def smoke_complete(prompt: str = "Reply with exactly: OK") -> str:
    """
    Tiny live check against the real API (costs a fraction of a cent).

    Use only when you intentionally want to verify the connection.
    """
    client = get_ai_client()
    return client.complete(
        [
            ChatMessage(role="system", content="You are a connection test. Be terse."),
            ChatMessage(role="user", content=prompt),
        ],
        temperature=0,
    )
