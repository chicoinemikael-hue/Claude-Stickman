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

# Draw order (back-to-front) so limbs on the far side of the body are
# laid down before the torso and near-side limbs cover their joints.
BONE_DRAW_ORDER = [
    ("hip", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "foot_l"), ("foot_l", "toe_l"),
    ("neck", "sh_l"), ("sh_l", "el_l"), ("el_l", "hand_l"),
    ("hip", "neck"),
    ("hip", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "foot_r"), ("foot_r", "toe_r"),
    ("neck", "sh_r"), ("sh_r", "el_r"), ("el_r", "hand_r"),
]


def draw_stickman(ctx, character, pose: Pose):
    """Draw one stickman onto a cairo context.

    `character` needs: x_px, y_px (ground position), height_px,
    facing ("left"/"right"), color (r, g, b 0..1), and expression.
    """
    import engine.expressions as expressions

    H = character.height_px
    points = layout_points(pose, H, character.facing)

    def to_screen(p):
        return (character.x_px + p[0], character.y_px + p[1])

    limb_width = LIMB_WIDTH_RATIO * H
    joint_radius = JOINT_RADIUS_RATIO * H

    ctx.set_line_cap(1)   # ROUND
    ctx.set_line_join(1)  # ROUND

    for a, b in BONE_DRAW_ORDER:
        pa, pb = to_screen(points[a]), to_screen(points[b])
        ctx.set_source_rgb(*character.color)
        ctx.set_line_width(limb_width)
        ctx.move_to(*pa)
        ctx.line_to(*pb)
        ctx.stroke()

    # Round joints hide the seams between bone segments.
    joint_names = {n for pair in BONES for n in pair}
    for name in joint_names:
        if name in ("toe_l", "toe_r"):
            continue
        x, y = to_screen(points[name])
        ctx.set_source_rgb(*character.color)
        ctx.arc(x, y, joint_radius, 0, 2 * math.pi)
        ctx.fill()

    # Head: neutral skin-tone circle with a colored outline.
    head_x, head_y = to_screen(points["head"])
    head_r = PROPORTIONS["head_radius"] * H
    ctx.set_source_rgb(0.98, 0.90, 0.76)
    ctx.arc(head_x, head_y, head_r, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(*character.color)
    ctx.set_line_width(HEAD_OUTLINE_RATIO * H)
    ctx.stroke()

    expressions.draw_face(ctx, (head_x, head_y), head_r, character.facing,
                            character.expression)
