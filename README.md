# AI Customer Support Engineer

An AI-powered customer support agent for **Sopoforix** (sleep better, live better). It answers from approved facts, speaks in warm customer language, stays inside safety guardrails, and escalates to humans when needed.

Business-specific content lives under `tenants/sopoforix/`. Shared engine code lives in `app/` so additional brands can be added later as new tenant packs.

This repository is a guided, production-shaped build: fundamentals first, then channels, quality, and operations.

---

## Purpose

Customer support teams spend significant time on repetitive, well-documented questions. This project builds an **AI Customer Support Engineer** that can:

- Answer using approved knowledge (docs, FAQs, policies) and order facts
- Stay within safety boundaries (no medical diagnosis, no refund promises, no leaking other customers’ data)
- Use tools when appropriate (order lookup / status / tracking)
- Hand off to a human with a structured escalation packet
- Keep the LLM behind a thin client so providers can change later

**Non-goals (for now):** replacing the entire support organization, fully autonomous refunds, or a full helpdesk suite on day one.

---

## Long-term vision

1. **Accurate first responses** — grounded in company knowledge, not model guesswork  
2. **Actionable workflows** — safe, permissioned tools for common support tasks  
3. **Channel-ready** — CLI today; later web chat, Twilio RCS/SMS, helpdesk  
4. **Measurable quality** — evaluation sets, conversation review, continuous improvement  
5. **Operable in production** — auth, rate limits, logging, monitoring, escalation paths  

---

## What exists today (module map)

```text
                    ┌─────────────┐     ┌─────────────┐
 Web / services ───►│  api.py     │     │  main.py    │◄── terminal (CLI)
                    │  (FastAPI)  │     │  (CLI)      │
                    └──────┬──────┘     └──────┬──────┘
                           │                   │
                           └─────────┬─────────┘
                                     ▼
                           agent_service.py
                           (shared pipeline)
                                     │
         ┌───────────┬───────────┬───┴───┬───────────┬────────────┐
         ▼           ▼           ▼       ▼           ▼            ▼
   guardrails   support.py   orders   knowledge  responses   request_log
                 classify              facts         │
                                                   ai_client
```

| File | Job in plain English | Technical role |
|------|----------------------|----------------|
| `app/main.py` | Terminal chat front door | CLI channel |
| `app/api.py` | HTTP front door for web/services | FastAPI app |
| `web/` | Browser chat page | Static HTML/CSS/JS channel |
| `app/tenant.py` | Loads the active business pack | Multi-tenant config |
| `tenants/sopoforix/` | Sopoforix name, knowledge, demo orders | Tenant pack |
| `app/schemas.py` | Describes JSON in/out | Pydantic models |
| `app/agent_service.py` | One function: handle a question end-to-end | Shared service layer |
| `app/config.py` | Loads API keys from `.env` | Configuration / secrets |
| `app/ai_client.py` | Talks to OpenAI (swap-ready) | LLM provider adapter |
| `app/support.py` | Picks a support lane; builds handoffs | Classifier + escalation |
| `app/orders.py` | Looks up what is true about an order | Tools / fact source |
| `app/knowledge.py` | Finds approved doc sections | Retrieval (R in RAG) |
| `app/responses.py` | Turns facts into customer language | Generation (G in RAG) |
| `app/guardrails.py` | Hard safety rules | Policy enforcement |
| `app/request_log.py` | Records each request for review | Observability (JSONL log) |
| `data/logs/support_requests.jsonl` | Local request diary (gitignored) | Learning / debugging |
| `data/evals/` | Gold questions for quality checks | Evaluation set |

### Study guides (printables)

| PDF | What to ruminate on |
|-----|---------------------|
| [`docs/rag-cheat-sheet.pdf`](docs/rag-cheat-sheet.pdf) | RAG compartments (R / A / G) + worked example |
| [`docs/ai-client-py-line-by-line.pdf`](docs/ai-client-py-line-by-line.pdf) | How we talk to OpenAI (provider adapter) |
| [`docs/request-log-py-line-by-line.pdf`](docs/request-log-py-line-by-line.pdf) | Request diary (question / lane / outcome) |
| [`docs/agent-service-py-line-by-line.pdf`](docs/agent-service-py-line-by-line.pdf) | Shared pipeline (CLI + API brain) |
| [`docs/api-py-line-by-line.pdf`](docs/api-py-line-by-line.pdf) | FastAPI HTTP front door |
| [`docs/responses-py-line-by-line.pdf`](docs/responses-py-line-by-line.pdf) | Facts → warm customer language |
| [`docs/knowledge-py-line-by-line.pdf`](docs/knowledge-py-line-by-line.pdf) | Retrieving approved doc sections |
| [`docs/orders-py-line-by-line.pdf`](docs/orders-py-line-by-line.pdf) | Order facts (status / tracking) |
| [`docs/guardrails-py-line-by-line.pdf`](docs/guardrails-py-line-by-line.pdf) | Hard safety rules |
| [`docs/support-py-line-by-line.pdf`](docs/support-py-line-by-line.pdf) | Classifier + escalation packet |
| [`docs/main-py-line-by-line.pdf`](docs/main-py-line-by-line.pdf) | How the CLI wires everything |
| [`docs/twilio-ai-support-architecture.pdf`](docs/twilio-ai-support-architecture.pdf) | Future messaging channel (RCS/SMS) |

