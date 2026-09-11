"""
On-screen text: big titles, date stamps, captions, and character
speech bubbles.

All of it is safe-margin aware: Shorts/TikTok apps draw their own UI
(follow button, caption, progress bar, ...) over roughly the top and
bottom 15% of the frame, so text defaults are chosen to stay inside
that safe zone. You can still override y_pct explicitly if you know
what you're doing.
"""

import cairo

FONT_FAMILY = "DejaVu Sans"
SAFE_TOP_PCT = 15.0
SAFE_BOTTOM_PCT = 85.0

INK = (0.12, 0.10, 0.09)
PAPER = (1.0, 0.98, 0.94)


def _wrap_text(ctx, text, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if ctx.text_extents(trial).width <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _set_font(ctx, size, bold=True):
    ctx.select_font_face(
        FONT_FAMILY, cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL,
    )
    ctx.set_font_size(size)


def _draw_outlined_text(ctx, x, y, text, fill_color, outline_color, outline_width):
    ctx.move_to(x, y)
    ctx.text_path(text)
    ctx.set_source_rgb(*outline_color)
    ctx.set_line_width(outline_width)
    ctx.set_line_join(1)
    ctx.stroke_preserve()
    ctx.set_source_rgb(*fill_color)
    ctx.fill()


def draw_title(ctx, w, h, text, y_pct=20.0, size_pct=7.0,
               color=(1.0, 1.0, 1.0), outline_color=(0.10, 0.08, 0.07)):
    """A big title card, e.g. "THE FALL OF ROME"."""
    size = h * size_pct / 100.0
    _set_font(ctx, size)
    max_width = w * 0.86
    lines = _wrap_text(ctx, text.upper(), max_width)

    line_height = size * 1.15
    total_height = line_height * len(lines)
    y = h * y_pct / 100.0 - total_height / 2 + size * 0.75

    for line in lines:
        ext = ctx.text_extents(line)
        x = (w - ext.width) / 2
        _draw_outlined_text(ctx, x, y, line, color, outline_color, size * 0.09)
        y += line_height


def draw_date_stamp(ctx, w, h, text, x_pct=50.0, y_pct=35.0, size_pct=4.5,
                     color=(1.0, 1.0, 1.0), bg_color=(0.15, 0.13, 0.12, 0.75)):
    """A small badge like "476 AD". Long text auto-shrinks to fit,
    but a date stamp is meant to be a short label -- use a caption
    for anything longer than a few words."""
    size = h * size_pct / 100.0
    _set_font(ctx, size)
    ext = ctx.text_extents(text)

    max_text_width = w * 0.80
    if ext.width > max_text_width:
        size *= max_text_width / ext.width
        _set_font(ctx, size)
        ext = ctx.text_extents(text)

    cx = w * x_pct / 100.0
    cy = h * y_pct / 100.0
    pad_x, pad_y = size * 0.6, size * 0.4
    box_w = ext.width + pad_x * 2
    box_h = size + pad_y * 2
    radius = box_h * 0.25

    _rounded_rect(ctx, cx - box_w / 2, cy - box_h / 2, box_w, box_h, radius)
    ctx.set_source_rgba(*bg_color)
    ctx.fill()

    ctx.set_source_rgb(*color)
    ctx.move_to(cx - ext.width / 2, cy + size * 0.35)
    ctx.show_text(text)


def draw_caption(ctx, w, h, text, y_pct=80.0, size_pct=4.2,
                  color=(1.0, 1.0, 1.0), outline_color=(0.08, 0.07, 0.06)):
    """A bottom caption line, kept above the unsafe bottom 15%."""
    size = h * size_pct / 100.0
    _set_font(ctx, size)
    max_width = w * 0.88
    lines = _wrap_text(ctx, text, max_width)

    line_height = size * 1.2
    y = h * y_pct / 100.0 - line_height * (len(lines) - 1)
    for line in lines:
        ext = ctx.text_extents(line)
        x = (w - ext.width) / 2
        _draw_outlined_text(ctx, x, y, line, color, outline_color, size * 0.08)
        y += line_height


def _rounded_rect(ctx, x, y, w, h, r):
    ctx.new_path()
    ctx.arc(x + r, y + r, r, 3.14159, 3.14159 * 1.5)
    ctx.arc(x + w - r, y + r, r, 3.14159 * 1.5, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, 3.14159 * 0.5)
    ctx.arc(x + r, y + h - r, r, 3.14159 * 0.5, 3.14159)
    ctx.close_path()


def draw_speech_bubble(ctx, w, h, text, anchor_x_pct, anchor_y_pct,
                        max_width_pct=42.0, size_pct=3.4,
                        bg_color=(1.0, 1.0, 1.0), text_color=(0.10, 0.09, 0.08),
                        outline_color=(0.10, 0.09, 0.08)):
    """A speech bubble with a tail, anchored above a point (usually a
    character's head position in pixels)."""
    size = h * size_pct / 100.0
    _set_font(ctx, size)
    max_width = w * max_width_pct / 100.0 - size * 1.6
    lines = _wrap_text(ctx, text, max_width)

    line_height = size * 1.25
    text_h = line_height * len(lines)
    text_w = max((ctx.text_extents(line).width for line in lines), default=0)

    pad_x, pad_y = size * 0.8, size * 0.6
    box_w = text_w + pad_x * 2
    box_h = text_h + pad_y * 2

    cx = anchor_x_pct
    tail_tip_y = anchor_y_pct
    box_bottom = tail_tip_y - h * 0.03
    box_top = box_bottom - box_h
    box_left = cx - box_w / 2
    box_left = max(w * 0.02, min(w - w * 0.02 - box_w, box_left))

    radius = min(box_h * 0.3, size)
    _rounded_rect(ctx, box_left, box_top, box_w, box_h, radius)
    ctx.set_source_rgb(*bg_color)
    ctx.fill_preserve()
    ctx.set_source_rgb(*outline_color)
    ctx.set_line_width(size * 0.09)
    ctx.stroke()

    tail_base_x = min(max(cx, box_left + box_w * 0.2), box_left + box_w * 0.8)
    ctx.move_to(tail_base_x - size * 0.4, box_bottom - 1)
    ctx.line_to(tail_base_x + size * 0.4, box_bottom - 1)
    ctx.line_to(cx, tail_tip_y)
    ctx.close_path()
    ctx.set_source_rgb(*bg_color)
    ctx.fill_preserve()
    ctx.set_source_rgb(*outline_color)
    ctx.set_line_width(size * 0.09)
    ctx.stroke()

    ctx.set_source_rgb(*text_color)
    ty = box_top + pad_y + size * 0.78
    for line in lines:
        ext = ctx.text_extents(line)
        tx = box_left + (box_w - ext.width) / 2
        ctx.move_to(tx, ty)
        ctx.show_text(line)
        ty += line_height
