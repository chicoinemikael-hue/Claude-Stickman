"""
Loads and validates a storyboard YAML file.

This module's job is to turn a YAML file into plain Python
dicts/lists (with defaults filled in and obvious mistakes caught
early) -- it doesn't do any drawing or animation itself. See
FORMAT.md for the full storyboard format with examples, and
timeline.py / scene.py for how a loaded storyboard gets turned into
video frames.

Whenever something in the file doesn't make sense, we raise a
StoryboardError with a message that names the scene and, where
possible, the character/action involved, plus a suggestion -- so a
beginner can find and fix the problem without reading a traceback.
"""

import os
import yaml

from engine.poses import POSES, CYCLES
from engine.props import ALL_PROPS
from engine.costumes import COSTUMES
from engine.expressions import EXPRESSIONS
from engine.background import PRESETS as BACKGROUND_PRESETS
from engine.effects import EFFECTS


class StoryboardError(Exception):
    """A problem in the storyboard file itself (not a bug in the
    engine). render.py catches this and prints it without a
    traceback."""


ACTION_TYPES = {
    "enter", "exit", "move_to", "pose", "expression", "say",
    "pickup", "drop", "costume", "fall_down",
}
TEXT_TYPES = {"title", "date_stamp", "caption"}
TRANSITIONS = {"cut", "fade"}

DEFAULT_FPS = 30
DEFAULT_RESOLUTION = (1080, 1920)


def parse_color(value, where):
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return tuple(float(c) for c in value)
    if isinstance(value, str) and value.startswith("#") and len(value) == 7:
        try:
            r = int(value[1:3], 16) / 255.0
            g = int(value[3:5], 16) / 255.0
            b = int(value[5:7], 16) / 255.0
            return (r, g, b)
        except ValueError:
            pass
    raise StoryboardError(
        f'{where}: "{value}" is not a valid color. Use a hex code like "#2E5AA8" '
        f"or a list like [0.18, 0.35, 0.66]."
    )


def _require(d, key, where, expected="a value"):
    if key not in d:
        raise StoryboardError(f'{where}: missing required field "{key}" ({expected}).')
    return d[key]


def _check_choice(value, choices, where, field):
    if value not in choices:
        available = ", ".join(sorted(choices))
        raise StoryboardError(
            f'{where}: unknown {field} "{value}". Available: {available}.'
        )


def load_storyboard(path: str) -> dict:
    if not os.path.exists(path):
        raise StoryboardError(f'Storyboard file not found: "{path}".')

    with open(path, "r") as f:
        try:
            raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise StoryboardError(
                f"Couldn't parse {path} as YAML -- there's likely a formatting "
                f"mistake (check indentation and colons). Details: {e}"
            )

    if not isinstance(raw, dict):
        raise StoryboardError(f"{path}: the file must be a YAML mapping (key: value pairs) at the top level.")

    board = {
        "fps": raw.get("fps", DEFAULT_FPS),
        "resolution": tuple(raw.get("resolution", DEFAULT_RESOLUTION)),
        "audio": raw.get("audio", {}) or {},
        "characters": {},
        "scenes": [],
    }

    char_defs = raw.get("characters", {}) or {}
    for name, cdef in char_defs.items():
        cdef = cdef or {}
        color = parse_color(cdef.get("color", "#2E5AA8"), f'Character "{name}"')
        board["characters"][name] = {
            "color": color,
            "scale": float(cdef.get("scale", 1.0)),
            "facing": cdef.get("facing", "right"),
            "label": cdef.get("label"),
        }

    scenes_raw = raw.get("scenes")
    if not scenes_raw:
        raise StoryboardError(f'{path}: no "scenes" found -- a storyboard needs at least one scene.')

    for i, scene_raw in enumerate(scenes_raw, start=1):
        where = f"Scene {i}"
        scene = _validate_scene(scene_raw, where, board["characters"])
        board["scenes"].append(scene)

    return board


