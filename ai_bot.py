"""AI-facts Instagram bot for @ai_facts_knowledge.

Mirrors the Tanted two-phase model so it runs in GitHub Actions:
    python ai_bot.py generate   -> fetch AI item, render card, write manifest
    python ai_bot.py publish     -> post the generated card to Instagram

Images are hosted via GitHub raw (PUBLIC_IMAGE_BASE_URL), same as the Tanted
bot. Uses its OWN credentials so it never touches the Tanted account:
    IG_AI_USER_ID, IG_AI_ACCESS_TOKEN   (repo secrets / .env)
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

import config
from ai_content import Item, fetch_arxiv, fetch_hn
from ai_image import render_card

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

HOST = "graph.instagram.com"
VER = os.getenv("GRAPH_API_VERSION", "v21.0")
HANDLE = os.getenv("IG_AI_HANDLE", "@ai_facts_knowledge")

TAGS = ("#AI #ArtificialIntelligence #MachineLearning #DeepLearning #LLM "
        "#TechNews #DataScience #Innovation #AInews #FutureTech")


def _date_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _run_dir() -> str:
    return os.path.join(config.OUTPUT_DIR, "ai", _date_slug())


def pick_item() -> Item:
    hn = fetch_hn(limit=1, min_points=150)
    if hn:
        return hn[0]
    return fetch_arxiv(categories=("cs.LG", "cs.CL"), max_results=1)[0]


def caption(item: Item) -> str:
    parts = [item.title]
    if item.extra:
        parts.append(item.extra)
    if item.blurb:
        parts.append(item.blurb[:300])
    parts.append(f"Source: {item.url}")
    parts.append(f"Follow {HANDLE} for daily AI drops.")
    parts.append(TAGS)
    return "\n\n".join(parts)


def generate() -> str:
    item = pick_item()
    out_dir = _run_dir()
    os.makedirs(out_dir, exist_ok=True)
    card = render_card(item, os.path.join(out_dir, "card.png"))
    cap = caption(item)
    manifest = {
        "date": _date_slug(),
        "source": item.source,
        "title": item.title,
        "caption": cap,
        "slide": os.path.relpath(card, config.OUTPUT_DIR),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated card in {out_dir}: {item.title}")
    print("--- caption ---\n" + cap)
    return out_dir


def publish() -> None:
    base = config.PUBLIC_IMAGE_BASE_URL
    if not base:
        raise RuntimeError("PUBLIC_IMAGE_BASE_URL not set (needs public HTTPS host).")
    user_id = os.environ["IG_AI_USER_ID"]
    token = os.environ["IG_AI_ACCESS_TOKEN"]
    with open(os.path.join(_run_dir(), "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    image_url = f"{base}/{manifest['slide']}"
    print("Publishing:", image_url)

    api = f"https://{HOST}/{VER}"
    c = requests.post(f"{api}/{user_id}/media",
                      data={"image_url": image_url, "caption": manifest["caption"],
                            "access_token": token}, timeout=60).json()
    if "id" not in c:
        raise RuntimeError(f"container failed: {c}")
    cid = c["id"]
    for _ in range(24):
        s = requests.get(f"{api}/{cid}",
                         params={"fields": "status_code", "access_token": token},
                         timeout=30).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"container error: {s}")
        time.sleep(5)
    pub = requests.post(f"{api}/{user_id}/media_publish",
                        data={"creation_id": cid, "access_token": token},
                        timeout=60).json()
    if "id" not in pub:
        raise RuntimeError(f"publish failed: {pub}")
    print(f"Published! media id {pub['id']} -> {HANDLE}")


def main():
    ap = argparse.ArgumentParser(description="AI-facts Instagram bot")
    ap.add_argument("command", choices=["generate", "publish"])
    args = ap.parse_args()
    if args.command == "generate":
        generate()
    else:
        publish()


if __name__ == "__main__":
    main()
