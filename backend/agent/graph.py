"""LangGraph agent graph — compiles the state machine for agentic reasoning.

Architecture:
    agent → (should_continue?) → tools → update_tools → agent → ... → END

The agent node calls the LLM which decides whether to invoke a tool.
If yes, the tool node executes it and feeds the result back to the agent.
The agent can then make another tool call or produce a final answer.

This loop continues until the LLM produces a response without tool calls.
"""

from langgraph.graph import END, StateGraph

from backend.agent.nodes import (
    agent_node,
    should_continue,
    tool_node,
    update_tools_used,
)
from backend.agent.state import AgentState


def build_graph() -> StateGraph:
    """Build and compile the agent state graph.

    Returns:
        A compiled LangGraph that can be invoked with an AgentState.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("update_tools", update_tools_used)

    # Set entry point
    graph.set_entry_point("agent")

    # Add conditional edge: agent decides whether to call a tool
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tool execution, update tracking, then loop back to agent
    graph.add_edge("tools", "update_tools")
    graph.add_edge("update_tools", "agent")

    return graph.compile()


# Compiled graph singleton — import this for use in API routes
compiled_graph = build_graph()
