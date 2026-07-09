"""Document retrieval tool — searches uploaded documents using RAG.

This is the primary tool for answering questions about user-uploaded
documents. It retrieves relevant chunks from the ChromaDB vector store
and formats them with source citations.
"""

from langchain_core.tools import tool

from backend.ingestion.embedder import retrieve_relevant_chunks


@tool
def search_documents(query: str) -> str:
    """Search through uploaded documents to find relevant information.

    Use this tool when the user asks a question about content from their
    uploaded documents, PDFs, or files. This searches a vector database
    of document chunks and returns the most relevant passages.

    Do NOT use this for general knowledge questions, current events,
    or research paper searches — use web_search or arxiv_search instead.

    Args:
        query: The question or search query about the uploaded documents.

    Returns:
        Relevant document passages with source citations, or a message
        indicating no relevant documents were found.
    """
    chunks = retrieve_relevant_chunks(query)

    if not chunks:
        return (
            "No relevant documents found. The user may not have uploaded any documents yet, "
            "or the uploaded documents don't contain information related to this query."
        )

    # Format results with source attribution
    results = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source_filename", "Unknown source")
        page = chunk.metadata.get("page", "")
        page_info = f", page {page}" if page else ""

        results.append(
            f"**[Source {i}: {source}{page_info}]**\n{chunk.page_content}"
        )

    return "\n\n---\n\n".join(results)
