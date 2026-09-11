"""
Backgrounds: flat, clean scenery built from small reusable pieces
(sky, ground, hills, columns, temple, city wall, triumphal arch,
palace, tents, trees, sea+boat), plus ready-made presets that combine
them (rome_city, throne_room, battlefield, barbarian_camp).

To add a new preset: write a function draw_<name>(ctx, w, h) that
calls a few of the piece functions below, then add it to PRESETS.

To add a new piece: write a function draw_<thing>(ctx, w, h, ...)
that paints directly onto the full frame using cairo. Keep shapes
flat and simple -- rectangles, triangles, circles -- to match the
clean, uncluttered look of the rest of the show.
"""

import math
import cairo

GROUND_Y_PCT = 80.0  # where the ground line sits by default


# ---------------------------------------------------------------------------
# Small drawing helpers
# ---------------------------------------------------------------------------
def _y(h, pct):
    return h * pct / 100.0


def _x(w, pct):
    return w * pct / 100.0


def draw_sky(ctx, w, h, top=(0.53, 0.74, 0.93), bottom=(0.82, 0.90, 0.96)):
    grad = cairo.LinearGradient(0, 0, 0, h)
    grad.add_color_stop_rgb(0, *top)
    grad.add_color_stop_rgb(1, *bottom)
    ctx.set_source(grad)
    ctx.rectangle(0, 0, w, h)
    ctx.fill()


def draw_ground(ctx, w, h, y_pct=GROUND_Y_PCT, color=(0.55, 0.67, 0.34)):
    y = _y(h, y_pct)
    ctx.set_source_rgb(*color)
    ctx.rectangle(0, y, w, h - y)
    ctx.fill()


def draw_hills(ctx, w, h, y_pct=GROUND_Y_PCT, color=(0.46, 0.60, 0.36), bumps=3):
    y = _y(h, y_pct)
    ctx.set_source_rgb(*color)
    ctx.move_to(0, y)
    step = w / bumps
    for i in range(bumps):
        cx = step * (i + 0.5)
        ctx.curve_to(cx - step * 0.3, y - h * 0.09, cx + step * 0.3, y - h * 0.09, cx + step, y)
    ctx.line_to(w, h)
    ctx.line_to(0, h)
    ctx.close_path()
    ctx.fill()


def draw_column(ctx, w, h, x_pct, base_y_pct=GROUND_Y_PCT, height_pct=30,
                 color=(0.87, 0.84, 0.76), width_pct=3.2):
    x = _x(w, x_pct)
    base_y = _y(h, base_y_pct)
    height = _y(h, height_pct)
    cw = _x(w, width_pct)
    ctx.set_source_rgb(*color)
    # shaft
    ctx.rectangle(x - cw / 2, base_y - height, cw, height)
    ctx.fill()
    # base + capital
    ctx.rectangle(x - cw * 0.72, base_y - height * 0.02, cw * 1.44, height * 0.035)
    ctx.fill()
    ctx.rectangle(x - cw * 0.72, base_y - height, cw * 1.44, height * 0.035)
    ctx.fill()


def draw_columns(ctx, w, h, x_positions_pct, base_y_pct=GROUND_Y_PCT, height_pct=30,
                  color=(0.87, 0.84, 0.76)):
    for xp in x_positions_pct:
        draw_column(ctx, w, h, xp, base_y_pct, height_pct, color)


def draw_temple(ctx, w, h, x_pct=50, base_y_pct=GROUND_Y_PCT, width_pct=56,
                 height_pct=32, color=(0.90, 0.87, 0.80)):
    x = _x(w, x_pct)
    base_y = _y(h, base_y_pct)
    width = _x(w, width_pct)
    height = _y(h, height_pct)

    n_columns = 6
    xs = [x - width / 2 + width * i / (n_columns - 1) for i in range(n_columns)]
    xs_pct = [p / w * 100 for p in xs]
    draw_columns(ctx, w, h, xs_pct, base_y_pct, height_pct * 0.72, color)

    # entablature (bar across the tops of the columns)
    col_top = base_y - height * 0.72
    ctx.set_source_rgb(*color)
    ctx.rectangle(x - width / 2 - width * 0.03, col_top - height * 0.06, width * 1.06, height * 0.06)
    ctx.fill()

    # pediment (triangular roof)
    ctx.move_to(x - width / 2 - width * 0.05, col_top - height * 0.06)
    ctx.line_to(x, col_top - height * 0.30)
    ctx.line_to(x + width / 2 + width * 0.05, col_top - height * 0.06)
    ctx.close_path()
    ctx.fill()

    # base steps
    ctx.set_source_rgb(color[0] * 0.92, color[1] * 0.92, color[2] * 0.92)
    ctx.rectangle(x - width / 2 - width * 0.06, base_y, width * 1.12, height * 0.05)
    ctx.fill()