Regenerate code walkthroughs:

```powershell
.\.venv\Scripts\python.exe docs\generate_walkthroughs.py
```

Regenerate the RAG cheat sheet:

```powershell
.\.venv\Scripts\python.exe docs\generate_rag_cheat_sheet.py
```

---

## Repository on GitHub

Remote (already connected):

`https://github.com/Laconius/AI-Support-Agent.git`

- **Git remote** (this folder ↔ that repo): Source Control sidebar, or `git remote -v`
- **Cursor ↔ GitHub account** (app login for PRs/features): Cursor Settings → search “GitHub”

Do not commit `.env`. Use `.env.example` as the safe template for collaborators.

---

## How RAG works here (current → next)

**RAG** = Retrieval-Augmented Generation.

Plain idea: don’t ask the AI to “remember” your catalog.  
**Retrieve** approved facts first, then ask the AI to **generate** wording from those facts only.

### Current implementation (working)

```text
1) RETRIEVE
   knowledge.search_knowledge(question)  → Snippet facts
   orders.get_order_help_facts(question) → OrderHelpFacts

2) DRAFT (deterministic)
   responses builds a factual template from those objects

3) GENERATE (warm rewrite)
   ai_client.complete(...) rewrites the template more warmly
   system prompt: use ONLY provided facts; no diagnosis / refund promises

4) SAFETY
   sleep disclaimer forced outside the AI rewrite when needed
   guardrails.check_output on the final draft
```

That is already a simple, auditable RAG loop: **facts stay in `orders` / `knowledge`; language lives in `responses`; connection details live in `ai_client`.**

### Where `ai_client.py` fits

`ai_client.py` is the **LLM provider adapter**:

- Reads `AI_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL` from `.env`
- Exposes `get_ai_client()` and `ChatMessage` / `complete()`
- Hides OpenAI SDK details so Anthropic (or another) can be added later behind the same interface
- Does **not** decide business answers — `responses.py` decides what facts to send

Toggle warm rewrite with `AI_WARM_REWRITE=true|false` (default true). If the API fails, templates are used unchanged.

### RAG roadmap going forward

| Step | What improves | Why |
|------|----------------|-----|
| **Now** | Keyword retrieval + AI warm rewrite | Easy to understand, debuggable, already grounded |
| **Next** | Better chunking / metadata filters per lane | Fewer wrong-doc hits (we already prefer files by classifier lane) |
| **Then** | Embeddings + vector store (e.g. Chroma / pgvector) | Better semantic match as docs grow |
| **Then** | Hybrid retrieve (keywords + vectors) | Precision + recall |
| **Later** | Citation checks / faithfulness eval | Catch “sounded nice but wasn’t in the facts” |
| **Later** | Multi-turn memory (stateful sessions) | “What’s the tracking?” after an earlier order id |

**Design rule we keep:** the model never becomes the system of record. Orders and markdown (later: databases) are the source of truth; the model is a writer, not a warehouse.

---

## High-level target architecture

Destination map (includes channels and ops we have not fully built yet):

```text
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Customer       │     │  Application API     │     │  Agent Orchestrator │
│  Channel        │────▶│  (auth, validation,  │────▶│  (classify, tools,  │
│  (CLI → chat /  │     │   sessions, routing) │     │   respond, escalate)│
│   Twilio later) │     └──────────────────────┘     └──────────┬──────────┘
└─────────────────┘                                             │
                    ┌───────────────────┬───────────────────────┼──────────────┐
                    ▼                   ▼                       ▼              ▼
           ┌────────────────┐  ┌────────────────┐     ┌────────────────┐  ┌──────────────┐
           │ Knowledge/RAG  │  │ ai_client.py   │     │ Support Tools  │  │ Escalation   │
           │ knowledge.py + │  │ (OpenAI today) │     │ orders.py …    │  │ packet/queue │
           │ data/knowledge │  │                │     │                │  │              │
           └────────────────┘  └────────────────┘     └────────────────┘  └──────────────┘
                    │
                    ▼
           ┌────────────────────────────────────────────────────────────────────────────┐
           │ Guardrails + Observability & Evaluation                                    │
           └────────────────────────────────────────────────────────────────────────────┘
```

