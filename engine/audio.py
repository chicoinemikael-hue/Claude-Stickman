"""
Mixes an optional voiceover and background music into the rendered
(silent) video, with the music turned down under the voiceover so it
doesn't compete with narration.

This is a post-processing step: renderer.render_video() makes the
silent MP4 first, then mux_audio() adds sound on top of it via
ffmpeg's audio filters. Nothing here touches video frames.
"""

import json
import shutil
import subprocess


def _probe_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Couldn't read audio/video info from {path}:\n{result.stderr[-1000:]}")
    return float(json.loads(result.stdout)["format"]["duration"])


def mux_audio(video_path: str, out_path: str, voiceover_path: str = None,
              music_path: str = None, music_volume: float = 0.55,
              duck_volume: float = 0.16):
    """Combine `video_path` (silent) with an optional voiceover and/or
    looping background music, written to `out_path`.

    - If neither audio file is given, the video is copied as-is.
    - If only music is given, it loops for the video's full length at
      `music_volume`.
    - If only a voiceover is given, it's laid over the video (padded
      with silence if shorter).
    - If both are given, the music plays at the quieter `duck_volume`
      so the voiceover stays clear.
    """
    if not voiceover_path and not music_path:
        shutil.copy(video_path, out_path)
        return

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg was not found on your system. Install it and make sure "
            "it's on your PATH -- see README.md for install instructions."
        )

    duration = _probe_duration(video_path)

    cmd = ["ffmpeg", "-y", "-i", video_path]
    next_idx = 1
    voice_idx = music_idx = None
    if voiceover_path:
        cmd += ["-i", voiceover_path]
        voice_idx = next_idx
        next_idx += 1
    if music_path:
        cmd += ["-stream_loop", "-1", "-i", music_path]
        music_idx = next_idx
        next_idx += 1

    filters = []
    mix_labels = []
    if voice_idx is not None:
        filters.append(f"[{voice_idx}:a]apad,atrim=0:{duration},volume=1.0[voice]")
        mix_labels.append("[voice]")
    if music_idx is not None:
        vol = duck_volume if voice_idx is not None else music_volume
        filters.append(f"[{music_idx}:a]atrim=0:{duration},volume={vol}[music]")
        mix_labels.append("[music]")

    if len(mix_labels) == 2:
        filters.append(
            f"{mix_labels[0]}{mix_labels[1]}amix=inputs=2:duration=first:"
            f"dropout_transition=0:normalize=0[aout]"
        )
    else:
        filters.append(f"{mix_labels[0]}anull[aout]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration),
        out_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed while mixing audio:\n{result.stderr[-2000:]}")
