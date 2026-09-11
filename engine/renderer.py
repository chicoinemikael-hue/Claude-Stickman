"""
Turns drawing calls into pixels. For now this just knows how to render
a single still frame to a PNG (used by --frame and for our own visual
checks while building the engine). Full scene/video rendering is added
once the timeline and storyboard system exist.
"""

import cairo

from engine.rig import draw_stickman

FRAME_WIDTH = 1080
FRAME_HEIGHT = 1920

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