**Design principle:** keep the LLM behind `ai_client.py` so providers/models can change without rewriting the agent.

---

## Technologies in use / expected

| Area | Choice | Notes |
|------|--------|-------|
| Language | Python 3.12+ | Learning-friendly, strong AI ecosystem |
| HTTP API | **FastAPI** + **Uvicorn** | Web/service front door (`app/api.py`) |
| Data validation | **Pydantic** (`schemas.py`) | Request/response contracts |
| LLM access | `ai_client.py` + OpenAI SDK | Anthropic (etc.) later behind same Protocol |
| Knowledge | Markdown in `tenants/<id>/knowledge/` | Vector DB later |
| Orders | `tenants/<id>/orders.json` | Stand-in for Shopify/ERP |
| Secrets | `.env` (gitignored) | See `.env.example` |
| Safety | `guardrails.py` | Input + output checks |
| Docs | `docs/*-line-by-line.pdf` | Regenerated with code changes |

Optional `.env` keys:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
AI_WARM_REWRITE=true
ACTIVE_TENANT=sopoforix
```

---

## Development roadmap

### Done / in progress
- **Foundation:** README, `.gitignore`, venv, `.env` pattern  
- **Classifier + escalation packet** (`support.py`)  
- **Order facts** (`orders.py`)  
- **Knowledge retrieval** (`knowledge.py`)  
- **Guardrails** (`guardrails.py`)  
- **Responses + AI warm rewrite** (`responses.py` + `ai_client.py`)  
- **Request logging** (`request_log.py`)  
- **Shared pipeline + FastAPI** (`agent_service.py`, `api.py`, `schemas.py`)  
- **CLI orchestrator** (`main.py`)  

### Next
- Stronger RAG retrieval (embeddings when doc volume needs it)  
- Conversation state (multi-turn)  
- Persist escalation queue  
- Twilio RCS/SMS webhook adapter calling `/v1/support/ask`  
- Production hardening (Postgres, auth, monitoring)  
### Quality checks
- Eval set: [`data/evals/support_eval_set.json`](data/evals/support_eval_set.json)  
  Run: `.\.venv\Scripts\python.exe -m pytest tests\test_support_eval.py -v`  
- API smoke tests: `tests/test_api_smoke.py` (health, chat UI, `/ask` wiring)  
  Run: `.\.venv\Scripts\python.exe -m pytest tests\test_api_smoke.py -v`  
- All tests: `.\.venv\Scripts\python.exe -m pytest -v` 

---

## How to run

### CLI (terminal)

```powershell
.\.venv\Scripts\python.exe app\main.py
```

### HTTP API + chat UI (FastAPI)

```powershell
.\.venv\Scripts\uvicorn.exe api:app --app-dir app --reload --host 127.0.0.1 --port 8000
```

Then open:

- **Chat UI:** http://127.0.0.1:8000/  
- Interactive docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

The page in `web/` POSTs to `/v1/support/ask` with `channel: "web"` — same agent as the CLI. Later a Shopify embed can call that same endpoint.

Example ask (PowerShell):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/v1/support/ask `
  -ContentType "application/json" `
  -Body '{"question":"Where is order ORD-1001?","channel":"web"}'
```

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Browser chat UI |
| `GET /health` | Is the service up? |
| `POST /v1/support/ask` | Send a customer question; get reply + metadata |
| `GET /docs` | Built-in Swagger UI (try the API in the browser) |
| `GET /api` | Machine-readable service pointers |

**How web traffic connects later:** a website, mobile app, or Twilio webhook calls `POST /v1/support/ask` (or a thin adapter that calls `handle_question`). The agent logic stays in `agent_service.py` — you add doors, not duplicate brains.

Install / refresh dependencies:

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Examples to try (CLI or API):

- `Where is order ORD-1001?` — order facts + warm wording  
- `Is the CloudRest pillow washable?` — knowledge retrieval + warm wording  
- `What is your return policy?` — policies.md retrieval (no refund promises)  
- `Do I have sleep apnea?` — blocked by guardrails  

---

## Contributing (personal learning project)

- Small, reviewable changes  
- Commit messages that explain *why*  
- Update this README when architecture or RAG strategy changes  
- New/changed `app/*.py` → update walkthrough PDFs via `docs/generate_walkthroughs.py`  
- Never commit API keys, customer data, or `.env`  

---

## License

License to be decided. Until then, treat the code as private / all rights reserved unless a license file is added.
