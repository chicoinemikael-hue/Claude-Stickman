"""
The pose library.

Every held pose is an engine.rig.Pose -- a bag of joint angles
(degrees, 0 = up, clockwise positive, "l_"/"r_" = back-side/front-side
limb in the canonical facing-right rig). Looping actions (walk, run,
wave, talk) are engine.pose_blend.PoseCycle objects: a small loop of
keyframe poses that blend into each other forever.

This is the ONE place to add new poses or cycles.

HOW TO ADD A HELD POSE (like "kneel" or "point"):
1. Copy the closest existing Pose below.
2. Tweak the angle numbers. Angle cheat sheet (limb hanging straight
   down/up = 180/0; smaller angle = swung toward the front of the
   character, i.e. the direction they're facing; bigger = swung back):
     torso_angle    lean forward(-)/back(+) from vertical
     neck_angle     head tilt continuing the torso line
     *_shoulder     upper arm direction (180 = hanging down)
     *_elbow        forearm direction (independent of the upper arm)
     *_hip          thigh direction (180 = straight down)
     *_knee         shin direction (independent of the thigh)
     *_ankle        foot direction (90 = flat, pointing forward)
     hip_y_offset   pelvis height; positive = lower (crouch/sit/kneel)
3. Give it a name and add it to POSES at the bottom. Render a still
   frame with `--frame` while you dial in the angles -- much easier
   than imagining it.

HOW TO ADD A LOOPING CYCLE (like "walk"):
1. Write 2-4 keyframe Poses that make up one repetition.
2. Wrap them in a PoseCycle (see WALK / RUN / WAVE / TALK below) and
   add it to CYCLES at the bottom.
"""

from engine.rig import Pose
from engine.pose_blend import PoseCycle

# ---------------------------------------------------------------------------
# Held poses
# ---------------------------------------------------------------------------

STAND = Pose(
    name="stand",
    l_shoulder_angle=185, l_elbow_angle=185,
    r_shoulder_angle=175, r_elbow_angle=175,
    l_hip_angle=182, l_knee_angle=182,
    r_hip_angle=178, r_knee_angle=178,
    l_ankle_angle=95, r_ankle_angle=85,
)

POINT = STAND.with_overrides(
    name="point",
    torso_angle=3,
    r_shoulder_angle=70, r_elbow_angle=75,
    l_shoulder_angle=200, l_elbow_angle=190,
)

WAVE_UP = STAND.with_overrides(
    name="wave_up",
    torso_angle=-2,
    r_shoulder_angle=25, r_elbow_angle=30,
)
WAVE_OUT = WAVE_UP.with_overrides(name="wave_out", r_elbow_angle=70)

CHEER = STAND.with_overrides(
    name="cheer",
    torso_angle=-3,
    l_shoulder_angle=325, l_elbow_angle=320,
    r_shoulder_angle=35, r_elbow_angle=40,
    l_hip_angle=190, r_hip_angle=170,
)

KNEEL = Pose(
    name="kneel",
    hip_y_offset=0.14,
    torso_angle=4,
    l_shoulder_angle=190, l_elbow_angle=195,
    r_shoulder_angle=130, r_elbow_angle=160,
    l_hip_angle=250, l_knee_angle=260,
    r_hip_angle=100, r_knee_angle=185,
    l_ankle_angle=170, r_ankle_angle=90,
)

BOW = STAND.with_overrides(
    name="bow",
    torso_angle=48,
    neck_angle=25,
    l_shoulder_angle=210, l_elbow_angle=205,
    r_shoulder_angle=200, r_elbow_angle=195,
    l_hip_angle=188, r_hip_angle=172,
)

SIT = Pose(
    name="sit",
    hip_y_offset=0.20,
    torso_angle=2,
    l_shoulder_angle=188, l_elbow_angle=195,
    r_shoulder_angle=172, r_elbow_angle=185,
    l_hip_angle=100, l_knee_angle=265,
    r_hip_angle=95, r_knee_angle=270,
    l_ankle_angle=80, r_ankle_angle=85,
)

