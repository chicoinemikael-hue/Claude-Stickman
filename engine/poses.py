"""
The pose library.

Every pose is a engine.rig.Pose -- a bag of joint angles (degrees,
0 = up, clockwise positive). This is the ONE place to add new poses.

To add a pose:
1. Copy an existing one that's roughly similar.
2. Tweak the angles. Easiest way: render a still frame with
   `--frame` while you adjust numbers, and look at the PNG.
3. Add it to the POSES dict at the bottom with a name -- that name is
   what storyboards use in `pose: <name>`.

Looping poses (walk, run, talk, ...) are handled in pose_blend.py,
which builds a cycle out of a few "key" poses defined here.
"""

from engine.rig import Pose

STAND = Pose(
    name="stand",
    hip_y_offset=0.0,
    torso_angle=0.0,
    neck_angle=0.0,
    l_shoulder_angle=185.0,
    l_elbow_angle=185.0,
    r_shoulder_angle=175.0,
    r_elbow_angle=175.0,
    l_hip_angle=182.0,
    l_knee_angle=182.0,
    r_hip_angle=178.0,
    r_knee_angle=178.0,
    l_ankle_angle=95.0,
    r_ankle_angle=85.0,
)

POSES = {
    "stand": STAND,
}


def get_pose(name: str) -> Pose:
    if name not in POSES:
        available = ", ".join(sorted(POSES))
        raise KeyError(f'Unknown pose "{name}". Available poses: {available}')
    return POSES[name]
