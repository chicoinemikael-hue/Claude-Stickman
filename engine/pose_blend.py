"""
Blending and easing between poses, and looping pose cycles (walk, run,
talking, ...).

Two building blocks:
- blend_poses(a, b, t): a single smooth interpolation between two
  poses, used for transitions ("stand" -> "wave").
- PoseCycle: a small loop of keyframe poses (e.g. 4 poses for a walk
  stride) that repeats forever as `phase` (0..1) increases. Used for
  actions that keep animating while held: walk, run, talk, wave.
"""

from engine.rig import Pose, ANGLE_FIELDS, OFFSET_FIELDS


# ---------------------------------------------------------------------------
# Easing functions: given t in [0, 1], return an eased t in [0, 1].
# ---------------------------------------------------------------------------
def linear(t):
    return t


def ease_in_out(t):
    """Smoothstep. The default for pose transitions -- gentle start
    and stop, no mechanical linear snap."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 2


def ease_in(t):
    t = max(0.0, min(1.0, t))
    return t * t


def _lerp_angle(a: float, b: float, t: float) -> float:
    """Interpolate between two angles by the shortest path (so going
    from 350deg to 10deg turns through 0, not the long way around)."""
    diff = ((b - a + 180) % 360) - 180
    return a + diff * t


def blend_poses(pose_a: Pose, pose_b: Pose, t: float, easing=ease_in_out) -> Pose:
    """Blend from pose_a (t=0) to pose_b (t=1)."""
    t = easing(max(0.0, min(1.0, t)))
    kwargs = {}
    for f in ANGLE_FIELDS:
        kwargs[f] = _lerp_angle(getattr(pose_a, f), getattr(pose_b, f), t)
    for f in OFFSET_FIELDS:
        va, vb = getattr(pose_a, f), getattr(pose_b, f)
        kwargs[f] = va + (vb - va) * t
    return Pose(name=f"{pose_a.name}->{pose_b.name}", **kwargs)


class PoseCycle:
    """A looping sequence of keyframe poses.

    `keyframes` is a list of (Pose, weight) pairs. Weight is the
    keyframe's relative share of the loop (equal weights = evenly
    spaced). sample(phase) returns the blended pose at that point in
    the loop, easing smoothly between consecutive keyframes and
    wrapping the last keyframe back to the first.
    """

    def __init__(self, name: str, keyframes):
        if len(keyframes) < 2:
            raise ValueError(f'Pose cycle "{name}" needs at least 2 keyframes')
        self.name = name
        self.keyframes = keyframes
        self.total_weight = sum(w for _, w in keyframes)

    def sample(self, phase: float) -> Pose:
        phase = phase % 1.0
        t = phase * self.total_weight
        acc = 0.0
        n = len(self.keyframes)
        for i in range(n):
            pose_a, w = self.keyframes[i]
            if t < acc + w or i == n - 1:
                pose_b, _ = self.keyframes[(i + 1) % n]
                local_t = (t - acc) / w if w > 0 else 0.0
                return blend_poses(pose_a, pose_b, local_t, easing=linear)
            acc += w
        return self.keyframes[0][0]
