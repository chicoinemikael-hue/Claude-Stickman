"""
Screen effects: fire, smoke, dust clouds, flying arrows, falling
coins, and a crumbling building.

Every effect is a function draw_<name>(ctx, w, h, x_pct, y_pct, t, ...)
that draws ONE frame of the effect, `t` seconds after it started (the
timeline is responsible for computing t and calling this every frame
-- these functions have no memory of their own). Effects use a fixed
random seed per particle so the same t always renders the same way
(important so `--frame` and `--preview` reproduce exactly what the
final render will show).

To add an effect: write draw_my_effect(ctx, w, h, x_pct, y_pct, t,
...) and add it to EFFECTS.
"""

import math
import random

FIRE_COLORS = [(1.0, 0.55, 0.10), (1.0, 0.75, 0.20), (1.0, 0.90, 0.50)]
SMOKE_COLOR = (0.55, 0.55, 0.58)
DUST_COLOR = (0.72, 0.64, 0.48)


def _seeded(seed):
    return random.Random(seed)


def draw_fire(ctx, w, h, x_pct, y_pct, t, scale=1.0):
    x, y = w * x_pct / 100.0, h * y_pct / 100.0
    size = h * 0.05 * scale
    for i, col in enumerate(FIRE_COLORS):
        flick = math.sin(t * 9.0 + i * 2.1) * 0.15 + math.sin(t * 5.3 + i) * 0.1
        r = size * (1.0 - i * 0.22) * (1.0 + flick)
        cy = y - size * (0.3 + i * 0.35) * (1.0 + flick * 0.3)
        ctx.set_source_rgb(*col)
        ctx.move_to(x, cy - r)
        ctx.curve_to(x - r * 0.8, cy - r * 0.2, x - r * 0.5, cy + r * 0.7, x, cy + r)
        ctx.curve_to(x + r * 0.5, cy + r * 0.7, x + r * 0.8, cy - r * 0.2, x, cy - r)
        ctx.fill()


def _puff(ctx, x, y, r, color, alpha):
    ctx.set_source_rgba(color[0], color[1], color[2], alpha)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def draw_smoke(ctx, w, h, x_pct, y_pct, t, scale=1.0, seed=1, duration=3.0):
    x0, y0 = w * x_pct / 100.0, h * y_pct / 100.0
    rnd = _seeded(seed)
    n_puffs = 6
    for i in range(n_puffs):
        offset = rnd.uniform(0, duration)
        drift = rnd.uniform(-0.15, 0.15)
        age = (t + offset) % duration
        progress = age / duration
        if progress > 0.98:
            continue
        r = h * 0.02 * scale * (0.5 + progress * 1.3)
        x = x0 + drift * h * progress * 2
        y = y0 - progress * h * 0.22 * scale
        alpha = 0.35 * (1.0 - progress)
        _puff(ctx, x, y, r, SMOKE_COLOR, alpha)


def draw_dust_cloud(ctx, w, h, x_pct, y_pct, t, scale=1.0, seed=2, duration=0.6):
    x0, y0 = w * x_pct / 100.0, h * y_pct / 100.0
    rnd = _seeded(seed)
    for i in range(8):
        offset = rnd.uniform(0, duration * 0.6)
        angle = rnd.uniform(-2.6, -0.5)
        speed = rnd.uniform(0.5, 1.0) * h * 0.05
        age = t - offset
        if age < 0 or age > duration:
            continue
        progress = age / duration
        dx = math.cos(angle) * speed * progress
        dy = math.sin(angle) * speed * progress
        r = h * 0.012 * scale * (0.6 + progress)
        alpha = 0.4 * (1.0 - progress)
        _puff(ctx, x0 + dx, y0 + dy, r, DUST_COLOR, alpha)


