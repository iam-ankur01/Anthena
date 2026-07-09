"""Upload endpoint — handles document uploads and triggers ingestion.

POST /upload accepts a file, saves it temporarily, runs the
ingestion pipeline (load → chunk → embed), and stores metadata.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.crud import create_document, update_document_status
from backend.database.session import get_db
from backend.ingestion.chunker import chunk_documents
from backend.ingestion.embedder import embed_and_store
from backend.ingestion.loader import load_document

router = APIRouter()


class UploadResponse(BaseModel):
    """Response body from the /upload endpoint."""

    document_id: str
    filename: str
    chunk_count: int
    status: str


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """Upload a document for RAG-based question answering.

    Accepts PDF, TXT, and MD files. The document is processed through:
    1. Loading — extracts text from the file
    2. Chunking — splits into overlapping chunks (1000 chars, 200 overlap)
    3. Embedding — generates vector embeddings and stores in ChromaDB

    The document metadata is stored in Postgres for tracking.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".md", ".rst"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: .pdf, .txt, .md, .rst",
        )

    # Create document record in DB (status: processing)
    document = await create_document(db, filename=file.filename, file_type=suffix)

    try:
        # Save uploaded file to a temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Run ingestion pipeline
        documents = load_document(tmp_path)
        chunks = chunk_documents(documents)
        chunk_count = embed_and_store(chunks, document_id=document.id)

        # Update document status
        await update_document_status(
            db, document.id, status="completed", chunk_count=chunk_count
        )

        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

        return UploadResponse(
            document_id=document.id,
            filename=file.filename,
            chunk_count=chunk_count,
            status="completed",
        )

    except Exception as e:
        # Mark document as failed
        await update_document_status(
            db, document.id, status="failed", error_message=str(e)
        )
        # Clean up temp file on error too
        if "tmp_path" in locals():
            Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
