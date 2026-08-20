# Evaluation set (eval set)

Plain idea: a **practice quiz** for the support agent.

Technical idea: a fixed list of customer questions with expected routing and
behavior so we can catch regressions when we change code.

## Files

| File | Purpose |
|------|---------|
| `support_eval_set.json` | The gold cases (source of truth for expectations) |
| `../../tests/test_support_eval.py` | Automated checks that load the JSON |

## How to run

From the project root (venv active):

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_support_eval.py -v
```

Tests turn off AI warm rewrite (`AI_WARM_REWRITE=false`) so wording stays
stable and grounded in templates / knowledge text.

## How to add a case

1. Add an object under `cases` in `support_eval_set.json`.
2. Fill `id`, `question`, and either:
   - `expected_classification` (normal support lane), or
   - `expected_input_action` (`block` / `escalate` for guardrails)
3. Set `expected_outcome` and usually `expected_action`.
4. Optionally add `reply_must_include` / `reply_must_not_include`.
5. Re-run pytest.

## Field cheat sheet

| Field | Meaning |
|-------|---------|
| `expected_classification` | Lane from `support.py` (snake_case) |
| `expected_input_action` | Guardrail decision before classify |
| `expected_outcome` | `answered` / `blocked` / `escalated` |
| `expected_action` | Logged action name (e.g. `returns_help`) |
| `reply_must_include` | Substrings that should appear (case-insensitive) |
| `reply_must_not_include` | Substrings that must never appear |
