"""Embedder — embeds document chunks and stores them in ChromaDB."""

import uuid

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.config import settings

# Module-level cache for the vector store instance
_vectorstore: Chroma | None = None


def get_embedding_function() -> GoogleGenerativeAIEmbeddings:
    """Create and return the Google Generative AI embedding function."""
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.gemini_api_key,
    )


def get_vectorstore() -> Chroma:
    """Get or create the ChromaDB vector store singleton.

    Returns:
        A Chroma vector store instance backed by persistent storage.
    """
    global _vectorstore

    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=get_embedding_function(),
            persist_directory=settings.chroma_persist_dir,
        )

    return _vectorstore


def embed_and_store(chunks: list[Document], document_id: str | None = None) -> int:
    """Embed document chunks and store them in the vector store.

    Args:
        chunks: List of chunked Documents to embed and store.
        document_id: Optional identifier to tag all chunks from the same document.

    Returns:
        Number of chunks successfully stored.
    """
    if not chunks:
        return 0

    # Tag each chunk with a document_id for later filtering/deletion
    doc_id = document_id or str(uuid.uuid4())
    for chunk in chunks:
        chunk.metadata["document_id"] = doc_id

    vectorstore = get_vectorstore()

    # Generate unique IDs for each chunk to enable upsert behavior
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

    import time
    batch_size = 15
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        
        retries = 3
        while retries > 0:
            try:
                vectorstore.add_documents(documents=batch_chunks, ids=batch_ids)
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if retries > 1:
                        time.sleep(15)
                        retries -= 1
                    else:
                        raise e
                else:
                    raise e
        
        if i + batch_size < len(chunks):
            time.sleep(2)

    return len(chunks)


def retrieve_relevant_chunks(query: str, top_k: int | None = None) -> list[Document]:
    """Retrieve the most relevant document chunks for a given query.

    Args:
        query: The search query to find relevant chunks for.
        top_k: Number of results to return. Defaults to config value.

    Returns:
        List of Documents ranked by relevance.
    """
    vectorstore = get_vectorstore()
    k = top_k or settings.retrieval_top_k

    return vectorstore.similarity_search(query, k=k)
