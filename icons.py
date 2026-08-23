"""Simple, original flat vector icons drawn with Pillow primitives.

Each icon draws inside a box centred at (cx, cy) with 'radius' r, in one colour.
Kept geometric and minimal so they look intentional and render identically in
CI (no external assets / licensing). Use draw(d, name, cx, cy, r, color)."""
from typing import Callable, Dict

from PIL import ImageDraw, ImageFont

import render


def _w(r: float) -> int:
    return max(3, int(r * 0.16))


def chart_up(d, cx, cy, r, c):
    pts = [(cx - r, cy + r * 0.55), (cx - r * 0.3, cy - r * 0.05),
           (cx + r * 0.2, cy + r * 0.25), (cx + r, cy - r * 0.6)]
    d.line(pts, fill=c, width=_w(r), joint="curve")
    ex, ey = cx + r, cy - r * 0.6
    d.polygon([(ex + r * 0.05, ey - r * 0.1), (ex - r * 0.45, ey - r * 0.15),
               (ex + r * 0.1, ey + r * 0.45)], fill=c)


def chart_down(d, cx, cy, r, c):
    pts = [(cx - r, cy - r * 0.55), (cx - r * 0.3, cy + r * 0.05),
           (cx + r * 0.2, cy - r * 0.25), (cx + r, cy + r * 0.6)]
    d.line(pts, fill=c, width=_w(r), joint="curve")
    ex, ey = cx + r, cy + r * 0.6
    d.polygon([(ex + r * 0.05, ey + r * 0.1), (ex - r * 0.45, ey + r * 0.15),
               (ex + r * 0.1, ey - r * 0.45)], fill=c)


def bar_chart(d, cx, cy, r, c):
    base = cy + r * 0.9
    bw = r * 0.42
    for x, h in ((cx - r * 0.75, r * 0.8), (cx, r * 1.35), (cx + r * 0.75, r * 1.8)):
        d.rounded_rectangle([x - bw / 2, base - h, x + bw / 2, base],
                            radius=bw * 0.25, fill=c)


def coins(d, cx, cy, r, c):
    w = _w(r)
    for dy in (r * 0.55, -r * 0.02, -r * 0.58):
        d.ellipse([cx - r, cy + dy - r * 0.3, cx + r, cy + dy + r * 0.3],
                  outline=c, width=w)


def piggy(d, cx, cy, r, c):
    w = _w(r)
    d.ellipse([cx - r, cy - r * 0.55, cx + r * 0.75, cy + r * 0.65], outline=c, width=w)
    # ear
    d.polygon([(cx + r * 0.15, cy - r * 0.5), (cx + r * 0.55, cy - r * 0.75),
               (cx + r * 0.5, cy - r * 0.35)], fill=c)
    # snout
    d.ellipse([cx + r * 0.45, cy - r * 0.1, cx + r * 0.95, cy + r * 0.3],
              outline=c, width=w)
    # coin slot
    d.line([(cx - r * 0.35, cy - r * 0.5), (cx + r * 0.05, cy - r * 0.5)],
           fill=c, width=w)
    # legs
    d.line([(cx - r * 0.55, cy + r * 0.6), (cx - r * 0.55, cy + r * 0.95)], fill=c, width=w)
    d.line([(cx + r * 0.35, cy + r * 0.6), (cx + r * 0.35, cy + r * 0.95)], fill=c, width=w)


def calendar(d, cx, cy, r, c):
    w = _w(r)
    d.rounded_rectangle([cx - r, cy - r * 0.75, cx + r, cy + r], radius=r * 0.2,
                        outline=c, width=w)
    d.line([(cx - r, cy - r * 0.3), (cx + r, cy - r * 0.3)], fill=c, width=w)
    for x in (cx - r * 0.55, cx + r * 0.45):
        d.line([(x, cy - r), (x, cy - r * 0.55)], fill=c, width=w)
    # a couple of "day" dots
    for x in (cx - r * 0.4, cx + r * 0.3):
        for y in (cy + r * 0.1, cy + r * 0.55):
            d.ellipse([x - r * 0.1, y - r * 0.1, x + r * 0.1, y + r * 0.1], fill=c)


def shield(d, cx, cy, r, c):
    w = _w(r)
    pts = [(cx, cy - r), (cx + r * 0.85, cy - r * 0.6), (cx + r * 0.85, cy + r * 0.15),
           (cx, cy + r), (cx - r * 0.85, cy + r * 0.15), (cx - r * 0.85, cy - r * 0.6)]
    d.polygon(pts, outline=c, width=w)
    d.line([(cx - r * 0.4, cy - r * 0.02), (cx - r * 0.05, cy + r * 0.35),
            (cx + r * 0.45, cy - r * 0.4)], fill=c, width=w, joint="curve")


