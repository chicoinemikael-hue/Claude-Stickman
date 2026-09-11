#!/usr/bin/env python3
"""
Render a storyboard YAML file into a finished MP4.

Usage:
    python render.py storyboards/fall_of_rome_demo.yaml
    python render.py storyboards/fall_of_rome_demo.yaml --preview
    python render.py storyboards/fall_of_rome_demo.yaml --frame 12.5
    python render.py storyboards/fall_of_rome_demo.yaml --scene 3

See README.md for setup and FORMAT.md for the storyboard file format.
"""

import argparse
import os
import sys

from engine.storyboard import load_storyboard, StoryboardError
from engine.scene import SceneRenderer
from engine.renderer import render_video, new_surface
from engine.audio import mux_audio


def _build_renderers(board):
    return [SceneRenderer(scene, board["characters"]) for scene in board["scenes"]]


def _frame_for_global_time(board, renderers, global_t):
    acc = 0.0
    scenes = board["scenes"]
    for i, scene in enumerate(scenes):
        is_last = i == len(scenes) - 1
        if global_t < acc + scene["duration"] or is_last:
            local_t = min(max(global_t - acc, 0.0), scene["duration"])
            return renderers[i], local_t
        acc += scene["duration"]
    return renderers[-1], scenes[-1]["duration"]


def main():
    parser = argparse.ArgumentParser(
        description="Render a stickman storyboard YAML file into a finished MP4."
    )
    parser.add_argument("storyboard", help="Path to a storyboard .yaml file")
    parser.add_argument("--preview", action="store_true",
                         help="Fast low-resolution render (540x960, 15fps) to check timing quickly")
    parser.add_argument("--frame", type=float, default=None, metavar="SECONDS",
                         help="Save a single PNG at this timestamp instead of rendering a video")
    parser.add_argument("--scene", type=int, default=None, metavar="N",
                         help="Render only scene N (1-based), useful while working on one scene")
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    args = parser.parse_args()

    try:
        board = load_storyboard(args.storyboard)
    except StoryboardError as e:
        print(f"\nStoryboard problem: {e}\n", file=sys.stderr)
        sys.exit(1)

    renderers = _build_renderers(board)
    width, height = board["resolution"]
    fps = board["fps"]
    if args.preview:
        width, height = 540, 960
        fps = 15

    base_name = os.path.splitext(os.path.basename(args.storyboard))[0]

    try:
        if args.frame is not None:
            renderer, local_t = _frame_for_global_time(board, renderers, args.frame)
            surface, ctx = new_surface(width, height)
            renderer.draw_frame(ctx, local_t, width, height)
            out_path = args.output or f"output/{base_name}_frame_{args.frame:g}s.png"
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            surface.write_to_png(out_path)
            print(f"Saved a still frame at t={args.frame}s to {out_path}")
            return

        if args.scene is not None:
            idx = args.scene - 1
            if idx < 0 or idx >= len(board["scenes"]):
                print(
                    f"\nStoryboard problem: --scene {args.scene} doesn't exist. "
                    f"This storyboard has {len(board['scenes'])} scene(s).\n",
                    file=sys.stderr,
                )
                sys.exit(1)
            scene_indices = [idx]
        else:
            scene_indices = list(range(len(board["scenes"])))

        suffix = ""
        if args.scene is not None:
            suffix += f"_scene{args.scene}"
        if args.preview:
            suffix += "_preview"
        out_path = args.output or f"output/{base_name}{suffix}.mp4"
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        def draw_frame(ctx, global_t, w, h):
            acc = 0.0
            for pos, idx in enumerate(scene_indices):
                d = board["scenes"][idx]["duration"]
                is_last = pos == len(scene_indices) - 1
                if global_t < acc + d or is_last:
                    local_t = min(max(global_t - acc, 0.0), d)
                    renderers[idx].draw_frame(ctx, local_t, w, h)
                    return
                acc += d

        duration = sum(board["scenes"][i]["duration"] for i in scene_indices)

        audio = board["audio"]
        wants_audio = args.scene is None and (audio.get("voiceover") or audio.get("music"))
        video_path = out_path + ".silent.mp4" if wants_audio else out_path

        print(f"Rendering {duration:.1f}s ({len(scene_indices)} scene(s)) at {width}x{height}, {fps}fps...")
        render_video(draw_frame, duration, video_path, fps=fps, width=width, height=height)

        if wants_audio:
            print("Mixing audio...")
            mux_audio(
                video_path, out_path,
                voiceover_path=audio.get("voiceover"),
                music_path=audio.get("music"),
                music_volume=float(audio.get("music_volume", 0.55)),
                duck_volume=float(audio.get("duck_volume", 0.16)),
            )
            os.remove(video_path)

        print(f"Done! Saved to {out_path}")

    except StoryboardError as e:
        print(f"\nStoryboard problem: {e}\n", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nRender problem: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
