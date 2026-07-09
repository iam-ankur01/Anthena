"""Text chunker — splits documents into overlapping chunks for embedding."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings


def chunk_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split documents into overlapping chunks suitable for vector embedding.

    Uses RecursiveCharacterTextSplitter which tries to split on natural
    boundaries (paragraphs, sentences, words) before falling back to
    character-level splitting.

    Args:
        documents: List of LangChain Documents to split.
        chunk_size: Maximum chunk size in characters. Defaults to config value.
        chunk_overlap: Overlap between consecutive chunks. Defaults to config value.

    Returns:
        List of chunked Document objects with preserved metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    # Add chunk index metadata for debugging and citation
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)

    return chunks