SWORD_SWING = STAND.with_overrides(
    name="sword_swing",
    torso_angle=15,
    r_shoulder_angle=95, r_elbow_angle=85,
    l_shoulder_angle=200, l_elbow_angle=195,
    r_hip_angle=155, l_hip_angle=200,
)

BLOCK = STAND.with_overrides(
    name="block",
    torso_angle=6,
    l_shoulder_angle=90, l_elbow_angle=95,
    r_shoulder_angle=200, r_elbow_angle=195,
    r_hip_angle=195, l_hip_angle=165,
)

FALL_OVER = Pose(
    name="fall_over",
    hip_y_offset=0.02,
    torso_angle=95,
    neck_angle=100,
    l_shoulder_angle=60, l_elbow_angle=40,
    r_shoulder_angle=130, r_elbow_angle=160,
    l_hip_angle=110, l_knee_angle=95,
    r_hip_angle=95, r_knee_angle=100,
    l_ankle_angle=100, r_ankle_angle=95,
)

LIE_DOWN = Pose(
    name="lie_down",
    hip_y_offset=0.02,
    torso_angle=92,
    neck_angle=88,
    l_shoulder_angle=100, l_elbow_angle=115,
    r_shoulder_angle=85, r_elbow_angle=70,
    l_hip_angle=95, l_knee_angle=100,
    r_hip_angle=88, r_knee_angle=90,
    l_ankle_angle=95, r_ankle_angle=90,
)

SHRUG = STAND.with_overrides(
    name="shrug",
    neck_angle=-4,
    l_shoulder_angle=140, l_elbow_angle=95,
    r_shoulder_angle=220, r_elbow_angle=265,
)

FACEPALM = STAND.with_overrides(
    name="facepalm",
    torso_angle=4,
    neck_angle=6,
    r_shoulder_angle=50, r_elbow_angle=300,
    l_shoulder_angle=195, l_elbow_angle=190,
)

ARMS_CROSSED = STAND.with_overrides(
    name="arms_crossed",
    l_shoulder_angle=95, l_elbow_angle=250,
    r_shoulder_angle=265, r_elbow_angle=110,
)

POSES = {
    "stand": STAND,
    "point": POINT,
    "cheer": CHEER,
    "kneel": KNEEL,
    "bow": BOW,
    "sit": SIT,
    "sword_swing": SWORD_SWING,
    "block": BLOCK,
    "fall_over": FALL_OVER,
    "lie_down": LIE_DOWN,
    "shrug": SHRUG,
    "facepalm": FACEPALM,
    "arms_crossed": ARMS_CROSSED,
}


# ---------------------------------------------------------------------------
# Looping cycles: walk, run, wave, talk
# ---------------------------------------------------------------------------

_WALK_CONTACT_R = STAND.with_overrides(
    name="walk_contact_r", torso_angle=2,
    r_hip_angle=145, r_knee_angle=165, r_ankle_angle=75,
    l_hip_angle=215, l_knee_angle=195, l_ankle_angle=100,
    l_shoulder_angle=145, l_elbow_angle=160,
    r_shoulder_angle=220, r_elbow_angle=235,
)
_WALK_PASS_R_SWING = STAND.with_overrides(
    name="walk_pass_r_swing", torso_angle=2,
    r_hip_angle=178, r_knee_angle=180, r_ankle_angle=88,
    l_hip_angle=170, l_knee_angle=110, l_ankle_angle=55,
    l_shoulder_angle=180, l_elbow_angle=178,
    r_shoulder_angle=182, r_elbow_angle=182,
)
_WALK_CONTACT_L = STAND.with_overrides(
    name="walk_contact_l", torso_angle=2,
    l_hip_angle=145, l_knee_angle=165, l_ankle_angle=75,
    r_hip_angle=215, r_knee_angle=195, r_ankle_angle=100,
    r_shoulder_angle=145, r_elbow_angle=160,
    l_shoulder_angle=220, l_elbow_angle=235,
)
_WALK_PASS_L_SWING = STAND.with_overrides(
    name="walk_pass_l_swing", torso_angle=2,
    l_hip_angle=178, l_knee_angle=180, l_ankle_angle=88,
    r_hip_angle=170, r_knee_angle=110, r_ankle_angle=55,
    r_shoulder_angle=180, r_elbow_angle=178,
    l_shoulder_angle=182, l_elbow_angle=182,
)
WALK = PoseCycle("walk", [
    (_WALK_CONTACT_R, 1.0),
    (_WALK_PASS_R_SWING, 1.0),
    (_WALK_CONTACT_L, 1.0),
    (_WALK_PASS_L_SWING, 1.0),
])

