"""
Camera: pan, zoom, and shake.

The "camera" is just a 2D transform applied to the whole scene
(background + characters + effects) before it's drawn. Text/captions
are drawn afterwards in fixed screen space, so titles stay put even
while the camera moves.

A Camera is defined by a few keyframes in the storyboard (see
FORMAT.md) -- this module only knows how to turn "camera state at
time t" into a cairo transform.
"""

import math
import random


class CameraState:
    """A camera position: where it's centered (percent of screen),
    how zoomed in it is (1.0 = normal), and how much shake to apply.
    """

    def __init__(self, center_x_pct=50.0, center_y_pct=50.0, zoom=1.0, shake=0.0):
        self.center_x_pct = center_x_pct
        self.center_y_pct = center_y_pct
        self.zoom = zoom
        self.shake = shake  # 0..1 intensity


def lerp(a, b, t):
    return a + (b - a) * t


def blend_camera(a: CameraState, b: CameraState, t: float) -> CameraState:
    t = max(0.0, min(1.0, t))
    return CameraState(
        center_x_pct=lerp(a.center_x_pct, b.center_x_pct, t),
        center_y_pct=lerp(a.center_y_pct, b.center_y_pct, t),
        zoom=lerp(a.zoom, b.zoom, t),
        shake=lerp(a.shake, b.shake, t),
    )


def apply_camera(ctx, state: CameraState, width: int, height: int, t: float = 0.0):
    """Apply the camera transform to `ctx`. Call ctx.save() before and
    ctx.restore() after (or use the `camera_view` context manager
    below)."""
    cx = state.center_x_pct / 100.0 * width
    cy = state.center_y_pct / 100.0 * height

    shake_x = shake_y = 0.0
    if state.shake > 0:
        # Deterministic-ish jitter driven by time, so repeated renders
        # of the same frame produce the same shake.
        amplitude = state.shake * 18.0
        shake_x = math.sin(t * 47.0) * math.cos(t * 13.0) * amplitude
        shake_y = math.cos(t * 53.0) * math.sin(t * 17.0) * amplitude

    ctx.translate(width / 2.0 + shake_x, height / 2.0 + shake_y)
    ctx.scale(state.zoom, state.zoom)
    ctx.translate(-cx, -cy)


class camera_view:
    """Context manager: `with camera_view(ctx, state, w, h, t): ...`"""

    def __init__(self, ctx, state: CameraState, width: int, height: int, t: float = 0.0):
        self.ctx = ctx
        self.state = state
        self.width = width
        self.height = height
        self.t = t

    def __enter__(self):
        self.ctx.save()
        apply_camera(self.ctx, self.state, self.width, self.height, self.t)
        return self.ctx

    def __exit__(self, *exc):
        self.ctx.restore()
        return False
