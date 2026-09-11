"""Publish a video as an Instagram Reel via the Instagram Login API.

Usage:
    python post_video.py --url <public_https_mp4> --caption-file <path> [--ai]

Reads creds from .env: IG_USER_ID/IG_ACCESS_TOKEN (Tanted, default) or
IG_AI_USER_ID/IG_AI_ACCESS_TOKEN with --ai. The video URL must be public HTTPS
(Meta fetches it). Reels containers process asynchronously, so we poll longer.
"""
import argparse
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

HOST = "graph.instagram.com"
VER = os.getenv("GRAPH_API_VERSION", "v21.0")


def publish_reel(video_url: str, caption: str, user_id: str, token: str) -> str:
    api = f"https://{HOST}/{VER}"
    c = requests.post(f"{api}/{user_id}/media",
                      data={"media_type": "REELS", "video_url": video_url,
                            "caption": caption, "access_token": token},
                      timeout=60).json()
    if "id" not in c:
        raise RuntimeError(f"container failed: {c}")
    cid = c["id"]
    # video processing is slower than images — poll up to ~4 min
    for _ in range(48):
        s = requests.get(f"{api}/{cid}",
                         params={"fields": "status_code,status", "access_token": token},
                         timeout=30).json()
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"container error: {s}")
        time.sleep(5)
    else:
        raise TimeoutError("Reel container not FINISHED in time")
    pub = requests.post(f"{api}/{user_id}/media_publish",
                        data={"creation_id": cid, "access_token": token},
                        timeout=60).json()
    if "id" not in pub:
        raise RuntimeError(f"publish failed: {pub}")
    # verify it actually materialized (guards the silent-drop hiccup)
    mid = pub["id"]
    v = requests.get(f"{api}/{mid}",
                     params={"fields": "permalink", "access_token": token},
                     timeout=30).json()
    print(f"PUBLISHED reel id {mid} -> {v.get('permalink', '(permalink pending)')}")
    return mid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--caption-file", required=True)
    ap.add_argument("--ai", action="store_true", help="use the AI account creds")
    args = ap.parse_args()
    if args.ai:
        uid, tok = os.environ["IG_AI_USER_ID"], os.environ["IG_AI_ACCESS_TOKEN"]
    else:
        uid, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    caption = open(args.caption_file, encoding="utf-8").read()
    publish_reel(args.url, caption, uid, tok)


if __name__ == "__main__":
    main()
