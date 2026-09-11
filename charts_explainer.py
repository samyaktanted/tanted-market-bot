"""Charts + graphics explainer (SIP / power of compounding).

Replaces text slides with Pillow-drawn charts, icon graphics, and a simple
coin mascot. Voiceover (Indian-English) + slideshow, assembled to an MP4.

Reuses render (canvas/fonts), icons (vector graphics), and the TTS/assembly
helpers from explainer_avatar.
"""
from __future__ import annotations

import os

from PIL import ImageDraw

import config
import icons
import render
from explainer_avatar import _voice, _tts, _read, _write, GAP, SR, OUT
import numpy as np
import subprocess

W, H, M = render.W, render.H, render.MARGIN
GOLD = render._hex(config.COLOR_ACCENT)
CYAN = (0, 200, 255)
MUTED = render._hex(config.COLOR_MUTED)
WHITE = (255, 255, 255)


# ---- SIP compounding math: Rs 5000/month at 12% p.a. ----
def _fv(years, monthly=5000, annual=0.12):
    i = annual / 12
    m = years * 12
    return monthly * (((1 + i) ** m - 1) / i) * (1 + i)


YEARS = [5, 10, 15, 20]
VALUES = [_fv(y) for y in YEARS]
INVESTED = [5000 * 12 * y for y in YEARS]


def _lakh(v):
    return f"Rs {v/1e5:.1f}L"


def _panel(d, x0, y0, x1, y1, alpha=150):
    d.rectangle([x0, y0, x1, y1], fill=(8, 15, 30, alpha))


