"""
Turns drawing calls into pixels: single still frames (used by --frame
and our own visual checks) and full PNG-sequence -> ffmpeg video
renders (used by the final CLI once the timeline/storyboard system
exists, and by our own dev tests in the meantime).
"""

import os
import shutil
import subprocess
import tempfile

import cairo

from engine.rig import draw_stickman

FRAME_WIDTH = 1080
FRAME_HEIGHT = 1920
FPS = 30

SKY_COLOR = (0.65, 0.80, 0.92)


def new_surface(width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)
    return surface, ctx


def render_still(characters, out_path: str,
                  width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT,
                  bg_color=SKY_COLOR):
    """Render a single frame containing `characters` (a list of
    Character, already posed/expressioned) to a PNG file."""
    surface, ctx = new_surface(width, height)

    ctx.set_source_rgb(*bg_color)
    ctx.paint()

    for character in characters:
        character.resolve(width, height)
        draw_stickman(ctx, character, character.pose)

    surface.write_to_png(out_path)


def render_video(draw_frame_fn, duration: float, out_path: str,
                  fps: int = FPS, width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT,
                  crf: int = 18):
    """Render a video by calling draw_frame_fn(ctx, t, width, height)
    once per frame (t in seconds, 0 <= t < duration), then encoding
    the PNG sequence to an H.264 MP4 with ffmpeg.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg was not found on your system. Install it and make sure "
            "it's on your PATH -- see README.md for install instructions."
        )

    num_frames = max(1, round(duration * fps))
    tmp_dir = tempfile.mkdtemp(prefix="stickman_frames_")
    try:
        for i in range(num_frames):
            t = i / fps
            surface, ctx = new_surface(width, height)
            draw_frame_fn(ctx, t, width, height)
            surface.write_to_png(os.path.join(tmp_dir, f"frame_{i:06d}.png"))

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", os.path.join(tmp_dir, "frame_%06d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", str(crf),
            "-movflags", "+faststart",
            out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-2000:]}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
