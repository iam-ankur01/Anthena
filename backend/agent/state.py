"""Agent state definition for the LangGraph state machine.

The AgentState flows through the graph, accumulating messages
and tracking which tools were invoked.
"""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State that flows through the LangGraph agent.

    Attributes:
        messages: The conversation message history. Uses LangGraph's
            add_messages reducer to append new messages automatically.
        tools_used: List of tool names that were invoked during this query.
            Tracked for observability and display in the UI.
    """

    messages: Annotated[list, add_messages]
    tools_used: list[str]
