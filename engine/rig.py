"""
The stickman skeleton (rig).

A Pose is just a bag of joint angles. Every bone has its own angle,
measured in degrees, clockwise from "straight up" (0 = up, 90 = right,
180 = down, 270/-90 = left). This is the ONE place that defines the
skeleton's shape and proportions.

To add a new pose, you don't edit this file — see engine/poses.py.
This file only knows how to turn a Pose into a set of 2D points
("forward kinematics") and how to draw those points as a stickman.

Coordinate convention used throughout this module:
- The rig is built in a local, unit-less space where 1.0 = the
  character's full standing height (H).
- The origin (0, 0) is the hip (pelvis) joint.
- x grows to the right, y grows DOWN (standard screen convention).
- The rig is authored "facing right". Drawing code mirrors it
  horizontally for characters facing left.
"""

import math
from dataclasses import dataclass, replace


# ---------------------------------------------------------------------------
# Bone proportions, as a fraction of character height H.
# Tweak these to change body shape (e.g. bigger heads for a cartoonier look).
# ---------------------------------------------------------------------------
PROPORTIONS = {
    "torso": 0.32,
    "neck": 0.045,
    "head_radius": 0.115,
    "upper_arm": 0.205,
    "forearm": 0.190,
    "thigh": 0.285,
    "shin": 0.270,
    "foot": 0.095,
    "shoulder_width": 0.25,
    "hip_width": 0.16,
}

LIMB_WIDTH_RATIO = 0.045   # bone stroke width, as a fraction of H
JOINT_RADIUS_RATIO = 0.026  # small filled circles drawn at each joint
HEAD_OUTLINE_RATIO = 0.026  # stroke width of the head outline


@dataclass
class Pose:
    """All joint angles that define a stickman's silhouette.

    Every field is an absolute angle in degrees (0 = up, clockwise
    positive). "l_"/"r_" refer to the back/front side of the body in
    the canonical facing-right rig (front = the side the character is
    facing). hip_y_offset shifts the pelvis down (positive) for
    crouching, sitting, kneeling, etc. -- fractions of H.
    """
    name: str = "pose"

    hip_y_offset: float = 0.0
    torso_angle: float = 0.0
    neck_angle: float = 0.0

    l_shoulder_angle: float = 185.0
    l_elbow_angle: float = 185.0
    r_shoulder_angle: float = 175.0
    r_elbow_angle: float = 175.0

    l_hip_angle: float = 182.0
    l_knee_angle: float = 182.0
    r_hip_angle: float = 178.0
    r_knee_angle: float = 178.0

    l_ankle_angle: float = 95.0
    r_ankle_angle: float = 85.0

    def with_overrides(self, **kwargs) -> "Pose":
        """Return a copy of this pose with some angles changed.

        Handy for defining new poses as a small diff from an existing
        one, e.g. Pose.STAND.with_overrides(r_shoulder_angle=40).
        """
        return replace(self, **kwargs)


# The angle fields, in the order joints are conceptually laid out.
# pose_blend.py uses this list to interpolate between two poses.
ANGLE_FIELDS = [
    "torso_angle", "neck_angle",
    "l_shoulder_angle", "l_elbow_angle",
    "r_shoulder_angle", "r_elbow_angle",
    "l_hip_angle", "l_knee_angle",
    "r_hip_angle", "r_knee_angle",
    "l_ankle_angle", "r_ankle_angle",
]
OFFSET_FIELDS = ["hip_y_offset"]


def _dir_vec(angle_deg: float) -> tuple:
    """Unit vector for an angle (0 = up, clockwise positive)."""
    a = math.radians(angle_deg)
    return (math.sin(a), -math.cos(a))


def _add(point: tuple, vec: tuple, length: float) -> tuple:
    return (point[0] + vec[0] * length, point[1] + vec[1] * length)


