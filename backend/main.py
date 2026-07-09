"""FastAPI application entry point.

Configures CORS, registers routes, and handles DB initialization
during the application lifespan.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.session import init_db
from backend.routes import conversations, query, upload


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — runs on startup and shutdown.

    Startup: initializes database tables.
    Shutdown: cleanup (currently none needed).
    """
    # Startup
    await init_db()
    print(f"✅ Athena backend started | model={settings.llm_model}")
    yield
    # Shutdown
    print("🛑 Athena backend shutting down")


app = FastAPI(
    title="Athena",
    description="Production-grade agentic RAG system with intelligent tool routing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Streamlit frontend to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(query.router, tags=["Query"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(conversations.router, tags=["Conversations"])


@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Health check endpoint for monitoring and deployment probes."""
    return {
        "status": "healthy",
        "service": "athena",
        "model": settings.llm_model,
    }
