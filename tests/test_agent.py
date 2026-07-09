"""Tests for the LangGraph agent — routing and graph execution."""


from langchain_core.messages import AIMessage, HumanMessage


class TestAgentGraph:
    """Tests for the compiled agent graph."""

    def test_agent_returns_direct_answer(self, mock_llm):
        """Agent should return a direct answer when no tool call is needed."""
        from backend.agent.graph import build_graph

        graph = build_graph()
        result = graph.invoke({
            "messages": [HumanMessage(content="Hello, how are you?")],
            "tools_used": [],
        })

        assert len(result["messages"]) >= 2  # Human + AI
        assert isinstance(result["messages"][-1], AIMessage)
        assert result["messages"][-1].content != ""

    def test_agent_routes_to_document_tool(self, mock_llm_with_tool_call, mock_vectorstore):
        """Agent should route document questions to search_documents tool."""
        from backend.agent.graph import build_graph

        graph = build_graph()
        result = graph.invoke({
            "messages": [HumanMessage(content="What does my document say about AI?")],
            "tools_used": [],
        })

        assert "search_documents" in result["tools_used"]


class TestAgentNodes:
    """Tests for individual agent nodes."""

    def test_should_continue_returns_tools_when_tool_call(self):
        """should_continue should return 'tools' when the LLM makes a tool call."""
        from backend.agent.nodes import should_continue

        state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{"id": "1", "name": "web_search", "args": {"query": "test"}}],
                )
            ],
            "tools_used": [],
        }

        assert should_continue(state) == "tools"

    def test_should_continue_returns_end_when_no_tool_call(self):
        """should_continue should return 'end' when the LLM gives a direct answer."""
        from backend.agent.nodes import should_continue

        state = {
            "messages": [AIMessage(content="Here is the answer.")],
            "tools_used": [],
        }

        assert should_continue(state) == "end"

    def test_update_tools_used_tracks_tools(self):
        """update_tools_used should populate the tools_used list."""
        from backend.agent.nodes import update_tools_used

        state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{"id": "1", "name": "web_search", "args": {"query": "test"}}],
                )
            ],
            "tools_used": [],
        }

        result = update_tools_used(state)
        assert "web_search" in result["tools_used"]
