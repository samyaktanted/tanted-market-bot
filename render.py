"""Renders the carousel slides as 1080x1350 (4:5) PNGs using Pillow."""
import os
import textwrap
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

import config
from market_data import Quote, Snapshot

W, H = 1080, 1350
MARGIN = 90

# Bundled Poppins (open-license) is preferred so slides look identical locally
# and in CI. Falls back to system fonts if the bundled files are missing.
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")

# Candidate font files, in priority order. First hit wins.
_REGULAR_CANDIDATES = [
    config.FONT_PATH,
    os.path.join(_ASSETS, "Poppins-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
_BOLD_CANDIDATES = [
    config.FONT_PATH,
    os.path.join(_ASSETS, "Poppins-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _first_existing(paths: List[str]) -> Optional[str]:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


_REGULAR_PATH = _first_existing(_REGULAR_CANDIDATES)
_BOLD_PATH = _first_existing(_BOLD_CANDIDATES) or _REGULAR_PATH


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = _BOLD_PATH if bold else _REGULAR_PATH
    if path:
        return ImageFont.truetype(path, size)
    # Last resort: Pillow's built-in bitmap font (small, but never crashes).
    return ImageFont.load_default()


def _new_canvas() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), config.COLOR_BG)
    draw = ImageDraw.Draw(img)
    # Accent bar top + footer text on every slide.
    draw.rectangle([0, 0, W, 14], fill=config.COLOR_ACCENT)
    draw.text((MARGIN, H - 70), config.BRAND_HANDLE, font=font(30),
              fill=config.COLOR_MUTED)
    return img, draw


def _wrap(draw, text, fnt, max_width) -> List[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _slide_cover(snap: Snapshot) -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 150), config.BRAND_NAME.upper(), font=font(44, True),
              fill=config.COLOR_ACCENT)
    draw.text((MARGIN, 320), "DAILY MARKET", font=font(96, True), fill=config.COLOR_TEXT)
    draw.text((MARGIN, 430), "RECAP", font=font(96, True), fill=config.COLOR_TEXT)
    draw.text((MARGIN, 580), snap.date_ist, font=font(48), fill=config.COLOR_MUTED)

    nifty = snap.nifty
    if nifty is not None:
        color = config.COLOR_UP if nifty.is_up else config.COLOR_DOWN
        draw.text((MARGIN, 760), "NIFTY 50", font=font(40, True), fill=config.COLOR_MUTED)
        draw.text((MARGIN, 820), f"{nifty.last:,.0f}", font=font(110, True),
                  fill=config.COLOR_TEXT)
        draw.text((MARGIN, 960), f"{nifty.change_pct:+.2f}%", font=font(64, True),
                  fill=color)
    return img


def _slide_indices(snap: Snapshot) -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 130), "Where markets closed", font=font(56, True),
              fill=config.COLOR_TEXT)
    y = 320
    for q in snap.indices:
        color = config.COLOR_UP if q.is_up else config.COLOR_DOWN
        draw.text((MARGIN, y), q.name, font=font(46, True), fill=config.COLOR_TEXT)
        draw.text((MARGIN, y + 60), f"{q.last:,.2f}", font=font(40),
                  fill=config.COLOR_MUTED)
        pct = f"{q.change_pct:+.2f}%"
        draw.text((W - MARGIN - draw.textlength(pct, font=font(56, True)), y + 20),
                  pct, font=font(56, True), fill=color)
        y += 200
    return img


def _slide_movers(title: str, movers: List[Quote], up: bool) -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 130), title, font=font(56, True), fill=config.COLOR_TEXT)
    color = config.COLOR_UP if up else config.COLOR_DOWN
    y = 300
    for q in movers:
        draw.text((MARGIN, y), q.name, font=font(46, True), fill=config.COLOR_TEXT)
        pct = f"{q.change_pct:+.2f}%"
        draw.text((W - MARGIN - draw.textlength(pct, font=font(46, True)), y),
                  pct, font=font(46, True), fill=color)
        draw.text((MARGIN, y + 56), f"Rs {q.last:,.2f}", font=font(32),
                  fill=config.COLOR_MUTED)
        y += 165
    return img


def _slide_tip(tip: Tuple[str, str]) -> Image.Image:
    title, body = tip
    img, draw = _new_canvas()
    draw.text((MARGIN, 150), "TIP OF THE DAY", font=font(44, True),
              fill=config.COLOR_ACCENT)
    draw.text((MARGIN, 260), title, font=font(64, True), fill=config.COLOR_TEXT)
    y = 420
    for line in _wrap(draw, body, font(46), W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=font(46), fill=config.COLOR_TEXT)
        y += 64
    return img


def _slide_outro() -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 220), "Save & follow for", font=font(60, True),
              fill=config.COLOR_TEXT)
    draw.text((MARGIN, 300), "a recap every day", font=font(60, True),
              fill=config.COLOR_TEXT)
    draw.text((MARGIN, 430), config.BRAND_HANDLE, font=font(54, True),
              fill=config.COLOR_ACCENT)
    draw.text((MARGIN, 510), config.BRAND_WEBSITE, font=font(40),
              fill=config.COLOR_MUTED)
    y = 720
    draw.text((MARGIN, y - 60), "Disclaimer", font=font(38, True),
              fill=config.COLOR_MUTED)
    body = config.DISCLAIMER
    if body.lower().startswith("disclaimer:"):
        body = body.split(":", 1)[1].strip()
    for line in _wrap(draw, body, font(34), W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=font(34), fill=config.COLOR_MUTED)
        y += 48
    return img


