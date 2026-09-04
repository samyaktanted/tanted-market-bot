"""Original festive greeting posters (single 1080x1350 image), drawn with
Pillow so there are no external asset/licensing dependencies."""
from datetime import date

from PIL import Image, ImageDraw, ImageFilter

import config
import premium
import render
import stock

W, H = render.W, render.H
font = render.font

GOLD = "#E8B04B"
GOLD_SOFT = "#F0C877"
CREAM = "#F3E7C9"
TEAL = "#1E9E86"
BLUE = "#2E6FB0"


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lerp(a, b, t):
    return int(a + (b - a) * t)


def _gradient(top, bottom):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    t0, b0 = _hex(top), _hex(bottom)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)],
               fill=(_lerp(t0[0], b0[0], t), _lerp(t0[1], b0[1], t),
                     _lerp(t0[2], b0[2], t)))
    return img


def _glow(img, cx, cy, r, color, alpha=120):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).ellipse([cx - r, cy - r, cx + r, cy + r],
                               fill=(*_hex(color), alpha))
    ov = ov.filter(ImageFilter.GaussianBlur(120))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def _centered(d, text, y, fnt, fill, spacing=0):
    if spacing:
        widths = [d.textlength(ch, font=fnt) + spacing for ch in text]
        total = sum(widths) - spacing
        x = (W - total) / 2
        for ch, wch in zip(text, widths):
            d.text((x, y), ch, font=fnt, fill=fill)
            x += wch
    else:
        tw = d.textlength(text, font=fnt)
        d.text(((W - tw) / 2, y), text, font=fnt, fill=fill)


def _peacock_feather(d, cx, eye_y):
    # barbs flowing down from the eye
    n, step, maxlen = 26, 8, 120
    for i in range(n):
        y = eye_y + 40 + i * step
        ln = maxlen * (1 - i / n)
        for sgn in (-1, 1):
            d.line([(cx, y), (cx + sgn * ln, y - ln * 0.55)], fill=TEAL, width=3)
    # quill
    d.line([(cx, eye_y + 40), (cx, eye_y + 40 + n * step)], fill=GOLD, width=4)
    # eye (layered ellipses)
    layers = [(64, 84, 70, TEAL), (46, 60, 52, BLUE), (30, 42, 40, GOLD),
              (18, 30, 26, "#0E0A24")]
    for wx, up, dn, col in layers:
        d.ellipse([cx - wx, eye_y - up, cx + wx, eye_y + dn], fill=col)
    d.ellipse([cx - 6, eye_y - 10, cx + 6, eye_y + 2], fill=GOLD_SOFT)
    # little stem above the eye
    d.line([(cx, eye_y - 84), (cx, eye_y - 120)], fill=GOLD, width=3)
    d.ellipse([cx - 5, eye_y - 128, cx + 5, eye_y - 118], fill=GOLD)


def _flute(d, cx, cy, length):
    d.rounded_rectangle([cx - length / 2, cy - 13, cx + length / 2, cy + 13],
                        radius=13, fill=GOLD_SOFT, outline=GOLD, width=2)
    holes = 6
    for i in range(holes):
        hx = cx - length / 2 + length * (0.28 + 0.6 * i / (holes - 1))
        d.ellipse([hx - 6, cy - 6, hx + 6, cy + 6], fill="#3A2A10")
    # mouth hole
    d.ellipse([cx - length / 2 + 24, cy - 6, cx - length / 2 + 36, cy + 6],
              fill="#3A2A10")


def _divider(d, cy):
    d.line([(W / 2 - 200, cy), (W / 2 - 30, cy)], fill=GOLD, width=2)
    d.line([(W / 2 + 30, cy), (W / 2 + 200, cy)], fill=GOLD, width=2)
    d.polygon([(W / 2, cy - 12), (W / 2 + 16, cy), (W / 2, cy + 12),
               (W / 2 - 16, cy)], fill=GOLD)


