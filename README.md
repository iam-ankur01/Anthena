# 🏛️ Athena — Intelligent Research Assistant

frontend - https://athena-frontend-tx5x.onrender.com

An agentic RAG system that intelligently routes your questions to the right tool — searching your uploaded documents, the web, or academic papers — powered by LangGraph for transparent, debuggable reasoning.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ What It Does

Ask Athena a question, and it automatically decides the best way to answer:

| Question Type | Tool Used | Example |
|---|---|---|
| 📄 About your documents | **Document Search** (RAG) | *"What does my paper say about the methodology?"* |
| 🌐 Current events | **Web Search** (DuckDuckGo) | *"What happened in tech news today?"* |
| 📚 Research papers | **arXiv Search** | *"Find papers on transformer architectures"* |

No manual tool selection — the LLM reads the tool docstrings and makes the routing decision itself.

---

## 🏗️ Architecture

```
User → Streamlit UI → FastAPI → LangGraph Agent → [Tool Selection]
                                       │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                   Document Tool   Web Search     arXiv Search
                   (ChromaDB)      (DuckDuckGo)   (arXiv API)
                         │
                    PostgreSQL
                  (conversations,
                   documents)
```

**Key technology choices:**
- **LangGraph over AgentExecutor** — explicit, debuggable state machine instead of a black-box chain-of-thought loop. Each node fires visibly, making it easy to trace why the agent chose a particular tool.
- **ChromaDB over Pinecone** — runs locally with zero external dependencies, persists to disk. No API keys or cloud accounts needed for the vector store.
- **DuckDuckGo over SerpAPI** — free, no API key required. Good enough for demonstrating web search routing.
- **Mocked LLM in tests** — all tests run without an OpenAI API key. CI never makes real LLM calls.

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- An OpenAI API key

### Run with Docker Compose

```bash
# Clone the repo
git clone https://github.com/yourusername/athena.git
cd athena

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start everything
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:8501
# API docs: http://localhost:8000/docs
```

### Run Locally (development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API key and database URL

# Start the backend
uvicorn backend.main:app --reload --port 8000

# In a separate terminal, start the frontend
streamlit run frontend/app.py
```

---

## 🧪 Testing

```bash
# Run all tests (no API key needed — uses mocked LLM)
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=backend --cov-report=term-missing

# Run the routing evaluation (needs API key)
python -m evaluation.eval_agent
```

---

## 📁 Project Structure

```
athena/
├── backend/
│   ├── agent/          # LangGraph agent + tools
│   ├── database/       # SQLAlchemy models + CRUD
│   ├── ingestion/      # Document loading + chunking + embedding
│   ├── routes/         # FastAPI endpoints
│   ├── config.py       # Centralized configuration
│   └── main.py         # App entry point
├── frontend/
│   └── app.py          # Streamlit chat interface
├── evaluation/
│   ├── test_cases.json # 10 curated routing test cases
│   └── eval_agent.py   # Routing accuracy evaluator
├── tests/              # pytest test suite
├── docker-compose.yml
├── Dockerfile
└── .github/workflows/  # CI/CD
```

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/query` | Ask a question — routes to the right tool |
| `POST` | `/upload` | Upload a document for RAG |
| `GET` | `/conversations` | List all conversations |
| `GET` | `/conversations/{id}/messages` | Get conversation messages |
| `DELETE` | `/conversations/{id}` | Delete a conversation |
| `GET` | `/documents` | List uploaded documents |
| `GET` | `/health` | Health check |

---

## 🛠️ Design Decisions

1. **LangGraph over AgentExecutor** — Explicit state machine with visible routing decisions. When debugging "why did the agent use web search instead of documents?", I can trace through individual nodes instead of reading chain-of-thought logs.

2. **ChromaDB over Pinecone** — Zero external dependencies for the vector store. Persists to disk, works offline, and the entire stack runs in Docker Compose without any cloud accounts.

3. **Mocked LLM in tests** — Tests never make real API calls. The mocked LLM returns deterministic responses, so CI runs are fast, free, and reproducible.

4. **Tool docstrings drive routing** — Instead of writing explicit routing rules, the LLM reads each tool's docstring (which says when to use it and when not to) and makes the routing decision itself. This is how production agent systems work.

5. **Async everywhere** — FastAPI with async SQLAlchemy. No blocking I/O in the request path. The database session lifecycle is managed by a FastAPI dependency with automatic commit/rollback.

---

## 📄 License

MIT
