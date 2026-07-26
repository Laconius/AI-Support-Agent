from ai_client import describe_ai_client
from config import print_openai_key_status
from guardrails import (
    ESCALATE,
    apply_output_guardrails,
    check_input,
)
from knowledge import search_knowledge
from orders import get_order_help_facts
from responses import (
    render_account_help,
    render_escalation_customer,
    render_knowledge_help,
    render_order_help,
    render_returns_help,
)
from support import (
    ACCOUNT_HELP,
    ESCALATION,
    ORDER_HELP,
    PRODUCT_QUESTIONS,
    RETURNS_REFUNDS_COMPLAINTS,
    SLEEP_GUIDANCE,
    build_escalation_packet,
    category_label,
    classify_request,
)

print("=" * 40)
print(" AI Support Agent — Better Sleep")
print("=" * 40)

# Prove the secret loaded without ever printing the secret itself.
print()
key_ok = print_openai_key_status()
if not key_ok:
    print("Fix .env before we wire live AI replies.")
print(describe_ai_client())
print()

question = input("How can I help you today?\n> ")

print(f"\nYou asked: {question}")

# Guardrails run BEFORE classification so emergencies / medical asks never
# get a casual product answer by accident.
safety = check_input(question)
if safety.action == ESCALATE:
    packet = build_escalation_packet(question, category=ESCALATION, channel="cli")
    print("\n" + safety.message)
    print("\n--- Escalation packet (for operators) ---")
    print(packet.summary())
    raise SystemExit(0)
if safety.action != "allow":
    print("\n" + safety.message)
    raise SystemExit(0)

category = classify_request(question)
label = category_label(category)

print(f"\nClassified as: {label}")

# Collect facts -> responses.py (template + AI warm rewrite) -> output guardrails.
if category == SLEEP_GUIDANCE:
    snippets = search_knowledge(question, prefer_file="sleep-tips.md")
    draft = render_knowledge_help(
        snippets,
        include_sleep_disclaimer=True,
        question=question,
    )
elif category == ORDER_HELP:
    draft = render_order_help(get_order_help_facts(question), question=question)
elif category == PRODUCT_QUESTIONS:
    draft = render_knowledge_help(search_knowledge(question), question=question)
elif category == ACCOUNT_HELP:
    draft = render_account_help(question=question)
elif category == RETURNS_REFUNDS_COMPLAINTS:
    draft = render_returns_help(question=question)
elif category == ESCALATION:
    packet = build_escalation_packet(question, category=category, channel="cli")
    print("\n" + render_escalation_customer(question=question))
    print("\n--- Escalation packet (for operators) ---")
    print(packet.summary())
    raise SystemExit(0)
else:
    draft = render_escalation_customer(question=question)

print("\n" + apply_output_guardrails(draft, question=question))
