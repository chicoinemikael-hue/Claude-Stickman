"""
Props: small items attached to a character's hand or head (crown,
helmets, weapons, shields, torch, scroll, gold, banner, ...).

Each prop is a draw function `draw_<name>(ctx, x, y, H, side, color)`:
- (x, y): the attach point in screen pixels (a hand or the head center).
- H: the character's height in pixels (scale everything off this).
- side: +1 if the character faces right, -1 if left -- mirror any
  left/right offsets by multiplying them by `side`.
- color: the prop's own color (props pick sensible defaults but honor
  an override).

To add a prop:
1. Write draw_my_prop(ctx, x, y, H, side, color=None).
2. Add an entry to PROPS below: attach point ("head", "hand_r", or
   "hand_l") and the draw function.
3. Use it in a storyboard with `props: [my_prop]` or a pickup/drop
   action -- see FORMAT.md.
"""

import math

METAL = (0.72, 0.72, 0.76)
WOOD = (0.52, 0.36, 0.22)
GOLD = (0.85, 0.68, 0.25)


def _c(override, default):
    return override if override is not None else default


# ---------------------------------------------------------------------------
# Head props
# ---------------------------------------------------------------------------
def draw_crown(ctx, x, y, H, side, color=None):
    col = _c(color, GOLD)
    r = H * 0.115
    w, h = r * 1.5, r * 0.6
    ctx.set_source_rgb(*col)
    top = y - r * 1.05
    ctx.move_to(x - w / 2, top)
    n_points = 4
    seg = w / n_points
    for i in range(n_points):
        px = x - w / 2 + seg * (i + 0.5)
        ctx.line_to(px, top - h * (0.9 if i % 2 == 0 else 0.5))
        ctx.line_to(px + seg / 2, top)
    ctx.line_to(x + w / 2, top)
    ctx.line_to(x + w / 2, top + h * 0.35)
    ctx.line_to(x - w / 2, top + h * 0.35)
    ctx.close_path()
    ctx.fill()


def draw_laurel_wreath(ctx, x, y, H, side, color=None):
    col = _c(color, (0.30, 0.52, 0.22))
    r = H * 0.125
    ctx.set_source_rgb(*col)
    for base_angle in (-1, 1):
        for i in range(5):
            a = base_angle * (0.15 + i * 0.18)
            lx = x + math.sin(a) * r * 1.02
            ly = y - math.cos(a) * r * 1.02
            leaf_r = r * 0.14
            ctx.save()
            ctx.translate(lx, ly)
            ctx.rotate(a * 1.3)
            ctx.scale(1.0, 0.5)
            ctx.arc(0, 0, leaf_r, 0, 2 * math.pi)
            ctx.restore()
            ctx.fill()


def draw_roman_helmet(ctx, x, y, H, side, color=None):
    col = _c(color, (0.68, 0.68, 0.72))
    r = H * 0.125
    ctx.set_source_rgb(*col)
    ctx.move_to(x - r, y - r * 0.1)
    ctx.arc(x, y - r * 0.1, r * 1.02, math.pi, 2 * math.pi)
    ctx.line_to(x + r, y - r * 0.1)
    ctx.close_path()
    ctx.fill()
    # cheek guard on the facing side
    ctx.move_to(x + side * r * 0.75, y - r * 0.05)
    ctx.line_to(x + side * r * 0.95, y + r * 0.55)
    ctx.line_to(x + side * r * 0.55, y + r * 0.55)
    ctx.line_to(x + side * r * 0.55, y - r * 0.05)
    ctx.close_path()
    ctx.fill()
    # crest
    ctx.set_source_rgb(0.75, 0.15, 0.15)
    crest_w = r * 0.30
    ctx.move_to(x - crest_w / 2, y - r * 1.0)
    ctx.curve_to(x - crest_w * 0.8, y - r * 1.6, x + crest_w * 0.8, y - r * 1.6, x + crest_w / 2, y - r * 1.0)
    ctx.close_path()
    ctx.fill()


