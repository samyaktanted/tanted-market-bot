"""Render an AI-content Item into a readable 1080x1350 PNG card.

Reuses the bot's fonts (render.font) and brand colors (config). Produces a
single shareable image for X or Instagram.
"""
import os
import textwrap

from PIL import Image, ImageDraw

import config
from render import font, _wrap, W, H, MARGIN
from ai_content import Item


def render_card(item: Item, out_path: str, tag: str = "AI") -> str:
    img = Image.new("RGB", (W, H), config.COLOR_BG)
    d = ImageDraw.Draw(img)

    # top accent bar
    d.rectangle([0, 0, W, 14], fill=config.COLOR_ACCENT)

    # source pill (e.g. "arXiv" / "HackerNews")
    pill = item.source.upper()
    pf = font(34, bold=True)
    pw = d.textlength(pill, font=pf)
    d.rounded_rectangle([MARGIN, 70, MARGIN + pw + 44, 130], radius=14,
                        fill=config.COLOR_ACCENT)
    d.text((MARGIN + 22, 82), pill, font=pf, fill=config.COLOR_BG)

    # kicker
    d.text((MARGIN, 175), f"#{tag} · for AI builders", font=font(30),
           fill=config.COLOR_MUTED)

    # headline (title), wrapped, size adapts to length
    title = item.title
    size = 78 if len(title) < 70 else (64 if len(title) < 110 else 52)
    hf = font(size, bold=True)
    lines = _wrap(d, title, hf, W - 2 * MARGIN)
    y = 260
    for ln in lines:
        d.text((MARGIN, y), ln, font=hf, fill=config.COLOR_TEXT)
        y += int(size * 1.25)

    # blurb / meta
    y += 30
    meta = item.extra or ""
    if meta:
        d.text((MARGIN, y), meta, font=font(36), fill=config.COLOR_ACCENT)
        y += 70
    if item.blurb:
        bf = font(34)
        blurb = item.blurb
        for ln in _wrap(d, blurb, bf, W - 2 * MARGIN)[:6]:
            d.text((MARGIN, y), ln, font=bf, fill=config.COLOR_MUTED)
            y += 46

    # footer: brand + link
    d.text((MARGIN, H - 130), item.url, font=font(28), fill=config.COLOR_MUTED)
    d.text((MARGIN, H - 70), config.BRAND_HANDLE, font=font(30),
           fill=config.COLOR_MUTED)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    from ai_content import fetch_hn
    item = fetch_hn(limit=1, min_points=150)[0]
    path = render_card(item, os.path.join(config.OUTPUT_DIR, "ai_card.png"))
    print("rendered:", path)
    print("title:", item.title)
