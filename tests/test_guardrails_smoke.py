import sys

sys.path.insert(0, "app")

from guardrails import (  # noqa: E402
    ALLOW,
    BLOCK,
    ESCALATE,
    apply_output_guardrails,
    check_input,
    check_output,
)

cases = [
    ("I have chest pain and cannot breathe", ESCALATE),
    ("Do I have sleep apnea?", BLOCK),
    ("Should I stop taking my medication?", BLOCK),
    ("Can you look up my husband's order?", BLOCK),
    ("Can you look up my husbands order?", BLOCK),
    ("Where is ORD-1001?", ALLOW),
]

for question, expected in cases:
    result = check_input(question)
    assert result.action == expected, (question, result.action, expected)
    print("IN OK:", result.action, "-", question)

bad = "Good news - I will issue you a refund today."
assert check_output(bad).action == BLOCK
print("OUT OK: refund promise blocked")
print(apply_output_guardrails(bad)[:70])

assert (
    check_output(
        "Order for alex@example.com is shipped",
        question="Where is my order?",
    ).action
    == BLOCK
)
print("OUT OK: unexpected email blocked")
print("ALL PASSED")