def draw_barbarian_helmet(ctx, x, y, H, side, color=None):
    col = _c(color, (0.45, 0.33, 0.22))
    r = H * 0.125
    ctx.set_source_rgb(*col)
    ctx.move_to(x - r, y)
    ctx.arc(x, y - r * 0.05, r * 1.02, math.pi, 2 * math.pi)
    ctx.line_to(x + r, y)
    ctx.close_path()
    ctx.fill()
    # horns
    ctx.set_source_rgb(0.90, 0.87, 0.80)
    for s in (-1, 1):
        hx = x + s * r * 0.85
        ctx.move_to(hx, y - r * 0.25)
        ctx.curve_to(hx + s * r * 0.6, y - r * 0.7, hx + s * r * 0.5, y - r * 1.2, hx + s * r * 0.75, y - r * 1.5)
        ctx.curve_to(hx + s * r * 0.55, y - r * 1.1, hx + s * r * 0.15, y - r * 0.55, hx, y - r * 0.05)
        ctx.close_path()
        ctx.fill()


HEAD_PROPS = {
    "crown": draw_crown,
    "laurel_wreath": draw_laurel_wreath,
    "roman_helmet": draw_roman_helmet,
    "barbarian_helmet": draw_barbarian_helmet,
}


# ---------------------------------------------------------------------------
# Hand props
# ---------------------------------------------------------------------------
def draw_sword(ctx, x, y, H, side, color=None):
    col = _c(color, METAL)
    length = H * 0.34
    ctx.set_source_rgb(*col)
    ctx.set_line_width(H * 0.030)
    ctx.set_line_cap(1)
    ctx.move_to(x, y)
    ctx.line_to(x + side * length * 0.15, y - length)
    ctx.stroke()
    # crossguard
    ctx.set_line_width(H * 0.022)
    ctx.move_to(x - H * 0.05, y - length * 0.10)
    ctx.line_to(x + H * 0.05, y - length * 0.10)
    ctx.stroke()
    # hilt
    ctx.set_source_rgb(0.35, 0.22, 0.12)
    ctx.set_line_width(H * 0.035)
    ctx.move_to(x, y)
    ctx.line_to(x, y + H * 0.06)
    ctx.stroke()


def draw_spear(ctx, x, y, H, side, color=None):
    col = _c(color, WOOD)
    length = H * 0.62
    ctx.set_source_rgb(*col)
    ctx.set_line_width(H * 0.026)
    ctx.set_line_cap(1)
    ctx.move_to(x, y + H * 0.10)
    ctx.line_to(x + side * length * 0.06, y - length)
    ctx.stroke()
    # spearhead
    ctx.set_source_rgb(*METAL)
    tip_x, tip_y = x + side * length * 0.06, y - length
    ctx.move_to(tip_x, tip_y - H * 0.09)
    ctx.line_to(tip_x - H * 0.025, tip_y + H * 0.02)
    ctx.line_to(tip_x + H * 0.025, tip_y + H * 0.02)
    ctx.close_path()
    ctx.fill()


