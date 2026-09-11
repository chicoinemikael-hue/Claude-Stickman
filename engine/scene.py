"""
Composites one scene into pixels: background, characters (via
timeline.py), effects, camera movement, and scene-level text.

render.py drives this: for a validated scene dict (storyboard.py) it
builds a SceneRenderer once, then calls draw_frame(ctx, t, ...) once
per output frame.

Draw order per frame:
  [inside the camera transform -- pans/zooms/shakes with the scene]
  1. background
  2. effects
  3. characters (back-to-front by ground y, so someone standing
     "lower" on screen -- closer to camera -- draws in front)
  4. speech bubbles (anchored to a character's head)
  [outside the camera transform -- fixed on screen]
  5. title / date stamp / caption text
  6. fade-to/from-black transition overlay, if this scene uses one
"""

import engine.background as background
import engine.map_scene as map_scene
import engine.text as text
import engine.effects as effects
from engine.camera import CameraState, camera_view, blend_camera
from engine.pose_blend import ease_in_out
from engine.character import Character
from engine.rig import draw_stickman
from engine.timeline import CharacterTimeline

DEFAULT_CAMERA = CameraState(50.0, 50.0, 1.0, 0.0)
TRANSITION_DURATION = 0.45


class SceneRenderer:
    def __init__(self, scene: dict, char_defs: dict):
        self.scene = scene
        self.timelines = {
            name: CharacterTimeline(char_defs[name], cdef)
            for name, cdef in scene["characters"].items()
        }
        self.char_defs = char_defs

    def camera_at(self, t: float) -> CameraState:
        keyframes = self.scene["camera"]
        if not keyframes:
            return DEFAULT_CAMERA
        if t <= keyframes[0]["t"]:
            kf = keyframes[0]
            return CameraState(kf["x"], kf["y"], kf["zoom"], kf["shake"])
        if t >= keyframes[-1]["t"]:
            kf = keyframes[-1]
            return CameraState(kf["x"], kf["y"], kf["zoom"], kf["shake"])
        for a, b in zip(keyframes, keyframes[1:]):
            if a["t"] <= t <= b["t"]:
                span = b["t"] - a["t"]
                progress = (t - a["t"]) / span if span > 0 else 1.0
                state_a = CameraState(a["x"], a["y"], a["zoom"], a["shake"])
                state_b = CameraState(b["x"], b["y"], b["zoom"], b["shake"])
                return blend_camera(state_a, state_b, ease_in_out(progress))
        return DEFAULT_CAMERA

    def _draw_background(self, ctx, w, h):
        bg = self.scene["background"]
        if isinstance(bg, dict):
            background.draw_custom_image(ctx, w, h, bg["image"])
        elif bg == "map":
            map_scene.draw_stylized_map(ctx, w, h)
        else:
            background.draw_preset(ctx, w, h, bg)

    def _draw_map_annotations(self, ctx, w, h, t):
        for label in self.scene["map_labels"]:
            map_scene.draw_map_label(ctx, w, h, label["x"], label["y"], label["text"])
        for arrow in self.scene["map_arrows"]:
            if t < arrow["t"]:
                continue
            progress = min((t - arrow["t"]) / arrow["duration"], 1.0) if arrow["duration"] > 0 else 1.0
            map_scene.draw_map_arrow(
                ctx, w, h, (arrow["from_x"], arrow["from_y"]), (arrow["to_x"], arrow["to_y"]),
                progress=progress,
            )

    def _draw_effects(self, ctx, w, h, t):
        for effect in self.scene["effects"]:
            if not (effect["t"] <= t <= effect["t"] + effect["duration"]):
                continue
            local_t = t - effect["t"]
            etype = effect["type"]
            if etype == "flying_arrows":
                effects.draw_flying_arrows(
                    ctx, w, h, (effect["x"], effect["y"]), (effect["to_x"], effect["to_y"]),
                    local_t, count=int(effect.get("count", 5)), duration=effect["duration"],
                )
            elif etype == "falling_coins":
                effects.draw_falling_coins(
                    ctx, w, h, effect["x"], effect["y"], local_t,
                    count=int(effect.get("count", 10)), duration=effect["duration"],
                )
            elif etype == "crumbling_building":
                effects.draw_crumbling_building(
                    ctx, w, h, effect["x"], effect["y"], local_t,
                    width_pct=float(effect.get("width_pct", 26)),
                    height_pct=float(effect.get("height_pct", 30)),
                    duration=effect["duration"],
                )
            else:
                effects.EFFECTS[etype](ctx, w, h, effect["x"], effect["y"], local_t,
                                        scale=float(effect.get("scale", 1.0)))

    def _draw_characters(self, ctx, w, h, t):
        resolved = []
        for name, timeline in self.timelines.items():
            state = timeline.state_at(t)
            character = Character(
                name=name, color=timeline.color, scale=timeline.scale,
                facing=state["facing"], label=timeline.label,
                x_pct=state["x"], y_pct=state["y"],
                pose=state["pose"], expression=state["expression"],
                props=state["props"], costume=state["costume"],
                costume_color=state["costume_color"],
            )
            character.resolve(w, h)
            resolved.append((character, state["speech"]))

        resolved.sort(key=lambda pair: pair[0].y_px)

        for character, _ in resolved:
            draw_stickman(ctx, character, character.pose)

        for character, speech in resolved:
            if speech:
                head_y = character.y_px - character.height_px * 0.85
                text.draw_speech_bubble(ctx, w, h, speech, character.x_px, head_y)

    def _draw_text(self, ctx, w, h, t):
        captions = [item for item in self.scene["text"] if item["type"] == "caption"]
        for item in self.scene["text"]:
            duration = item["duration"]
            if duration is not None:
                end_t = item["t"] + duration
            elif item["type"] == "caption":
                later = [c["t"] for c in captions if c["t"] > item["t"]]
                end_t = min(later) if later else self.scene["duration"]
            else:
                end_t = self.scene["duration"]
            if not (item["t"] <= t <= end_t):
                continue
            if item["type"] == "title":
                text.draw_title(ctx, w, h, item["text"])
            elif item["type"] == "date_stamp":
                text.draw_date_stamp(ctx, w, h, item["text"])
            elif item["type"] == "caption":
                text.draw_caption(ctx, w, h, item["text"])

    def _draw_transition_overlay(self, ctx, w, h, t):
        duration = self.scene["duration"]
        alpha = 0.0
        if self.scene["transition_in"] == "fade" and t < TRANSITION_DURATION:
            alpha = max(alpha, 1.0 - t / TRANSITION_DURATION)
        if self.scene["transition_out"] == "fade" and t > duration - TRANSITION_DURATION:
            alpha = max(alpha, 1.0 - (duration - t) / TRANSITION_DURATION)
        if alpha > 0:
            ctx.set_source_rgba(0, 0, 0, min(alpha, 1.0))
            ctx.rectangle(0, 0, w, h)
            ctx.fill()

    def draw_frame(self, ctx, t: float, w: int, h: int):
        cam = self.camera_at(t)
        with camera_view(ctx, cam, w, h, t):
            self._draw_background(ctx, w, h)
            self._draw_map_annotations(ctx, w, h, t)
            self._draw_effects(ctx, w, h, t)
            self._draw_characters(ctx, w, h, t)

        self._draw_text(ctx, w, h, t)
        self._draw_transition_overlay(ctx, w, h, t)
