# AI Customer Support Engineer

An AI-powered customer support agent designed to answer product questions accurately, take safe support actions, and escalate to humans when confidence or risk requires it.

This repository is the home of a production-oriented support agent we will build step by step — starting with fundamentals, then growing into a system suitable for real customers and real operations.

---

## Purpose

Customer support teams spend significant time on repetitive, well-documented questions: how a feature works, how billing works, how to troubleshoot common issues. The goal of this project is to build an **AI Customer Support Engineer** that can:

- Answer customer questions using approved knowledge (docs, FAQs, policies)
- Stay within clear safety boundaries (no inventing refunds, no leaking private data)
- Use tools when appropriate (look up an order, create a ticket, fetch account status)
- Hand off to a human agent when the situation is ambiguous, sensitive, or high-impact
- Leave an audit trail so support leaders can review what the AI said and did

**Non-goals (for now):** replacing the entire support organization, fully autonomous refunds/account changes without review, or competing with enterprise suites on day one.

---

## Long-term vision

Over time, this project should become a reliable **support co-pilot and first-line agent**:

1. **Accurate first responses** — grounded in company knowledge, not model guesswork
2. **Actionable workflows** — safe, permissioned tools for common support tasks
3. **Channel-ready** — usable from a web chat UI first, then email, Slack, or helpdesk systems
4. **Measurable quality** — evaluation harnesses, conversation review, and continuous improvement
5. **Operable in production** — authentication, rate limits, logging, monitoring, and clear escalation paths

Success looks like: fewer repetitive tickets for humans, faster answers for customers, and support leadership that trusts the system because its behavior is visible and controllable.

---

## High-level architecture

Think of the system as a few cooperating layers. We will implement them gradually; this diagram is the destination map, not the week-one build.

```text
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Customer       │     │  Application API     │     │  Agent Orchestrator │
│  Channel        │────▶│  (auth, validation,  │────▶│  (reason, plan,     │
│  (web chat…)    │     │   sessions, routing) │     │   call tools, reply)│
└─────────────────┘     └──────────────────────┘     └──────────┬──────────┘
                                                                │
                    ┌───────────────────┬───────────────────────┼──────────────┐
                    ▼                   ▼                       ▼              ▼
           ┌────────────────┐  ┌────────────────┐     ┌────────────────┐  ┌──────────────┐
           │ Knowledge / RAG│  │ LLM Provider   │     │ Support Tools  │  │ Escalation   │
           │ (docs, FAQs,   │  │ (chat model)   │     │ (tickets, CRM, │  │ (human queue)│
           │  embeddings)   │  │                │     │  order lookup) │  │              │
           └────────────────┘  └────────────────┘     └────────────────┘  └──────────────┘
                    │
                    ▼
           ┌────────────────────────────────────────────────────────────────────────────┐
           │ Observability & Evaluation (logs, traces, metrics, offline test sets)      │
           └────────────────────────────────────────────────────────────────────────────┘
```

### Layer responsibilities

| Layer | Role in plain language | Technical role |
|-------|------------------------|----------------|
| **Customer channel** | Where the user talks to us | Web UI, later helpdesk/email adapters |
| **Application API** | Front door of the backend | Auth, request validation, session/conversation IDs |
| **Agent orchestrator** | The “brain” that decides what to do next | Prompting, planning, tool calls, reply formatting |
| **Knowledge / RAG** | Looking things up before answering | Document store + retrieval (later: vector search) |
| **LLM provider** | The language model service | Hosted API (e.g. OpenAI / Anthropic) behind a thin client |
| **Support tools** | Actions beyond chat | Ticket creation, order lookup, CRM read APIs |
| **Escalation** | Human backup | Handoff rules and queue integration |
| **Observability & evaluation** | How we know it works | Structured logs, traces, golden-question test sets |

**Design principle:** keep the LLM behind a clear interface so we can change providers or models without rewriting the whole app.

---

## Expected technologies

