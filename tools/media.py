"""Audio & video — everything runs through FFmpeg (needs ffmpeg)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from core.tool import F, ToolError, tool

from ._util import human_size, need_file, out_path, report_table, run_command, which

MEDIA_FILTER = "Media (*.mp4 *.mkv *.mov *.avi *.webm *.mp3 *.wav *.flac *.m4a *.ogg *.gif)"
VIDEO_FILTER = "Video (*.mp4 *.mkv *.mov *.avi *.webm *.gif)"
AUDIO_FILTER = "Audio (*.mp3 *.wav *.flac *.m4a *.ogg *.aac *.opus)"


def _ffmpeg() -> str:
    exe = which("ffmpeg") or which("ffmpeg.exe")
    if not exe:
        raise ToolError("FFmpeg is not on PATH — install it from gyan.dev, then reopen")
    return exe


def _ffprobe() -> str:
    exe = which("ffprobe") or which("ffprobe.exe")
    if not exe:
        raise ToolError("ffprobe is not on PATH — it ships with FFmpeg")
    return exe


def _duration(path: Path) -> float:
    code, out, _ = run_command([_ffprobe(), "-v", "quiet", "-print_format", "json",
                                "-show_format", str(path)], timeout=60)
    if code != 0:
        return 0.0
    try:
        return float(json.loads(out)["format"].get("duration", 0))
    except (ValueError, KeyError, TypeError):
        return 0.0


def _run(args: list[str], ctx, target: Path, timeout: int = 1800) -> None:
    code, _, err = run_command([_ffmpeg(), "-hide_banner", "-y", *args], ctx=ctx, timeout=timeout)
    if code != 0 or not target.exists():
        raise ToolError(f"FFmpeg failed: {err.strip().splitlines()[-1] if err.strip() else code}")
    ctx.output(str(target))


@tool(id="media-info", name="Media Info", category="Media",
      summary="Duration, resolution, codecs, frame rate, bitrate and audio tracks.",
      keywords="media info video audio codec resolution bitrate duration",
      needs=("ffprobe",),
      fields=[F.file("file", "Media file", filters=MEDIA_FILTER)])
def media_info(v, ctx):
    path = need_file(v["file"], "Media file")
    code, out, err = run_command([_ffprobe(), "-v", "quiet", "-print_format", "json",
                                  "-show_format", "-show_streams", str(path)], timeout=120)
    if code != 0:
        raise ToolError(f"ffprobe failed: {err.strip()[:200]}")
    data = json.loads(out or "{}")
    fmt = data.get("format", {})
    rows = []
    for stream in data.get("streams", []):
        rows.append({
            "type": stream.get("codec_type"),
            "codec": stream.get("codec_name"),
            "details": (f"{stream.get('width')}×{stream.get('height')} "
                        f"@ {stream.get('r_frame_rate')}" if stream.get("codec_type") == "video"
                        else f"{stream.get('channels')} ch · {stream.get('sample_rate')} Hz"),
            "bitrate": f"{int(stream.get('bit_rate', 0)) // 1000} kbps" if stream.get("bit_rate") else "",
        })
    ctx.log(report_table(rows, ["type", "codec", "details", "bitrate"]))
    seconds = float(fmt.get("duration", 0) or 0)
    return {
        "file": path.name,
        "size": human_size(path.stat().st_size),
        "duration": f"{int(seconds // 60)}m {seconds % 60:04.1f}s",
        "container": fmt.get("format_long_name"),
        "overall_bitrate": f"{int(fmt.get('bit_rate', 0)) // 1000} kbps",
        "streams": len(rows),
    }


@tool(id="convert-media", name="Convert Media", category="Media",
      summary="Convert video or audio between formats, choosing codec and quality.",
      keywords="convert transcode mp4 mp3 wav mkv webm format",
      needs=("ffmpeg",),
      fields=[F.file("file", "Media file", filters=MEDIA_FILTER),
              F.choice("format", "Convert to", ["mp4", "mkv", "webm", "avi", "mov", "mp3",
                                                "wav", "flac", "m4a", "ogg", "gif"], "mp4"),
              F.choice("quality", "Quality", ["High", "Balanced", "Small file"], "Balanced"),
              F.save("output", "Save as", required=False)])
def convert_media(v, ctx):
    path = need_file(v["file"], "Media file")
    fmt = v["format"]
    target = out_path(v["output"], f"{path.stem}.{fmt}")
    if target.suffix.lower().lstrip(".") != fmt:
        target = target.with_suffix("." + fmt)
    crf = {"High": "20", "Balanced": "23", "Small file": "28"}[v["quality"]]
    if fmt in ("mp3", "wav", "flac", "m4a", "ogg"):
        args = ["-i", str(path), "-vn"]
        if fmt == "mp3":
            args += ["-c:a", "libmp3lame", "-q:a", {"High": "0", "Balanced": "2",
                                                    "Small file": "5"}[v["quality"]]]
        elif fmt == "wav":
            args += ["-c:a", "pcm_s16le"]
        elif fmt == "flac":
            args += ["-c:a", "flac"]
        elif fmt == "ogg":
            args += ["-c:a", "libvorbis", "-q:a", "5"]
        else:
            args += ["-c:a", "aac", "-b:a", "192k"]
        args.append(str(target))
    else:
        args = ["-i", str(path), "-c:v", "libx264" if fmt in ("mp4", "mkv", "mov", "avi") else "libvpx-vp9",
                "-crf", crf, "-c:a", "aac", str(target)]
    _run(args, ctx, target)
    return (f"{path.name} → {target.name}  ·  {human_size(path.stat().st_size)} → "
            f"{human_size(target.stat().st_size)}")


@tool(id="extract-audio", name="Extract Audio", category="Media",
      summary="Pull the sound track out of a video as MP3, WAV, M4A or FLAC.",
      keywords="extract audio sound mp3 from video rip",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.choice("format", "Audio format", ["mp3", "wav", "m4a", "flac", "ogg"], "mp3"),
              F.integer("bitrate", "MP3 bitrate (kbps)", 192, minimum=64, maximum=320),
              F.save("output", "Save as", required=False)])
def extract_audio(v, ctx):
    path = need_file(v["file"], "Video file")
    fmt = v["format"]
    target = out_path(v["output"], f"{path.stem}.{fmt}").with_suffix("." + fmt)
    codec = {"mp3": ["-c:a", "libmp3lame", "-b:a", f"{v['bitrate']}k"],
             "wav": ["-c:a", "pcm_s16le"], "m4a": ["-c:a", "aac", "-b:a", "192k"],
             "flac": ["-c:a", "flac"], "ogg": ["-c:a", "libvorbis", "-q:a", "5"]}[fmt]
    _run(["-i", str(path), "-vn", *codec, str(target)], ctx, target)
    return f"Audio extracted → {target.name} ({human_size(target.stat().st_size)})"


@tool(id="compress-video", name="Compress Video", category="Media",
      summary="Make a video smaller by raising CRF or capping the resolution.",
      keywords="compress video smaller shrink crf bitrate",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.integer("crf", "Quality (18 best – 32 smallest)", 26, minimum=16, maximum=34),
              F.integer("max_width", "Limit width to (0 = keep)", 1280, minimum=0, maximum=7680),
              F.choice("preset", "Speed", ["fast", "medium", "slow"], "medium"),
              F.save("output", "Save as", required=False)])
def compress_video(v, ctx):
    path = need_file(v["file"], "Video file")
    target = out_path(v["output"], f"{path.stem}-small.mp4").with_suffix(".mp4")
    filters = []
    if v["max_width"]:
        filters.append(f"scale='min({v['max_width']},iw)':-2")
    args = ["-i", str(path), "-c:v", "libx264", "-crf", str(v["crf"]),
            "-preset", v["preset"], "-c:a", "aac", "-b:a", "128k"]
    if filters:
        args += ["-vf", ",".join(filters)]
    args.append(str(target))
    _run(args, ctx, target)
    before, after = path.stat().st_size, target.stat().st_size
    return (f"{human_size(before)} → {human_size(after)}  "
            f"({(1 - after / before) * 100:.0f}% smaller)  {target.name}")


@tool(id="trim-media", name="Trim Media", category="Media",
      summary="Cut a section out of a video or audio file by start time and duration.",
      keywords="trim cut clip crop section start end",
      needs=("ffmpeg",),
      fields=[F.file("file", "Media file", filters=MEDIA_FILTER),
              F.text("start", "Start at", "00:00:00", help="HH:MM:SS or seconds"),
              F.text("end", "End at", help="Leave blank to use the duration"),
              F.number("duration", "…or duration (seconds)", 0.0, minimum=0.0),
              F.flag("reencode", "Re-encode for frame-accurate cuts", False),
              F.save("output", "Save as", required=False)])
def trim_media(v, ctx):
    path = need_file(v["file"], "Media file")
    target = out_path(v["output"], f"{path.stem}-trimmed{path.suffix or '.mp4'}")
    args = ["-i", str(path), "-ss", v["start"].strip() or "0"]
    if v["end"].strip():
        args += ["-to", v["end"].strip()]
    elif v["duration"]:
        args += ["-t", str(v["duration"])]
    if v["reencode"]:
        args += ["-c:v", "libx264", "-crf", "20", "-c:a", "aac"]
    else:
        args += ["-c", "copy"]
    args.append(str(target))
    _run(args, ctx, target)
    return f"Trimmed to {target.name} ({human_size(target.stat().st_size)})"


@tool(id="resize-video", name="Resize Video", category="Media",
      summary="Scale a video to a new resolution, keeping the aspect ratio.",
      keywords="resize scale resolution 1080p 720p video",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.integer("width", "Width (px)", 1280, minimum=16, maximum=7680),
              F.integer("height", "Height (px)", 0, minimum=0, maximum=4320,
                        help="0 = work it out from the width"),
              F.save("output", "Save as", required=False)])
def resize_video(v, ctx):
    path = need_file(v["file"], "Video file")
    target = out_path(v["output"], f"{path.stem}-{v['width']}p.mp4").with_suffix(".mp4")
    height = v["height"] or -2
    _run(["-i", str(path), "-vf", f"scale={v['width']}:{height}",
          "-c:v", "libx264", "-crf", "22", "-c:a", "copy", str(target)], ctx, target)
    return f"Resized to {v['width']}px wide → {target.name}"


@tool(id="video-to-gif", name="Video to GIF", category="Media",
      summary="Make an animated GIF from a section of a video, with size and frame rate control.",
      keywords="gif animation video convert loop",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.text("start", "Start at", "00:00:00"),
              F.number("duration", "Length (seconds)", 5.0, minimum=0.5, maximum=120.0),
              F.integer("width", "Width (px)", 480, minimum=64, maximum=1920),
              F.integer("fps", "Frames per second", 12, minimum=4, maximum=30),
              F.save("output", "Save as", required=False, filters="GIF (*.gif)")])
def video_to_gif(v, ctx):
    path = need_file(v["file"], "Video file")
    target = out_path(v["output"], f"{path.stem}.gif").with_suffix(".gif")
    filters = (f"fps={v['fps']},scale={v['width']}:-1:flags=lanczos,"
               "split[a][b];[a]palettegen[p];[b][p]paletteuse")
    _run(["-ss", v["start"].strip() or "0", "-t", str(v["duration"]), "-i", str(path),
          "-vf", filters, "-loop", "0", str(target)], ctx, target)
    return f"GIF made: {target.name} ({human_size(target.stat().st_size)})"


@tool(id="extract-frames", name="Extract Video Frames", category="Media",
      summary="Save still frames from a video at a fixed interval — for thumbnails or review.",
      keywords="frames stills screenshot video extract images",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.number("every_seconds", "One frame every (seconds)", 5.0, minimum=0.1, maximum=600.0),
              F.folder("output", "Save into", required=False)])
def extract_frames(v, ctx):
    path = need_file(v["file"], "Video file")
    out_dir = Path(v["output"]) if v["output"].strip() else path.parent / f"{path.stem}-frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(out_dir / "frame-%04d.jpg")
    _run(["-i", str(path), "-vf", f"fps=1/{v['every_seconds']}", "-q:v", "3", pattern],
         ctx, out_dir, timeout=1800)
    made = sorted(out_dir.glob("frame-*.jpg"))
    for item in made:
        ctx.output(str(item))
    return f"{len(made)} frame(s) every {v['every_seconds']}s in {out_dir}"


@tool(id="frames-to-video", name="Images to Video", category="Media",
      summary="Turn a numbered image sequence into a video at a chosen frame rate.",
      keywords="images video timelapse slideshow sequence",
      needs=("ffmpeg",),
      fields=[F.folder("folder", "Folder of images"),
              F.integer("fps", "Frames per second", 24, minimum=1, maximum=60),
              F.save("output", "Save as", required=True, filters="Video (*.mp4)")])
def frames_to_video(v, ctx):
    from ._util import need_dir
    root = need_dir(v["folder"])
    images = sorted(p for p in root.iterdir()
                    if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp"))
    if not images:
        raise ToolError("No images found in that folder")
    target = out_path(v["output"], "video.mp4").with_suffix(".mp4")
    pattern = str(root / ("%04d" + images[0].suffix.lower()))
    import shutil
    staging = root / ".all4one-frames"
    staging.mkdir(exist_ok=True)
    for index, image in enumerate(images, start=1):
        shutil.copy2(image, staging / f"{index:04d}{images[0].suffix.lower()}")
    _run(["-framerate", str(v["fps"]), "-i", str(staging / ("%04d" + images[0].suffix.lower())),
          "-c:v", "libx264", "-pix_fmt", "yuv420p", str(target)], ctx, target)
    shutil.rmtree(staging, ignore_errors=True)
    return f"{len(images)} image(s) → {target.name} at {v['fps']} fps"


@tool(id="concat-media", name="Join Media Files", category="Media",
      summary="Concatenate several audio or video files that share the same format.",
      keywords="join concat merge combine media files",
      needs=("ffmpeg",),
      fields=[F.files("files", "Files (in order)", filters=MEDIA_FILTER),
              F.save("output", "Save as", required=True)])
def concat_media(v, ctx):
    import tempfile
    files = v["files"] if isinstance(v["files"], list) else [f for f in v["files"].split("|") if f]
    if len(files) < 2:
        raise ToolError("Choose at least two files")
    paths = [need_file(raw) for raw in files]
    target = out_path(v["output"], "joined.mp4")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        for path in paths:
            handle.write(f"file '{path.as_posix()}'\n")
        listing = handle.name
    _run(["-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", str(target)], ctx, target)
    Path(listing).unlink(missing_ok=True)
    return f"Joined {len(paths)} file(s) → {target.name} ({human_size(target.stat().st_size)})"


@tool(id="normalise-audio", name="Normalise Loudness", category="Media",
      summary="Even out volume across a recording to a broadcast loudness target.",
      keywords="normalise loudness volume audio even level",
      needs=("ffmpeg",),
      fields=[F.file("file", "Audio or video", filters=MEDIA_FILTER),
              F.number("target", "Target loudness (LUFS)", -16.0, minimum=-30.0, maximum=-8.0),
              F.save("output", "Save as", required=False)])
def normalise_audio(v, ctx):
    path = need_file(v["file"])
    target = out_path(v["output"], f"{path.stem}-normalised{path.suffix or '.mp3'}")
    _run(["-i", str(path), "-af", f"loudnorm=I={v['target']}:TP=-1.5:LRA=11",
          "-c:v", "copy" if path.suffix.lower() in (".mp4", ".mkv", ".mov") else "none",
          *([] if path.suffix.lower() in (".mp4", ".mkv", ".mov") else ["-c:a", "aac", "-b:a", "192k"]),
          str(target)], ctx, target)
    return f"Normalised to {v['target']} LUFS → {target.name}"


@tool(id="audio-volume", name="Change Volume", category="Media",
      summary="Boost or quieten audio by a number of decibels or a multiplier.",
      keywords="volume boost quieter louder gain audio",
      needs=("ffmpeg",),
      fields=[F.file("file", "Audio or video", filters=MEDIA_FILTER),
              F.choice("mode", "Change by", ["Decibels", "Multiplier"], "Decibels"),
              F.number("amount", "Amount", 6.0, minimum=-60.0, maximum=60.0),
              F.save("output", "Save as", required=False)])
def audio_volume(v, ctx):
    path = need_file(v["file"])
    target = out_path(v["output"], f"{path.stem}-volume{path.suffix or '.mp3'}")
    gain = f"{v['amount']}dB" if v["mode"] == "Decibels" else str(v["amount"])
    _run(["-i", str(path), "-af", f"volume={gain}", str(target)], ctx, target)
    return f"Volume changed by {gain} → {target.name}"


@tool(id="change-speed", name="Change Playback Speed", category="Media",
      summary="Speed up or slow down media while keeping the pitch natural.",
      keywords="speed fast slow motion timelapse playback",
      needs=("ffmpeg",),
      fields=[F.file("file", "Media file", filters=MEDIA_FILTER),
              F.number("speed", "Speed multiplier", 2.0, minimum=0.1, maximum=10.0, step=0.1),
              F.flag("keep_pitch", "Keep the pitch natural", True),
              F.save("output", "Save as", required=False)])
def change_speed(v, ctx):
    path = need_file(v["file"])
    target = out_path(v["output"], f"{path.stem}-{v['speed']}x{path.suffix or '.mp4'}")
    speed = v["speed"]
    audio = f"atempo={speed}" if 0.5 <= speed <= 2.0 else (
        f"atempo=2.0,atempo={speed / 2:.3f}" if speed > 2.0 else f"atempo=0.5,atempo={speed / 0.5:.3f}")
    filters = [f"setpts={1 / speed:.4f}*PTS"]
    args = ["-i", str(path), "-filter:v", filters[0]]
    if v["keep_pitch"]:
        args += ["-filter:a", audio]
    args.append(str(target))
    _run(args, ctx, target)
    return f"Playback speed {speed}× → {target.name}"


@tool(id="mute-video", name="Remove Audio Track", category="Media",
      summary="Strip the sound from a video entirely, leaving a silent file.",
      keywords="mute silent remove audio strip no sound",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.save("output", "Save as", required=False)])
def mute_video(v, ctx):
    path = need_file(v["file"], "Video file")
    target = out_path(v["output"], f"{path.stem}-silent.mp4").with_suffix(".mp4")
    _run(["-i", str(path), "-an", "-c:v", "copy", str(target)], ctx, target)
    return f"Audio removed → {target.name}"


@tool(id="video-rotate", name="Rotate Video", category="Media",
      summary="Rotate a video 90, 180 or 270 degrees — fixes phone footage on its side.",
      keywords="rotate video portrait landscape sideways phone",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.choice("angle", "Rotate", ["90", "180", "270"], "90"),
              F.save("output", "Save as", required=False)])
def video_rotate(v, ctx):
    path = need_file(v["file"], "Video file")
    target = out_path(v["output"], f"{path.stem}-rotated.mp4").with_suffix(".mp4")
    transpose = {"90": "transpose=1", "180": "transpose=1,transpose=1", "270": "transpose=2"}
    _run(["-i", str(path), "-vf", transpose[v["angle"]], "-c:a", "copy", str(target)], ctx, target)
    return f"Rotated {v['angle']}° → {target.name}"


@tool(id="media-metadata", name="Strip Media Metadata", category="Media",
      summary="Remove titles, GPS tags and device names from a video or audio file.",
      keywords="metadata strip privacy gps tags clean video",
      needs=("ffmpeg",),
      fields=[F.file("file", "Media file", filters=MEDIA_FILTER),
              F.save("output", "Save as", required=False)])
def media_metadata(v, ctx):
    path = need_file(v["file"])
    target = out_path(v["output"], f"{path.stem}-clean{path.suffix or '.mp4'}")
    _run(["-i", str(path), "-map_metadata", "-1", "-c", "copy", str(target)], ctx, target)
    return f"Metadata removed → {target.name}"


@tool(id="video-thumbnail", name="Grab a Thumbnail", category="Media",
      summary="Save one frame from a chosen timestamp as a JPEG or PNG thumbnail.",
      keywords="thumbnail poster frame screenshot cover",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.text("at", "At time", "00:00:05", help="HH:MM:SS"),
              F.integer("width", "Width (px)", 1280, minimum=64, maximum=3840),
              F.save("output", "Save as", required=False, filters="Image (*.jpg *.png)")])
def video_thumbnail(v, ctx):
    path = need_file(v["file"], "Video file")
    target = out_path(v["output"], f"{path.stem}-thumb.jpg").with_suffix(".jpg")
    _run(["-ss", v["at"].strip() or "0", "-i", str(path), "-frames:v", "1",
          "-vf", f"scale={v['width']}:-2", str(target)], ctx, target)
    return f"Thumbnail saved → {target.name}"


@tool(id="add-subtitles", name="Add Subtitles", category="Media",
      summary="Burn subtitles into the picture, or mux them as a selectable track.",
      keywords="subtitles srt burn in caption mux track",
      needs=("ffmpeg",),
      fields=[F.file("file", "Video file", filters=VIDEO_FILTER),
              F.file("subtitles", "Subtitle file", filters="Subtitles (*.srt *.ass *.vtt)"),
              F.choice("mode", "How", ["Burn into the video", "Add as a selectable track"],
                       "Burn into the video"),
              F.save("output", "Save as", required=False)])
def add_subtitles(v, ctx):
    path = need_file(v["file"], "Video file")
    subs = need_file(v["subtitles"], "Subtitle file")
    target = out_path(v["output"], f"{path.stem}-subbed.mkv").with_suffix(".mkv")
    if v["mode"].startswith("Burn"):
        escaped = str(subs).replace("\\", "/").replace(":", "\\:")
        _run(["-i", str(path), "-vf", f"subtitles='{escaped}'",
              "-c:v", "libx264", "-crf", "22", "-c:a", "copy", str(target)], ctx, target)
    else:
        _run(["-i", str(path), "-i", str(subs), "-c", "copy",
              "-c:s", "srt", "-metadata:s:s:0", "language=eng", str(target)], ctx, target)
    return f"{v['mode']} → {target.name}"


@tool(id="audio-trim-silence", name="Trim Silence", category="Media",
      summary="Remove leading and trailing silence from a recording automatically.",
      keywords="silence trim quiet remove audio clean",
      needs=("ffmpeg",),
      fields=[F.file("file", "Audio file", filters=AUDIO_FILTER),
              F.number("threshold", "Silence threshold (dB)", -40.0, minimum=-80.0, maximum=-10.0),
              F.save("output", "Save as", required=False)])
def audio_trim_silence(v, ctx):
    path = need_file(v["file"], "Audio file")
    target = out_path(v["output"], f"{path.stem}-trimmed{path.suffix or '.mp3'}")
    _run(["-i", str(path), "-af",
          f"silenceremove=start_periods=1:start_threshold={v['threshold']}dB:"
          f"stop_periods=-1:stop_threshold={v['threshold']}dB", str(target)], ctx, target)
    return f"Silence trimmed → {target.name} ({human_size(target.stat().st_size)})"


@tool(id="media-batch-convert", name="Batch Convert Media", category="Media",
      summary="Convert every video or audio file in a folder to one format.",
      keywords="batch convert folder media bulk transcode",
      needs=("ffmpeg",),
      fields=[F.folder("folder", "Folder"),
              F.choice("format", "Convert to", ["mp4", "mkv", "mp3", "wav", "m4a"], "mp4"),
              F.folder("output", "Save into", required=False),
              F.flag("recursive", "Include subfolders", False)])
def media_batch_convert(v, ctx):
    from ._util import iter_files, need_dir
    root = need_dir(v["folder"])
    out_dir = Path(v["output"]) if v["output"].strip() else root / f"converted-{v['format']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    exts = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".flac", ".m4a", ".ogg")
    files = [p for p in iter_files(root, v["recursive"], "*") if p.suffix.lower() in exts]
    if not files:
        raise ToolError("No media files found in that folder")
    done = 0
    for index, path in enumerate(files, start=1):
        ctx.check_cancel()
        target = out_dir / (path.stem + "." + v["format"])
        args = ["-i", str(path)]
        if v["format"] in ("mp3", "wav", "m4a"):
            args += ["-vn", "-c:a", {"mp3": "libmp3lame", "wav": "pcm_s16le",
                                     "m4a": "aac"}[v["format"]]]
        else:
            args += ["-c:v", "libx264", "-crf", "23", "-c:a", "aac"]
        args.append(str(target))
        try:
            _run(args, ctx, target)
            done += 1
        except ToolError as exc:
            ctx.log(f"! {path.name}: {exc}")
        ctx.progress(index / len(files) * 100, path.name)
    return f"Converted {done} of {len(files)} file(s) to {v['format']} in {out_dir}"
