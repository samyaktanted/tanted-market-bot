"""SIF explainer = SadTalker talking-head INTRO + Pexels slideshow w/ voiceover.

- Segment 1 narration is spoken by a talking-head avatar (SadTalker, local),
  framed into a branded 1080x1350 canvas.
- Segments 2..N are the usual slides, each shown for its narration length.
- Everything is concatenated into one MP4 for an Instagram Reel.

Factual, advice-free (SEBI SIF). Original TTS audio. Requires ffmpeg + the
SadTalker install at ~/sadtalker (its own venv + checkpoints).
"""
from __future__ import annotations

import glob
import os
import subprocess
import wave

import numpy as np

import config
import render

SR = 44100
GAP = 0.5
OUT = "output/video"
SAD = os.path.expanduser("~/sadtalker")
SAD_PY = os.path.join(SAD, ".venv/bin/python")
AVATAR = os.path.join(SAD, "examples/source_image/art_10.png")
VOICE_PREFS = ["Aman", "Rishi", "Veena", "Samantha"]  # prefer Indian English


def _voice() -> str:
    out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    names = [ln.split("  ")[0].strip() for ln in out.splitlines()]
    for v in VOICE_PREFS:
        if any(n == v or n.startswith(v + " ") for n in names):
            return v
    return "Alex"


def _tts(text: str, wav: str, voice: str) -> float:
    aiff = wav + ".aiff"
    subprocess.run(["say", "-v", voice, "-o", aiff, text], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", aiff, "-ar", str(SR), "-ac", "1",
                    "-sample_fmt", "s16", wav], check=True, capture_output=True)
    os.remove(aiff)
    with wave.open(wav) as w:
        return w.getnframes() / w.getframerate()


def _read(w):
    with wave.open(w) as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16)


def _write(path, samples):
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(samples.astype(np.int16).tobytes())


def _burn_caption(img, text: str, fs: int = 32) -> None:
    """Burn the spoken transcript as a translucent caption bar near the bottom."""
    from PIL import ImageDraw
    W, H, M = render.W, render.H, render.MARGIN
    d = ImageDraw.Draw(img, "RGBA")
    lines = render._wrap(d, text, render.font(fs), W - 2 * M - 40)
    lh = fs + 12
    box_h = len(lines) * lh + 36
    y0 = H - 120 - box_h
    d.rectangle([40, y0, W - 40, y0 + box_h], fill=(0, 0, 0, 150))
    y = y0 + 18
    for ln in lines:
        d.text((60, y), ln, font=render.font(fs), fill=(255, 255, 255))
        y += lh


def _intro_bg(path: str, caption: str):
    img, draw = render._new_canvas()
    draw.text((render.MARGIN, 130), "SEBI'S NEWEST FUND",
              font=render.font(40, True), fill=config.COLOR_ACCENT)
    draw.text((render.MARGIN, 210), "What is a SIF?",
              font=render.font(76, True), fill=config.COLOR_TEXT)
    _burn_caption(img, caption)
    img.save(path, "PNG")


def _segments():
    return [
        dict(kind="slide",
             slide=render.title_slide("SEBI'S NEWEST FUND", ["What is", "a SIF?"],
                 "Specialised Investment Fund, explained"),
             narration="Let's break down S I F, the Specialised Investment Fund, "
                       "S E B I's newest way to invest."),
        dict(kind="slide",
             slide=render.text_slide("WHAT IS IT", "A new SEBI category",
                 "A Specialised Investment Fund, or SIF, is a brand-new category "
                 "from SEBI that sits between mutual funds and portfolio "
                 "management services."),
             narration="A Specialised Investment Fund, or SIF, is a brand new "
                       "category from SEBI. It sits between mutual funds and "
                       "portfolio management services."),
        dict(kind="slide",
             slide=render.text_slide("WHO IT'S FOR", "Higher ticket size",
                 "It's built for experienced investors — the minimum investment "
                 "is around ten lakh rupees across the fund house."),
             narration="It's built for experienced investors. The minimum "
                       "investment is around ten lakh rupees across the fund house."),
        dict(kind="slide",
             slide=render.text_slide("WHAT'S DIFFERENT", "Advanced strategies",
                 "Unlike regular mutual funds, SIFs can use advanced strategies "
                 "like long-short equity — aiming for higher, but riskier, returns."),
             narration="Unlike regular mutual funds, SIFs can use more advanced "
                       "strategies, like long short equity, aiming for higher, but "
                       "riskier, returns."),
        dict(kind="slide",
             slide=render.text_slide("WHY IT EXISTS", "Regulated & flexible",
                 "SEBI created it to offer sophisticated strategies in a regulated "
                 "way, and to curb unregistered PMS-like schemes."),
             narration="SEBI created it to offer sophisticated strategies in a "
                       "regulated way, and to curb unregistered schemes."),
        dict(kind="slide", slide=render.outro_slide(),
             narration="In short, SIF is a regulated middle path for informed "
                       "investors, with a higher ticket size. This is education, "
                       "not investment advice. Always read the scheme documents."),
    ]


