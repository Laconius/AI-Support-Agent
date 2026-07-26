"""
Load secrets and settings from the project .env file.

Plain idea: keep API keys out of code.
Technical idea: environment variables loaded via python-dotenv.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the app/ folder (where README.md and .env live)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

OPENAI_API_KEY_NAME = "OPENAI_API_KEY"


def load_env() -> None:
    """Read .env into process environment variables (if the file exists)."""
    load_dotenv(ENV_PATH)


def get_openai_api_key() -> str | None:
    """Return the OpenAI API key, or None if missing."""
    load_env()
    key = os.getenv(OPENAI_API_KEY_NAME)
    if key is None:
        return None
    key = key.strip().strip('"').strip("'")
    return key or None


def openai_key_status() -> dict:
    """
    Safe status for display/logging.

    Never includes the full key — only whether it loaded and a few checks.
    """
    key = get_openai_api_key()

    if not key:
        return {
            "loaded": False,
            "message": (
                f"API key not loaded. Create {ENV_PATH.name} in the project root "
                f"with a line like: {OPENAI_API_KEY_NAME}=sk-proj-..."
            ),
        }

    # Soft validation — helps catch the double-prefix mistake (sk-sk-...)
    looks_like_openai = key.startswith("sk-") and not key.startswith("sk-sk-")
    prefix = "sk-proj-..." if key.startswith("sk-proj-") else "sk-..."

    return {
        "loaded": True,
        "looks_like_openai": looks_like_openai,
        "prefix": prefix,
        "length": len(key),
        "message": (
            "API key loaded successfully "
            f"(prefix {prefix}, length {len(key)})."
            if looks_like_openai
            else "API key loaded, but the format looks unusual. "
            "Confirm it matches the key shown in your OpenAI dashboard."
        ),
    }


def print_openai_key_status() -> bool:
    """Print a safe status line. Returns True if a usable-looking key is loaded."""
    status = openai_key_status()
    print(status["message"])
    return bool(status.get("loaded") and status.get("looks_like_openai", False))