def scale(d, cx, cy, r, c):
    w = _w(r)
    d.line([(cx, cy - r), (cx, cy + r * 0.7)], fill=c, width=w)          # post
    d.line([(cx - r, cy - r * 0.7), (cx + r, cy - r * 0.7)], fill=c, width=w)  # beam
    d.line([(cx - r * 0.5, cy + r * 0.7), (cx + r * 0.5, cy + r * 0.7)], fill=c, width=w)
    for sx in (cx - r, cx + r):
        d.arc([sx - r * 0.45, cy - r * 0.35, sx + r * 0.45, cy + r * 0.25],
              start=0, end=180, fill=c, width=w)
        d.line([(sx, cy - r * 0.7), (sx, cy - r * 0.1)], fill=c, width=max(2, w - 1))


def bulb(d, cx, cy, r, c):
    w = _w(r)
    d.ellipse([cx - r * 0.7, cy - r, cx + r * 0.7, cy + r * 0.4], outline=c, width=w)
    d.rounded_rectangle([cx - r * 0.35, cy + r * 0.35, cx + r * 0.35, cy + r * 0.75],
                        radius=r * 0.1, outline=c, width=w)
    d.line([(cx - r * 0.25, cy + r * 0.9), (cx + r * 0.25, cy + r * 0.9)], fill=c, width=w)


def newspaper(d, cx, cy, r, c):
    w = _w(r)
    d.rounded_rectangle([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], radius=r * 0.15,
                        outline=c, width=w)
    d.rectangle([cx - r * 0.75, cy - r * 0.55, cx - r * 0.05, cy], fill=c)
    for y in (cy - r * 0.5, cy - r * 0.2):
        d.line([(cx + r * 0.15, y), (cx + r * 0.75, y)], fill=c, width=max(2, w - 1))
    for y in (cy + r * 0.25, cy + r * 0.5):
        d.line([(cx - r * 0.75, y), (cx + r * 0.75, y)], fill=c, width=max(2, w - 1))


def globe(d, cx, cy, r, c):
    w = _w(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
    d.arc([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], 0, 360, fill=c, width=max(2, w - 1))
    d.line([(cx - r, cy), (cx + r, cy)], fill=c, width=max(2, w - 1))
    d.line([(cx - r * 0.9, cy - r * 0.5), (cx + r * 0.9, cy - r * 0.5)],
           fill=c, width=max(2, w - 1))
    d.line([(cx - r * 0.9, cy + r * 0.5), (cx + r * 0.9, cy + r * 0.5)],
           fill=c, width=max(2, w - 1))


def building(d, cx, cy, r, c):
    w = _w(r)
    d.rounded_rectangle([cx - r * 0.75, cy - r, cx + r * 0.75, cy + r], radius=r * 0.1,
                        outline=c, width=w)
    for yy in (cy - r * 0.65, cy - r * 0.2, cy + r * 0.25):
        for xx in (cx - r * 0.4, cx, cx + r * 0.4):
            d.rectangle([xx - r * 0.13, yy - r * 0.13, xx + r * 0.13, yy + r * 0.13], fill=c)
    d.rectangle([cx - r * 0.18, cy + r * 0.6, cx + r * 0.18, cy + r], fill=c)


def road(d, cx, cy, r, c):
    w = _w(r)
    d.polygon([(cx - r, cy + r), (cx - r * 0.25, cy - r), (cx + r * 0.25, cy - r),
               (cx + r, cy + r)], outline=c, width=w)
    dash_y = cy - r
    for _ in range(3):
        d.line([(cx, dash_y), (cx, dash_y + r * 0.4)], fill=c, width=w)
        dash_y += r * 0.7


def percent(d, cx, cy, r, c):
    w = _w(r)
    d.line([(cx - r * 0.7, cy + r * 0.7), (cx + r * 0.7, cy - r * 0.7)], fill=c, width=w)
    d.ellipse([cx - r * 0.75, cy - r * 0.75, cx - r * 0.2, cy - r * 0.2], outline=c, width=w)
    d.ellipse([cx + r * 0.2, cy + r * 0.2, cx + r * 0.75, cy + r * 0.75], outline=c, width=w)


def target(d, cx, cy, r, c):
    w = _w(r)
    for rr in (r, r * 0.6):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=c, width=w)
    d.ellipse([cx - r * 0.22, cy - r * 0.22, cx + r * 0.22, cy + r * 0.22], fill=c)


