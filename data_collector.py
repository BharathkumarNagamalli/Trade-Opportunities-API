"""
data_collector.py — Fetches current market news/data via DuckDuckGo search
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger("trade_api.data_collector")

# DuckDuckGo search queries per sector
SECTOR_SEARCH_TEMPLATES = [
    "{sector} sector India trade opportunities 2024 2025",
    "{sector} India export import market growth",
    "{sector} India FDI investment news",
    "India {sector} industry market analysis latest",
]


class DataCollector:
    """
    Collects current market information for a given sector using
    DuckDuckGo text search (no API key required).
    Returns a dict with articles, headlines, and raw snippets for AI analysis.
    """

    async def fetch(self, sector: str) -> dict[str, Any]:
        """
        Run multiple searches concurrently and aggregate results.
        Falls back gracefully if duckduckgo_search is not installed.
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            logger.warning(
                "duckduckgo_search not installed – returning placeholder data. "
                "Install with: pip install duckduckgo-search"
            )
            return self._placeholder_data(sector)

        queries = [t.format(sector=sector) for t in SECTOR_SEARCH_TEMPLATES]
        loop = asyncio.get_event_loop()

        results = await asyncio.gather(
            *[loop.run_in_executor(None, self._ddg_search, q) for q in queries],
            return_exceptions=True,
        )

        articles = []
        for batch in results:
            if isinstance(batch, Exception):
                logger.warning("DDG search batch failed: %s", batch)
                continue
            articles.extend(batch)

        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for art in articles:
            url = art.get("href", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(art)

        logger.info(
            "Collected %d unique articles for sector=%s", len(unique_articles), sector
        )
        return {
            "sector": sector,
            "articles": unique_articles[:20],           # Cap at 20 for prompt length
            "queries_used": queries,
        }

    def _ddg_search(self, query: str, max_results: int = 6) -> list[dict]:
        """Synchronous DuckDuckGo text search."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception as exc:
            logger.error("DDG search error for '%s': %s", query, exc)
            return []

    def _placeholder_data(self, sector: str) -> dict[str, Any]:
        """
        Minimal fallback used when duckduckgo_search is unavailable.
        Gemini will analyse based on its own training knowledge.
        """
        return {
            "sector": sector,
            "articles": [],
            "queries_used": [],
            "note": (
                "Live web search unavailable. "
                "Analysis is based on Gemini's training knowledge."
            ),
        }
