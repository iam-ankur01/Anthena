"""Agent graph nodes — the individual steps in the agent's reasoning pipeline.

Nodes:
    1. agent_node: Calls the LLM with tool-binding. The LLM decides whether
       to invoke a tool based on the user's question and tool docstrings.
    2. tool_node: Executes the tool selected by the LLM.
"""

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode

from backend.agent.state import AgentState
from backend.agent.tools.arxiv_tool import arxiv_search
from backend.agent.tools.document_tool import search_documents
from backend.agent.tools.web_search import web_search
from backend.config import settings

# All tools available to the agent
ALL_TOOLS = [search_documents, web_search, arxiv_search]

# The tool execution node — LangGraph's built-in ToolNode handles
# parsing the LLM's tool_call and executing the right function
tool_node = ToolNode(ALL_TOOLS)


def get_llm() -> ChatGoogleGenerativeAI:
    """Create the LLM instance with tool-binding.

    Returns a ChatGoogleGenerativeAI model with all tools bound, so the LLM can
    decide which tool to call based on the user's question.
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        api_key=settings.gemini_api_key,
        temperature=0,
    )
    return llm.bind_tools(ALL_TOOLS)


def agent_node(state: AgentState) -> dict:
    """The agent reasoning node — calls the LLM to decide what to do.

    The LLM sees the full conversation history and the tool definitions.
    It either:
    - Returns a tool_call (routed to tool_node next)
    - Returns a direct text response (goes to END)

    Args:
        state: Current agent state with message history.

    Returns:
        Updated state with the LLM's response appended to messages.
    """
    llm = get_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Routing function — decides whether to call a tool or finish.

    Examines the last message from the LLM:
    - If it contains tool_calls → route to "tools" node
    - Otherwise → route to END

    Args:
        state: Current agent state.

    Returns:
        "tools" if a tool should be called, "end" otherwise.
    """
    last_message = state["messages"][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # Track which tools are being called
        tools_used = state.get("tools_used", [])
        for tc in last_message.tool_calls:
            if tc["name"] not in tools_used:
                tools_used.append(tc["name"])
        # We don't update state here — that happens in the node return
        return "tools"

    return "end"


def update_tools_used(state: AgentState) -> dict:
    """Post-tool node — updates the tools_used list in state.

    This node runs after tool execution to record which tools were used,
    so we can display this information in the UI.

    Args:
        state: Current agent state after tool execution.

    Returns:
        Updated state with tools_used populated.
    """
    tools_used = list(state.get("tools_used", []))

    # Scan all AI messages for tool calls
    for msg in state["messages"]:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc["name"] not in tools_used:
                    tools_used.append(tc["name"])

    return {"tools_used": tools_used}
