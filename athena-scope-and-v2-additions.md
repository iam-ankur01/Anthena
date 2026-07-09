# Athena — Final Scope Document (Core + V2)

This supersedes the previous blueprint's scope. Core build stays as originally planned (Phases 1-10). This doc adds what to layer in **after** core ships, and explicitly lists what got cut and why.

**Rule for using this doc:** don't start V2 until core is deployed, tested, and you can demo it end-to-end. A half-finished V2 feature on top of a shipped core is a worse portfolio than a fully-finished core alone.

---

## Decision Summary

| Addition | Verdict | Where it goes |
|---|---|---|
| RAGAS / DeepEval | ✅ Keep | V2 — upgrades Phase 7 |
| Streaming responses | ✅ Keep | V2 |
| Ruff / Black / MyPy / pre-commit | ✅ Keep | V2 — cheap, do this early in V2 |
| Comprehensive README + demo video | ✅ Keep, highest priority | Core — do this the moment core is deployed, before any V2 work |
| Observability / metrics | ✅ Keep, scoped down | V2 — structured logging + basic counters only, no Grafana |
| Background processing | ✅ Keep, scoped down | V2 — FastAPI `BackgroundTasks`, not Celery/Redis |
| Long-term memory | ⚠️ Include, simplified | V2 — running summary, not a second retrieval subsystem |
| Authentication | ⚠️ Include, but treat as checkbox | V2 — you've built this before in CafeQR, don't over-invest time here |
| Async FastAPI | Not a separate item | Just don't write blocking code in Core — no extra phase needed |
| Multi-agent architecture | ❌ Cut | Not planned — see rationale below |
| Admin dashboard | ❌ Cut | Not planned — low learning value for the time cost |
| "Richer API surface" | ❌ Deferred, undefined | Only add specific endpoints if a real use case demands them |

---

## Why Multi-Agent Is Cut

A single well-routed agent with good tool docstrings already demonstrates agentic reasoning — that's the hard part. Multiple coordinating agents adds a new failure surface: agent A's bad output silently becomes agent B's bad input, and debugging *which* agent caused a wrong answer is a system-design problem you haven't practiced yet (you flagged this gap yourself).

The real risk isn't build time — it's interview risk. If "multi-agent" is on your resume, an interviewer will ask *why multiple agents instead of one agent with more tools, and how do they hand off state*. If you can't answer that crisply and confidently, it costs you more than having a single, deeply-understood agent would have. Add multi-agent later, as a v3, once you've shipped one production agent and genuinely want to learn agent coordination — not because it looks good on paper.

## Why Admin Dashboard Is Cut

It's mostly repeated frontend work — a second Streamlit/React view showing data you already have. It makes the demo look a little more "enterprise," but teaches you very little you haven't already practiced in Phase 5. Not worth the time against higher-value V2 items.

---

## Core Build (unchanged — Phases 1-10)

Reference: your existing `athena-flagship-rag-blueprint.md`. Build in this order, don't skip Phase 6 (testing) or Phase 7 (evaluation) even under time pressure — they're your biggest differentiators.

1. Tools (document, web search, arxiv)
2. Agent graph (LangGraph routing)
3. Database layer (Postgres + SQLAlchemy)
4. FastAPI wiring
5. Streamlit UI
6. Testing (pytest, mocked LLM)
7. Evaluation (routing accuracy script)
8. Docker + docker-compose
9. CI/CD (GitHub Actions)
10. Deploy live (Render/Railway)

**Immediately after Phase 10:** write the README and record the demo video before touching anything below. This is the step most people skip and it's the one recruiters actually see.

---

## V2 — Build After Core Ships

### V2.1 — README + Demo (do this first, not last)

No Cursor prompt needed — write this yourself, it's how you think about your own work.

Include:
- 2-3 sentence pitch (the one-liner from the original blueprint)
- Architecture diagram (reuse the one from the blueprint, or regenerate with your actual final structure)
- Setup instructions (`docker-compose up`, env vars needed)
- A **"Design Decisions"** section — 4-5 short bullets on why LangGraph over plain AgentExecutor, why Chroma over Pinecone, why you mock LLM calls in tests, etc. This section alone often gets read more closely than your code.
- Link to the live deployment
- Link to a 90-second Loom/screen-recording demo (show a multi-tool question happening live, not a slide deck)
- CI badge once Phase 9 is done

---

### V2.2 — Code Quality Tooling

**Cursor prompt:**
```
Add Ruff and Black configuration to pyproject.toml (line length 100, 
standard rule sets). Add mypy.ini or pyproject.toml [tool.mypy] section 
targeting Python 3.11, with reasonable strictness (disallow_untyped_defs 
for backend/ only, ignore tests/ and frontend/ initially).

Create .pre-commit-config.yaml running ruff, black, and mypy on commit.

Run ruff and black across the existing codebase and fix all violations. 
Do NOT auto-fix mypy errors blindly — review each one, some may reveal 
real type bugs worth understanding.
```

Do the mypy review yourself — don't let Cursor silently "fix" type errors by adding `Any` everywhere, that defeats the purpose.