def draw_round_shield(ctx, x, y, H, side, color=None):
    col = _c(color, (0.62, 0.15, 0.13))
    r = H * 0.17
    ctx.set_source_rgb(*col)
    ctx.arc(x - side * r * 0.15, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(*GOLD)
    ctx.arc(x - side * r * 0.15, y, r * 0.32, 0, 2 * math.pi)
    ctx.fill()


def draw_rect_shield(ctx, x, y, H, side, color=None):
    col = _c(color, (0.62, 0.42, 0.15))
    w, h = H * 0.20, H * 0.32
    ctx.set_source_rgb(*col)
    cx = x - side * w * 0.25
    ctx.rectangle(cx - w / 2, y - h / 2, w, h)
    ctx.fill()
    ctx.set_source_rgb(*GOLD)
    ctx.rectangle(cx - w * 0.08, y - h * 0.35, w * 0.16, h * 0.7)
    ctx.fill()


def draw_torch(ctx, x, y, H, side, color=None):
    ctx.set_source_rgb(*_c(color, WOOD))
    ctx.set_line_width(H * 0.028)
    ctx.set_line_cap(1)
    ctx.move_to(x, y)
    ctx.line_to(x, y - H * 0.28)
    ctx.stroke()
    for r, col, a in [(H * 0.06, (1.0, 0.55, 0.10), 1.0), (H * 0.035, (1.0, 0.85, 0.30), 1.0)]:
        ctx.set_source_rgba(*col, a)
        ctx.move_to(x, y - H * 0.28 - r * 1.6)
        ctx.curve_to(x - r, y - H * 0.28 - r * 0.4, x - r * 0.6, y - H * 0.28 + r * 0.3, x, y - H * 0.28)
        ctx.curve_to(x + r * 0.6, y - H * 0.28 + r * 0.3, x + r, y - H * 0.28 - r * 0.4, x, y - H * 0.28 - r * 1.6)
        ctx.fill()


def draw_scroll(ctx, x, y, H, side, color=None):
    col = _c(color, (0.92, 0.87, 0.72))
    length = H * 0.16
    ctx.set_source_rgb(*col)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(side * 0.3)
    ctx.rectangle(-length / 2, -H * 0.02, length, H * 0.04)
    ctx.fill()
    ctx.restore()


def draw_gold_bag(ctx, x, y, H, side, color=None):
    col = _c(color, GOLD)
    r = H * 0.075
    ctx.set_source_rgb(*col)
    ctx.arc(x, y + r * 0.3, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.45, 0.32, 0.10)
    ctx.set_line_width(H * 0.018)
    ctx.move_to(x - r * 0.5, y - r * 0.5)
    ctx.curve_to(x - r * 0.3, y - r * 1.1, x + r * 0.3, y - r * 1.1, x + r * 0.5, y - r * 0.5)
    ctx.stroke()


def draw_banner(ctx, x, y, H, side, color=None):
    col = _c(color, (0.62, 0.13, 0.13))
    ctx.set_source_rgb(*WOOD)
    ctx.set_line_width(H * 0.022)
    ctx.move_to(x, y + H * 0.05)
    ctx.line_to(x, y - H * 0.45)
    ctx.stroke()

    w, h = H * 0.18, H * 0.14
    ctx.set_source_rgb(*col)
    ctx.move_to(x, y - H * 0.45)
    ctx.line_to(x + side * w, y - H * 0.45 + h * 0.15)
    ctx.line_to(x + side * w * 0.85, y - H * 0.45 + h * 0.5)
    ctx.line_to(x + side * w, y - H * 0.45 + h * 0.85)
    ctx.line_to(x, y - H * 0.45 + h)
    ctx.close_path()
    ctx.fill()


HAND_PROPS = {
    "sword": draw_sword,
    "spear": draw_spear,
    "round_shield": draw_round_shield,
    "rect_shield": draw_rect_shield,
    "torch": draw_torch,
    "scroll": draw_scroll,
    "gold_bag": draw_gold_bag,
    "banner": draw_banner,
}

# Which hand a prop attaches to by default when a storyboard doesn't say.
DEFAULT_HAND = {
    "sword": "r", "spear": "r", "torch": "r", "scroll": "r",
    "gold_bag": "r", "banner": "r",
    "round_shield": "l", "rect_shield": "l",
}

ALL_PROPS = {**HEAD_PROPS, **HAND_PROPS}


def is_head_prop(name: str) -> bool:
    return name in HEAD_PROPS


def is_hand_prop(name: str) -> bool:
    return name in HAND_PROPS


def get_prop_drawer(name: str):
    if name not in ALL_PROPS:
        available = ", ".join(sorted(ALL_PROPS))
        raise KeyError(f'Unknown prop "{name}". Available props: {available}')
    return ALL_PROPS[name]
