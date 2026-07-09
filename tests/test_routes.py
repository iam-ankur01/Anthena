"""Tests for FastAPI API endpoints."""


import pytest


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    async def test_health_returns_200(self, client):
        """Health check should return 200 with service info."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "athena"


@pytest.mark.asyncio
class TestQueryEndpoint:
    """Tests for the /query endpoint."""

    async def test_query_creates_conversation(self, client, mock_llm):
        """POST /query without conversation_id should create a new conversation."""
        response = await client.post(
            "/query",
            json={"question": "What is machine learning?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "conversation_id" in data
        assert data["conversation_id"] is not None

    async def test_query_requires_question(self, client):
        """POST /query without a question should return 422."""
        response = await client.post("/query", json={})
        assert response.status_code == 422

    async def test_query_invalid_conversation(self, client, mock_llm):
        """POST /query with a nonexistent conversation_id should return 404."""
        response = await client.post(
            "/query",
            json={"question": "test", "conversation_id": "nonexistent-id"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestConversationsEndpoint:
    """Tests for the /conversations endpoints."""

    async def test_list_conversations_empty(self, client):
        """GET /conversations should return empty list initially."""
        response = await client.get("/conversations")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_conversations_after_query(self, client, mock_llm):
        """GET /conversations should return conversations after a query."""
        # Create a conversation via query
        await client.post(
            "/query",
            json={"question": "Hello"},
        )

        response = await client.get("/conversations")
        assert response.status_code == 200
        conversations = response.json()
        assert len(conversations) >= 1

    async def test_delete_conversation(self, client, mock_llm):
        """DELETE /conversations/{id} should remove the conversation."""
        # Create a conversation
        query_response = await client.post(
            "/query",
            json={"question": "Hello"},
        )
        conv_id = query_response.json()["conversation_id"]

        # Delete it
        delete_response = await client.delete(f"/conversations/{conv_id}")
        assert delete_response.status_code == 200

        # Verify it's gone
        list_response = await client.get("/conversations")
        conv_ids = [c["id"] for c in list_response.json()]
        assert conv_id not in conv_ids

    async def test_delete_nonexistent_conversation(self, client):
        """DELETE /conversations/{id} with bad ID should return 404."""
        response = await client.delete("/conversations/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDocumentsEndpoint:
    """Tests for the /documents endpoint."""

    async def test_list_documents_empty(self, client):
        """GET /documents should return empty list initially."""
        response = await client.get("/documents")
        assert response.status_code == 200
        assert response.json() == []
