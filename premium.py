"""A nicer 'premium' slide template: vertical gradient background, a soft accent
glow, a kicker chip, rounded content cards, and a footer with page numbers.

Built on top of render.py's font helpers so it shares the brand fonts."""
import os
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

import config
import render

W, H, MARGIN = render.W, render.H, render.MARGIN
font = render.font
_wrap = render._wrap

_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "assets", "logo.png")
_logo_cache = {}


def _logo_badge(size: int) -> Optional[Image.Image]:
    """Return the brand logo as a rounded-square RGBA badge, or None if missing."""
    if size in _logo_cache:
        return _logo_cache[size]
    if not os.path.exists(_LOGO_PATH):
        _logo_cache[size] = None
        return None
    im = Image.open(_LOGO_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size],
                                           radius=int(size * 0.18), fill=255)
    im.putalpha(mask)
    _logo_cache[size] = im
    return im

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

    # Footer: divider + small logo + handle (left) + page number (right).
    fy = H - 96
    draw.line([(MARGIN, fy), (W - MARGIN, fy)], fill="#24466B", width=2)
    handle_x = MARGIN
    badge = _logo_badge(52)
    if badge is not None:
        img.paste(badge, (MARGIN, fy + 18), badge)
        handle_x = MARGIN + 68
    draw.text((handle_x, fy + 28), config.BRAND_HANDLE, font=font(28, True),
              fill=config.COLOR_MUTED)
    if total:
        pg = f"{page}/{total}"
        draw.text((W - MARGIN - draw.textlength(pg, font=font(30, True)), fy + 28),
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
    # Hero logo badge, top-right.
    hero = _logo_badge(150)
    if hero is not None:
        img.paste(hero, (W - MARGIN - 150, 150), hero)
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


def text_block(kicker: str, title: str, body: str, page: int, total: int,
               body_size: int = 46) -> Image.Image:
    img, draw = canvas(page=page, total=total)
    y = 170
    if kicker:
        y = chip(draw, MARGIN, y, kicker) + 50
    for ln in _wrap(draw, title, font(60, True), W - 2 * MARGIN):
        draw.text((MARGIN, y), ln, font=font(60, True), fill=config.COLOR_TEXT)
        y += 78
    y += 30
    for ln in _wrap(draw, body, font(body_size), W - 2 * MARGIN):
        draw.text((MARGIN, y), ln, font=font(body_size), fill=config.COLOR_MUTED)
        y += int(body_size * 1.4)
    return img


def rows(title: str, quotes, page: int, total: int) -> Image.Image:
    """A market-data slide: name + value (left) and % change (right, coloured)."""
    img, draw = canvas(page=page, total=total)
    draw.text((MARGIN, 150), title, font=font(58, True), fill=config.COLOR_TEXT)
    y = 320
    for q in quotes:
        color = config.COLOR_UP if q.is_up else config.COLOR_DOWN
        draw.text((MARGIN, y), q.name, font=font(44, True), fill=config.COLOR_TEXT)
        draw.text((MARGIN, y + 56), f"{q.last:,.2f}", font=font(32),
                  fill=config.COLOR_MUTED)
        pct = f"{q.change_pct:+.2f}%"
        draw.text((W - MARGIN - draw.textlength(pct, font=font(52, True)), y + 14),
                  pct, font=font(52, True), fill=color)
        draw.line([(MARGIN, y + 120), (W - MARGIN, y + 120)], fill="#1C3A5B", width=2)
        y += 158
    return img


def list_slide(title: str, items: List[Tuple[str, str]], page: int,
               total: int) -> Image.Image:
    """Numbered list: accent number chip + wrapped main text + muted sub."""
    img, draw = canvas(page=page, total=total)
    draw.text((MARGIN, 140), title, font=font(58, True), fill=config.COLOR_TEXT)
    y = 300
    for i, (main, sub) in enumerate(items, start=1):
        # number chip
        draw.rounded_rectangle([MARGIN, y, MARGIN + 56, y + 56], radius=16,
                               fill=config.COLOR_ACCENT)
        num = str(i)
        draw.text((MARGIN + 28 - draw.textlength(num, font=font(34, True)) / 2, y + 8),
                  num, font=font(34, True), fill=GRAD_TOP)
        tx = MARGIN + 84
        lines = _wrap(draw, main, font(38, True), W - MARGIN - tx)
        for j, ln in enumerate(lines):
            draw.text((tx, y + j * 48), ln, font=font(38, True), fill=config.COLOR_TEXT)
        h = len(lines) * 48
        if sub:
            draw.text((tx, y + h), sub, font=font(30), fill=config.COLOR_MUTED)
            h += 42
        y += max(h, 56) + 34
    return img


def versus(a: str, b: str, page: int, total: int) -> Image.Image:
    img, draw = canvas(page=page, total=total)
    draw.line([(0, H // 2 - 2), (W, H // 2 + 2)], fill=config.COLOR_ACCENT, width=4)
    for label, cy in ((a, H // 4 + 20), (b, 3 * H // 4 - 60)):
        w = draw.textlength(label, font=font(84, True))
        draw.text(((W - w) / 2, cy), label, font=font(84, True), fill=config.COLOR_TEXT)
    r = 54
    draw.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=config.COLOR_ACCENT)
    vs = "VS"
    draw.text((W // 2 - draw.textlength(vs, font=font(40, True)) / 2, H // 2 - 26),
              vs, font=font(40, True), fill=GRAD_TOP)
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
