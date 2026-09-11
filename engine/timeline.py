"""
Turns one validated scene (see storyboard.py) into "what does
everything look like at time t" -- the actual animation logic.

For each character, a list of timed actions (enter, move_to, pose,
say, pickup, ...) is turned into a handful of independent tracks
(position+pose, expression, props/costume, speech bubble). Querying
`CharacterTimeline.state_at(t)` walks those tracks and returns a
fully resolved snapshot: x/y, facing, a blended Pose, expression,
props, costume, and any currently-showing speech text.

This is where "move to a position" becomes an automatic walk/run
cycle, and where pose changes get their smooth eased transition.
"""

import math

from engine.poses import get_pose, is_cycle, get_cycle, STAND, FALL_OVER
from engine.pose_blend import blend_poses, ease_in_out

STRIDE_DURATION = {"walk": 0.55, "run": 0.32}
RUN_SPEED_THRESHOLD = 22.0  # percent-of-screen per second
OFFSCREEN_LEFT = -14.0
OFFSCREEN_RIGHT = 114.0
SETTLE_DURATION = 0.25  # short blend from a walk cycle back to standing


def _lerp(a, b, t):
    return a + (b - a) * t


class CharacterTimeline:
    def __init__(self, char_def, scene_char):
        self.color = char_def["color"]
        self.scale = char_def["scale"]
        self.label = char_def["label"]
        self.start = scene_char["start"]
        self.actions = scene_char["actions"]

        self._build_movement_segments()
        self._build_expression_events()
        self._build_prop_events()
        self._build_costume_events()
        self._build_speech_events()

    # -- movement/pose segments -------------------------------------------------
    def _build_movement_segments(self):
        segments = []
        x, y = self.start["x"], self.start["y"]
        facing = self.start["facing"]
        last_pose_name = self.start["pose"]

        for action in self.actions:
            t = action["t"]
            atype = action["type"]

            if atype == "enter":
                x0 = OFFSCREEN_LEFT if action["side"] == "left" else OFFSCREEN_RIGHT
                y0 = action.get("y", y)
                x1 = action["x"]
                y1 = action.get("y", y0)
                duration = float(action.get("duration", 1.0))
                new_facing = action.get("facing") or ("right" if x1 >= x0 else "left")
                segments.append({
                    "kind": "move", "t_start": t, "duration": duration,
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1, "facing": new_facing,
                })
                x, y, facing = x1, y1, new_facing

            elif atype == "move_to":
                x0, y0 = x, y
                x1 = action["x"]
                y1 = action.get("y", y0)
                duration = float(action.get("duration", 1.0))
                new_facing = action.get("facing") or (
                    facing if x1 == x0 else ("right" if x1 > x0 else "left")
                )
                segments.append({
                    "kind": "move", "t_start": t, "duration": duration,
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1, "facing": new_facing,
                })
                x, y, facing = x1, y1, new_facing

            elif atype == "exit":
                x0, y0 = x, y
                x1 = OFFSCREEN_LEFT if action["side"] == "left" else OFFSCREEN_RIGHT
                y1 = y0
                duration = float(action.get("duration", 1.0))
                new_facing = action.get("facing") or ("right" if x1 >= x0 else "left")
                segments.append({
                    "kind": "move", "t_start": t, "duration": duration,
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1, "facing": new_facing,
                })
                x, y, facing = x1, y1, new_facing

            elif atype == "pose":
                duration = float(action.get("duration", 0.4))
                segments.append({
                    "kind": "pose", "t_start": t, "duration": duration,
                    "x0": x, "y0": y, "x1": x, "y1": y, "facing": facing,
                    "pose_name": action["pose"], "from_pose_name": last_pose_name,
                })
                last_pose_name = action["pose"]

            elif atype == "fall_down":
                duration = float(action.get("duration", 0.6))
                segments.append({
                    "kind": "pose", "t_start": t, "duration": duration,
                    "x0": x, "y0": y, "x1": x, "y1": y, "facing": facing,
                    "pose_name": "fall_over", "from_pose_name": last_pose_name,
                })
                last_pose_name = "fall_over"

        segments.sort(key=lambda s: s["t_start"])
        self.segments = segments

    def _pose_for(self, name, phase_time):
        if is_cycle(name):
            stride = STRIDE_DURATION.get(name, 0.5)
            return get_cycle(name).sample(phase_time / stride)
        return get_pose(name)

    def _cycle_name_for_speed(self, seg):
        distance = math.hypot(seg["x1"] - seg["x0"], seg["y1"] - seg["y0"])
        speed = distance / seg["duration"] if seg["duration"] > 0 else 0
        return "run" if speed > RUN_SPEED_THRESHOLD else "walk"

    def _resolve_movement(self, t):
        """Return (x, y, facing, pose) from the movement/pose segments."""
        start_pose = get_pose(self.start["pose"]) if not is_cycle(self.start["pose"]) \
            else self._pose_for(self.start["pose"], 0.0)

        if not self.segments or t < self.segments[0]["t_start"]:
            return self.start["x"], self.start["y"], self.start["facing"], start_pose

        active = self.segments[0]
        for seg in self.segments:
            if seg["t_start"] <= t:
                active = seg
            else:
                break

        t_end = active["t_start"] + active["duration"]
        local_t = t - active["t_start"]

        if active["kind"] == "move":
            progress = min(max(local_t / active["duration"], 0.0), 1.0) if active["duration"] > 0 else 1.0
            x = _lerp(active["x0"], active["x1"], progress)
            y = _lerp(active["y0"], active["y1"], progress)
            cycle_name = self._cycle_name_for_speed(active)

            if t <= t_end:
                pose = self._pose_for(cycle_name, local_t)
            else:
                settle_t = t - t_end
                cycle_pose = self._pose_for(cycle_name, active["duration"])
                if settle_t < SETTLE_DURATION:
                    pose = blend_poses(cycle_pose, STAND, settle_t / SETTLE_DURATION)
                else:
                    pose = STAND
            return x, y, active["facing"], pose

        else:  # kind == "pose"
            from_pose = self._pose_for(active["from_pose_name"], active["duration"])
            to_pose = self._pose_for(active["pose_name"], 0.0)
            progress = min(max(local_t / active["duration"], 0.0), 1.0) if active["duration"] > 0 else 1.0
            pose = blend_poses(from_pose, to_pose, progress)
            return active["x0"], active["y0"], active["facing"], pose

    # -- simple piecewise tracks --------------------------------------------
    def _build_expression_events(self):
        events = [(-1.0, self.start["expression"])]
        for a in self.actions:
            if a["type"] == "expression":
                events.append((a["t"], a["expression"]))
        events.sort(key=lambda e: e[0])
        self._expression_events = events

    def _resolve_expression(self, t):
        current = self._expression_events[0][1]
        for et, val in self._expression_events:
            if et <= t:
                current = val
        return current

    def _build_prop_events(self):
        events = [(-1.0, "init", list(self.start["props"]))]
        for a in self.actions:
            if a["type"] == "pickup":
                events.append((a["t"], "pickup", a["prop"]))
            elif a["type"] == "drop":
                events.append((a["t"], "drop", a["prop"]))
        events.sort(key=lambda e: e[0])
        self._prop_events = events

    def _resolve_props(self, t):
        props = []
        for et, kind, val in self._prop_events:
            if et > t:
                break
            if kind == "init":
                props = list(val)
            elif kind == "pickup" and val not in props:
                props.append(val)
            elif kind == "drop" and val in props:
                props.remove(val)
        return props

    def _build_costume_events(self):
        events = [(-1.0, self.start["costume"], None)]
        for a in self.actions:
            if a["type"] == "costume":
                events.append((a["t"], a.get("costume"), a.get("color")))
        events.sort(key=lambda e: e[0])
        self._costume_events = events

    def _resolve_costume(self, t):
        costume, color = self._costume_events[0][1], self._costume_events[0][2]
        for et, c, col in self._costume_events:
            if et <= t:
                costume, color = c, col
        color_rgb = None
        if color:
            from engine.storyboard import parse_color
            color_rgb = parse_color(color, "costume color")
        return costume, color_rgb

    def _build_speech_events(self):
        events = []
        for a in self.actions:
            if a["type"] == "say":
                text = a["text"]
                duration = float(a.get("duration", max(1.8, 0.07 * len(text))))
                events.append((a["t"], a["t"] + duration, text))
        self._speech_events = events

    def _resolve_speech(self, t):
        active = None
        for t_start, t_end, text in self._speech_events:
            if t_start <= t <= t_end:
                active = text
        return active

    # -- public API -----------------------------------------------------------
    def state_at(self, t: float) -> dict:
        x, y, facing, pose = self._resolve_movement(t)
        costume, costume_color = self._resolve_costume(t)
        return {
            "x": x, "y": y, "facing": facing, "pose": pose,
            "expression": self._resolve_expression(t),
            "props": self._resolve_props(t),
            "costume": costume,
            "costume_color": costume_color,
            "speech": self._resolve_speech(t),
        }