def build_janmashtami() -> Image.Image:
    img = _gradient("#241A5C", "#0D0A22")
    img = _glow(img, W // 2, 620, 360, GOLD, alpha=90)
    d = ImageDraw.Draw(img)

    # decorative border + corner dots
    d.rounded_rectangle([40, 40, W - 40, H - 40], radius=28, outline=GOLD, width=3)
    for cx, cy in [(72, 72), (W - 72, 72), (72, H - 72), (W - 72, H - 72)]:
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=GOLD)

    _peacock_feather(d, W // 2, 300)

    _centered(d, "Happy", 540, font(72, True), GOLD_SOFT)
    _centered(d, "JANMASHTAMI", 630, font(92, True), GOLD, spacing=6)

    _divider(d, 800)

    sub = ["May the melody of Krishna's flute fill",
           "your life with joy, peace & prosperity."]
    y = 850
    for line in sub:
        _centered(d, line, y, font(40), CREAM)
        y += 56

    _flute(d, W // 2, 1010, 520)
    # small note accents
    for nx in (W // 2 - 300, W // 2 + 300):
        d.ellipse([nx - 8, 998, nx + 8, 1014], fill=GOLD)
        d.line([(nx + 8, 1006), (nx + 8, 978)], fill=GOLD, width=3)

    # brand footer: logo + name + handle
    logo = premium._logo_badge(96)
    if logo is not None:
        img.paste(logo, (W // 2 - 48, 1120), logo)
    d = ImageDraw.Draw(img)
    _centered(d, config.BRAND_HANDLE, 1235, font(34, True), GOLD_SOFT)
    _centered(d, config.BRAND_WEBSITE, 1278, font(28), CREAM)
    return img


# --- Photo-backed quote (uses Pexels; falls back to gradient) -------------
QUOTES = [
    (["Every rupee you invest today", "is a seed for tomorrow."], "sunrise mountains"),
    (["Wealth is built by habits,", "not by timing."], "calm ocean sunrise"),
    (["Save first.", "Spend what is left."], "green plant growth"),
    (["Time in the market beats", "timing the market."], "city skyline dawn"),
    (["Small, steady steps", "compound into big results."], "forest path morning"),
]


def _cover_fit(path):
    im = Image.open(path).convert("RGB")
    scale = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)))
    left, top = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((left, top, left + W, top + H))


def _scrim(im):
    """Darken a photo with a navy gradient so text stays legible."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    nv = _hex(config.COLOR_BG)
    for y in range(H):
        a = int(120 + 110 * (y / H))
        od.line([(0, y), (W, y)], fill=(nv[0], nv[1], nv[2], a))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def build_photoquote() -> Image.Image:
    (lines, query) = QUOTES[date.today().timetuple().tm_yday % len(QUOTES)]
    path = stock.get_photo(query, orientation="portrait")
    if path:
        img = _scrim(_cover_fit(path))
    else:
        img = _gradient("#241A5C", "#0D0A22")  # graceful fallback
        img = _glow(img, W // 2, 620, 360, GOLD, alpha=70)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([40, 40, W - 40, H - 40], radius=28, outline=GOLD, width=3)
    chip_text = "MONEY WISDOM"
    chip_w = d.textlength(chip_text, font=font(34, True)) + 56
    premium.chip(d, int((W - chip_w) / 2), 150, chip_text)

    y = 560
    for line in lines:
        _centered(d, line, y, font(66, True), "#FFFFFF")
        y += 92
    _divider(d, y + 30)

    logo = premium._logo_badge(96)
    if logo is not None:
        img.paste(logo, (W // 2 - 48, 1120), logo)
    d = ImageDraw.Draw(img)
    _centered(d, config.BRAND_HANDLE, 1235, font(34, True), GOLD_SOFT)
    _centered(d, config.BRAND_WEBSITE, 1278, font(28), CREAM)
    return img
