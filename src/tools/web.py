import os

import httpx
from bs4 import BeautifulSoup

from src.tools.registry import tool


def _duckduckgo_search(query: str, max_results: int) -> list[dict]:
    from duckduckgo_search import DDGS
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    return results


def _tavily_search(query: str, max_results: int) -> list[dict]:
    from tavily import TavilyClient
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query=query, max_results=max_results, include_raw_content=False)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
        }
        for r in response.get("results", [])
    ]


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the internet using DuckDuckGo (default) or Tavily (if TAVILY_API_KEY is set).
    :param query: Search query
    :param max_results: Maximum number of results to return
    """
    try:
        if os.getenv("TAVILY_API_KEY"):
            results = _tavily_search(query, max_results)
        else:
            results = _duckduckgo_search(query, max_results)
    except Exception as e:
        return f"Search failed: {e}"

    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        lines.append(f"   {r['snippet']}")
        lines.append("")
    return "\n".join(lines)


@tool
def web_fetch(url: str) -> str:
    """Fetch a web page and extract its readable text content.
    :param url: Full URL to fetch (e.g. https://example.com/page)
    """
    try:
        response = httpx.get(url, follow_redirects=True, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return f"Failed to fetch {url}: {e}"

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    max_chars = 10000
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n... (truncated, full page is {len(text)} characters)"

    return text