def _mascot(d, cx, cy, r):
    """A friendly rupee-coin character."""
    icons.draw(d, "coin_r", cx, cy, r, GOLD)
    # eyes + smile
    eye = max(3, r // 9)
    d.ellipse([cx - r*0.32 - eye, cy - r*0.15 - eye, cx - r*0.32 + eye, cy - r*0.15 + eye], fill=(10, 15, 30))
    d.ellipse([cx + r*0.32 - eye, cy - r*0.15 - eye, cx + r*0.32 + eye, cy - r*0.15 + eye], fill=(10, 15, 30))
    d.arc([cx - r*0.4, cy - r*0.1, cx + r*0.4, cy + r*0.45], 20, 160, fill=(10, 15, 30), width=max(3, r//12))


def slide_title():
    img, d = render._new_canvas()
    dr = ImageDraw.Draw(img, "RGBA")
    d.text((M, 150), "THE POWER OF", font=render.font(48, True), fill=GOLD)
    d.text((M, 220), "Compounding", font=render.font(96, True), fill=WHITE)
    d.text((M, 350), "how small, steady SIPs snowball", font=render.font(40), fill=MUTED)
    _mascot(dr, W // 2, 800, 260)
    d.text((M, 1080), "Rs 5,000 / month  ·  assumed ~12% a year*",
           font=render.font(38, True), fill=CYAN)
    return img


def slide_growth_chart():
    img, d = render._new_canvas()
    dr = ImageDraw.Draw(img, "RGBA")
    _panel(dr, 60, 360, W - 60, 1200)
    d.text((M, 150), "GROWTH OVER TIME", font=render.font(40, True), fill=GOLD)
    d.text((M, 220), "Rs 5,000/month at ~12%*", font=render.font(58, True), fill=WHITE)

    base_y, top_y = 1120, 470
    vmax = max(VALUES) * 1.1
    xs = [230, 450, 670, 890]
    bw = 120
    for x, yr, val, inv in zip(xs, YEARS, VALUES, INVESTED):
        h_val = (base_y - top_y) * (val / vmax)
        h_inv = (base_y - top_y) * (inv / vmax)
        # growth portion (gold) then invested portion (muted) on top of baseline
        d.rectangle([x - bw//2, base_y - h_val, x + bw//2, base_y], fill=GOLD)
        d.rectangle([x - bw//2, base_y - h_inv, x + bw//2, base_y], fill=(90, 110, 140))
        d.text((x, base_y - h_val - 46), _lakh(val), font=render.font(30, True),
               fill=WHITE, anchor="mm")
        d.text((x, base_y + 30), f"{yr} yrs", font=render.font(32, True),
               fill=MUTED, anchor="mm")
    d.line([100, base_y, W - 100, base_y], fill=MUTED, width=3)
    # legend
    d.rectangle([M, 1160, M + 34, 1186], fill=(90, 110, 140)); d.text((M+46, 1160), "Invested", font=render.font(28), fill=MUTED)
    d.rectangle([M + 320, 1160, M + 354, 1186], fill=GOLD); d.text((M+366, 1160), "Total value", font=render.font(28), fill=MUTED)
    return img


def slide_bigsplit():
    img, d = render._new_canvas()
    dr = ImageDraw.Draw(img, "RGBA")
    d.text((M, 150), "20 YEARS", font=render.font(48, True), fill=GOLD)
    d.text((M, 230), "You invest vs what it becomes", font=render.font(48, True), fill=WHITE)
    # two big figures with icons
    icons.draw(dr, "coins", 300, 620, 150, (90, 110, 140))
    d.text((300, 800), _lakh(INVESTED[-1]), font=render.font(64, True), fill=WHITE, anchor="mm")
    d.text((300, 870), "you put in", font=render.font(34), fill=MUTED, anchor="mm")
    d.text((W//2, 620), "→", font=render.font(120, True), fill=CYAN, anchor="mm")
    icons.draw(dr, "chart_up", 800, 620, 150, GOLD)
    d.text((800, 800), _lakh(VALUES[-1]), font=render.font(72, True), fill=GOLD, anchor="mm")
    d.text((800, 870), "it can grow to", font=render.font(34), fill=MUTED, anchor="mm")
    d.text((M, 1050), "*illustrative at ~12% p.a. — not guaranteed",
           font=render.font(30), fill=MUTED)
    return img


def slide_snowball():
    img, d = render._new_canvas()
    dr = ImageDraw.Draw(img, "RGBA")
    d.text((M, 150), "WHY IT WORKS", font=render.font(40, True), fill=GOLD)
    d.text((M, 220), "Returns earn returns", font=render.font(64, True), fill=WHITE)
    # growing snowballs
    for i, (cx, r) in enumerate([(240, 70), (470, 120), (760, 190)]):
        icons.draw(dr, "coins", cx, 720, r, GOLD if i == 2 else CYAN)
        d.text((cx, 720 + r + 40), ["Year 1", "Year 10", "Year 20"][i],
               font=render.font(32, True), fill=MUTED, anchor="mm")
    d.text((M, 1050), "The longer you stay invested, the faster the snowball grows.",
           font=render.font(38), fill=WHITE)
    return img


def slide_takeaway():
    img, d = render._new_canvas()
    dr = ImageDraw.Draw(img, "RGBA")
    d.text((M, 200), "THE TAKEAWAY", font=render.font(44, True), fill=GOLD)
    d.text((M, 290), "Start early.", font=render.font(80, True), fill=WHITE)
    d.text((M, 390), "Stay consistent.", font=render.font(80, True), fill=WHITE)
    _mascot(dr, W // 2, 820, 240)
    d.text((M, 1080), "Time does the heavy lifting.", font=render.font(42), fill=CYAN)
    return img


def _segments():
    return [
        (slide_title(),
         "Let's see the power of compounding. Invest five thousand rupees a "
         "month, and let time work."),
        (slide_growth_chart(),
         "At about twelve percent a year, your money grows faster and faster. "
         "The gold shows the total value; the grey is what you actually put in."),
        (slide_bigsplit(),
         "In twenty years you invest just twelve lakh rupees, but it can grow to "
         "around fifty lakh."),
        (slide_snowball(),
         "That's because your returns start earning their own returns. The "
         "snowball grows bigger the longer you stay invested."),
        (slide_takeaway(),
         "So start early, stay consistent, and let time do the heavy lifting."),
        (render.outro_slide(),
         "Returns are not guaranteed and vary with the market. This is education, "
         "not investment advice."),
    ]


def build():
    render._BG_QUERY = "finance growth chart money"
    render._BG_MEMO.clear()
    os.makedirs(OUT, exist_ok=True)
    voice = _voice(); print("voice:", voice)
    segs = _segments()
    silence = np.zeros(int(SR * GAP), dtype=np.int16)
    parts, listlines, imgs = [], [], []
    for i, (img, narration) in enumerate(segs, 1):
        wav = os.path.join(OUT, f"c_seg_{i}.wav")
        dur = _tts(narration, wav, voice)
        p = os.path.join(OUT, f"c_slide_{i}.png"); img.save(p, "PNG")
        imgs.append(p)
        listlines.append(f"file '{os.path.abspath(p)}'\nduration {dur + GAP:.3f}")
        parts.append(np.concatenate([_read(wav), silence]))
    voice_wav = os.path.join(OUT, "chart_voice.wav"); _write(voice_wav, np.concatenate(parts))
    listfile = os.path.join(OUT, "chart_list.txt")
    with open(listfile, "w") as f:
        f.write("\n".join(listlines) + f"\nfile '{os.path.abspath(imgs[-1])}'\n")
    out = os.path.join(OUT, "compounding_charts.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
        "-i", voice_wav, "-vf", "scale=1080:1350,fps=30,format=yuv420p",
        "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-shortest",
        "-movflags", "+faststart", out], check=True, capture_output=True)
    caption = (
        "The power of compounding, in charts.\n\n"
        "Rs 5,000/month at an assumed ~12% p.a. (illustrative only):\n"
        "• 5 yrs: ~" + _lakh(VALUES[0]) + "  • 10 yrs: ~" + _lakh(VALUES[1]) +
        "  • 15 yrs: ~" + _lakh(VALUES[2]) + "  • 20 yrs: ~" + _lakh(VALUES[3]) +
        "\n\nStart early, stay consistent, let time work.\n\n"
        "Returns are not guaranteed and vary with the market. Educational only, "
        "not investment advice.\n\n"
        "#compounding #sip #mutualfunds #investing #personalfinance #stockmarket"
    )
    open(os.path.join(OUT, "chart_caption.txt"), "w").write(caption)
    print("DONE:", out)
    return out


if __name__ == "__main__":
    build()
