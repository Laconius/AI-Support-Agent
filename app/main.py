"""
CLI front door for the AI Support Agent.

Plain idea: talk to the agent in the terminal.
The real pipeline lives in agent_service.py (shared with the FastAPI API).
"""

from ai_client import describe_ai_client
from agent_service import handle_question
from config import print_openai_key_status
from request_log import LOG_PATH

print("=" * 40)
print(" AI Support Agent — Better Sleep")
print("=" * 40)

print()
key_ok = print_openai_key_status()
if not key_ok:
    print("Fix .env before we wire live AI replies.")
print(describe_ai_client())
print()

question = input("How can I help you today?\n> ")

print(f"\nYou asked: {question}")

result = handle_question(question, channel="cli")

if result.classification_label:
    print(f"\nClassified as: {result.classification_label}")

print(f"\n{result.reply}")

if result.escalation:
    print("\n--- Escalation packet (for operators) ---")
    for key, value in result.escalation.items():
        if key == "transcript":
            continue
        print(f"{key}: {value}")

print(f"\n(Logged to {LOG_PATH})")
print(f"(outcome={result.outcome}, action={result.action})")
