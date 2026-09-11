"""
A simple stylized map background, with text labels and animated
arrows for showing invasions/territory changes.

v1 does not aim for geographic accuracy -- draw_stylized_map() paints
a plain parchment-colored placeholder landmass. If you want a real
map, use your own PNG as the background (background.draw_custom_image)
and just layer draw_map_label()/draw_map_arrow() on top of it, using
x/y percent coordinates that match your image.
"""

import math
import cairo


def draw_stylized_map(ctx, w, h, sea_color=(0.68, 0.80, 0.82), land_color=(0.88, 0.82, 0.66)):
    ctx.set_source_rgb(*sea_color)
    ctx.rectangle(0, 0, w, h)
    ctx.fill()

    ctx.set_source_rgb(*land_color)
    ctx.move_to(w * 0.10, h * 0.30)
    ctx.curve_to(w * 0.05, h * 0.45, w * 0.15, h * 0.62, w * 0.30, h * 0.68)
    ctx.curve_to(w * 0.45, h * 0.74, w * 0.55, h * 0.62, w * 0.68, h * 0.66)
    ctx.curve_to(w * 0.85, h * 0.70, w * 0.95, h * 0.55, w * 0.90, h * 0.40)
    ctx.curve_to(w * 0.88, h * 0.28, w * 0.70, h * 0.20, w * 0.55, h * 0.24)
    ctx.curve_to(w * 0.40, h * 0.18, w * 0.20, h * 0.18, w * 0.10, h * 0.30)
    ctx.close_path()
    ctx.fill()


def draw_map_label(ctx, w, h, x_pct, y_pct, text, size_pct=3.2,
                    color=(0.20, 0.15, 0.10)):
    ctx.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    size = h * size_pct / 100.0
    ctx.set_font_size(size)
    ext = ctx.text_extents(text)
    x = w * x_pct / 100.0 - ext.width / 2
    y = h * y_pct / 100.0
    ctx.set_source_rgb(*color)
    ctx.move_to(x, y)
    ctx.show_text(text)


def draw_map_arrow(ctx, w, h, from_pct, to_pct, progress=1.0,
                    color=(0.72, 0.15, 0.13), width_pct=0.9):
    """Draw an invasion-route arrow from from_pct to to_pct, both
    (x, y) in percent. `progress` (0..1) animates the line growing
    toward the target, with the arrowhead appearing at the very end.
    """
    progress = max(0.0, min(1.0, progress))
    x1, y1 = w * from_pct[0] / 100.0, h * from_pct[1] / 100.0
    x2, y2 = w * to_pct[0] / 100.0, h * to_pct[1] / 100.0
    cx = x1 + (x2 - x1) * progress
    cy = y1 + (y2 - y1) * progress

    line_width = h * width_pct / 100.0
    ctx.set_source_rgb(*color)
    ctx.set_line_width(line_width)
    ctx.set_line_cap(1)
    ctx.move_to(x1, y1)
    ctx.line_to(cx, cy)
    ctx.stroke()

    if progress > 0.92:
        angle = math.atan2(y2 - y1, x2 - x1)
        head_len = line_width * 3.2
        head_w = line_width * 2.0
        ctx.move_to(cx, cy)
        ctx.line_to(cx - head_len * math.cos(angle - 0.45), cy - head_len * math.sin(angle - 0.45))
        ctx.line_to(cx - head_len * math.cos(angle + 0.45), cy - head_len * math.sin(angle + 0.45))
        ctx.close_path()
        ctx.fill()
