"""Fetches real finance/market headlines from Indian RSS feeds.

We only ever surface the *headline + source + link* — we never rewrite or
invent article summaries, so nothing can be misattributed or fabricated.
Feeds that fail are skipped."""
import html
from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree as ET

import requests

# Public RSS feeds. Add/remove as you like.
FEEDS = [
    ("Economic Times",
     "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml"),
    ("Business Standard",
     "https://www.business-standard.com/rss/markets-106.rss"),
    ("Livemint", "https://www.livemint.com/rss/markets"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (TantedInvestments RSS reader)"}


@dataclass
class Headline:
    title: str
    source: str
    link: str


def _clean(text: str) -> str:
    return html.unescape(" ".join((text or "").split()))


def get_headlines(limit: int = 5) -> List[Headline]:
    # Collect each source's headlines separately, then round-robin so the final
    # list has a spread of outlets instead of all-from-one.
    per_source: List[List[Headline]] = []
    for source, url in FEEDS:
        got: List[Headline] = []
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for item in root.iter("item"):
                title = _clean(item.findtext("title", ""))
                link = _clean(item.findtext("link", ""))
                if title:
                    got.append(Headline(title=title, source=source, link=link))
        except Exception as exc:
            print(f"[warn] feed {source} failed: {exc}")
        if got:
            per_source.append(got)

    out: List[Headline] = []
    seen = set()
    i = 0
    while len(out) < limit and per_source:
        progressed = False
        for src in per_source:
            if i < len(src):
                h = src[i]
                if h.title.lower() not in seen:
                    seen.add(h.title.lower())
                    out.append(h)
                    progressed = True
                    if len(out) >= limit:
                        break
        if not progressed:
            break
        i += 1
    return out


if __name__ == "__main__":
    for h in get_headlines(6):
        print(f"[{h.source}] {h.title}")
