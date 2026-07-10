# 🏛️ Athena — Intelligent Agentic RAG System

Athena is a production-grade, full-stack Artificial Intelligence application that allows users to upload documents (PDF, TXT, MD) and chat with an AI that can intelligently search those documents, search the web, and search academic papers to provide accurate answers.

## 🚀 Tech Stack

**Frontend:**
*   **[Streamlit](https://streamlit.io/):** A Python-based framework for rapidly building data and AI user interfaces.

**Backend:**
*   **[FastAPI](https://fastapi.tiangolo.com/):** A lightning-fast, modern Python web framework for building APIs.
*   **[Google Gemini 2.5](https://ai.google.dev/):** The core Large Language Model (LLM) powering the intelligence.

**Databases:**
*   **[PostgreSQL](https://www.postgresql.org/):** Stores relational data like user conversations and message history.
*   **[ChromaDB](https://www.trychroma.com/):** A Vector Database that stores mathematical representations (embeddings) of uploaded documents for semantic search.

## 🏗️ Architecture

1.  **User uploads a document** via the Streamlit frontend.
2.  The FastAPI backend receives the file, splits it into smaller "chunks", converts those chunks into vectors (embeddings), and stores them in ChromaDB.
3.  **User asks a question** in the chat.
4.  The backend uses an **Agentic System** (LangChain/LangGraph) to decide which tool to use.
5.  If the question is about the uploaded document, the Agent queries ChromaDB, retrieves the relevant chunks, and generates a response.
6.  The response is sent back to the frontend and displayed to the user.

## 💻 Local Development

### Prerequisites
*   Python 3.11+
*   PostgreSQL running locally (or via Docker)

### Setup
1.  Clone the repository.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY` and `DATABASE_URL`.
4.  Run the backend: `uvicorn backend.main:app --reload`
5.  Run the frontend (in a separate terminal): `streamlit run frontend/app.py`

## ☁️ Deployment (Render)

This project is configured to deploy seamlessly to [Render.com](https://render.com/) using the `render.yaml` Blueprint.

1. Connect your GitHub repository to Render.
2. Go to **Blueprints** and sync `render.yaml`.
3. Render will automatically provision:
    *   A managed PostgreSQL database (`athena-db`)
    *   A backend web service (`athena-backend`)
    *   A frontend web service (`athena-frontend`)
4. Add your `GEMINI_API_KEY` to the `athena-backend` environment variables in the Render dashboard.