_RUN_CONTACT_R = STAND.with_overrides(
    name="run_contact_r", torso_angle=10, hip_y_offset=-0.01,
    r_hip_angle=115, r_knee_angle=150, r_ankle_angle=70,
    l_hip_angle=235, l_knee_angle=270, l_ankle_angle=110,
    l_shoulder_angle=100, l_elbow_angle=70,
    r_shoulder_angle=250, r_elbow_angle=295,
)
_RUN_PASS_R_SWING = STAND.with_overrides(
    name="run_pass_r_swing", torso_angle=12, hip_y_offset=0.03,
    r_hip_angle=170, r_knee_angle=90, r_ankle_angle=40,
    l_hip_angle=150, l_knee_angle=200, l_ankle_angle=95,
    l_shoulder_angle=170, l_elbow_angle=130,
    r_shoulder_angle=190, r_elbow_angle=230,
)
_RUN_CONTACT_L = STAND.with_overrides(
    name="run_contact_l", torso_angle=10, hip_y_offset=-0.01,
    l_hip_angle=115, l_knee_angle=150, l_ankle_angle=70,
    r_hip_angle=235, r_knee_angle=270, r_ankle_angle=110,
    r_shoulder_angle=100, r_elbow_angle=70,
    l_shoulder_angle=250, l_elbow_angle=295,
)
_RUN_PASS_L_SWING = STAND.with_overrides(
    name="run_pass_l_swing", torso_angle=12, hip_y_offset=0.03,
    l_hip_angle=170, l_knee_angle=90, l_ankle_angle=40,
    r_hip_angle=150, r_knee_angle=200, r_ankle_angle=95,
    r_shoulder_angle=170, r_elbow_angle=130,
    l_shoulder_angle=190, l_elbow_angle=230,
)
RUN = PoseCycle("run", [
    (_RUN_CONTACT_R, 1.0),
    (_RUN_PASS_R_SWING, 1.0),
    (_RUN_CONTACT_L, 1.0),
    (_RUN_PASS_L_SWING, 1.0),
])

WAVE = PoseCycle("wave", [
    (WAVE_UP, 1.0),
    (WAVE_OUT, 1.0),
])

_TALK_A = STAND.with_overrides(
    name="talk_a", torso_angle=2,
    r_shoulder_angle=110, r_elbow_angle=60,
)
_TALK_B = STAND.with_overrides(
    name="talk_b", torso_angle=1,
    r_shoulder_angle=90, r_elbow_angle=110,
)
_TALK_C = STAND.with_overrides(
    name="talk_c", torso_angle=2,
    r_shoulder_angle=100, r_elbow_angle=40,
)
TALK = PoseCycle("talk", [
    (_TALK_A, 1.0), (_TALK_B, 1.0), (_TALK_C, 1.0), (_TALK_B, 1.0),
])

CYCLES = {
    "walk": WALK,
    "run": RUN,
    "wave": WAVE,
    "talk": TALK,
}


def get_pose(name: str) -> Pose:
    if name not in POSES:
        available = ", ".join(sorted(POSES))
        raise KeyError(f'Unknown pose "{name}". Available poses: {available}')
    return POSES[name]


def get_cycle(name: str) -> PoseCycle:
    if name not in CYCLES:
        available = ", ".join(sorted(CYCLES))
        raise KeyError(f'Unknown pose cycle "{name}". Available cycles: {available}')
    return CYCLES[name]


def is_cycle(name: str) -> bool:
    return name in CYCLES