def compute_points(pose: Pose, H: float = 1.0) -> dict:
    """Forward-kinematics: turn a Pose into a dict of 2D joint points.

    Points are in the canonical "facing right" local space described
    at the top of this file, scaled by H (character height in
    whatever units the caller wants, e.g. pixels).
    """
    P = PROPORTIONS

    hip = (0.0, pose.hip_y_offset * H)
    neck = _add(hip, _dir_vec(pose.torso_angle), P["torso"] * H)
    head = _add(neck, _dir_vec(pose.neck_angle), (P["neck"] + P["head_radius"]) * H)

    perp_front = pose.torso_angle + 90
    perp_back = pose.torso_angle - 90

    sh_r = _add(neck, _dir_vec(perp_front), P["shoulder_width"] / 2 * H)
    sh_l = _add(neck, _dir_vec(perp_back), P["shoulder_width"] / 2 * H)
    hip_r = _add(hip, _dir_vec(perp_front), P["hip_width"] / 2 * H)
    hip_l = _add(hip, _dir_vec(perp_back), P["hip_width"] / 2 * H)

    el_r = _add(sh_r, _dir_vec(pose.r_shoulder_angle), P["upper_arm"] * H)
    hand_r = _add(el_r, _dir_vec(pose.r_elbow_angle), P["forearm"] * H)
    el_l = _add(sh_l, _dir_vec(pose.l_shoulder_angle), P["upper_arm"] * H)
    hand_l = _add(el_l, _dir_vec(pose.l_elbow_angle), P["forearm"] * H)

    knee_r = _add(hip_r, _dir_vec(pose.r_hip_angle), P["thigh"] * H)
    foot_r = _add(knee_r, _dir_vec(pose.r_knee_angle), P["shin"] * H)
    toe_r = _add(foot_r, _dir_vec(pose.r_ankle_angle), P["foot"] * H)

    knee_l = _add(hip_l, _dir_vec(pose.l_hip_angle), P["thigh"] * H)
    foot_l = _add(knee_l, _dir_vec(pose.l_knee_angle), P["shin"] * H)
    toe_l = _add(foot_l, _dir_vec(pose.l_ankle_angle), P["foot"] * H)

    return {
        "hip": hip, "neck": neck, "head": head,
        "sh_r": sh_r, "sh_l": sh_l, "hip_r": hip_r, "hip_l": hip_l,
        "el_r": el_r, "hand_r": hand_r, "el_l": el_l, "hand_l": hand_l,
        "knee_r": knee_r, "foot_r": foot_r, "toe_r": toe_r,
        "knee_l": knee_l, "foot_l": foot_l, "toe_l": toe_l,
    }


def _mirror(points: dict) -> dict:
    """Mirror all points across x=0 (hip stays on the mirror line)."""
    return {k: (-x, y) for k, (x, y) in points.items()}


def layout_points(pose: Pose, H: float, facing: str) -> dict:
    """compute_points(), mirrored for facing and auto-grounded so the
    lowest point (feet) always sits at y = 0, regardless of pose.

    This means a kneeling or crouching character's feet still land on
    the ground line the caller places them at -- no manual per-pose
    height tuning needed.
    """
    points = compute_points(pose, H)
    if facing == "left":
        points = _mirror(points)

    ground_y = max(points["toe_r"][1], points["toe_l"][1],
                    points["foot_r"][1], points["foot_l"][1])
    return {k: (x, y - ground_y) for k, (x, y) in points.items()}


# Bones drawn as thick strokes, as (from, to) point-name pairs.
BONES = [
    ("hip", "neck"),
    ("neck", "sh_l"), ("sh_l", "el_l"), ("el_l", "hand_l"),
    ("neck", "sh_r"), ("sh_r", "el_r"), ("el_r", "hand_r"),
    ("hip", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "foot_l"), ("foot_l", "toe_l"),
    ("hip", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "foot_r"), ("foot_r", "toe_r"),
]

# Draw order split into layers (back-to-front) so a cape can be drawn
# behind everything, and a toga drawn over the torso but under the
# arms that emerge from it.
BACK_LEG_BONES = [("hip", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "foot_l"), ("foot_l", "toe_l")]
BACK_ARM_BONES = [("neck", "sh_l"), ("sh_l", "el_l"), ("el_l", "hand_l")]
TORSO_BONES = [("hip", "neck")]
FRONT_LEG_BONES = [("hip", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "foot_r"), ("foot_r", "toe_r")]
FRONT_ARM_BONES = [("neck", "sh_r"), ("sh_r", "el_r"), ("el_r", "hand_r")]


