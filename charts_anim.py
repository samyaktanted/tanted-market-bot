"""Animated charts explainer (SIP / power of compounding).

Frame-by-frame animation with Pillow: bars grow, numbers count up, the snowball
scales, the coin mascot bobs. Encoded with ffmpeg + Indian-English voiceover.
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess

import numpy as np
from PIL import ImageDraw

import config
import icons
import render
from charts_explainer import YEARS, VALUES, INVESTED, _lakh
from explainer_avatar import _voice, _tts, _read, _write, GAP, SR, OUT

W, H, M = render.W, render.H, render.MARGIN
GOLD = render._hex(config.COLOR_ACCENT)
CYAN = (0, 200, 255)
MUTED = render._hex(config.COLOR_MUTED)
WHITE = (255, 255, 255)
FPS = 30
ANIM = 1.4  # seconds of reveal before holding

_FC: dict = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _FC:
        _FC[k] = render.font(size, bold)
    return _FC[k]


def _ease(t):
    x = min(1.0, t / ANIM)
    return 1 - (1 - x) ** 3


def _mascot(d, cx, cy, r):
    icons.draw(d, "coin_r", cx, cy, r, GOLD)
    eye = max(3, int(r // 9))
    for sx in (-0.32, 0.32):
        d.ellipse([cx + sx*r - eye, cy - r*0.15 - eye,
                   cx + sx*r + eye, cy - r*0.15 + eye], fill=(10, 15, 30))
    d.arc([cx - r*0.4, cy - r*0.1, cx + r*0.4, cy + r*0.45], 20, 160,
          fill=(10, 15, 30), width=max(3, int(r//12)))


# ---- per-frame draw functions: draw dynamic content onto a base copy ----
def d_title(img, p, t):
    d = ImageDraw.Draw(img, "RGBA")
    e = _ease(t)
    xoff = int((1 - e) * -320)
    d.text((M + xoff, 150), "THE POWER OF", font=F(48, True), fill=GOLD)
    d.text((M + xoff, 220), "Compounding", font=F(96, True), fill=WHITE)
    d.text((M + xoff, 350), "how small, steady SIPs snowball", font=F(40), fill=MUTED)
    bob = math.sin(max(0, t - ANIM) * 5) * 14 if t > ANIM else 0
    _mascot(d, W // 2, int(800 + bob), int(260 * e))
    d.text((M, 1080), "Rs 5,000 / month  ·  assumed ~12% a year*",
           font=F(38, True), fill=CYAN)


def d_chart(img, p, t):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([60, 360, W - 60, 1200], fill=(8, 15, 30, 150))
    d.text((M, 150), "GROWTH OVER TIME", font=F(40, True), fill=GOLD)
    d.text((M, 220), "Rs 5,000/month at ~12%*", font=F(58, True), fill=WHITE)
    base_y, top_y = 1120, 470
    vmax = max(VALUES) * 1.1
    xs = [230, 450, 670, 890]
    for j, (x, yr, val, inv) in enumerate(zip(xs, YEARS, VALUES, INVESTED)):
        # stagger bars: each starts a little later
        lt = t - j * 0.25
        e = _ease(lt) if lt > 0 else 0.0
        h_val = (base_y - top_y) * (val / vmax) * e
        h_inv = (base_y - top_y) * (inv / vmax) * e
        d.rectangle([x - 60, base_y - h_val, x + 60, base_y], fill=GOLD)
        d.rectangle([x - 60, base_y - h_inv, x + 60, base_y], fill=(90, 110, 140))
        if e > 0.05:
            d.text((x, base_y - h_val - 40), _lakh(val * e), font=F(30, True),
                   fill=WHITE, anchor="mm")
        d.text((x, base_y + 30), f"{yr} yrs", font=F(32, True), fill=MUTED, anchor="mm")
    d.line([100, base_y, W - 100, base_y], fill=MUTED, width=3)
    d.rectangle([M, 1160, M+34, 1186], fill=(90, 110, 140)); d.text((M+46, 1160), "Invested", font=F(28), fill=MUTED)
    d.rectangle([M+320, 1160, M+354, 1186], fill=GOLD); d.text((M+366, 1160), "Total value", font=F(28), fill=MUTED)


def d_split(img, p, t):
    d = ImageDraw.Draw(img, "RGBA")
    e = _ease(t)
    d.text((M, 150), "20 YEARS", font=F(48, True), fill=GOLD)
    d.text((M, 230), "You invest vs what it becomes", font=F(48, True), fill=WHITE)
    icons.draw(d, "coins", 300, 620, 150, (90, 110, 140))
    d.text((300, 800), _lakh(INVESTED[-1] * e), font=F(64, True), fill=WHITE, anchor="mm")
    d.text((300, 870), "you put in", font=F(34), fill=MUTED, anchor="mm")
    pulse = 100 + int(math.sin(t * 6) * 12)
    d.text((W//2, 620), "→", font=F(pulse, True), fill=CYAN, anchor="mm")
    icons.draw(d, "chart_up", 800, 620, 150, GOLD)
    d.text((800, 800), _lakh(VALUES[-1] * e), font=F(72, True), fill=GOLD, anchor="mm")
    d.text((800, 870), "it can grow to", font=F(34), fill=MUTED, anchor="mm")
    d.text((M, 1050), "*illustrative at ~12% p.a. — not guaranteed", font=F(30), fill=MUTED)


def d_snow(img, p, t):
    d = ImageDraw.Draw(img, "RGBA")
    d.text((M, 150), "WHY IT WORKS", font=F(40, True), fill=GOLD)
    d.text((M, 220), "Returns earn returns", font=F(64, True), fill=WHITE)
    for i, (cx, r) in enumerate([(240, 70), (470, 120), (760, 190)]):
        lt = t - i * 0.35
        e = _ease(lt) if lt > 0 else 0.0
        icons.draw(d, "coins", cx, 720, max(6, int(r * e)), GOLD if i == 2 else CYAN)
        d.text((cx, 720 + r + 40), ["Year 1", "Year 10", "Year 20"][i],
               font=F(32, True), fill=MUTED, anchor="mm")
    d.text((M, 1050), "The longer you stay invested, the faster the snowball grows.",
           font=F(38), fill=WHITE)


def d_take(img, p, t):
    d = ImageDraw.Draw(img, "RGBA")
    e = _ease(t)
    xoff = int((1 - e) * -320)
    d.text((M + xoff, 200), "THE TAKEAWAY", font=F(44, True), fill=GOLD)
    d.text((M + xoff, 290), "Start early.", font=F(80, True), fill=WHITE)
    d.text((M + xoff, 390), "Stay consistent.", font=F(80, True), fill=WHITE)
    bob = math.sin(max(0, t - ANIM) * 5) * 14 if t > ANIM else 0
    _mascot(d, W // 2, int(820 + bob), int(240 * e))
    d.text((M, 1080), "Time does the heavy lifting.", font=F(42), fill=CYAN)


SEGMENTS = [
    (d_title, "Let's see the power of compounding. Invest five thousand rupees a "
              "month, and let time work."),
    (d_chart, "At about twelve percent a year, your money grows faster and faster. "
              "The gold shows the total value; the grey is what you put in."),
    (d_split, "In twenty years you invest just twelve lakh rupees, but it can grow "
              "to around fifty lakh."),
    (d_snow,  "That's because your returns start earning their own returns. The "
              "snowball grows bigger the longer you stay invested."),
    (d_take,  "So start early, stay consistent, and let time do the heavy lifting."),
]


def build():
    render._BG_QUERY = "finance growth chart money"
    render._BG_MEMO.clear()
    os.makedirs(OUT, exist_ok=True)
    frames_dir = os.path.join(OUT, "anim_frames")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir)
    voice = _voice(); print("voice:", voice)

    base = render._new_canvas()[0]          # one shared background
    outro = render.outro_slide()            # static closing slide
    silence = np.zeros(int(SR * GAP), dtype=np.int16)

    parts, fi = [], 0
    seg_list = list(SEGMENTS) + [(None, "Returns are not guaranteed and vary with "
                                       "the market. This is education, not "
                                       "investment advice.")]
    for draw_fn, narration in seg_list:
        wav = os.path.join(OUT, f"an_{fi}.wav")
        dur = _tts(narration, wav, voice)
        parts.append(np.concatenate([_read(wav), silence]))
        nframes = int(round((dur + GAP) * FPS))
        for k in range(nframes):
            t = k / FPS
            if draw_fn is None:
                img = outro.copy()
            else:
                img = base.copy()
                draw_fn(img, min(1.0, t / ANIM), t)
            img.save(os.path.join(frames_dir, f"f_{fi:06d}.png"), "PNG")
            fi += 1
    print("frames:", fi)

    voice_wav = os.path.join(OUT, "anim_voice.wav"); _write(voice_wav, np.concatenate(parts))
    out = os.path.join(OUT, "compounding_anim.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "f_%06d.png"), "-i", voice_wav,
        "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart", out],
        check=True, capture_output=True)
    caption = (
        "The power of compounding — animated.\n\n"
        "Rs 5,000/month at an assumed ~12% p.a. (illustrative only):\n"
        "• 5 yrs: ~" + _lakh(VALUES[0]) + "  • 10 yrs: ~" + _lakh(VALUES[1]) +
        "  • 15 yrs: ~" + _lakh(VALUES[2]) + "  • 20 yrs: ~" + _lakh(VALUES[3]) +
        "\n\nStart early, stay consistent, let time work.\n\n"
        "Returns are not guaranteed and vary with the market. Educational only, "
        "not investment advice.\n\n"
        "#compounding #sip #mutualfunds #investing #personalfinance #stockmarket"
    )
    open(os.path.join(OUT, "anim_caption.txt"), "w").write(caption)
    print("DONE:", out)
    return out


if __name__ == "__main__":
    build()
