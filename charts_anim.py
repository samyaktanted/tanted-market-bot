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


def _money(v):
    return f"Rs {v/1e7:.2f}Cr" if v >= 1e7 else f"Rs {v/1e5:.1f}L"


def _render(segments, out_name, caption, bg_query="finance growth chart money"):
    """Generic animator: segments = [(draw_fn(img,p,t), narration), ...].
    A disclaimer outro is appended automatically. Returns (mp4, caption_file)."""
    render._BG_QUERY = bg_query
    render._BG_MEMO.clear()
    os.makedirs(OUT, exist_ok=True)
    frames_dir = os.path.join(OUT, "anim_frames")
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(frames_dir)
    voice = _voice(); print("voice:", voice)

    base = render._new_canvas()[0]
    outro = render.outro_slide()
    silence = np.zeros(int(SR * GAP), dtype=np.int16)

    parts, fi = [], 0
    seg_list = list(segments) + [(None, "Returns are not guaranteed and vary with "
                                        "the market. This is education, not "
                                        "investment advice.")]
    for draw_fn, narration in seg_list:
        wav = os.path.join(OUT, f"an_{fi}.wav")
        dur = _tts(narration, wav, voice)
        parts.append(np.concatenate([_read(wav), silence]))
        for k in range(int(round((dur + GAP) * FPS))):
            t = k / FPS
            img = outro.copy() if draw_fn is None else base.copy()
            if draw_fn is not None:
                draw_fn(img, min(1.0, t / ANIM), t)
            img.save(os.path.join(frames_dir, f"f_{fi:06d}.png"), "PNG")
            fi += 1
    print("frames:", fi)

    voice_wav = os.path.join(OUT, f"{out_name}_voice.wav"); _write(voice_wav, np.concatenate(parts))
    out = os.path.join(OUT, f"{out_name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "f_%06d.png"), "-i", voice_wav,
        "-vf", "format=yuv420p", "-c:v", "libx264", "-crf", "20",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart", out],
        check=True, capture_output=True)
    cap_file = os.path.join(OUT, f"{out_name}_caption.txt")
    open(cap_file, "w").write(caption)
    print("DONE:", out)
    return out, cap_file


def build():  # compounding topic
    cap = ("The power of compounding — animated.\n\n"
           "Rs 5,000/month at an assumed ~12% p.a. (illustrative only):\n"
           "• 5 yrs: ~" + _lakh(VALUES[0]) + "  • 10 yrs: ~" + _lakh(VALUES[1]) +
           "  • 15 yrs: ~" + _lakh(VALUES[2]) + "  • 20 yrs: ~" + _lakh(VALUES[3]) +
           "\n\nStart early, stay consistent, let time work.\n\n"
           "Returns are not guaranteed and vary with the market. Educational only, "
           "not investment advice.\n\n"
           "#compounding #sip #mutualfunds #investing #personalfinance #stockmarket")
    return _render(SEGMENTS, "compounding_anim", cap)


# ---------------- Topic: The cost of waiting (start at 25 vs 35) ----------------
from charts_explainer import _fv
A_VAL, B_VAL = _fv(35), _fv(25)          # invest Rs5k/mo till 60
A_INV, B_INV = 5000*12*35, 5000*12*25
GAP_VAL = A_VAL - B_VAL