def draw_city_wall(ctx, w, h, base_y_pct=GROUND_Y_PCT, gate_x_pct=50, gate_width_pct=12,
                    height_pct=26, color=(0.68, 0.62, 0.52)):
    base_y = _y(h, base_y_pct)
    height = _y(h, height_pct)
    top = base_y - height
    gate_x = _x(w, gate_x_pct)
    gate_w = _x(w, gate_width_pct)

    ctx.set_source_rgb(*color)
    ctx.rectangle(0, top, w, height)
    ctx.fill()

    # crenellations
    merlon_w = w * 0.035
    gap = merlon_w
    n = int(w / (merlon_w + gap))
    for i in range(n + 1):
        mx = i * (merlon_w + gap)
        ctx.rectangle(mx, top - height * 0.10, merlon_w, height * 0.10)
        ctx.fill()

    # arched gate (cut out with sky-ish shadow color)
    ctx.set_source_rgb(0.16, 0.13, 0.11)
    ctx.move_to(gate_x - gate_w / 2, base_y)
    ctx.line_to(gate_x - gate_w / 2, top + height * 0.45)
    ctx.arc(gate_x, top + height * 0.45, gate_w / 2, math.pi, 0)
    ctx.line_to(gate_x + gate_w / 2, base_y)
    ctx.close_path()
    ctx.fill()


def draw_triumphal_arch(ctx, w, h, x_pct=50, base_y_pct=GROUND_Y_PCT, height_pct=34,
                         width_pct=24, color=(0.88, 0.84, 0.76)):
    x = _x(w, x_pct)
    base_y = _y(h, base_y_pct)
    height = _y(h, height_pct)
    width = _x(w, width_pct)

    ctx.set_source_rgb(*color)
    ctx.rectangle(x - width / 2, base_y - height, width, height)
    ctx.fill()

    opening_w = width * 0.42
    opening_h = height * 0.72
    ctx.set_source_rgb(0.16, 0.13, 0.11)
    ctx.move_to(x - opening_w / 2, base_y)
    ctx.line_to(x - opening_w / 2, base_y - opening_h + opening_w / 2)
    ctx.arc(x, base_y - opening_h + opening_w / 2, opening_w / 2, math.pi, 0)
    ctx.line_to(x + opening_w / 2, base_y)
    ctx.close_path()
    ctx.fill()

    ctx.set_source_rgb(color[0] * 0.9, color[1] * 0.9, color[2] * 0.9)
    ctx.rectangle(x - width / 2 - width * 0.04, base_y - height, width * 1.08, height * 0.08)
    ctx.fill()


def draw_palace(ctx, w, h, x_pct=50, base_y_pct=GROUND_Y_PCT, width_pct=70,
                 height_pct=38, color=(0.85, 0.80, 0.70)):
    x = _x(w, x_pct)
    base_y = _y(h, base_y_pct)
    width = _x(w, width_pct)
    height = _y(h, height_pct)

    ctx.set_source_rgb(*color)
    ctx.rectangle(x - width / 2, base_y - height * 0.75, width, height * 0.75)
    ctx.fill()

    # roof
    ctx.move_to(x - width / 2 - width * 0.04, base_y - height * 0.75)
    ctx.line_to(x, base_y - height)
    ctx.line_to(x + width / 2 + width * 0.04, base_y - height * 0.75)
    ctx.close_path()
    ctx.fill()

    # front columns
    n_columns = 5
    xs = [x - width * 0.38 + width * 0.76 * i / (n_columns - 1) for i in range(n_columns)]
    draw_columns(ctx, w, h, [p / w * 100 for p in xs], base_y_pct, height_pct * 0.68,
                 (min(color[0] + 0.08, 1), min(color[1] + 0.08, 1), min(color[2] + 0.08, 1)))

    # central doorway
    ctx.set_source_rgb(0.20, 0.15, 0.12)
    door_w, door_h = width * 0.10, height * 0.30
    ctx.rectangle(x - door_w / 2, base_y - door_h, door_w, door_h)
    ctx.fill()


