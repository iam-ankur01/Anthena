"""Tests for the document ingestion pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.ingestion.chunker import chunk_documents
from backend.ingestion.loader import load_document

import pytest


class TestDocumentLoader:
    """Tests for the document loader."""

    def test_load_text_file(self, tmp_path):
        """Should load a .txt file into Documents."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test document about artificial intelligence.")

        docs = load_document(str(test_file))
        assert len(docs) >= 1
        assert "artificial intelligence" in docs[0].page_content
        assert docs[0].metadata["source_filename"] == "test.txt"
        assert docs[0].metadata["file_type"] == ".txt"

    def test_load_markdown_file(self, tmp_path):
        """Should load a .md file into Documents."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is a markdown file about deep learning.")

        docs = load_document(str(test_file))
        assert len(docs) >= 1
        assert "deep learning" in docs[0].page_content

    def test_unsupported_file_type(self, tmp_path):
        """Should raise ValueError for unsupported file types."""
        test_file = tmp_path / "test.xlsx"
        test_file.write_text("data")

        with pytest.raises(ValueError, match="Unsupported file type"):
            load_document(str(test_file))

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            load_document("/nonexistent/path/file.txt")


class TestTextChunker:
    """Tests for the text chunker."""

    def test_chunks_are_created(self, tmp_path):
        """Should split a long document into multiple chunks."""
        # Create a document longer than the chunk size
        test_file = tmp_path / "long.txt"
        test_file.write_text("This is a test sentence. " * 200)

        docs = load_document(str(test_file))
        chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=100)

        assert len(chunks) > 1

    def test_chunk_metadata_is_preserved(self, tmp_path):
        """Chunks should preserve the original document metadata."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Short content for metadata testing.")

        docs = load_document(str(test_file))
        chunks = chunk_documents(docs)

        for chunk in chunks:
            assert "source_filename" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "total_chunks" in chunk.metadata

    def test_short_document_single_chunk(self, tmp_path):
        """A short document should produce a single chunk."""
        test_file = tmp_path / "short.txt"
        test_file.write_text("Short text.")

        docs = load_document(str(test_file))
        chunks = chunk_documents(docs)

        assert len(chunks) == 1
        assert chunks[0].metadata["chunk_index"] == 0


class TestEmbedder:
    """Tests for the embedding and storage pipeline."""

    def test_embed_and_store(self, mock_vectorstore, tmp_path):
        """Should embed chunks and store them in the vector store."""
        from backend.ingestion.embedder import embed_and_store

        test_file = tmp_path / "test.txt"
        test_file.write_text("Content about machine learning and neural networks. " * 50)

        docs = load_document(str(test_file))
        chunks = chunk_documents(docs)
        count = embed_and_store(chunks, document_id="test-doc-1")

        assert count == len(chunks)
        mock_vectorstore.add_documents.assert_called_once()

    def test_embed_empty_list(self, mock_vectorstore):
        """Should return 0 for empty chunk list."""
        from backend.ingestion.embedder import embed_and_store

        count = embed_and_store([])
        assert count == 0
