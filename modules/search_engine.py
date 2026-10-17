"""Live Web Search Engine for NoteNest.

Uses DuckDuckGo (via `ddgs` / `duckduckgo_search`) to retrieve real-time online documentation,
career trends, tutorials, and technical insights.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("notenest.search")

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


class WebSearchEngine:
    """Wrapper for real-time web search grounding."""

    @classmethod
    def is_available(cls) -> bool:
        """Check if search backend is installed."""
        return DDGS is not None

    @classmethod
    def search(cls, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform a web search and return structured snippets.
        
        Args:
            query: The search query string.
            max_results: Max number of results (default: 5).
            
        Returns:
            List of dicts: [{'title': str, 'href': str, 'body': str}]
        """
        if not cls.is_available():
            logger.warning("Neither ddgs nor duckduckgo_search is installed.")
            return []

        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        results = []
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(cleaned_query, max_results=max_results))
                for item in raw_results:
                    title = item.get("title", "").strip()
                    href = item.get("href", "").strip()
                    body = item.get("body", "").strip()
                    if title or href or body:
                        results.append({
                            "title": title,
                            "href": href,
                            "body": body
                        })
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            # Fallback attempts or empty list
            return []

        return results

    @classmethod
    def format_for_llm(cls, results: List[Dict[str, str]]) -> str:
        """Format search results into a clean markdown grounding block for the LLM."""
        if not results:
            return "No web search results found."

        parts = ["### 🌐 Live Web Search Results:"]
        for idx, res in enumerate(results, 1):
            title = res.get("title", f"Result {idx}")
            href = res.get("href", "")
            body = res.get("body", "")
            parts.append(f"{idx}. **[{title}]({href})**\n   {body}")

        return "\n\n".join(parts)
