"""Entry point.

  python main.py generate --type recap        -> build slides + caption + manifest
  python main.py publish  --type recap        -> post that run to Instagram
  python main.py generate --type auto-extra    -> pick today's rotating extra post

Post types: recap, global, news, quiz, term, thisorthat  (and 'auto-extra').

Two phases so it fits CI: generate -> commit images -> publish (with the images
now reachable at PUBLIC_IMAGE_BASE_URL)."""
import argparse
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import posts
import render

IST = ZoneInfo("Asia/Kolkata")


def _date_slug() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def _run_dir(post_type: str) -> str:
    # Concrete type in the folder name so recap + extra never collide, and so
    # generate/publish agree on the path.
    concrete = posts.resolve_type(post_type)
    return os.path.join(config.OUTPUT_DIR, f"{_date_slug()}_{concrete}")


def generate(post_type: str) -> str:
    out_dir = _run_dir(post_type)
    concrete = posts.resolve_type(post_type)
    print(f"Building post type: {concrete}")

    images, caption = posts.build(post_type)
    paths = render.save_images(images, out_dir)

    with open(os.path.join(out_dir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)
    manifest = {
        "date": _date_slug(),
        "type": concrete,
        "caption": caption,
        "slides": [os.path.relpath(p, config.OUTPUT_DIR) for p in paths],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(paths)} slides in {out_dir}")
    print("--- caption preview ---")
    print(caption)
    return out_dir


def publish(post_type: str) -> None:
    if not config.PUBLIC_IMAGE_BASE_URL:
        raise RuntimeError(
            "PUBLIC_IMAGE_BASE_URL is not set. It must point to the public "
            "folder that serves OUTPUT_DIR so Instagram can fetch the images."
        )
    out_dir = _run_dir(post_type)
    with open(os.path.join(out_dir, "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)

    image_urls = [f"{config.PUBLIC_IMAGE_BASE_URL}/{rel}" for rel in manifest["slides"]]
    print(f"Publishing '{manifest.get('type')}' carousel:")
    for u in image_urls:
        print(" ", u)

    import instagram
    media_id = instagram.publish(image_urls, manifest["caption"])
    print(f"Published! Instagram media id: {media_id}")


def main():
    ap = argparse.ArgumentParser(description="Tanted Investments post bot")
    ap.add_argument("command", choices=["generate", "publish"])
    ap.add_argument("--type", default="recap",
                    help="recap | global | news | quiz | term | thisorthat | auto-extra")
    ap.add_argument("--publish", action="store_true",
                    help="with 'generate': also publish immediately")
    args = ap.parse_args()

    if args.command == "generate":
        generate(args.type)
        if args.publish:
            publish(args.type)
    else:
        publish(args.type)


if __name__ == "__main__":
    main()
