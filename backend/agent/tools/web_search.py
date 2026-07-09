"""Web search tool — searches the internet for current information.

Uses DuckDuckGo for free, keyless web search. No API key required.
"""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the internet for current, up-to-date information.

    Use this tool when the user asks about:
    - Current events, news, or recent developments
    - General knowledge questions that aren't about their uploaded documents
    - Real-time information (weather, stock prices, sports scores)
    - Any topic where the answer might have changed recently

    Do NOT use this for questions about the user's uploaded documents
    (use search_documents) or for academic research papers (use arxiv_search).

    Args:
        query: The search query to look up on the internet.

    Returns:
        A summary of relevant web search results.
    """
    try:
        search = DuckDuckGoSearchRun()
        results = search.invoke(query)

        if not results:
            return "No web search results found for this query. Try rephrasing the question."

        return f"**Web Search Results:**\n\n{results}"

    except Exception as e:
        return f"Web search encountered an error: {str(e)}. Try rephrasing the query."
