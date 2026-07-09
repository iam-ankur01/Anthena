"""CRUD operations for conversations, messages, and documents.

All functions accept an AsyncSession and return model instances or lists.
They don't manage transactions — that's handled by the session context
in get_db().
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Conversation, Document, Message

# ─── Conversations ────────────────────────────────────────────────


async def create_conversation(
    db: AsyncSession, title: str = "New Conversation"
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(title=title)
    db.add(conversation)
    await db.flush()
    return conversation


async def get_conversation(db: AsyncSession, conversation_id: str) -> Conversation | None:
    """Get a conversation by ID, with messages eagerly loaded."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()


async def list_conversations(db: AsyncSession) -> list[Conversation]:
    """List all conversations, most recent first."""
    result = await db.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def delete_conversation(db: AsyncSession, conversation_id: str) -> bool:
    """Delete a conversation and all its messages (cascade).

    Returns True if the conversation existed and was deleted.
    """
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        return False
    await db.delete(conversation)
    await db.flush()
    return True


async def update_conversation_title(
    db: AsyncSession, conversation_id: str, title: str
) -> Conversation | None:
    """Update the title of an existing conversation."""
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        return None
    conversation.title = title
    conversation.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return conversation


# ─── Messages ─────────────────────────────────────────────────────


async def add_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    tools_used: list[str] | None = None,
) -> Message:
    """Add a message to a conversation.

    Also updates the conversation's updated_at timestamp and auto-generates
    a title from the first user message if the conversation is still titled
    'New Conversation'.
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tools_used=",".join(tools_used) if tools_used else None,
    )
    db.add(message)

    # Update conversation timestamp
    conversation = await db.get(Conversation, conversation_id)
    if conversation:
        conversation.updated_at = datetime.now(UTC).replace(tzinfo=None)

        # Auto-title from first user message
        if conversation.title == "New Conversation" and role == "user":
            conversation.title = content[:80] + ("..." if len(content) > 80 else "")

    await db.flush()
    return message


async def get_messages(db: AsyncSession, conversation_id: str) -> list[Message]:
    """Get all messages in a conversation, ordered chronologically."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


# ─── Documents ────────────────────────────────────────────────────


async def create_document(
    db: AsyncSession,
    filename: str,
    file_type: str | None = None,
) -> Document:
    """Create a document metadata record (status: processing)."""
    document = Document(filename=filename, file_type=file_type)
    db.add(document)
    await db.flush()
    return document


async def update_document_status(
    db: AsyncSession,
    document_id: str,
    status: str,
    chunk_count: int | None = None,
    error_message: str | None = None,
) -> Document | None:
    """Update a document's processing status."""
    document = await db.get(Document, document_id)
    if document is None:
        return None
    document.status = status
    if chunk_count is not None:
        document.chunk_count = chunk_count
    if error_message is not None:
        document.error_message = error_message
    await db.flush()
    return document


async def get_document(db: AsyncSession, document_id: str) -> Document | None:
    """Get a document by ID."""
    return await db.get(Document, document_id)


async def list_documents(db: AsyncSession) -> list[Document]:
    """List all documents, most recent first."""
    result = await db.execute(
        select(Document).order_by(Document.upload_date.desc())
    )
    return list(result.scalars().all())
