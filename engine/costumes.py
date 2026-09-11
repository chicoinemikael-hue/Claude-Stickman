"""
Costumes: toga and cape, worn over the torso (attach point "body"
rather than a hand or the head).

Unlike hand/head props, costumes need a few body joint points to drape
correctly, so their draw functions take the full screen-space points
dict from the rig (see engine.rig.layout_points) instead of a single
anchor point.

draw_back(...) is called BEFORE the limbs are drawn (so a cape hangs
behind the body). draw_front(...) is called right after the torso bone
but before the arms (so a toga wraps the torso and arms emerge from
on top of it).

To add a costume: write draw_back and/or draw_front functions and add
an entry to COSTUMES.
"""


def _toga_draw_front(ctx, points, H, character):
    color = character.costume_color or (0.92, 0.88, 0.80)
    ctx.set_source_rgb(*color)
    neck = points["neck"]
    hip_l = points["hip_l"]
    hip_r = points["hip_r"]
    sh_far = points["sh_l"]

    ctx.move_to(*sh_far)
    ctx.line_to(*neck)
    ctx.line_to(*hip_r)
    ctx.line_to(*hip_l)
    ctx.close_path()
    ctx.fill()

    # a diagonal sash for a bit of toga detail
    ctx.set_source_rgb(color[0] * 0.85, color[1] * 0.85, color[2] * 0.85)
    ctx.set_line_width(H * 0.02)
    ctx.move_to(sh_far[0], sh_far[1] + H * 0.02)
    ctx.line_to(hip_r[0], hip_r[1])
    ctx.stroke()


def _cape_draw_back(ctx, points, H, character):
    color = character.costume_color or (0.55, 0.12, 0.12)
    neck = points["neck"]
    sh_l = points["sh_l"]
    sh_r = points["sh_r"]
    hip = points["hip"]

    sway = H * 0.06
    ctx.set_source_rgb(*color)
    ctx.move_to(*sh_l)
    ctx.line_to(*sh_r)
    ctx.curve_to(hip[0] + sway * 1.4, hip[1] + H * 0.05,
                 hip[0] - sway * 1.4, hip[1] + H * 0.20,
                 hip[0], hip[1] + H * 0.30)
    ctx.curve_to(hip[0] - sway, hip[1] + H * 0.10, hip[0] - sway * 0.6, hip[1] - H * 0.02, sh_l[0], sh_l[1])
    ctx.close_path()
    ctx.fill()


COSTUMES = {
    "toga": {"front": _toga_draw_front},
    "cape": {"back": _cape_draw_back},
}


def get_costume(name: str):
    if name not in COSTUMES:
        available = ", ".join(sorted(COSTUMES))
        raise KeyError(f'Unknown costume "{name}". Available costumes: {available}')
    return COSTUMES[name]
