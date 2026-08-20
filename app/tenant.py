"""
Active business (tenant) configuration.

Plain idea: one shared agent engine; each business has a folder of its own
name, knowledge, and sample orders.

Technical idea: load tenants/<id>/config.json and resolve paths from there.
Default tenant is sopoforix (ACTIVE_TENANT in .env).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from config import PROJECT_ROOT, load_env

TENANTS_DIR = PROJECT_ROOT / "tenants"
DEFAULT_TENANT_ID = "sopoforix"
ACTIVE_TENANT_ENV = "ACTIVE_TENANT"


@dataclass(frozen=True)
class TenantConfig:
    """One business pack loaded from disk."""

    id: str
    display_name: str
    tagline: str
    support_intro: str
    root: Path
    knowledge_dir: Path
    orders_path: Path

    def brand_line(self) -> str:
        return f"{self.display_name} — {self.tagline}"


def active_tenant_id() -> str:
    load_env()
    raw = (os.getenv(ACTIVE_TENANT_ENV) or DEFAULT_TENANT_ID).strip()
    return raw or DEFAULT_TENANT_ID


@lru_cache(maxsize=4)
def load_tenant(tenant_id: str | None = None) -> TenantConfig:
    """
    Read tenants/<id>/config.json and return resolved paths.

    Raises FileNotFoundError if the pack is missing.
    """
    tid = (tenant_id or active_tenant_id()).strip()
    root = TENANTS_DIR / tid
    config_path = root / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Tenant pack not found: {config_path}. "
            f"Expected tenants/{tid}/config.json"
        )

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    knowledge_rel = raw.get("knowledge_dir") or "knowledge"
    orders_rel = raw.get("orders_file") or "orders.json"

    return TenantConfig(
        id=str(raw.get("id") or tid),
        display_name=str(raw.get("display_name") or tid.title()),
        tagline=str(raw.get("tagline") or ""),
        support_intro=str(
            raw.get("support_intro")
            or f"Hi — I’m the {raw.get('display_name', tid)} support agent."
        ),
        root=root,
        knowledge_dir=root / knowledge_rel,
        orders_path=root / orders_rel,
    )


def get_tenant() -> TenantConfig:
    """Load the active tenant (from ACTIVE_TENANT / default)."""
    return load_tenant(active_tenant_id())


def clear_tenant_cache() -> None:
    """Test helper: drop cached tenant configs."""
    load_tenant.cache_clear()
