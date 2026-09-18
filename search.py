"""
search.py — DuckDuckGo Search Module

Takes a search query and returns top URLs + snippets.
Uses the ddgs library for web search.

Usage:
    python search.py "latest AI agent architectures"
"""

import sys
import urllib.parse
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

# Fix Windows console encoding safely
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


@dataclass
class SearchResult:
    """A single search result with URL, title, and snippet."""
    url: str
    title: str
    snippet: str


def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """
    Search web using multi-tier fallback:
    1. DuckDuckGo HTML parser (bypasses datacenter bot blocks)
    2. ddgs library
    3. Wikipedia API (guaranteed high-quality encyclopedic sources)
    """
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    # Tier 1: DuckDuckGo HTML Search
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=headers,
            timeout=8
        )
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for result_div in soup.find_all("div", class_="result"):
                # Skip sponsored ads
                classes = result_div.get("class", [])
                if "result--ad" in classes:
                    continue
                title_elem = result_div.find("a", class_="result__a")
                snippet_elem = result_div.find("a", class_="result__snippet")
                if title_elem and title_elem.get("href"):
                    href = title_elem["href"]
                    # Extract target URL from redirect
                    if "uddg=" in href:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                        if "uddg" in parsed:
                            href = parsed["uddg"][0]
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    if href and href.startswith("http") and href not in seen_urls:
                        seen_urls.add(href)
                        results.append(SearchResult(url=href, title=title, snippet=snippet))
                        if len(results) >= max_results:
                            break
    except Exception as e:
        print(f"  ⚠ DuckDuckGo HTML search error: {e}")

    if results:
        return results

    # Tier 2: ddgs Python package
    try:
        ddgs = DDGS()
        raw_results = ddgs.text(query, max_results=max_results)
        for r in raw_results:
            u = r.get("href", "")
            if u and u.startswith("http") and u not in seen_urls:
                seen_urls.add(u)
                results.append(SearchResult(
                    url=u,
                    title=r.get("title", ""),
                    snippet=r.get("body", ""),
                ))
    except Exception as e:
        print(f"  ⚠ ddgs library error: {e}")

    if results:
        return results

    # Tier 3: Wikipedia OpenSearch API (guaranteed results, zero API keys, never blocked)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit={max_results}&namespace=0&format=json"
        r = requests.get(wiki_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            titles = data[1] if len(data) > 1 else []
            urls = data[3] if len(data) > 3 else []
            for t, u in zip(titles, urls):
                if u not in seen_urls:
                    seen_urls.add(u)
                    results.append(SearchResult(url=u, title=t, snippet=f"Wikipedia encyclopedic reference for {t}"))
    except Exception as e:
        print(f"  ⚠ Wikipedia search fallback error: {e}")

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
