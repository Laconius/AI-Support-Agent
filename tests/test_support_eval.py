"""
Run the support eval set.

Plain idea: replay our gold questions and check the agent still behaves.
Technical idea: load JSON cases; assert classification / outcome / reply text.

Warm rewrite is forced off so checks stay deterministic (templates + docs).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_PATH = PROJECT_ROOT / "data" / "evals" / "support_eval_set.json"

sys.path.insert(0, str(PROJECT_ROOT / "app"))

from agent_service import handle_question  # noqa: E402
from guardrails import check_input  # noqa: E402
from support import classify_request  # noqa: E402


def _load_cases() -> list[dict]:
    payload = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    return payload["cases"]


@pytest.fixture(autouse=True)
def _deterministic_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_WARM_REWRITE", "false")


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_support_eval_case(case: dict) -> None:
    question = case["question"]

    if "expected_input_action" in case:
        safety = check_input(question)
        assert safety.action == case["expected_input_action"], (
            f"{case['id']}: input guardrail expected "
            f"{case['expected_input_action']}, got {safety.action}"
        )
    else:
        category = classify_request(question)
        assert category == case["expected_classification"], (
            f"{case['id']}: classification expected "
            f"{case['expected_classification']}, got {category}"
        )

    result = handle_question(question, channel="eval")

    if "expected_outcome" in case:
        assert result.outcome == case["expected_outcome"], (
            f"{case['id']}: outcome expected {case['expected_outcome']}, "
            f"got {result.outcome}"
        )

    if "expected_action" in case:
        assert result.action == case["expected_action"], (
            f"{case['id']}: action expected {case['expected_action']}, "
            f"got {result.action}"
        )

    reply_lower = (result.reply or "").lower()

    for needle in case.get("reply_must_include") or []:
        assert needle.lower() in reply_lower, (
            f"{case['id']}: reply missing {needle!r}\nReply:\n{result.reply}"
        )

    for needle in case.get("reply_must_not_include") or []:
        assert needle.lower() not in reply_lower, (
            f"{case['id']}: reply must not contain {needle!r}\nReply:\n{result.reply}"
        )
