"""Narrated SIP + power-of-compounding explainer video.

A natural TTS voice (macOS `say`) reads a factual script; each slide is shown
for exactly as long as its narration segment, so voice and visuals stay in sync.
Original audio (your own device voice) — no third-party music/voice licensing.

Output: output/video/sip_explainer.mp4  (+ caption.txt)
Requires: ffmpeg, macOS `say`.
"""
from __future__ import annotations

import os
import subprocess
import wave

import numpy as np

import config
import render

SR = 44100
GAP = 0.5           # pause between segments (seconds)
VOICE_PREFS = ["Samantha", "Aman", "Ava", "Daniel", "Karen"]

OUT_DIR = "output/video"


def _pick_voice() -> str:
    out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    names = [ln.split("  ")[0].strip() for ln in out.splitlines()]
    for v in VOICE_PREFS:
        if any(n == v or n.startswith(v + " ") for n in names):
            return v
    return "Alex"


def _tts(text: str, path_wav: str, voice: str) -> float:
    """Speak text -> wav (mono 44.1k s16); return duration in seconds."""
    aiff = path_wav + ".aiff"
    subprocess.run(["say", "-v", voice, "-o", aiff, text], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", aiff, "-ar", str(SR), "-ac", "1",
                    "-sample_fmt", "s16", path_wav], check=True, capture_output=True)
    os.remove(aiff)
    with wave.open(path_wav) as w:
        return w.getnframes() / w.getframerate()


def _read_wav(path: str) -> np.ndarray:
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def _write_wav(path: str, samples: np.ndarray) -> None:
    with wave.open(path, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(samples.astype(np.int16).tobytes())


# (slide builder, narration) — factual, illustrative, no fund recommendation.
def _segments():
    return [
        (render.title_slide("SIP & Compounding",
                            ["The power of", "compounding"],
                            "why small, steady investing wins"),
         "Let's talk about S I P and the power of compounding — "
         "one of the simplest, most powerful ideas in investing."),
        (render.text_slide("WHAT IS A SIP", "Invest a fixed sum, monthly",
                           "A Systematic Investment Plan puts a set amount, say five "
                           "thousand rupees, into a mutual fund automatically, every month."),
         "A S I P, or Systematic Investment Plan, simply means investing a fixed "
         "amount every month, say five thousand rupees, into a mutual fund, automatically."),
        (render.text_slide("COMPOUNDING", "Returns earn returns",
                           "Your gains start generating their own gains. This snowball "
                           "grows faster the longer you stay invested."),
         "Here's the magic. Your returns start earning their own returns. "
         "That snowball effect is called compounding, and it grows faster the "
         "longer you stay invested."),
        (render.bullets_slide("Rs 5,000 / month at ~12% a year*", [
            "10 years: you invest Rs 6 lakh, it can grow to about Rs 11.6 lakh",
            "20 years: you invest Rs 12 lakh, it can grow to about Rs 50 lakh",
         ], tags=["*assumed return — illustrative only, not guaranteed", ""]),
         "Suppose you invest five thousand rupees a month, and earn about twelve "
         "percent a year. In ten years you'd put in six lakh rupees, but it could "
         "grow to around eleven point six lakh. Stay for twenty years, and that "
         "same habit could become roughly fifty lakh."),
        (render.text_slide("THE TAKEAWAY", "Start early. Stay consistent.",
                           "Time does the heavy lifting — the earlier you begin, the "
                           "more compounding works for you."),
         "So the lesson is simple. Start early, stay consistent, and let time do "
         "the heavy lifting."),
        (render.outro_slide(),
         "Remember, returns are not guaranteed and vary with the market. "
         "This is education, not investment advice."),
    ]


def build() -> str:
    render._BG_QUERY = "money growth savings financial planning"
    render._BG_MEMO.clear()
    os.makedirs(OUT_DIR, exist_ok=True)
    voice = _pick_voice()
    print("voice:", voice)

    segs = _segments()
    durations, img_paths, audio_parts = [], [], []
    silence = np.zeros(int(SR * GAP), dtype=np.int16)

    for i, (img, narration) in enumerate(segs, 1):
        sp = os.path.join(OUT_DIR, f"seg_{i}.png")
        img.save(sp, "PNG")
        img_paths.append(sp)
        wp = os.path.join(OUT_DIR, f"seg_{i}.wav")
        dur = _tts(narration, wp, voice)
        durations.append(dur + GAP)
        audio_parts.append(np.concatenate([_read_wav(wp), silence]))

    voice_wav = os.path.join(OUT_DIR, "voice.wav")
    _write_wav(voice_wav, np.concatenate(audio_parts))

    # concat list with per-slide durations matching each narration segment
    listfile = os.path.join(OUT_DIR, "list.txt")
    with open(listfile, "w") as f:
        for p, d in zip(img_paths, durations):
            f.write(f"file '{os.path.abspath(p)}'\nduration {d:.3f}\n")
        f.write(f"file '{os.path.abspath(img_paths[-1])}'\n")

    out = os.path.join(OUT_DIR, "sip_explainer.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
        "-i", voice_wav,
        "-vf", "scale=1080:1350,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        out,
    ], check=True, capture_output=True)

    caption = (
        "SIP & the power of compounding, explained in a minute.\n\n"
        "A SIP means investing a fixed amount every month, automatically. "
        "Compounding means your returns start earning returns — so the longer "
        "you stay invested, the faster it grows.\n\n"
        "Example (₹5,000/month at an assumed ~12% p.a., illustrative only):\n"
        "• 10 yrs: ₹6L invested → ~₹11.6L\n"
        "• 20 yrs: ₹12L invested → ~₹50L\n\n"
        "Start early, stay consistent, let time work.\n\n"
        "Returns are not guaranteed and vary with the market. Educational only, "
        "not investment advice.\n\n"
        "#sip #compounding #mutualfunds #investing #personalfinance #stockmarket"
    )
    open(os.path.join(OUT_DIR, "explainer_caption.txt"), "w").write(caption)
    print("wrote", out, "| total ~%.1fs" % sum(durations))
    return out


if __name__ == "__main__":
    build()
