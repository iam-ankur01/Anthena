"""arXiv search tool — searches for academic research papers.

Uses the arXiv API via LangChain's ArxivQueryRun wrapper.
Note: langchain-community is sunset but langchain-arxiv is not yet ready.
"""

import warnings

warnings.filterwarnings("ignore", message=".*langchain-community.*is being sunset.*")

from langchain_community.tools import ArxivQueryRun  # noqa: E402
from langchain_community.utilities import ArxivAPIWrapper  # noqa: E402
from langchain_core.tools import tool  # noqa: E402


@tool
def arxiv_search(query: str) -> str:
    """Search arXiv for academic research papers and preprints.

    Use this tool when the user asks about:
    - Scientific research papers or academic publications
    - Technical topics that benefit from peer-reviewed research
    - Specific paper titles, authors, or arXiv IDs
    - State-of-the-art methods in AI/ML, physics, math, etc.
    - Literature reviews or finding related work

    Do NOT use this for questions about the user's uploaded documents
    (use search_documents) or for general/current information
    (use web_search).

    Args:
        query: The research topic, paper title, or arXiv query.

    Returns:
        Summaries of relevant research papers with titles and authors.
    """
    try:
        arxiv_wrapper = ArxivAPIWrapper(
            top_k_results=3,
            doc_content_chars_max=3000,
        )
        search = ArxivQueryRun(api_wrapper=arxiv_wrapper)
        results = search.invoke(query)

        if not results:
            return "No arXiv papers found for this query. Try different search terms."

        return f"**arXiv Research Results:**\n\n{results}"

    except Exception as e:
        return f"arXiv search encountered an error: {str(e)}. Try rephrasing the query."
