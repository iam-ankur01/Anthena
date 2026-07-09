"""Conversations endpoints — manage chat conversation history.

Provides CRUD operations for conversations and their messages.
"""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.crud import (
    delete_conversation,
    get_conversation,
    get_messages,
    list_conversations,
    list_documents,
)
from backend.database.session import get_db

router = APIRouter()


class ConversationOut(BaseModel):
    """Serialized conversation for API responses."""

    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    """Serialized message for API responses."""

    id: str
    role: str
    content: str
    tools_used: list[str] | None
    created_at: str


class DocumentOut(BaseModel):
    """Serialized document for API responses."""

    id: str
    filename: str
    file_type: str | None
    chunk_count: int | None
    status: str
    upload_date: str


@router.get("/conversations", response_model=list[ConversationOut])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
) -> list[ConversationOut]:
    """List all conversations, most recent first."""
    conversations = await list_conversations(db)
    return [
        ConversationOut(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    """Get all messages in a conversation, ordered chronologically."""
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await get_messages(db, conversation_id)
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            tools_used=m.tools_used.split(",") if m.tools_used else None,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a conversation and all its messages."""
    deleted = await delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/documents", response_model=list[DocumentOut])
async def get_documents(
    db: AsyncSession = Depends(get_db),
) -> list[DocumentOut]:
    """List all uploaded documents with their processing status."""
    documents = await list_documents(db)
    return [
        DocumentOut(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            chunk_count=d.chunk_count,
            status=d.status,
            upload_date=d.upload_date.isoformat(),
        )
        for d in documents
    ]
