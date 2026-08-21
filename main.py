"""Entry point.

Two phases so it fits a CI pipeline cleanly:

  python main.py generate   -> pulls data, writes slides + caption + manifest.json
  python main.py publish     -> reads manifest.json and posts to Instagram

Between them, CI commits the images to a public location and sets
PUBLIC_IMAGE_BASE_URL so the Graph API can fetch them.

  python main.py generate --publish   -> do both in one process (needs the base
                                          URL already reachable; use for local
                                          testing with a hosting service)."""
import argparse
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import content
import market_data
import render
import tips

IST = ZoneInfo("Asia/Kolkata")


def _date_slug() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def generate() -> str:
    """Build slides + caption. Returns the output directory for this run."""
    slug = _date_slug()
    out_dir = os.path.join(config.OUTPUT_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)

    print("Fetching market data...")
    snap = market_data.get_snapshot()
    tip = tips.tip_for_today()

    print("Rendering slides...")
    paths = render.render_carousel(snap, tip, out_dir)

    caption = content.build_caption(snap, tip)
    with open(os.path.join(out_dir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    manifest = {
        "date": slug,
        "caption": caption,
        # store paths relative to OUTPUT_DIR so URLs are easy to build in CI
        "slides": [os.path.relpath(p, config.OUTPUT_DIR) for p in paths],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(paths)} slides in {out_dir}")
    print("--- caption preview ---")
    print(caption)
    return out_dir


def publish(out_dir: str) -> None:
    if not config.PUBLIC_IMAGE_BASE_URL:
        raise RuntimeError(
            "PUBLIC_IMAGE_BASE_URL is not set. It must point to the public "
            "folder that serves OUTPUT_DIR so Instagram can fetch the images."
        )
    with open(os.path.join(out_dir, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)

    image_urls = [
        f"{config.PUBLIC_IMAGE_BASE_URL}/{rel}" for rel in manifest["slides"]
    ]
    print("Publishing carousel with images:")
    for u in image_urls:
        print(" ", u)

    media_id = __import__("instagram").publish_carousel(image_urls, manifest["caption"])
    print(f"Published! Instagram media id: {media_id}")


def main():
    ap = argparse.ArgumentParser(description="Tanted Investments daily post bot")
    ap.add_argument("command", choices=["generate", "publish"],
                    help="generate slides+caption, or publish an existing run")
    ap.add_argument("--publish", action="store_true",
                    help="with 'generate': also publish immediately")
    ap.add_argument("--dir", default="",
                    help="with 'publish': the run dir (default: today's)")
    args = ap.parse_args()

    if args.command == "generate":
        out_dir = generate()
        if args.publish:
            publish(out_dir)
    else:
        out_dir = args.dir or os.path.join(config.OUTPUT_DIR, _date_slug())
        publish(out_dir)


if __name__ == "__main__":
    main()
