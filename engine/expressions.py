"""
Faces! Each expression is a small function that draws eyes + eyebrows +
mouth inside the head circle. Faces are drawn "in profile" toward the
direction the character is facing, like most simple explainer-video
stickmen.

To add a new expression:
1. Write a function draw_<name>(ctx, cx, cy, r, side) below. `side` is
   +1 if facing right, -1 if facing left -- multiply any left/right
   offsets by `side` so the face automatically mirrors correctly.
2. Add it to the EXPRESSIONS dict at the bottom.
That's it -- characters can now use expression: <name> in a storyboard.
"""

import math

FACE_COLOR = (0.15, 0.13, 0.12)


def _eye(ctx, x, y, r, openness=1.0):
    ctx.save()
    ctx.set_source_rgb(*FACE_COLOR)
    ctx.translate(x, y)
    ctx.scale(1.0, max(openness, 0.08))
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()


def draw_neutral(ctx, cx, cy, r, side):
    eye_r = r * 0.10
    ex = cx + side * r * 0.30
    ey = cy - r * 0.05
    _eye(ctx, ex - side * r * 0.22, ey, eye_r)
    _eye(ctx, ex + side * r * 0.22, ey, eye_r)

    ctx.set_source_rgb(*FACE_COLOR)
    ctx.set_line_width(r * 0.09)
    ctx.set_line_cap(1)
    mx = cx + side * r * 0.30
    ctx.move_to(mx - r * 0.20, cy + r * 0.40)
    ctx.line_to(mx + side * r * 0.10, cy + r * 0.40)
    ctx.stroke()


def draw_happy(ctx, cx, cy, r, side):
    eye_r = r * 0.10
    ex = cx + side * r * 0.30
    ey = cy - r * 0.06
    _eye(ctx, ex - side * r * 0.22, ey, eye_r)
    _eye(ctx, ex + side * r * 0.22, ey, eye_r)

    ctx.set_source_rgb(*FACE_COLOR)
    ctx.set_line_width(r * 0.09)
    ctx.set_line_cap(1)
    mx = cx + side * r * 0.28
    my = cy + r * 0.38
    ctx.move_to(mx - r * 0.24, my)
    ctx.curve_to(mx - r * 0.10, my + r * 0.22,
                 mx + side * r * 0.10, my + r * 0.22,
                 mx + side * r * 0.22, my - r * 0.02)
    ctx.stroke()


def draw_angry(ctx, cx, cy, r, side):
    eye_r = r * 0.09
    ex = cx + side * r * 0.30
    ey = cy - r * 0.04
    _eye(ctx, ex - side * r * 0.22, ey, eye_r, openness=0.75)
    _eye(ctx, ex + side * r * 0.22, ey, eye_r, openness=0.75)

    ctx.set_source_rgb(*FACE_COLOR)
    ctx.set_line_width(r * 0.09)
    ctx.set_line_cap(1)
    # angled eyebrows, slanting down toward the nose
    ctx.move_to(ex - side * r * 0.36, ey - r * 0.30)
    ctx.line_to(ex - side * r * 0.10, ey - r * 0.14)
    ctx.stroke()
    ctx.move_to(ex + side * r * 0.36, ey - r * 0.30)
    ctx.line_to(ex + side * r * 0.10, ey - r * 0.14)
    ctx.stroke()

    mx = cx + side * r * 0.28
    ctx.move_to(mx - r * 0.20, cy + r * 0.42)
    ctx.line_to(mx + side * r * 0.16, cy + r * 0.34)
    ctx.stroke()


def draw_sad(ctx, cx, cy, r, side):
    eye_r = r * 0.10
    ex = cx + side * r * 0.30
    ey = cy - r * 0.02
    _eye(ctx, ex - side * r * 0.22, ey, eye_r)
    _eye(ctx, ex + side * r * 0.22, ey, eye_r)

    ctx.set_source_rgb(*FACE_COLOR)
    ctx.set_line_width(r * 0.07)
    ctx.set_line_cap(1)
    # inner eyebrow corners raised = sad
    ctx.move_to(ex - side * r * 0.36, ey - r * 0.16)
    ctx.line_to(ex - side * r * 0.10, ey - r * 0.28)
    ctx.stroke()
    ctx.move_to(ex + side * r * 0.36, ey - r * 0.16)
    ctx.line_to(ex + side * r * 0.10, ey - r * 0.28)
    ctx.stroke()

    mx = cx + side * r * 0.28
    my = cy + r * 0.44
    ctx.set_line_width(r * 0.09)
    ctx.move_to(mx - r * 0.22, my + r * 0.10)
    ctx.curve_to(mx - r * 0.10, my - r * 0.08,
                 mx + side * r * 0.10, my - r * 0.08,
                 mx + side * r * 0.20, my + r * 0.06)
    ctx.stroke()


def draw_shocked(ctx, cx, cy, r, side):
    eye_r = r * 0.14
    ex = cx + side * r * 0.28
    ey = cy - r * 0.06
    _eye(ctx, ex - side * r * 0.22, ey, eye_r)
    _eye(ctx, ex + side * r * 0.22, ey, eye_r)

    ctx.set_source_rgb(*FACE_COLOR)
    mx = cx + side * r * 0.30
    ctx.arc(mx, cy + r * 0.42, r * 0.13, 0, 2 * math.pi)
    ctx.fill()


def draw_scared(ctx, cx, cy, r, side):
    eye_r = r * 0.13
    ex = cx + side * r * 0.28
    ey = cy - r * 0.06
    _eye(ctx, ex - side * r * 0.24, ey, eye_r, openness=1.0)
    _eye(ctx, ex + side * r * 0.20, ey, eye_r, openness=1.0)

    ctx.set_source_rgb(*FACE_COLOR)
    ctx.set_line_width(r * 0.07)
    ctx.set_line_cap(1)
    ctx.move_to(ex - side * r * 0.38, ey - r * 0.30)
    ctx.line_to(ex - side * r * 0.14, ey - r * 0.20)
    ctx.stroke()
    ctx.move_to(ex + side * r * 0.34, ey - 0.30 * r)
    ctx.line_to(ex + side * r * 0.10, ey - r * 0.20)
    ctx.stroke()

    mx = cx + side * r * 0.28
    ctx.save()
    ctx.translate(mx, cy + r * 0.42)
    ctx.scale(0.6, 1.0)
    ctx.arc(0, 0, r * 0.12, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()


EXPRESSIONS = {
    "neutral": draw_neutral,
    "happy": draw_happy,
    "angry": draw_angry,
    "sad": draw_sad,
    "shocked": draw_shocked,
    "scared": draw_scared,
}


def draw_face(ctx, center, radius, facing, expression):
    fn = EXPRESSIONS.get(expression, draw_neutral)
    side = 1 if facing == "right" else -1
    fn(ctx, center[0], center[1], radius, side)