def _fmt_ts(t: float) -> str:
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _wrap_cap(text: str, width: int = 38) -> str:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def _probe_dur(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "default=nw=1:nk=1", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def _write_srt(segs, intro_dur: float, path: str) -> None:
    windows = [(segs[0]["narration"], intro_dur)]
    for s in segs[1:]:
        windows.append((s["narration"], s["dur"] + GAP))
    out, t, idx = [], 0.0, 1
    for text, dur in windows:
        out += [str(idx), f"{_fmt_ts(t)} --> {_fmt_ts(t + dur)}",
                _wrap_cap(text), ""]
        t += dur; idx += 1
    open(path, "w").write("\n".join(out))


def _run_sadtalker(audio_wav: str) -> str:
    resdir = os.path.abspath(os.path.join(OUT, "sad_results"))
    os.makedirs(resdir, exist_ok=True)
    existing = sorted(glob.glob(os.path.join(resdir, "*.mp4")), key=os.path.getmtime)
    if os.getenv("REUSE_TALK") and existing:
        print("reusing existing talking-head:", existing[-1])
        return existing[-1]
    subprocess.run([SAD_PY, "inference.py",
                    "--driven_audio", os.path.abspath(audio_wav),
                    "--source_image", AVATAR,
                    "--result_dir", resdir,
                    "--preprocess", "crop", "--size", "256", "--still", "--cpu"],
                   cwd=SAD, check=True)
    mp4s = sorted(glob.glob(os.path.join(resdir, "*.mp4")), key=os.path.getmtime)
    if not mp4s:
        raise RuntimeError("SadTalker produced no mp4")
    return mp4s[-1]


def build() -> str:
    render._BG_QUERY = "stock market investment finance india"
    render._BG_MEMO.clear()
    os.makedirs(OUT, exist_ok=True)
    voice = _voice()
    print("voice:", voice)
    segs = _segments()

    # Slideshow + voiceover only (no talking head, no burned captions).
    silence = np.zeros(int(SR * GAP), dtype=np.int16)
    parts, listlines, imgs = [], [], []
    for i, s in enumerate(segs, 1):
        wav = os.path.join(OUT, f"a_seg_{i}.wav")
        dur = _tts(s["narration"], wav, voice)
        p = os.path.join(OUT, f"a_slide_{i}.png"); s["slide"].save(p, "PNG")
        imgs.append(p)
        listlines.append(f"file '{os.path.abspath(p)}'\nduration {dur + GAP:.3f}")
        parts.append(np.concatenate([_read(wav), silence]))
    voice_wav = os.path.join(OUT, "sif_voice.wav"); _write(voice_wav, np.concatenate(parts))
    listfile = os.path.join(OUT, "sif_list.txt")
    with open(listfile, "w") as f:
        f.write("\n".join(listlines) + f"\nfile '{os.path.abspath(imgs[-1])}'\n")
    out = os.path.join(OUT, "sif_explainer.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
        "-i", voice_wav, "-vf", "scale=1080:1350,fps=30,format=yuv420p",
        "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-shortest",
        "-movflags", "+faststart", out], check=True, capture_output=True)

    caption = (
        "What is a SIF? SEBI's newest investment category, explained.\n\n"
        "A Specialised Investment Fund (SIF) sits between mutual funds and PMS. "
        "Built for experienced investors (minimum ~Rs 10 lakh), it can use more "
        "advanced strategies like long-short equity — higher potential returns, "
        "higher risk. SEBI introduced it to offer sophisticated, regulated "
        "options and curb unregistered schemes.\n\n"
        "Educational only, not investment advice. Always read the scheme "
        "documents and check eligibility.\n\n"
        "#SIF #SEBI #mutualfunds #investing #personalfinance #stockmarket #india"
    )
    open(os.path.join(OUT, "sif_caption.txt"), "w").write(caption)
    print("DONE:", out)
    return out


if __name__ == "__main__":
    build()