def draw_tent(ctx, w, h, x_pct, base_y_pct=GROUND_Y_PCT, height_pct=14,
              color=(0.72, 0.45, 0.24)):
    x = _x(w, x_pct)
    base_y = _y(h, base_y_pct)
    height = _y(h, height_pct)
    width = height * 1.1

    ctx.set_source_rgb(*color)
    ctx.move_to(x - width / 2, base_y)
    ctx.line_to(x, base_y - height)
    ctx.line_to(x + width / 2, base_y)
    ctx.close_path()
    ctx.fill()

    ctx.set_source_rgb(color[0] * 0.7, color[1] * 0.7, color[2] * 0.7)
    ctx.move_to(x, base_y)
    ctx.line_to(x, base_y - height)
    ctx.line_to(x + width * 0.14, base_y - height * 0.86)
    ctx.line_to(x + width * 0.14, base_y)
    ctx.close_path()
    ctx.fill()


def draw_tents(ctx, w, h, x_positions_pct, base_y_pct=GROUND_Y_PCT, height_pct=14,
               color=(0.72, 0.45, 0.24)):
    for xp in x_positions_pct:
        draw_tent(ctx, w, h, xp, base_y_pct, height_pct, color)


def draw_tree(ctx, w, h, x_pct, base_y_pct=GROUND_Y_PCT, height_pct=16,
              trunk_color=(0.42, 0.30, 0.20), leaf_color=(0.30, 0.52, 0.28)):
    x = _x(w, x_pct)
    base_y = _y(h, base_y_pct)
    height = _y(h, height_pct)

    ctx.set_source_rgb(*trunk_color)
    trunk_w = height * 0.14
    ctx.rectangle(x - trunk_w / 2, base_y - height * 0.45, trunk_w, height * 0.45)
    ctx.fill()

    ctx.set_source_rgb(*leaf_color)
    for dx, dy, r in [(0, -0.72, 0.34), (-0.26, -0.55, 0.26), (0.26, -0.55, 0.26)]:
        ctx.arc(x + dx * height, base_y + dy * height, r * height, 0, 2 * math.pi)
        ctx.fill()


def draw_trees(ctx, w, h, x_positions_pct, base_y_pct=GROUND_Y_PCT, height_pct=16,
               trunk_color=(0.42, 0.30, 0.20), leaf_color=(0.30, 0.52, 0.28)):
    for xp in x_positions_pct:
        draw_tree(ctx, w, h, xp, base_y_pct, height_pct, trunk_color, leaf_color)


def draw_sea(ctx, w, h, base_y_pct=GROUND_Y_PCT, color=(0.24, 0.48, 0.62), boat_x_pct=None):
    base_y = _y(h, base_y_pct)
    ctx.set_source_rgb(*color)
    ctx.rectangle(0, base_y, w, h - base_y)
    ctx.fill()

    ctx.set_source_rgba(1, 1, 1, 0.25)
    ctx.set_line_width(h * 0.004)
    for i in range(6):
        wy = base_y + (h - base_y) * (0.15 + 0.13 * i)
        ctx.move_to(0, wy)
        for sx in range(0, int(w) + 40, 40):
            ctx.line_to(sx, wy + math.sin(sx * 0.05 + i) * 4)
        ctx.stroke()

    if boat_x_pct is not None:
        draw_boat(ctx, w, h, boat_x_pct, base_y_pct)


