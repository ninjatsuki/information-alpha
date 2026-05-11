"""Module A — Ingestion Engine.

Pulls raw signals from three edges of the internet:
  1. GitHub repos matching alpha keywords, sorted by recent stars
  2. Hacker News front page (via Algolia)
  3. arXiv cs.AI RSS feed

httpx + asyncio for speed; minimal error handling per spec.
"""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

KEYWORDS = ["arbitrage", "bypass", "exploit", "automation-tool", "low-code", "scraping"]

GITHUB_SEARCH = "https://api.github.com/search/repositories"
HN_API = "https://hn.algolia.com/api/v1/search"
ARXIV_RSS = "http://export.arxiv.org/rss/cs.AI"

RSS_NS = "{http://purl.org/rss/1.0/}"


async def fetch_github_trending(
    client: httpx.AsyncClient, github_token: str | None
) -> list[dict[str, Any]]:
    """Approximate 'daily trending': repos created in last 7d matching keywords, top 10 by stars."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    keyword_query = " OR ".join(KEYWORDS)
    q = f"({keyword_query}) created:>{cutoff}"
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    params = {"q": q, "sort": "stars", "order": "desc", "per_page": 10}
    r = await client.get(GITHUB_SEARCH, params=params, headers=headers, timeout=30)
    data = r.json()
    return [
        {
            "source": "github",
            "title": repo["full_name"],
            "url": repo["html_url"],
            "description": repo.get("description") or "",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language"),
            "created_at": repo.get("created_at"),
        }
        for repo in data.get("items", [])[:10]
    ]


async def fetch_hackernews(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Pull current HN front page via Algolia."""
    params = {"tags": "front_page", "hitsPerPage": 30}
    r = await client.get(HN_API, params=params, timeout=30)
    data = r.json()
    return [
        {
            "source": "hackernews",
            "title": hit.get("title") or "",
            "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "description": hit.get("story_text") or "",
            "points": hit.get("points", 0),
            "author": hit.get("author"),
            "created_at": hit.get("created_at"),
        }
        for hit in data.get("hits", [])
    ]


async def fetch_arxiv(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Pull recent arXiv cs.AI papers from RSS."""
    r = await client.get(ARXIV_RSS, timeout=30)
    root = ET.fromstring(r.text)
    out: list[dict[str, Any]] = []
    for item in root.findall(f".//{RSS_NS}item")[:20]:
        out.append(
            {
                "source": "arxiv",
                "title": (item.findtext(f"{RSS_NS}title") or "").strip(),
                "url": (item.findtext(f"{RSS_NS}link") or "").strip(),
                "description": (item.findtext(f"{RSS_NS}description") or "").strip(),
            }
        )
    return out


async def ingest_all(github_token: str | None = None) -> list[dict[str, Any]]:
    """Run all three ingestion sources concurrently and return a flat list."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(
            fetch_github_trending(client, github_token),
            fetch_hackernews(client),
            fetch_arxiv(client),
            return_exceptions=True,
        )
    items: list[dict[str, Any]] = []
    for r in results:
        if isinstance(r, Exception):
            print(f"[ingest] source failed: {r!r}")
            continue
        items.extend(r)
    return items
