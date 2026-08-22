"""A nicer 'premium' slide template: vertical gradient background, a soft accent
glow, a kicker chip, rounded content cards, and a footer with page numbers.

Built on top of render.py's font helpers so it shares the brand fonts."""
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

import config
import render

W, H, MARGIN = render.W, render.H, render.MARGIN
font = render.font
_wrap = render._wrap

# Palette derived from config, with a couple of template-only shades.
GRAD_TOP = config.COLOR_BG          # navy
GRAD_BOTTOM = "#07152A"             # darker navy for the gradient bottom
CARD_FILL = "#12324F"              # slightly lighter card surface
CARD_FILL_ALT = "#173A5C"


def _hex(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def canvas(page: int = 0, total: int = 0) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    top, bot = _hex(GRAD_TOP), _hex(GRAD_BOTTOM)
    img = Image.new("RGB", (W, H), GRAD_TOP)
    draw = ImageDraw.Draw(img)
    # Vertical gradient (one line per row — fast).
    for y in range(H):
        t = y / (H - 1)
        draw.line([(0, y), (W, y)],
                  fill=(_lerp(top[0], bot[0], t),
                        _lerp(top[1], bot[1], t),
                        _lerp(top[2], bot[2], t)))
    # Soft accent glow, top-right: draw a gold disc on an overlay, blur it into a
    # soft radial glow, then composite. Blurring is what makes it read as a glow
    # rather than a flat blob.
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    ac = _hex(config.COLOR_ACCENT)
    od.ellipse([W - 340, -220, W + 180, 300], fill=(ac[0], ac[1], ac[2], 120))
    overlay = overlay.filter(ImageFilter.GaussianBlur(110))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Top accent bar.
    draw.rectangle([0, 0, W, 12], fill=config.COLOR_ACCENT)

    # Footer: divider + handle (left) + page number (right).
    fy = H - 96
    draw.line([(MARGIN, fy), (W - MARGIN, fy)], fill="#24466B", width=2)
    draw.text((MARGIN, fy + 22), config.BRAND_HANDLE, font=font(30, True),
              fill=config.COLOR_MUTED)
    if total:
        pg = f"{page}/{total}"
        draw.text((W - MARGIN - draw.textlength(pg, font=font(30, True)), fy + 22),
                  pg, font=font(30, True), fill=config.COLOR_MUTED)
    return img, draw


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str) -> int:
    """Rounded accent chip with dark text. Returns its bottom y."""
    f = font(34, True)
    tw = draw.textlength(text, font=f)
    pad_x, pad_y, h = 28, 16, 62
    draw.rounded_rectangle([x, y, x + tw + pad_x * 2, y + h], radius=h // 2,
                           fill=config.COLOR_ACCENT)
    draw.text((x + pad_x, y + pad_y), text, font=f, fill=GRAD_TOP)
    return y + h


def card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, title: str, body: str,
         fill: str = CARD_FILL) -> int:
    """Rounded card with an accent side-bar, a title and wrapped body.
    Returns the bottom y so callers can stack cards."""
    inner_x = x + 46
    inner_w = w - 46 - 40
    tf, bf = font(40, True), font(34)
    body_lines = _wrap(draw, body, bf, inner_w) if body else []
    title_h = 54 if title else 0
    body_h = len(body_lines) * 46
    pad = 34
    h = pad + title_h + (14 if title and body_lines else 0) + body_h + pad

    draw.rounded_rectangle([x, y, x + w, y + h], radius=28, fill=fill)
    # accent side bar
    draw.rounded_rectangle([x + 18, y + 22, x + 30, y + h - 22], radius=6,
                           fill=config.COLOR_ACCENT)
    cy = y + pad
    if title:
        draw.text((inner_x, cy), title, font=tf, fill=config.COLOR_TEXT)
        cy += title_h + (14 if body_lines else 0)
    for ln in body_lines:
        draw.text((inner_x, cy), ln, font=bf, fill=config.COLOR_MUTED)
        cy += 46
    return y + h


def cover(kicker: str, title_lines: List[str], subtitle: str,
          total: int) -> Image.Image:
    img, draw = canvas(page=1, total=total)
    y = 220
    y = chip(draw, MARGIN, y, kicker) + 70
    for line in title_lines:
        draw.text((MARGIN, y), line, font=font(92, True), fill=config.COLOR_TEXT)
        y += 108
    if subtitle:
        y += 24
        for ln in _wrap(draw, subtitle, font(44), W - 2 * MARGIN):
            draw.text((MARGIN, y), ln, font=font(44), fill=config.COLOR_MUTED)
            y += 60
    return img


def section(title: str, cards: List[Tuple[str, str]], page: int,
            total: int) -> Image.Image:
    """A titled slide with a stack of cards. cards = [(title, body), ...]."""
    img, draw = canvas(page=page, total=total)
    draw.text((MARGIN, 150), title, font=font(60, True), fill=config.COLOR_TEXT)
    y = 300
    alt = False
    for c_title, c_body in cards:
        y = card(draw, MARGIN, y, W - 2 * MARGIN, c_title, c_body,
                 fill=CARD_FILL_ALT if alt else CARD_FILL) + 26
        alt = not alt
    return img


def outro(page: int, total: int) -> Image.Image:
    img, draw = canvas(page=page, total=total)
    y = 240
    y = chip(draw, MARGIN, y, "FOLLOW FOR MORE") + 70
    draw.text((MARGIN, y), "Simple money,", font=font(74, True),
              fill=config.COLOR_TEXT)
    draw.text((MARGIN, y + 90), "every day.", font=font(74, True),
              fill=config.COLOR_TEXT)
    y += 240
    draw.text((MARGIN, y), config.BRAND_HANDLE, font=font(52, True),
              fill=config.COLOR_ACCENT)
    draw.text((MARGIN, y + 74), config.BRAND_WEBSITE, font=font(40),
              fill=config.COLOR_MUTED)

    dy = y + 210
    draw.text((MARGIN, dy), "Disclaimer", font=font(34, True), fill=config.COLOR_MUTED)
    body = config.DISCLAIMER.split(":", 1)[-1].strip()
    dy += 48
    for ln in _wrap(draw, body, font(32), W - 2 * MARGIN):
        draw.text((MARGIN, dy), ln, font=font(32), fill=config.COLOR_MUTED)
        dy += 44
    return img
