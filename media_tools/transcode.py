from __future__ import annotations
import argparse, shutil, subprocess


def run(args=None):
    p = argparse.ArgumentParser(description="Transcode media through ffmpeg.")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--video-codec")
    p.add_argument("--audio-codec")
    a = p.parse_args(args or [])
    exe = shutil.which("ffmpeg")
    if not exe:
        print("ffmpeg not found.")
        return 3
    cmd = [exe, "-hide_banner", "-y", "-i", a.input]
    if a.video_codec:
        cmd += ["-c:v", a.video_codec]
    if a.audio_codec:
        cmd += ["-c:a", a.audio_codec]
    cmd += [a.output]
    print(" ".join(cmd))
    r = subprocess.run(cmd, check=False)
    return r.returncode