def build_recap_slides(snap: Snapshot, tip: Tuple[str, str]) -> List[Image.Image]:
    slides = [_slide_cover(snap), _slide_indices(snap)]
    if snap.gainers:
        slides.append(_slide_movers("Top gainers", snap.gainers, up=True))
    if snap.losers:
        slides.append(_slide_movers("Top losers", snap.losers, up=False))
    slides.append(_slide_tip(tip))
    slides.append(_slide_outro())
    return slides


def save_images(images: List[Image.Image], out_dir: str) -> List[str]:
    """Save a list of slide images as slide_1.png ... and return their paths."""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, im in enumerate(images, start=1):
        p = os.path.join(out_dir, f"slide_{i}.png")
        im.save(p, "PNG")
        paths.append(p)
    return paths


def render_carousel(snap: Snapshot, tip: Tuple[str, str], out_dir: str) -> List[str]:
    return save_images(build_recap_slides(snap, tip), out_dir)


# ---------------------------------------------------------------------------
# Generic, reusable slide primitives used by the other post types (posts.py).
# ---------------------------------------------------------------------------

def title_slide(kicker: str, title_lines: List[str], subtitle: str = "") -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 200), kicker.upper(), font=font(44, True),
              fill=config.COLOR_ACCENT)
    y = 320
    for line in title_lines:
        draw.text((MARGIN, y), line, font=font(88, True), fill=config.COLOR_TEXT)
        y += 110
    if subtitle:
        draw.text((MARGIN, y + 30), subtitle, font=font(46), fill=config.COLOR_MUTED)
    return img


def quotes_slide(title: str, quotes: List[Quote]) -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 130), title, font=font(56, True), fill=config.COLOR_TEXT)
    y = 300
    for q in quotes:
        color = config.COLOR_UP if q.is_up else config.COLOR_DOWN
        draw.text((MARGIN, y), q.name, font=font(44, True), fill=config.COLOR_TEXT)
        val = f"{q.last:,.2f}"
        draw.text((MARGIN, y + 54), val, font=font(32), fill=config.COLOR_MUTED)
        pct = f"{q.change_pct:+.2f}%"
        draw.text((W - MARGIN - draw.textlength(pct, font=font(48, True)), y + 10),
                  pct, font=font(48, True), fill=color)
        y += 165
    return img


def text_slide(kicker: str, title: str, body: str,
               body_size: int = 46) -> Image.Image:
    img, draw = _new_canvas()
    if kicker:
        draw.text((MARGIN, 150), kicker.upper(), font=font(40, True),
                  fill=config.COLOR_ACCENT)
    draw.text((MARGIN, 250), title, font=font(60, True), fill=config.COLOR_TEXT)
    y = 400
    for line in _wrap(draw, body, font(body_size), W - 2 * MARGIN):
        draw.text((MARGIN, y), line, font=font(body_size), fill=config.COLOR_TEXT)
        y += int(body_size * 1.4)
    return img


def bullets_slide(title: str, bullets: List[str], numbered: bool = False,
                  tags: Optional[List[str]] = None) -> Image.Image:
    img, draw = _new_canvas()
    draw.text((MARGIN, 130), title, font=font(56, True), fill=config.COLOR_TEXT)
    y = 300
    for i, b in enumerate(bullets):
        marker = f"{i + 1}." if numbered else "•"
        draw.text((MARGIN, y), marker, font=font(40, True), fill=config.COLOR_ACCENT)
        lines = _wrap(draw, b, font(38), W - 2 * MARGIN - 70)
        for j, line in enumerate(lines):
            draw.text((MARGIN + 70, y + j * 50), line, font=font(38),
                      fill=config.COLOR_TEXT)
        block_h = max(1, len(lines)) * 50
        if tags and i < len(tags) and tags[i]:
            draw.text((MARGIN + 70, y + block_h), tags[i], font=font(28, True),
                      fill=config.COLOR_MUTED)
            block_h += 44
        y += block_h + 40
    return img


def two_option_slide(a: str, b: str) -> Image.Image:
    img, draw = _new_canvas()
    # Option A (top half), Option B (bottom half) with a divider.
    draw.rectangle([0, H // 2 - 3, W, H // 2 + 3], fill=config.COLOR_ACCENT)
    for label, cy in ((a, H // 4 + 40), (b, 3 * H // 4 - 20)):
        w = draw.textlength(label, font=font(80, True))
        draw.text(((W - w) / 2, cy), label, font=font(80, True), fill=config.COLOR_TEXT)
    vs_w = draw.textlength("VS", font=font(52, True))
    draw.text(((W - vs_w) / 2, H // 2 - 34), "VS", font=font(52, True),
              fill=config.COLOR_ACCENT)
    return img


def outro_slide() -> Image.Image:
    return _slide_outro()
