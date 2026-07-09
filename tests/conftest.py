"""Shared test fixtures — mocked LLM, test DB, FastAPI test client.

All tests use mocked LLM calls so they run without an API key,
and use SQLite in-memory for database isolation.
"""

from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.database.models import Base
from backend.database.session import get_db
from backend.main import app

# ─── Test Database ─────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Provide a clean test database session.

    Creates all tables before the test and drops them after.
    Uses SQLite in-memory for speed and isolation.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Provide a FastAPI test client with the test database injected."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Mocked LLM ───────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    """Mock the ChatGoogleGenerativeAI LLM to return deterministic responses.

    This ensures tests don't make real API calls and are reproducible.
    Returns a mock that produces an AIMessage with no tool calls
    (direct answer mode).
    """
    from langchain_core.messages import AIMessage

    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="This is a mocked response from the agent.")
    mock.bind_tools.return_value = mock

    with patch("backend.agent.nodes.ChatGoogleGenerativeAI", return_value=mock):
        yield mock


@pytest.fixture
def mock_llm_with_tool_call():
    """Mock the LLM to return a tool call (for routing tests).

    Simulates the LLM deciding to call the search_documents tool.
    """
    from langchain_core.messages import AIMessage

    tool_call_message = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_123",
                "name": "search_documents",
                "args": {"query": "test query"},
            }
        ],
    )

    follow_up_message = AIMessage(
        content="Based on the documents, here is the answer.",
    )

    mock = MagicMock()
    mock.invoke.side_effect = [tool_call_message, follow_up_message]
    mock.bind_tools.return_value = mock

    with patch("backend.agent.nodes.ChatGoogleGenerativeAI", return_value=mock):
        yield mock


# ─── Mocked Vector Store ──────────────────────────────────────────


@pytest.fixture
def mock_vectorstore():
    """Mock ChromaDB to avoid needing embeddings in tests."""
    from langchain_core.documents import Document

    mock_docs = [
        Document(
            page_content="This is test document content about machine learning.",
            metadata={"source_filename": "test.pdf", "page": 1, "chunk_index": 0},
        ),
    ]

    with patch("backend.ingestion.embedder.get_vectorstore") as mock_vs:
        mock_store = MagicMock()
        mock_store.similarity_search.return_value = mock_docs
        mock_store.add_documents.return_value = None
        mock_vs.return_value = mock_store
        yield mock_store