---

### V2.3 — Streaming Responses

**Cursor prompt:**
```
Modify backend/routes/query.py to add a streaming variant: 
POST /query/stream using FastAPI's StreamingResponse with 
media_type="text/event-stream" (SSE). Stream the agent's final answer 
token-by-token as it's generated (LangGraph/LangChain supports 
.astream() on the compiled graph — use that instead of .invoke()).

Update frontend/app.py to consume the stream using requests with 
stream=True, updating the chat message incrementally with 
st.empty() + a loop, instead of waiting for the full response.
```

**What to understand:** why SSE instead of WebSockets here (simpler, one-directional, no need for bidirectional connection for a chat response stream).

---

### V2.4 — RAG/Agent Evaluation with RAGAS

**Cursor prompt:**
```
Add ragas to requirements.txt. Extend evaluation/eval_agent.py to also 
compute RAGAS metrics (faithfulness, answer_relevancy, context_precision) 
on your existing 10 test cases — for the document-tool cases specifically, 
since RAGAS needs retrieved context to score against.

Structure results as a small pandas DataFrame and print a summary table. 
Save results to evaluation/results.csv so you can reference specific 
numbers later (interviews, README).
```

This is what upgrades your evaluation story from "I checked if the right tool was called" to "I measured faithfulness and relevancy using the standard RAG evaluation framework" — a meaningfully more senior sentence.

---

### V2.5 — Structured Logging + Basic Metrics (scoped-down observability)

**Cursor prompt:**
```
Add structlog for structured JSON logging in backend/. Log: every 
/query request (question, tools_called, latency_ms, conversation_id), 
every tool invocation with its own latency, and any errors with 
full context.

Add a simple in-memory counter module (backend/metrics.py) tracking: 
total queries, tool-call distribution (count per tool), average latency. 
Expose it at GET /metrics as JSON — no Prometheus/Grafana needed, 
just a real, honest metrics endpoint.
```

Keep this genuinely small. The value is "I thought about observability," not "I ran a monitoring stack for a portfolio project."

---

### V2.6 — Background Processing for Ingestion
 
**Cursor prompt:**
```
Modify backend/routes/upload.py: instead of running ingestion 
synchronously inside the POST /upload handler, use FastAPI's 
BackgroundTasks to run chunk+embed after immediately returning a 
{"status": "processing", "document_id": ...} response.

Add a GET /upload/status/{document_id} endpoint that checks whether 
ingestion has completed (track status in Postgres — add a 
processing_status column to a documents table).

Update frontend/app.py to poll the status endpoint after upload and 
show a progress indicator instead of blocking on the upload call.
```

**What to understand:** why this matters for large PDFs specifically — without this, a big document upload would time out the HTTP request or freeze the UI.

---

### V2.7 — Long-Term Memory (simplified)

**Cursor prompt:**
```
Add a conversation summarization step: when a conversation exceeds 10 
messages, use the LLM to generate a running summary of the conversation 
so far (stored in the Conversation table as a summary column), and use 
that summary instead of the full message history when building context 
for new questions.

Keep this as ONE additional LLM call, not a separate retrieval system — 
this is meant to bound context size for long conversations, not to be 
a second RAG pipeline.
```

Be able to explain: this trades some fidelity (older details get compressed) for keeping the prompt from growing unbounded — a real, common production tradeoff.

---

### V2.8 — Authentication (treat as a checkbox, not a learning phase)

You've already built JWT auth in CafeQR. Reuse that pattern rather than treating this as new learning time.

**Cursor prompt:**
```
Add JWT-based auth to backend/: a User model in Postgres, POST 
/auth/register and POST /auth/login endpoints (passwords hashed with 
bcrypt via passlib), and a get_current_user dependency that protects 
/query and /upload routes. Scope conversations and documents to the 
authenticated user_id.

Update frontend/app.py with a simple login form before the chat interface.
```

Budget no more than a day for this — if it's taking longer, you're relearning something you already know instead of building new signal.

---

## What NOT to Add (final list)

- Multi-agent coordination
- Admin dashboard
- Any message queue / Celery / Redis (BackgroundTasks covers your actual need)
- Kubernetes, Prometheus, Grafana, or any infra beyond Docker Compose — none of it is proportionate to a portfolio project and all of it is a rabbit hole
- Vague "richer API surface" — if you find a genuine missing endpoint while building, add it; don't plan for it abstractly

---

## Suggested Sequencing

**Weeks 1-2:** Core build (Phases 1-10), as originally planned.
**Immediately after:** README + demo video (V2.1) — do not skip or postpone this.
**Week 3, if you have runway:** V2.2 → V2.4 → V2.3, in that order (tooling is cheap and fast, evaluation is high-signal, streaming is a nice UX finisher).
**Only if you still have time and energy:** V2.5, V2.6, V2.7, V2.8 — genuinely optional, prioritize by what a specific job posting asks for.

If applications are due soon, ship after Core + V2.1 and call it done. A finished, well-documented core project beats a half-built feature list every time an interviewer actually looks at your repo.
