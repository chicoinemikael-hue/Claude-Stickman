"""
The Character class: a stickman's appearance and current state.

A Character doesn't know anything about storyboards or timelines --
it just holds the visual settings (color, scale, facing, label) and
whatever pose/expression it should be drawn in *right now*. The
timeline (engine/timeline.py, added in a later step) is what decides
which pose a character should be in at a given moment and updates
these fields frame by frame.
"""

from dataclasses import dataclass, field

from engine.poses import STAND

# A character at scale=1.0 is this tall, in pixels, on a 1080x1920 frame.
BASE_HEIGHT_PX = 560.0


@dataclass
class Character:
    name: str
    color: tuple = (0.20, 0.30, 0.75)   # RGB 0..1
    scale: float = 1.0
    facing: str = "right"               # "left" or "right"
    label: str = None                   # optional name shown above head

    # Position as percent of the screen (0-100), matching the
    # storyboard format. x/y are the point where the feet touch.
    x_pct: float = 50.0
    y_pct: float = 80.0

    pose: object = field(default_factory=lambda: STAND)
    expression: str = "neutral"

    # Costume worn on the torso ("toga", "cape", or None) and props
    # held/worn (e.g. ["roman_helmet", "sword", "round_shield"]).
    costume: str = None
    costume_color: tuple = None
    props: list = field(default_factory=list)

    # --- resolved screen-space values, set by resolve() before drawing ---
    x_px: float = 0.0
    y_px: float = 0.0
    height_px: float = 0.0

    def resolve(self, frame_width: int, frame_height: int):
        """Compute pixel position/size from percent position + scale.

        Call this once per frame, after x_pct/y_pct/scale are set for
        that frame, and before draw_stickman().
        """
        self.x_px = self.x_pct / 100.0 * frame_width
        self.y_px = self.y_pct / 100.0 * frame_height
        self.height_px = BASE_HEIGHT_PX * self.scale