def check(d, cx, cy, r, c):
    w = _w(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
    d.line([(cx - r * 0.45, cy + r * 0.05), (cx - r * 0.1, cy + r * 0.4),
            (cx + r * 0.5, cy - r * 0.4)], fill=c, width=w, joint="curve")


def warning(d, cx, cy, r, c):
    w = _w(r)
    d.polygon([(cx, cy - r), (cx + r, cy + r * 0.8), (cx - r, cy + r * 0.8)],
              outline=c, width=w)
    d.line([(cx, cy - r * 0.3), (cx, cy + r * 0.25)], fill=c, width=w)
    d.ellipse([cx - r * 0.1, cy + r * 0.45, cx + r * 0.1, cy + r * 0.65], fill=c)


def swap(d, cx, cy, r, c):
    w = _w(r)
    d.line([(cx - r, cy - r * 0.4), (cx + r * 0.7, cy - r * 0.4)], fill=c, width=w)
    d.polygon([(cx + r, cy - r * 0.4), (cx + r * 0.55, cy - r * 0.7),
               (cx + r * 0.55, cy - r * 0.1)], fill=c)
    d.line([(cx + r, cy + r * 0.4), (cx - r * 0.7, cy + r * 0.4)], fill=c, width=w)
    d.polygon([(cx - r, cy + r * 0.4), (cx - r * 0.55, cy + r * 0.1),
               (cx - r * 0.55, cy + r * 0.7)], fill=c)


def snowball(d, cx, cy, r, c):
    for x, rr in ((cx - r * 0.6, r * 0.3), (cx, r * 0.5), (cx + r * 0.65, r * 0.85)):
        d.ellipse([x - rr, cy + r - rr * 2, x + rr, cy + r], fill=c)


def pie(d, cx, cy, r, c):
    w = _w(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], start=-90, end=30, fill=c)


def grid(d, cx, cy, r, c):
    s = r * 0.8
    for ox in (-1, 1):
        for oy in (-1, 1):
            x = cx + ox * s * 0.6
            y = cy + oy * s * 0.6
            d.rounded_rectangle([x - s * 0.45, y - s * 0.45, x + s * 0.45, y + s * 0.45],
                                radius=s * 0.15, fill=c)


def book(d, cx, cy, r, c):
    w = _w(r)
    d.line([(cx, cy - r * 0.7), (cx, cy + r * 0.8)], fill=c, width=w)
    for sx in (-1, 1):
        d.polygon([(cx, cy - r * 0.7), (cx + sx * r, cy - r * 0.45),
                   (cx + sx * r, cy + r * 0.8), (cx, cy + r * 0.55)],
                  outline=c, width=max(2, w - 1))


def chat(d, cx, cy, r, c):
    w = _w(r)
    d.rounded_rectangle([cx - r, cy - r * 0.8, cx + r, cy + r * 0.35], radius=r * 0.3,
                        outline=c, width=w)
    d.polygon([(cx - r * 0.55, cy + r * 0.3), (cx - r * 0.15, cy + r * 0.3),
               (cx - r * 0.55, cy + r * 0.9)], fill=c)
    for dx in (-r * 0.45, 0, r * 0.45):
        d.ellipse([cx + dx - r * 0.12, cy - r * 0.35, cx + dx + r * 0.12, cy - r * 0.11],
                  fill=c)


def spark(d, cx, cy, r, c):
    # four-point sparkle (AI feel)
    d.polygon([(cx, cy - r), (cx + r * 0.22, cy - r * 0.22), (cx + r, cy),
               (cx + r * 0.22, cy + r * 0.22), (cx, cy + r),
               (cx - r * 0.22, cy + r * 0.22), (cx - r, cy),
               (cx - r * 0.22, cy - r * 0.22)], fill=c)


def question(d, cx, cy, r, c):
    w = _w(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
    f = render.font(int(r * 1.5), bold=True)
    tw = d.textlength("?", font=f)
    d.text((cx - tw / 2, cy - r * 0.85), "?", font=f, fill=c)


def coin_r(d, cx, cy, r, c):
    """A coin with a ₹-like mark drawn from strokes (no font dependency)."""
    w = _w(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=w)
    x0 = cx - r * 0.3
    d.line([(x0, cy - r * 0.5), (x0 + r * 0.6, cy - r * 0.5)], fill=c, width=max(2, w - 1))
    d.line([(x0, cy - r * 0.2), (x0 + r * 0.6, cy - r * 0.2)], fill=c, width=max(2, w - 1))
    d.line([(x0, cy - r * 0.5), (x0, cy + r * 0.5)], fill=c, width=max(2, w - 1))
    d.line([(x0, cy - r * 0.2), (x0 + r * 0.55, cy + r * 0.55)], fill=c, width=max(2, w - 1))


ICONS: Dict[str, Callable] = {
    "chart_up": chart_up, "chart_down": chart_down, "bar_chart": bar_chart,
    "coins": coins, "piggy": piggy, "calendar": calendar, "shield": shield,
    "scale": scale, "bulb": bulb, "newspaper": newspaper, "globe": globe,
    "building": building, "road": road, "percent": percent, "target": target,
    "check": check, "warning": warning, "swap": swap, "snowball": snowball,
    "pie": pie, "grid": grid, "book": book, "question": question, "rupee": coin_r,
    "chat": chat, "spark": spark,
}


def draw(d: ImageDraw.ImageDraw, name: str, cx: float, cy: float, r: float, color):
    fn = ICONS.get(name)
    if fn is None:  # fallback: a simple dot
        d.ellipse([cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4], fill=color)
        return
    fn(d, cx, cy, r, color)