def se_title(img, p, t):
    d = ImageDraw.Draw(img, "RGBA"); e = _ease(t); xo = int((1-e)*-320)
    d.text((M+xo, 150), "THE COST OF", font=F(50, True), fill=GOLD)
    d.text((M+xo, 225), "Waiting", font=F(110, True), fill=WHITE)
    d.text((M+xo, 380), "start at 25 vs 35 — same Rs 5,000/month", font=F(38), fill=MUTED)
    bob = math.sin(max(0, t-ANIM)*5)*14 if t > ANIM else 0
    _mascot(d, W//2, int(820+bob), int(240*e))


def se_chart(img, p, t):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([60, 360, W-60, 1200], fill=(8, 15, 30, 150))
    d.text((M, 150), "VALUE AT AGE 60", font=F(40, True), fill=GOLD)
    d.text((M, 220), "Same SIP, at ~12%*", font=F(58, True), fill=WHITE)
    base_y, top_y = 1120, 470
    vmax = A_VAL * 1.12
    for x, lab, val, inv in [(330, "Start at 25", A_VAL, A_INV),
                             (740, "Start at 35", B_VAL, B_INV)]:
        e = _ease(t)
        hv = (base_y-top_y)*(val/vmax)*e
        hi = (base_y-top_y)*(inv/vmax)*e
        d.rectangle([x-110, base_y-hv, x+110, base_y], fill=GOLD)
        d.rectangle([x-110, base_y-hi, x+110, base_y], fill=(90, 110, 140))
        d.text((x, base_y-hv-46), _money(val*e), font=F(38, True), fill=WHITE, anchor="mm")
        d.text((x, base_y+34), lab, font=F(34, True), fill=MUTED, anchor="mm")
    d.line([100, base_y, W-100, base_y], fill=MUTED, width=3)
    d.rectangle([M, 1160, M+34, 1186], fill=(90, 110, 140)); d.text((M+46, 1160), "Invested", font=F(28), fill=MUTED)
    d.rectangle([M+320, 1160, M+354, 1186], fill=GOLD); d.text((M+366, 1160), "Value at 60", font=F(28), fill=MUTED)


def se_gap(img, p, t):
    d = ImageDraw.Draw(img, "RGBA"); e = _ease(t)
    d.text((M, 220), "WAITING 10 YEARS COSTS", font=F(44, True), fill=GOLD)
    d.text((W//2, 620), _money(GAP_VAL*e), font=F(150, True), fill=CYAN, anchor="mm")
    d.text((W//2, 780), "same monthly amount — only time changed", font=F(40), fill=WHITE, anchor="mm")
    icons.draw(d, "warning", W//2, 1000, 90, GOLD)


def se_take(img, p, t):
    d = ImageDraw.Draw(img, "RGBA"); e = _ease(t); xo = int((1-e)*-320)
    d.text((M+xo, 220), "THE LESSON", font=F(44, True), fill=GOLD)
    d.text((M+xo, 300), "Start today.", font=F(88, True), fill=WHITE)
    bob = math.sin(max(0, t-ANIM)*5)*14 if t > ANIM else 0
    _mascot(d, W//2, int(820+bob), int(240*e))
    d.text((M, 1080), "The best time was yesterday. The next best is now.", font=F(38), fill=CYAN)


SEG_STARTEARLY = [
    (se_title, "Meet two investors. Both put in five thousand rupees a month. "
               "One starts at twenty-five, the other at thirty-five."),
    (se_chart, "By age sixty, at about twelve percent, the early starter has "
               "around three crore. The one who waited just ten years? "
               "About one crore."),
    (se_gap,   "That ten-year delay costs over two crore rupees. Same monthly "
               "amount — only the starting time changed."),
    (se_take,  "So the best time to start was yesterday. The next best time is today."),
]


def build_startearly():
    cap = ("The cost of waiting — animated.\n\n"
           "Rs 5,000/month till age 60, assumed ~12% p.a. (illustrative only):\n"
           "• Start at 25 (invest " + _money(A_INV) + "): ~" + _money(A_VAL) + "\n"
           "• Start at 35 (invest " + _money(B_INV) + "): ~" + _money(B_VAL) + "\n"
           "• A 10-year delay costs ~" + _money(GAP_VAL) + "\n\n"
           "Start early — time matters more than amount.\n\n"
           "Returns are not guaranteed and vary with the market. Educational only, "
           "not investment advice.\n\n"
           "#compounding #sip #investing #personalfinance #mutualfunds #stockmarket")
    return _render(SEG_STARTEARLY, "startearly_anim", cap, "clock time money finance")


TOPICS = {"compounding": build, "startearly": build_startearly}

if __name__ == "__main__":
    import sys
    TOPICS.get(sys.argv[1] if len(sys.argv) > 1 else "compounding", build)()