Choices below favor learning professional Python practices while staying production-realistic. Exact libraries may change as we learn; the README will be updated when they do.

| Area | Expected choice | Why |
|------|-----------------|-----|
| Language | **Python 3.12+** | Dominant ecosystem for AI apps; readable for learners |
| API framework | **FastAPI** | Typed request/response models, excellent docs, async-ready |
| Data validation | **Pydantic** | Comes with FastAPI; catches bad inputs early |
| LLM access | Provider SDK (e.g. OpenAI / Anthropic) | Start with a thin wrapper; add frameworks when needed |
| Agent workflows | Start custom → consider **LangGraph** later | Avoid heavy frameworks until multi-step flows justify them |
| Knowledge | Markdown/docs first → **vector DB** (e.g. Chroma/pgvector) later | Ship retrieval basics before infrastructure complexity |
| Persistence | **SQLite** early → **Postgres** for production | Local simplicity first; durable multi-user storage later |
| Frontend (later) | Simple web chat (e.g. React or a lightweight template) | Prove the agent before investing in UI polish |
| Config & secrets | Environment variables + `.env` (never committed) | Standard secure configuration practice |
| Testing | **pytest** | Automated checks for tools, APIs, and evaluation cases |
| Packaging / env | **uv** or **venv** + `requirements`/`pyproject` | Reproducible environments |
| Quality gates | Linter/formatter (e.g. Ruff), type hints | Habits that scale with team size |

### Approach tradeoffs (honest defaults)

- **Thin custom agent vs. full agent framework:** Custom code is easier to understand early. Frameworks help when you need complex graphs, retries, and branching. We start thin.
- **SQLite vs. Postgres:** SQLite is one file and great for learning. Postgres is the usual production database once we need concurrent users and stronger ops tooling.
- **Files vs. vector search:** Searching a few markdown files is enough for a first demo. Vector search (embeddings) becomes valuable when the knowledge base grows.

---

## Development roadmap

Each phase should end with something you can run and demo. We do not jump to “full production” in one step.

### Phase 0 — Project foundation *(current)*
- Professional README and project intent
- Repository hygiene (ignore secrets, clear folder plan)
- Local Python environment setup (next session)

### Phase 1 — Smallest working agent
- CLI or minimal API that accepts a question and returns an answer
- System prompt with support persona and safety rules
- Conversation history for a single session
- Basic logging of inputs/outputs

### Phase 2 — Knowledge grounding
- Load approved support docs from the repo
- Retrieve relevant snippets before answering (simple search → RAG)
- Cite sources in responses where useful
- Add “I don’t know / escalate” behavior when knowledge is missing

### Phase 3 — Tools and actions
- Define a small set of safe tools (e.g. FAQ lookup, create support ticket stub)
- Tool permission model (what the agent may vs. may not do)
- Structured tool results fed back into the conversation

### Phase 4 — Product surface
- HTTP API with clear contracts (FastAPI)
- Simple chat UI for demos
- Session/conversation persistence
- Basic auth for non-public demos

### Phase 5 — Quality and operations
- Evaluation set of real-ish support questions with expected behaviors
- Observability (structured logs, request IDs, latency)
- Rate limiting, error handling, and escalation policies
- Deployment checklist (env config, health checks, secrets management)

### Phase 6 — Production hardening & channels
- Postgres, stronger auth, audit trails
- Helpdesk / Slack / email adapters as needed
- Human review workflows for high-risk actions
- Continuous evaluation in CI

---

## Repository status

This project is in **Phase 0**. No application code has been written yet. The next step is environment setup and a minimal “hello, support agent” skeleton — still taught one concept at a time.

---

## Contributing (personal learning project)

This repository is primarily a guided build for learning professional software engineering while shipping a real product shape. Prefer:

- Small, reviewable changes
- Clear commit messages that explain *why*
- Updating this README when architecture or roadmap decisions change
- Never committing API keys, customer data, or `.env` files

---

## License

License to be decided. Until then, treat the code as private / all rights reserved unless a license file is added.
`}