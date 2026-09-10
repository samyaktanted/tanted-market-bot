"""Render an AI-content Item into a modern 1080x1350 PNG card for
@ai_facts_knowledge.

Self-contained theme (Picsart-style gradient) — does NOT read Tanted's brand
colors or handle from config, so restyling this never affects the Tanted bot.
"""
from __future__ import annotations

import io
import os

import requests
from PIL import Image, ImageDraw, ImageFilter

from render import font, _wrap  # font loader only — no Tanted branding
from ai_content import Item

W, H = 1080, 1350
MARGIN = 96

# --- AI-bot theme (independent of Tanted config) ---
HANDLE = os.getenv("IG_AI_HANDLE", "@ai_facts_knowledge")
# Separate key from Tanted's PEXELS_API_KEY so the two bots never interfere.
PEXELS_KEY = os.getenv("PEXELS_API_KEY_AI") or os.getenv("PEXELS_API_KEY", "")

# Pexels search query per topic tag (falls back to a generic AI query).
BG_QUERY = {
    "AI": "artificial intelligence technology abstract",
    "AIStartups": "startup technology office",
    "Robotics": "robot robotics",
}
GRAD_TOP = (15, 12, 41)      # #0F0C29 deep indigo
GRAD_MID = (48, 43, 99)      # #302B63
GRAD_BOT = (36, 36, 62)      # #24243E
ACCENT_A = (0, 229, 255)     # cyan
ACCENT_B = (255, 78, 205)    # magenta
TEXT = (255, 255, 255)
MUTED = (176, 184, 214)      # soft lavender-grey


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient_bg() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        # two-stop gradient through the mid color
        if t < 0.5:
            c = _lerp(GRAD_TOP, GRAD_MID, t * 2)
        else:
            c = _lerp(GRAD_MID, GRAD_BOT, (t - 0.5) * 2)
        for x in range(W):
            px[x, y] = c
    return img


def _glow(img: Image.Image, center, radius, color, alpha=90):
    """Soft radial accent blob (Picsart-style)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius // 2))
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"),
              (0, 0))


def _fetch_bg(query: str) -> Image.Image | None:
    """Fetch a portrait Pexels photo, cropped to fill 1080x1350. None on failure."""
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         headers={"Authorization": PEXELS_KEY},
                         params={"query": query, "per_page": 15,
                                 "orientation": "portrait"}, timeout=20)
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            return None
        src = photos[0]["src"].get("portrait") or photos[0]["src"]["large2x"]
        raw = requests.get(src, timeout=25)
        raw.raise_for_status()
        photo = Image.open(io.BytesIO(raw.content)).convert("RGB")
        # cover-crop to WxH
        scale = max(W / photo.width, H / photo.height)
        photo = photo.resize((int(photo.width * scale) + 1,
                              int(photo.height * scale) + 1))
        left = (photo.width - W) // 2
        top = (photo.height - H) // 2
        return photo.crop((left, top, left + W, top + H))
    except Exception:
        return None


def _scrim(img: Image.Image) -> None:
    """Darken the photo with a top-heavy gradient so text stays readable."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    px = layer.load()
    for y in range(H):
        t = y / (H - 1)
        # ~78% dark at the top (behind headline), ~55% at the bottom
        a = int(200 - 60 * t)
        for x in range(W):
            px[x, y] = (10, 10, 26, a)
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"),
              (0, 0))


def render_card(item: Item, out_path: str, tag: str = "AI") -> str:
    bg = _fetch_bg(BG_QUERY.get(tag, BG_QUERY["AI"]))
    if bg is not None:
        img = bg
        _scrim(img)
        _glow(img, (W - 120, 160), 300, ACCENT_B, 55)
    else:
        img = _gradient_bg()
        _glow(img, (W - 120, 160), 320, ACCENT_B, 70)
        _glow(img, (140, H - 220), 360, ACCENT_A, 60)

    d = ImageDraw.Draw(img)

    # top gradient accent bar
    for x in range(W):
        d.line([(x, 0), (x, 10)], fill=_lerp(ACCENT_A, ACCENT_B, x / W))

    # brand handle (top-left) — the AI account, not Tanted
    d.text((MARGIN, 70), HANDLE, font=font(34, bold=True), fill=ACCENT_A)

    # source pill
    pill = item.source.upper()
    pf = font(32, bold=True)
    pw = d.textlength(pill, font=pf)
    d.rounded_rectangle([MARGIN, 140, MARGIN + pw + 46, 198], radius=29,
                        fill=ACCENT_B)
    d.text((MARGIN + 23, 150), pill, font=pf, fill=(255, 255, 255))

    # kicker
    d.text((MARGIN, 226), f"#{tag} · for AI builders", font=font(30), fill=MUTED)

    # headline — size adapts to length
    title = item.title
    size = 84 if len(title) < 60 else (70 if len(title) < 100 else 56)
    hf = font(size, bold=True)
    y = 320
    for ln in _wrap(d, title, hf, W - 2 * MARGIN):
        d.text((MARGIN, y), ln, font=hf, fill=TEXT)
        y += int(size * 1.24)

    # accent divider under headline
    y += 24
    d.rounded_rectangle([MARGIN, y, MARGIN + 160, y + 10], radius=5, fill=ACCENT_A)
    y += 44

    # meta (points/comments or authors)
    if item.extra:
        d.text((MARGIN, y), item.extra, font=font(36, bold=True), fill=ACCENT_A)
        y += 66
    # blurb
    if item.blurb:
        bf = font(33)
        for ln in _wrap(d, item.blurb, bf, W - 2 * MARGIN)[:5]:
            d.text((MARGIN, y), ln, font=bf, fill=MUTED)
            y += 45

    # footer: link + handle
    d.text((MARGIN, H - 150), item.url[:70], font=font(26), fill=MUTED)
    d.text((MARGIN, H - 96), f"{HANDLE}  ·  Daily AI drops",
           font=font(30, bold=True), fill=TEXT)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    from ai_content import fetch_hn
    it = fetch_hn(limit=1, min_points=150)[0]
    p = render_card(it, "output/ai_card_preview.png")
    print("rendered:", p, "|", it.title)
