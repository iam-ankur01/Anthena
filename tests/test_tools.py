"""Tests for the agent tools — document search, web search, arXiv search."""

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


class TestDocumentTool:
    """Tests for the search_documents tool."""

    def test_returns_results_when_documents_exist(self, mock_vectorstore):
        """search_documents should return formatted results with source citations."""
        from backend.agent.tools.document_tool import search_documents

        result = search_documents.invoke({"query": "machine learning"})

        assert "test.pdf" in result
        assert "machine learning" in result
        assert "Source 1" in result

    def test_returns_no_results_message_when_empty(self):
        """search_documents should return a helpful message when no docs are found."""
        from backend.agent.tools.document_tool import search_documents

        with patch("backend.agent.tools.document_tool.retrieve_relevant_chunks", return_value=[]):
            result = search_documents.invoke({"query": "nonexistent topic"})

        assert "No relevant documents found" in result


class TestWebSearchTool:
    """Tests for the web_search tool."""

    def test_returns_results(self):
        """web_search should return formatted web search results."""
        from backend.agent.tools.web_search import web_search

        with patch(
            "backend.agent.tools.web_search.DuckDuckGoSearchRun"
        ) as mock_ddg:
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = "Result about Python programming"
            mock_ddg.return_value = mock_instance

            result = web_search.invoke({"query": "Python programming"})

        assert "Web Search Results" in result
        assert "Python programming" in result

    def test_handles_errors_gracefully(self):
        """web_search should return an error message instead of crashing."""
        from backend.agent.tools.web_search import web_search

        with patch(
            "backend.agent.tools.web_search.DuckDuckGoSearchRun"
        ) as mock_ddg:
            mock_ddg.side_effect = Exception("Network error")

            result = web_search.invoke({"query": "test"})

        assert "error" in result.lower()


class TestArxivTool:
    """Tests for the arxiv_search tool."""

    def test_returns_results(self):
        """arxiv_search should return formatted paper results."""
        from backend.agent.tools.arxiv_tool import arxiv_search

        with patch(
            "backend.agent.tools.arxiv_tool.ArxivQueryRun"
        ) as mock_arxiv:
            mock_instance = MagicMock()
            mock_instance.invoke.return_value = "Paper: Attention Is All You Need"
            mock_arxiv.return_value = mock_instance

            result = arxiv_search.invoke({"query": "transformers"})

        assert "arXiv Research Results" in result

    def test_handles_errors_gracefully(self):
        """arxiv_search should return an error message instead of crashing."""
        from backend.agent.tools.arxiv_tool import arxiv_search

        with patch(
            "backend.agent.tools.arxiv_tool.ArxivQueryRun"
        ) as mock_arxiv:
            mock_arxiv.side_effect = Exception("API error")

            result = arxiv_search.invoke({"query": "test"})

        assert "error" in result.lower()
