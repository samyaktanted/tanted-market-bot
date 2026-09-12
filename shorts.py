"""Wrap a 1080x1350 (4:5) video into a 1080x1920 YouTube Short / IG Reel.

Pads onto a brand-navy background and overlays a hook title (top) + follow CTA
(bottom) via a Pillow-rendered transparent band (this ffmpeg build has no
drawtext/libass, so text is baked into a PNG).
"""
from __future__ import annotations

import os
import subprocess

from PIL import Image, ImageDraw

import config
import render

SW, SH = 1080, 1920


def _band(title: str, cta: str, path: str) -> str:
    img = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gold = render._hex(config.COLOR_ACCENT)
    # top hook title (wrapped, centered)
    y = 70
    for ln in render._wrap(d, title, render.font(60, True), SW - 120):
        w = d.textlength(ln, font=render.font(60, True))
        d.text(((SW - w) / 2, y), ln, font=render.font(60, True), fill=(255, 255, 255))
        y += 74
    # bottom CTA
    cw = d.textlength(cta, font=render.font(40, True))
    d.text(((SW - cw) / 2, SH - 150), cta, font=render.font(40, True), fill=gold)
    img.save(path, "PNG")
    return path


def make_short(in_mp4: str, out_mp4: str, title: str,
               cta: str = "Follow @tanted_investments") -> str:
    band = _band(title, cta, os.path.splitext(out_mp4)[0] + "_band.png")
    navy = "0x%02X%02X%02X" % render._hex(config.COLOR_BG)
    subprocess.run(["ffmpeg", "-y", "-i", in_mp4, "-loop", "1", "-i", band,
        "-filter_complex",
        f"color=c={navy}:s={SW}x{SH}[bg];"
        "[0:v]scale=1080:1350[v0];"
        "[bg][v0]overlay=0:400[base];"
        "[base][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "20", "-c:a", "aac",
        "-shortest", "-movflags", "+faststart", out_mp4],
        check=True, capture_output=True)
    return out_mp4


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "output/video/compounding_anim.mp4"
    title = sys.argv[2] if len(sys.argv) > 2 else "The power of compounding"
    out = make_short(src, "output/video/short.mp4", title)
    print("wrote", out)
