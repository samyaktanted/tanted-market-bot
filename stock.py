"""Pexels stock-photo integration. Free key from https://www.pexels.com/api/
set as PEXELS_API_KEY. Photos are under the Pexels License (free commercial use,
modification allowed, no attribution required).

get_photo() returns a local file path to a downloaded photo, or None if there's
no key / no result / any error — callers must handle None (fall back to a drawn
background)."""
import hashlib
import os

import requests

import config

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "cache")


def get_photo(query: str, orientation: str = "portrait") -> "str | None":
    if not config.PEXELS_API_KEY:
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": config.PEXELS_API_KEY},
            params={"query": query, "orientation": orientation,
                    "per_page": 15, "size": "large"},
            timeout=20,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            print(f"[warn] pexels: no photos for '{query}'")
            return None
        src = photos[0]["src"]
        url = src.get("portrait") or src.get("large2x") or src.get("large")
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = os.path.join(CACHE_DIR,
                            hashlib.md5((query + url).encode()).hexdigest() + ".jpg")
        if not os.path.exists(path):
            data = requests.get(url, timeout=30).content
            with open(path, "wb") as f:
                f.write(data)
        return path
    except Exception as exc:
        print(f"[warn] pexels fetch failed: {exc}")
        return None
