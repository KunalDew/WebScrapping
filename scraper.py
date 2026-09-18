"""
scraper.py — Web Scraper Module

Takes URLs, downloads pages, and extracts clean text using trafilatura.
Falls back to BeautifulSoup if trafilatura fails.

Usage:
    python scraper.py "https://en.wikipedia.org/wiki/Photosynthesis"
"""

import sys
from dataclasses import dataclass

import requests
import trafilatura
from bs4 import BeautifulSoup

from config import SCRAPE_TIMEOUT, SCRAPE_MAX_CHARS

sys.stdout.reconfigure(encoding='utf-8')


@dataclass
class ScrapedPage:
    """A scraped web page with its extracted text."""
    url: str
    title: str
    text: str
    success: bool


def _fetch_html(url: str) -> str | None:
    """Download raw HTML from a URL with timeout."""
    try:
        resp = requests.get(url, timeout=SCRAPE_TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ⚠ Failed to download {url}: {e}")
        return None


def _extract_with_trafilatura(html: str) -> tuple[str, str]:
    """Extract clean text and title using trafilatura."""
    text = trafilatura.extract(html, include_comments=False,
                                include_tables=True, favor_recall=True) or ""
    metadata = trafilatura.extract(html, output_format="xml",
                                    include_comments=False) or ""
    # Try to get title from metadata
    title = ""
    if "<title>" in metadata:
        start = metadata.index("<title>") + 7
        end = metadata.index("</title>", start)
        title = metadata[start:end]
    return text, title


def _extract_with_bs4(html: str) -> tuple[str, str]:
    """Fallback: extract text using BeautifulSoup."""
    soup = BeautifulSoup(html, "lxml")
    
    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    
    title = soup.title.string if soup.title else ""
    text = soup.get_text(separator="\n", strip=True)
    return text, title


def scrape_url(url: str) -> ScrapedPage:
    """
    Scrape a single URL and return clean extracted text.
    Tries trafilatura first, falls back to BeautifulSoup.
    """
    html = _fetch_html(url)
    if not html:
        return ScrapedPage(url=url, title="", text="", success=False)
    
    # Try trafilatura first (better at extracting article content)
    text, title = _extract_with_trafilatura(html)
    
    # Fallback to BeautifulSoup if trafilatura returned nothing useful
    if len(text.strip()) < 100:
        text, title = _extract_with_bs4(html)
    
    # Truncate to stay within context limits
    if len(text) > SCRAPE_MAX_CHARS:
        text = text[:SCRAPE_MAX_CHARS] + "\n\n[...truncated...]"
    
    return ScrapedPage(
        url=url,
        title=title.strip() if title else url,
        text=text.strip(),
        success=bool(text.strip()),
    )


def scrape_urls(urls: list[str]) -> list[ScrapedPage]:
    """Scrape multiple URLs and return results."""
    pages = []
    for url in urls:
        page = scrape_url(url)
        pages.append(page)
        status = "✅" if page.success else "❌"
        print(f"  {status} {page.title[:60]}")
    return pages


# ─── Standalone Test ────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"📄 Scraping: {url}\n")
    
    page = scrape_url(url)
    
    if page.success:
        print(f"Title: {page.title}")
        print(f"Text length: {len(page.text)} chars")
        print(f"\n--- [ Preview ] ---")
        print(page.text[:500])
    else:
        print("❌ Failed to scrape this URL.")
