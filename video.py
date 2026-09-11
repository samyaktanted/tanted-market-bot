"""Turn a set of slide PNGs into an MP4 (H.264 + AAC) for Instagram video/Reels.

Audio: by default a short ORIGINAL ambient bed is synthesized with numpy (no
copyright risk). To use your own royalty-free track instead, pass audio_path
to a local .mp3/.wav (e.g. assets/audio/bed.mp3).

Requires ffmpeg on PATH (CI: `apt-get install -y ffmpeg`).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100


def synth_audio(out_path: str, seconds: float) -> str:
    """Write a gentle original ambient pad (A-minor triad) as a 16-bit WAV."""
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    freqs = [220.0, 277.18, 329.63]  # A3, C#4, E4
    sig = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    sig *= 0.3 * (1 + 0.2 * np.sin(2 * np.pi * 0.15 * t))  # slow tremolo
    fade = int(SR * 1.0)
    if len(sig) > 2 * fade:
        sig[:fade] *= np.linspace(0, 1, fade)
        sig[-fade:] *= np.linspace(1, 0, fade)
    pcm = (np.clip(sig, -1, 1) * 0.25 * 32767).astype(np.int16)
    with wave.open(out_path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path


def make_video(image_paths, out_path: str, sec_per: float = 3.0,
               audio_path: str | None = None) -> str:
    if not image_paths:
        raise ValueError("no images to render")
    total = sec_per * len(image_paths)

    tmp = tempfile.mkdtemp()
    # concat demuxer list (last image repeated so its duration applies)
    listfile = os.path.join(tmp, "list.txt")
    with open(listfile, "w") as f:
        for p in image_paths:
            f.write(f"file '{os.path.abspath(p)}'\nduration {sec_per}\n")
        f.write(f"file '{os.path.abspath(image_paths[-1])}'\n")

    made_audio = None
    if audio_path is None:
        made_audio = os.path.join(tmp, "bed.wav")
        synth_audio(made_audio, total)
        audio_path = made_audio

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", listfile,
        "-i", audio_path,
        "-vf", "scale=1080:1350:force_original_aspect_ratio=decrease,"
               "pad=1080:1350:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart",
        out_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


if __name__ == "__main__":
    import sys
    imgs = sys.argv[1:] or []
    make_video(imgs, "output/sample_video.mp4")
    print("wrote output/sample_video.mp4")
