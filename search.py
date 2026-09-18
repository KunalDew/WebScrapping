"""
search.py — DuckDuckGo Search Module

Takes a search query and returns top URLs + snippets.
Uses the ddgs library for web search.

Usage:
    python search.py "latest AI agent architectures"
"""

import sys
from dataclasses import dataclass
from ddgs import DDGS

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class SearchResult:
    """A single search result with URL, title, and snippet."""
    url: str
    title: str
    snippet: str


def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """
    Search DuckDuckGo for the given query.
    
    Args:
        query: The search query string.
        max_results: Maximum number of results to return.
    
    Returns:
        List of SearchResult objects.
    """
    results = []
    try:
        ddgs = DDGS()
        raw_results = ddgs.text(query, max_results=max_results)
        for r in raw_results:
            results.append(SearchResult(
                url=r.get("href", ""),
                title=r.get("title", ""),
                snippet=r.get("body", ""),
            ))
    except Exception as e:
        print(f"  ⚠ Search failed for '{query}': {e}")
    
    return results


# ─── Standalone Test ────────────────────────────────────────────
if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "what are AI agents"
    print(f"🔍 Searching: \"{query}\"\n")
    
    results = search(query)
    
    if not results:
        print("No results found.")
    else:
        for i, r in enumerate(results, 1):
            print(f"  [{i}] {r.title}")
            print(f"      {r.url}")
            print(f"      {r.snippet[:120]}...")
            print()
    
    print(f"Total: {len(results)} results")
