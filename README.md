# AI Customer Support Engineer

An AI-powered customer support agent for a **better-sleep** brand. It answers from approved facts, speaks in warm customer language, stays inside safety guardrails, and escalates to humans when needed.

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
Customer question
    │
    ▼
main.py                 orchestrator (CLI front door)
    │
    ├─► guardrails.py   allow / block / escalate (input + output)
    ├─► support.py      classify lane + EscalationPacket
    ├─► orders.py       order FACTS (status, tracking)
    ├─► knowledge.py    knowledge FACTS (retrieve snippets)
    ├─► responses.py    wording (template → AI warm rewrite)
    │       └─► ai_client.py   OpenAI (or future provider) connection
    └─► config.py       .env secrets (never hardcode keys)
```

| File | Job in plain English | Technical role |
|------|----------------------|----------------|
| `app/main.py` | Runs the conversation loop | Orchestration |
| `app/config.py` | Loads API keys from `.env` | Configuration / secrets |
| `app/ai_client.py` | Talks to OpenAI (swap-ready) | LLM provider adapter |
| `app/support.py` | Picks a support lane; builds handoffs | Classifier + escalation |
| `app/orders.py` | Looks up what is true about an order | Tools / fact source |
| `app/knowledge.py` | Finds approved doc sections | Retrieval (R in RAG) |
| `app/responses.py` | Turns facts into customer language | Generation (G in RAG) |
| `app/guardrails.py` | Hard safety rules | Policy enforcement |
| `data/orders.json` | Sample orders | Stand-in order system |
| `data/knowledge/*.md` | Approved product / policy / sleep tips | Knowledge base |

Study PDFs (living docs): `docs/*-line-by-line.pdf` — regenerated when modules change.

**RAG study sheet (print this):** [`docs/rag-cheat-sheet.pdf`](docs/rag-cheat-sheet.pdf) — discrete concept compartments + a worked example from this repo. Regenerate with:

```powershell
.\.venv\Scripts\python.exe docs\generate_rag_cheat_sheet.py
```

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
| LLM access | `ai_client.py` + OpenAI SDK | Anthropic (etc.) later behind same Protocol |
| Knowledge | Markdown in `data/knowledge/` | Vector DB later |
| Orders | `data/orders.json` | Stand-in for Shopify/ERP |
| Secrets | `.env` (gitignored) | See `.env.example` |
| Safety | `guardrails.py` | Input + output checks |
| Docs | `docs/*-line-by-line.pdf` | Regenerated with code changes |

Optional `.env` keys:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
AI_WARM_REWRITE=true
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
- **CLI orchestrator** (`main.py`)  

### Next
- Stronger RAG retrieval (embeddings when doc volume needs it)  
- Conversation state (multi-turn)  
- Persist escalation queue  
- Evaluation set of support questions  
- FastAPI + webhook path (Twilio RCS/SMS)  
- Production hardening (Postgres, auth, monitoring)  

---

## How to run (CLI)

```powershell
cd app
..\.venv\Scripts\python.exe main.py
```

Examples:

- `Where is order ORD-1001?` — order facts + warm wording  
- `Is the CloudRest pillow washable?` — knowledge retrieval + warm wording  
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
