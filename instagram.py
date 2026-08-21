"""Publishes a carousel to Instagram via the Meta Graph API.

Flow (per Meta's Content Publishing API):
  1. Create an item container for each image (is_carousel_item=true).
  2. Create a CAROUSEL container referencing those children + the caption.
  3. Poll the carousel container until status_code == FINISHED.
  4. Publish it.

Requirements (Instagram API with Instagram Login):
  - An Instagram *Business* or *Creator* account.
  - A long-lived Instagram user token with the instagram_business_content_publish
    (and instagram_business_basic) permissions.
  - Each image must be reachable at a public HTTPS URL (Meta fetches them).

Uses host graph.instagram.com by default (config.IG_API_HOST)."""
import time
from typing import List

import requests

import config

BASE = f"https://{config.IG_API_HOST}/{config.GRAPH_API_VERSION}"


def _post(path: str, params: dict) -> dict:
    params = dict(params)
    params["access_token"] = config.IG_ACCESS_TOKEN
    resp = requests.post(f"{BASE}/{path}", data=params, timeout=60)
    data = resp.json()
    if resp.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Graph API error on {path}: {data}")
    return data


def _get(path: str, params: dict) -> dict:
    params = dict(params)
    params["access_token"] = config.IG_ACCESS_TOKEN
    resp = requests.get(f"{BASE}/{path}", params=params, timeout=60)
    data = resp.json()
    if resp.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Graph API error on GET {path}: {data}")
    return data


def _wait_finished(container_id: str, timeout_s: int = 180) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = _get(container_id, {"fields": "status_code,status"})
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise RuntimeError(f"Container {container_id} failed: {status}")
        time.sleep(5)
    raise TimeoutError(f"Container {container_id} not FINISHED within {timeout_s}s")


def publish_carousel(image_urls: List[str], caption: str) -> str:
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        raise RuntimeError("IG_USER_ID and IG_ACCESS_TOKEN must be set to publish.")
    if not (2 <= len(image_urls) <= 10):
        raise ValueError("Instagram carousels need between 2 and 10 images.")

    # 1) child item containers
    child_ids = []
    for url in image_urls:
        res = _post(f"{config.IG_USER_ID}/media", {
            "image_url": url,
            "is_carousel_item": "true",
        })
        child_ids.append(res["id"])

    # 2) carousel container
    carousel = _post(f"{config.IG_USER_ID}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": caption,
    })
    carousel_id = carousel["id"]

    # 3) wait until Meta has ingested all children
    _wait_finished(carousel_id)

    # 4) publish
    published = _post(f"{config.IG_USER_ID}/media_publish", {
        "creation_id": carousel_id,
    })
    return published["id"]
