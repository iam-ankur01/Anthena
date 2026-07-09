"""Query endpoint — the core interface to the Athena agent.

POST /query accepts a user question and optional conversation_id,
invokes the LangGraph agent, stores the exchange in the database,
and returns the agent's response with metadata.
"""

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.graph import compiled_graph
from backend.database.crud import (
    add_message,
    create_conversation,
    get_conversation,
    get_messages,
)
from backend.database.session import get_db

router = APIRouter()


class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    question: str = Field(..., min_length=1, description="The user's question")
    conversation_id: str | None = Field(
        None, description="Existing conversation ID. If None, creates a new conversation."
    )


class QueryResponse(BaseModel):
    """Response body from the /query endpoint."""

    answer: str
    conversation_id: str
    tools_used: list[str]


@router.post("/query", response_model=QueryResponse)
async def query_agent(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Send a question to the Athena agent and get an intelligent response.

    The agent automatically routes to the right tool:
    - Document questions → searches uploaded documents (RAG)
    - Current events → searches the web (DuckDuckGo)
    - Research topics → searches arXiv papers

    If no conversation_id is provided, a new conversation is created.
    All messages are persisted for conversation history.
    """
    # Get or create conversation
    if request.conversation_id:
        conversation = await get_conversation(db, request.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await create_conversation(db)

    # Build message history from previous messages in this conversation
    history_messages = []
    if request.conversation_id:
        db_messages = await get_messages(db, conversation.id)
        for msg in db_messages:
            if msg.role == "user":
                history_messages.append(HumanMessage(content=msg.content))
            else:
                from langchain_core.messages import AIMessage
                history_messages.append(AIMessage(content=msg.content))

    # Add the current question
    history_messages.append(HumanMessage(content=request.question))

    # Invoke the agent graph
    try:
        result = compiled_graph.invoke(
            {
                "messages": history_messages,
                "tools_used": [],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Extract the final answer and tools used
    final_message = result["messages"][-1]
    answer = final_message.content

    # Handle langchain-google-genai returning content as a list of blocks
    if isinstance(answer, list):
        text_parts = []
        for block in answer:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                text_parts.append(block["text"])
        answer = "".join(text_parts)
    elif not isinstance(answer, str):
        answer = str(answer)

    tools_used = result.get("tools_used", [])

    # Persist user message and assistant response
    await add_message(db, conversation.id, "user", request.question)
    await add_message(db, conversation.id, "assistant", answer, tools_used=tools_used)

    return QueryResponse(
        answer=answer,
        conversation_id=conversation.id,
        tools_used=tools_used,
    )