def draw_boat(ctx, w, h, x_pct, base_y_pct=GROUND_Y_PCT,
              hull_color=(0.42, 0.28, 0.18), sail_color=(0.96, 0.94, 0.88)):
    x = _x(w, x_pct)
    y = _y(h, base_y_pct) + h * 0.02
    size = w * 0.11

    ctx.set_source_rgb(*hull_color)
    ctx.move_to(x - size, y)
    ctx.curve_to(x - size * 0.8, y + size * 0.35, x + size * 0.8, y + size * 0.35, x + size, y)
    ctx.line_to(x, y)
    ctx.close_path()
    ctx.fill()

    ctx.set_source_rgb(*hull_color)
    ctx.rectangle(x - size * 0.03, y - size * 1.3, size * 0.06, size * 1.3)
    ctx.fill()

    ctx.set_source_rgb(*sail_color)
    ctx.move_to(x, y - size * 1.28)
    ctx.line_to(x, y - size * 0.15)
    ctx.line_to(x - size * 0.55, y - size * 0.15)
    ctx.close_path()
    ctx.fill()


def draw_custom_image(ctx, w, h, path):
    """Fill the frame with the user's own PNG, scaled to cover it."""
    surface = cairo.ImageSurface.create_from_png(path)
    iw, ih = surface.get_width(), surface.get_height()
    scale = max(w / iw, h / ih)
    ctx.save()
    ctx.translate((w - iw * scale) / 2, (h - ih * scale) / 2)
    ctx.scale(scale, scale)
    ctx.set_source_surface(surface, 0, 0)
    ctx.paint()
    ctx.restore()


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

def preset_rome_city(ctx, w, h):
    draw_sky(ctx, w, h)
    draw_hills(ctx, w, h, y_pct=GROUND_Y_PCT - 2, color=(0.62, 0.68, 0.52), bumps=2)
    draw_temple(ctx, w, h, x_pct=22, base_y_pct=GROUND_Y_PCT - 1, width_pct=28, height_pct=18)
    draw_ground(ctx, w, h, color=(0.68, 0.62, 0.48))
    draw_columns(ctx, w, h, [78, 88], base_y_pct=GROUND_Y_PCT, height_pct=22)


def preset_throne_room(ctx, w, h):
    draw_sky(ctx, w, h, top=(0.42, 0.28, 0.20), bottom=(0.55, 0.38, 0.26))
    draw_ground(ctx, w, h, color=(0.55, 0.40, 0.28))
    draw_columns(ctx, w, h, [10, 26, 74, 90], base_y_pct=GROUND_Y_PCT, height_pct=48,
                 color=(0.78, 0.68, 0.50))
    # throne dais
    x = _x(w, 50)
    base_y = _y(h, GROUND_Y_PCT)
    ctx.set_source_rgb(0.60, 0.20, 0.20)
    ctx.rectangle(x - w * 0.09, base_y - h * 0.20, w * 0.18, h * 0.20)
    ctx.fill()
    ctx.set_source_rgb(0.82, 0.68, 0.30)
    ctx.rectangle(x - w * 0.10, base_y - h * 0.02, w * 0.20, h * 0.02)
    ctx.fill()


def preset_battlefield(ctx, w, h):
    draw_sky(ctx, w, h, top=(0.55, 0.42, 0.38), bottom=(0.80, 0.68, 0.55))
    draw_hills(ctx, w, h, y_pct=GROUND_Y_PCT - 1, color=(0.48, 0.40, 0.30), bumps=4)
    draw_ground(ctx, w, h, color=(0.50, 0.42, 0.28))


def preset_barbarian_camp(ctx, w, h):
    draw_sky(ctx, w, h, top=(0.45, 0.55, 0.62), bottom=(0.78, 0.82, 0.80))
    draw_hills(ctx, w, h, y_pct=GROUND_Y_PCT - 1, color=(0.35, 0.45, 0.32), bumps=3)
    draw_ground(ctx, w, h, color=(0.42, 0.48, 0.30))
    draw_trees(ctx, w, h, [6, 94], base_y_pct=GROUND_Y_PCT, height_pct=20)
    draw_tents(ctx, w, h, [22, 38, 65, 80], base_y_pct=GROUND_Y_PCT, height_pct=13)


PRESETS = {
    "rome_city": preset_rome_city,
    "throne_room": preset_throne_room,
    "battlefield": preset_battlefield,
    "barbarian_camp": preset_barbarian_camp,
}


def draw_preset(ctx, w, h, name):
    if name not in PRESETS:
        available = ", ".join(sorted(PRESETS) + ["map", "<your own .png>"])
        raise KeyError(f'Unknown background preset "{name}". Available: {available}')
    PRESETS[name](ctx, w, h)