def _stroke_bones(ctx, screen_points, bone_list, color, limb_width):
    ctx.set_source_rgb(*color)
    ctx.set_line_width(limb_width)
    for a, b in bone_list:
        ctx.move_to(*screen_points[a])
        ctx.line_to(*screen_points[b])
        ctx.stroke()


def draw_stickman(ctx, character, pose: Pose):
    """Draw one stickman (plus costume/props, if any) onto a cairo
    context.

    `character` needs: x_px, y_px (ground position), height_px,
    facing ("left"/"right"), color (r, g, b 0..1), expression, and
    optionally costume/costume_color/props (see engine.character).
    """
    import engine.expressions as expressions
    import engine.costumes as costumes
    import engine.props as props

    H = character.height_px
    local_points = layout_points(pose, H, character.facing)
    screen_points = {k: (character.x_px + x, character.y_px + y) for k, (x, y) in local_points.items()}
    side = 1 if character.facing == "right" else -1

    limb_width = LIMB_WIDTH_RATIO * H
    joint_radius = JOINT_RADIUS_RATIO * H

    ctx.set_line_cap(1)   # ROUND
    ctx.set_line_join(1)  # ROUND

    costume_def = costumes.get_costume(character.costume) if character.costume else None
    if costume_def and "back" in costume_def:
        costume_def["back"](ctx, screen_points, H, character)

    _stroke_bones(ctx, screen_points, BACK_LEG_BONES, character.color, limb_width)
    _stroke_bones(ctx, screen_points, BACK_ARM_BONES, character.color, limb_width)
    _stroke_bones(ctx, screen_points, TORSO_BONES, character.color, limb_width)

    if costume_def and "front" in costume_def:
        costume_def["front"](ctx, screen_points, H, character)

    _stroke_bones(ctx, screen_points, FRONT_LEG_BONES, character.color, limb_width)
    _stroke_bones(ctx, screen_points, FRONT_ARM_BONES, character.color, limb_width)

    # Round joints hide the seams between bone segments.
    joint_names = {n for pair in BONES for n in pair}
    for name in joint_names:
        if name in ("toe_l", "toe_r"):
            continue
        x, y = screen_points[name]
        ctx.set_source_rgb(*character.color)
        ctx.arc(x, y, joint_radius, 0, 2 * math.pi)
        ctx.fill()

    # Head: neutral skin-tone circle with a colored outline.
    head_x, head_y = screen_points["head"]
    head_r = PROPORTIONS["head_radius"] * H
    ctx.set_source_rgb(0.98, 0.90, 0.76)
    ctx.arc(head_x, head_y, head_r, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(*character.color)
    ctx.set_line_width(HEAD_OUTLINE_RATIO * H)
    ctx.stroke()

    expressions.draw_face(ctx, (head_x, head_y), head_r, character.facing,
                            character.expression)

    for prop_name in character.props:
        if props.is_head_prop(prop_name):
            drawer = props.get_prop_drawer(prop_name)
            drawer(ctx, head_x, head_y, H, side, None)
    for prop_name in character.props:
        if props.is_hand_prop(prop_name):
            hand = props.DEFAULT_HAND.get(prop_name, "r")
            hx, hy = screen_points[f"hand_{hand}"]
            hand_side = side if hand == "r" else -side
            drawer = props.get_prop_drawer(prop_name)
            drawer(ctx, hx, hy, H, hand_side, None)

    if character.label:
        ctx.select_font_face("DejaVu Sans", 0, 1)
        label_size = H * 0.075
        ctx.set_font_size(label_size)
        ext = ctx.text_extents(character.label)
        lx = head_x - ext.width / 2
        ly = head_y - head_r - label_size * 0.7
        ctx.set_source_rgb(1, 1, 1)
        ctx.move_to(lx, ly)
        ctx.text_path(character.label)
        ctx.set_line_width(label_size * 0.18)
        ctx.set_line_join(1)
        ctx.stroke_preserve()
        ctx.set_source_rgb(0.15, 0.13, 0.12)
        ctx.fill()