def _validate_scene(scene_raw, where, known_characters):
    duration = _require(scene_raw, "duration", where, "length of the scene, in seconds")
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        raise StoryboardError(f"{where}: duration must be a number of seconds.")
    if duration <= 0:
        raise StoryboardError(f"{where}: duration must be greater than 0.")

    background = scene_raw.get("background", "rome_city")
    if isinstance(background, dict):
        if "image" not in background:
            raise StoryboardError(f'{where}: a background image entry needs an "image" path, e.g. {{image: my_bg.png}}.')
        if not os.path.exists(background["image"]):
            raise StoryboardError(f'{where}: background image not found: "{background["image"]}".')
    elif isinstance(background, str):
        if background != "map" and background not in BACKGROUND_PRESETS:
            available = ", ".join(sorted(list(BACKGROUND_PRESETS) + ["map"]))
            raise StoryboardError(
                f'{where}: unknown background preset "{background}". Available: {available}. '
                f"Or use your own image: background: {{image: path/to.png}}."
            )
    else:
        raise StoryboardError(f"{where}: background must be a preset name or {{image: path}}.")

    transition_in = scene_raw.get("transition_in", "cut")
    transition_out = scene_raw.get("transition_out", "cut")
    _check_choice(transition_in, TRANSITIONS, where, "transition_in")
    _check_choice(transition_out, TRANSITIONS, where, "transition_out")

    camera = []
    for j, kf in enumerate(scene_raw.get("camera", []) or []):
        t = float(_require(kf, "t", f"{where}, camera keyframe {j + 1}"))
        camera.append({
            "t": t,
            "x": float(kf.get("x", 50.0)),
            "y": float(kf.get("y", 50.0)),
            "zoom": float(kf.get("zoom", 1.0)),
            "shake": float(kf.get("shake", 0.0)),
        })
    camera.sort(key=lambda k: k["t"])

    texts = []
    for j, td in enumerate(scene_raw.get("text", []) or []):
        twhere = f"{where}, text item {j + 1}"
        ttype = _require(td, "type", twhere, "title, date_stamp, or caption")
        _check_choice(ttype, TEXT_TYPES, twhere, "text type")
        text_value = _require(td, "text", twhere)
        texts.append({
            "type": ttype,
            "text": str(text_value),
            "t": float(td.get("t", 0.0)),
            "duration": float(td["duration"]) if "duration" in td else None,
        })

    effects = []
    for j, ed in enumerate(scene_raw.get("effects", []) or []):
        ewhere = f"{where}, effect {j + 1}"
        etype = _require(ed, "type", ewhere)
        _check_choice(etype, set(EFFECTS), ewhere, "effect type")
        _require(ed, "x", ewhere, "x position, 0-100")
        _require(ed, "y", ewhere, "y position, 0-100")
        if etype == "flying_arrows":
            _require(ed, "to_x", ewhere, "target x position, 0-100")
            _require(ed, "to_y", ewhere, "target y position, 0-100")
        effect = dict(ed)
        effect["t"] = float(ed.get("t", 0.0))
        effect["duration"] = float(ed.get("duration", 1.5))
        effects.append(effect)

    characters = {}
    for name, cdef in (scene_raw.get("characters", {}) or {}).items():
        cwhere = f'{where}, character "{name}"'
        if name not in known_characters:
            available = ", ".join(sorted(known_characters)) or "(none defined)"
            raise StoryboardError(
                f'{cwhere}: "{name}" is not defined in the top-level "characters:" '
                f"section. Defined characters: {available}."
            )
        characters[name] = _validate_character_scene(cdef or {}, cwhere)

    return {
        "duration": duration,
        "background": background,
        "transition_in": transition_in,
        "transition_out": transition_out,
        "camera": camera,
        "text": texts,
        "effects": effects,
        "characters": characters,
    }


def _validate_character_scene(cdef, cwhere):
    start = cdef.get("start", {}) or {}
    start_resolved = {
        "x": float(start.get("x", 50.0)),
        "y": float(start.get("y", 80.0)),
        "facing": start.get("facing", "right"),
        "pose": start.get("pose", "stand"),
        "expression": start.get("expression", "neutral"),
        "props": list(start.get("props", []) or []),
        "costume": start.get("costume"),
    }
    _check_pose_name(start_resolved["pose"], cwhere)
    _check_choice(start_resolved["expression"], set(EXPRESSIONS), cwhere, "expression")
    for p in start_resolved["props"]:
        _check_choice(p, set(ALL_PROPS), cwhere, "prop")
    if start_resolved["costume"]:
        _check_choice(start_resolved["costume"], set(COSTUMES), cwhere, "costume")

    actions = []
    for k, action_raw in enumerate(cdef.get("actions", []) or []):
        awhere = f"{cwhere}, action {k + 1}"
        atype = _require(action_raw, "type", awhere, "/".join(sorted(ACTION_TYPES)))
        _check_choice(atype, ACTION_TYPES, awhere, "action type")
        t = float(_require(action_raw, "t", awhere, "when this action starts, in seconds"))
        action = {"type": atype, "t": t, **{k: v for k, v in action_raw.items() if k not in ("type", "t")}}

        if atype in ("enter", "exit"):
            _check_choice(action.get("side"), {"left", "right"}, awhere, "side")
        if atype in ("enter", "move_to"):
            if "x" not in action:
                raise StoryboardError(f'{awhere}: "{atype}" needs an "x" (0-100).')
        if atype == "pose":
            _check_pose_name(_require(action, "pose", awhere), awhere)
        if atype == "expression":
            _check_choice(_require(action, "expression", awhere), set(EXPRESSIONS), awhere, "expression")
        if atype == "say":
            _require(action, "text", awhere)
        if atype in ("pickup", "drop"):
            _check_choice(_require(action, "prop", awhere), set(ALL_PROPS), awhere, "prop")
        if atype == "costume" and action.get("costume"):
            _check_choice(action["costume"], set(COSTUMES), awhere, "costume")

        actions.append(action)

    actions.sort(key=lambda a: a["t"])
    return {"start": start_resolved, "actions": actions}


def _check_pose_name(name, where):
    if name not in POSES and name not in CYCLES:
        available = ", ".join(sorted(set(POSES) | set(CYCLES)))
        raise StoryboardError(f'{where}: unknown pose "{name}". Available poses: {available}.')