def draw_flying_arrows(ctx, w, h, from_pct, to_pct, t, count=5, duration=1.0,
                        spread=8.0, color=(0.25, 0.20, 0.15), seed=3):
    x1, y1 = w * from_pct[0] / 100.0, h * from_pct[1] / 100.0
    x2, y2 = w * to_pct[0] / 100.0, h * to_pct[1] / 100.0
    rnd = _seeded(seed)
    length = h * 0.045
    for i in range(count):
        stagger = i / count * duration * 0.5
        offset_pct = rnd.uniform(-spread, spread)
        age = t - stagger
        if age < 0 or age > duration:
            continue
        progress = age / duration
        px = x1 + (x2 - x1) * progress
        py = y1 + (y2 - y1) * progress + h * offset_pct / 100.0 * math.sin(progress * math.pi)
        angle = math.atan2(y2 - y1, x2 - x1)
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(angle)
        ctx.set_source_rgb(*color)
        ctx.set_line_width(h * 0.006)
        ctx.move_to(-length / 2, 0)
        ctx.line_to(length / 2, 0)
        ctx.stroke()
        ctx.move_to(length / 2, 0)
        ctx.line_to(length / 2 - h * 0.012, -h * 0.008)
        ctx.line_to(length / 2 - h * 0.012, h * 0.008)
        ctx.close_path()
        ctx.fill()
        ctx.restore()


def draw_falling_coins(ctx, w, h, x_pct, y_pct, t, count=10, duration=1.6,
                        spread_pct=14.0, seed=4):
    x0, y0 = w * x_pct / 100.0, h * y_pct / 100.0
    rnd = _seeded(seed)
    for i in range(count):
        stagger = rnd.uniform(0, duration * 0.5)
        dx = rnd.uniform(-spread_pct, spread_pct) / 100.0 * w
        spin_speed = rnd.uniform(4, 9)
        fall_dist = rnd.uniform(0.20, 0.32) * h
        age = t - stagger
        if age < 0 or age > duration:
            continue
        progress = age / duration
        y = y0 + fall_dist * progress * progress
        x = x0 + dx * progress
        r = h * 0.012
        squash = abs(math.cos(age * spin_speed))
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(max(squash, 0.15), 1.0)
        ctx.set_source_rgb(0.85, 0.68, 0.25)
        ctx.arc(0, 0, r, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()


def draw_crumbling_building(ctx, w, h, x_pct, y_pct, t, width_pct=26, height_pct=30,
                             duration=2.2, color=(0.75, 0.70, 0.62), seed=5):
    """A simple rectangular building that shakes, then breaks into
    falling chunks. y_pct is the building's ground line."""
    cx = w * x_pct / 100.0
    base_y = h * y_pct / 100.0
    width = w * width_pct / 100.0
    height = h * height_pct / 100.0
    rnd = _seeded(seed)

    shake_end = duration * 0.35
    if t < shake_end:
        jitter = (1 - t / shake_end) * w * 0.006
        ox = math.sin(t * 40) * jitter
        ctx.save()
        ctx.translate(ox, 0)
        ctx.set_source_rgb(*color)
        ctx.rectangle(cx - width / 2, base_y - height, width, height)
        ctx.fill()
        ctx.restore()
        return

    progress = min((t - shake_end) / (duration - shake_end), 1.0)
    n_cols, n_rows = 4, 5
    piece_w, piece_h = width / n_cols, height / n_rows
    for row in range(n_rows):
        for col in range(n_cols):
            piece_seed = row * n_cols + col
            prnd = _seeded(seed * 1000 + piece_seed)
            delay = prnd.uniform(0, 0.4)
            piece_progress = max(0.0, min((progress - delay) / (1 - delay), 1.0))
            if piece_progress <= 0:
                px_off, py_off, alpha = 0, 0, 1.0
            else:
                fall = piece_progress ** 2 * height * 1.4
                drift = prnd.uniform(-0.3, 0.3) * width * piece_progress
                px_off, py_off = drift, fall
                alpha = max(0.0, 1.0 - piece_progress * 1.1)
            if alpha <= 0:
                continue
            px = cx - width / 2 + piece_w * col + px_off
            py = base_y - height + piece_h * row + py_off
            rot = piece_progress * prnd.uniform(-1.2, 1.2)
            ctx.save()
            ctx.translate(px + piece_w / 2, py + piece_h / 2)
            ctx.rotate(rot)
            ctx.set_source_rgba(color[0], color[1], color[2], alpha)
            ctx.rectangle(-piece_w / 2, -piece_h / 2, piece_w * 0.92, piece_h * 0.92)
            ctx.fill()
            ctx.restore()


EFFECTS = {
    "fire": draw_fire,
    "smoke": draw_smoke,
    "dust_cloud": draw_dust_cloud,
    "flying_arrows": draw_flying_arrows,
    "falling_coins": draw_falling_coins,
    "crumbling_building": draw_crumbling_building,
}
