"""Fetch AI content for enthusiasts from free, no-auth sources.

Sources:
  - arXiv API   (export.arxiv.org/api/query)  -> latest AI research papers
  - Hacker News (hn.algolia.com/api/v1)        -> trending AI news/discussion

Neither requires an API key. Output is a list of Item dicts, plus a helper
that renders each into tweet-ready text (<=280 chars).
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List

import requests

ARXIV_URL = "http://export.arxiv.org/api/query"
HN_URL = "https://hn.algolia.com/api/v1/search"
UA = {"User-Agent": "tanted-ai-bot/1.0 (+https://example.com)"}


@dataclass
class Item:
    source: str
    title: str
    url: str
    blurb: str = ""
    extra: str = ""  # authors (arxiv) or points/comments (hn)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def fetch_arxiv(categories=("cs.AI", "cs.LG", "cs.CL"), max_results: int = 5) -> List[Item]:
    cat_q = "+OR+".join(f"cat:{c}" for c in categories)
    params = {
        "search_query": cat_q,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    # arxiv wants the search_query pre-encoded with + for OR; requests would
    # escape it, so build the query string manually for that one field.
    r = requests.get(
        f"{ARXIV_URL}?search_query={cat_q}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}",
        headers=UA, timeout=30,
    )
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.text)
    items: List[Item] = []
    for e in root.findall("a:entry", ns):
        title = _clean(e.findtext("a:title", default="", namespaces=ns))
        summary = _clean(e.findtext("a:summary", default="", namespaces=ns))
        link = e.findtext("a:id", default="", namespaces=ns).strip()
        authors = [
            _clean(a.findtext("a:name", default="", namespaces=ns))
            for a in e.findall("a:author", ns)
        ]
        who = authors[0] + (" et al." if len(authors) > 1 else "") if authors else ""
        items.append(Item("arXiv", title, link, blurb=summary, extra=who))
    return items


def fetch_hn(query: str = "AI OR LLM OR \"machine learning\"", limit: int = 5,
             min_points: int = 50) -> List[Item]:
    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"points>{min_points}",
        "hitsPerPage": limit,
    }
    r = requests.get(HN_URL, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    items: List[Item] = []
    for h in r.json().get("hits", []):
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
        items.append(Item(
            "HackerNews",
            _clean(h.get("title", "")),
            url,
            extra=f"{h.get('points', 0)} pts, {h.get('num_comments', 0)} comments",
        ))
    return items


def to_tweet(item: Item, tags: str = "#AI") -> str:
    """Compose a <=280-char tweet. URL counts as 23 chars (t.co)."""
    TCO = 23
    budget = 280 - TCO - len(tags) - 3  # spaces/newline padding
    lead = item.title
    if item.extra:
        extra = f" ({item.extra})"
        if len(lead) + len(extra) <= budget:
            lead += extra
    if len(lead) > budget:
        lead = lead[: budget - 1].rstrip() + "…"
    return f"{lead} {item.url} {tags}"


if __name__ == "__main__":
    print("=== arXiv (latest AI papers) ===")
    for it in fetch_arxiv(max_results=3):
        print("-", to_tweet(it, "#AI #arXiv"))
    print("\n=== Hacker News (trending AI) ===")
    for it in fetch_hn(limit=3):
        print("-", to_tweet(it, "#AI #tech"))
