# CLAUDE.md

Project map for Claude Code sessions working on this repo. For the
user-facing install/usage guide, see `README.md`. For the storyboard
YAML format, see `FORMAT.md` (keep it in sync with `storyboard.py` —
it's meant to be pasted into a chat to generate new storyboards, so it
must exactly match what the validator accepts).

## What this is

A tool that renders stickman-animated YouTube Shorts/TikTok videos
(vertical, 1080x1920, 30fps, H.264) from a YAML storyboard file. First
use case: history explainer videos (`storyboards/fall_of_rome_demo.yaml`
is the reference example). Built for a non-programmer end user, so
error messages, docs, and defaults all favor being beginner-friendly
over flexible/configurable.

Stack: Python + **pycairo** (anti-aliased 2D drawing) + **ffmpeg**
(subprocess, PNG sequence -> H.264 MP4). No GPU, no web server, no
database — it's a CLI that reads a YAML file and writes an MP4.

## How to run things

```
pip install -r requirements.txt
python render.py storyboards/fall_of_rome_demo.yaml [--preview] [--frame N] [--scene N]
```

There's no automated test suite (a couple of lightweight sanity
checks live in `tests/`, but they're not comprehensive). The actual
way to verify a change is visual: render a still with `--frame` or a
short clip, and **look at the output** — this project was built by
rendering after every change and inspecting the PNG/MP4 output, and
that's still the right workflow. `engine/renderer.render_still()` is
the fastest way to spot-check a pose/character/scene in a one-off
Python snippet without going through a full storyboard file.

## Module map (`engine/`)

Rough dependency order (each mostly depends only on modules above it):

- **`rig.py`** — the skeleton. `Pose` is a dataclass of ~13 joint
  angles (absolute, degrees, 0=up/clockwise-positive; see the
  docstring at the top of the file for the full convention).
  `compute_points()`/`layout_points()` do forward kinematics into a
  local, height-normalized point space, auto-grounding the pose (feet
  always land at y=0 in local space, whatever the pose) and mirroring
  for `facing: left`. `draw_stickman()` draws bones, joints, head,
  face, costume, props, and the name label, in that back-to-front
  layered order — this is the only place that knows the full draw
  order.
- **`expressions.py`** — face-drawing functions keyed by expression
  name. Faces are drawn "toward" `facing`, not front-on.
- **`poses.py`** — the actual pose *library* (as opposed to `rig.py`'s
  generic `Pose` machinery). Static poses are just `Pose(...)`
  literals. Looping poses (walk/run/wave/talk) are `PoseCycle`s: a few
  keyframe `Pose`s with relative weights. **This is the one place to
  add a new pose or cycle** — nothing elsewhere needs to change.
- **`pose_blend.py`** — easing functions, `blend_poses()` (shortest-
  path angle interpolation between two poses), and `PoseCycle`
  (keyframe loop sampling). Pure math, no drawing.
- **`character.py`** — `Character` dataclass: appearance (color,
  scale, facing, label) + current pose/expression/props/costume +
  position as x/y **percent** (0-100, feet position). `resolve()`
  turns percent position + scale into pixel position/size right
  before drawing a frame — call it before `draw_stickman()`.
- **`props.py`** / **`costumes.py`** — small drawing functions for
  held/worn items. Props attach to a hand or the head (registered in
  `HEAD_PROPS`/`HAND_PROPS`); costumes (toga/cape) need more of the
  rig's joint layout to drape correctly, so they get the full
  screen-space points dict and draw in two passes (`back` before
  limbs, `front` after the torso but before arms) — see `rig.py`'s
  `draw_stickman()` for exactly where each hook fires.
- **`background.py`** — scenery pieces (sky/ground/hills/columns/
  temple/wall/arch/palace/tents/trees/sea) as plain cairo drawing
  functions on the full frame, plus `PRESETS` combining them, plus
  `draw_custom_image()` for a user's own PNG background.
- **`map_scene.py`** — the stylized map background plus
  `draw_map_label()`/`draw_map_arrow()`, wired into storyboards via
  `background: map` + `map_labels`/`map_arrows` (see `scene.py`).
- **`text.py`** — title/date-stamp/caption/speech-bubble drawing, all
  safe-margin aware (`SAFE_TOP_PCT`/`SAFE_BOTTOM_PCT` = 15/85).
- **`effects.py`** — fire/smoke/dust/arrows/coins/crumbling-building.
  Each is a pure function of `t` (seconds since the effect started) —
  no internal state — using a per-particle `random.Random(seed)` so
  the same `t` always renders identically (needed for `--frame` to
  match what the real render would show).
- **`camera.py`** — `CameraState` + `apply_camera()`/`camera_view()`
  (a `with`-statement wrapper). Applied around
  background+effects+characters; text/UI is drawn *after* the
  `camera_view` block exits, so it stays fixed on screen regardless of
  camera movement.
- **`audio.py`** — post-processes the silent rendered MP4 with ffmpeg
  to mix in voiceover/music (music ducked under voiceover). Doesn't
  touch video frames at all; `render.py` calls it after
  `renderer.render_video()`.
- **`renderer.py`** — the actual pixel/video output. `render_still()`
  for one-off PNGs, `render_video()` for the PNG-sequence -> ffmpeg
  pipeline (writes frames to a temp dir, shells out to ffmpeg, cleans
  up).
- **`storyboard.py`** — loads + validates a storyboard YAML into
  plain dicts, filling in defaults. This is the *only* place that
  should raise `StoryboardError` (caught in `render.py` and printed
  without a traceback) — validate early here rather than letting a
  malformed storyboard cause a confusing crash deeper in
  `timeline.py`/`scene.py`. Every error message should name the
  scene/character/action and, where relevant, list valid options.
- **`timeline.py`** — turns one scene's per-character action list into
  continuous state at any time `t`: `CharacterTimeline.state_at(t)`.
  Movement actions (`enter`/`move_to`/`exit`) become "segments" with
  an automatic walk/run cycle (picked by speed,
  `RUN_SPEED_THRESHOLD`); `pose`/`fall_down` become blend segments.
  Expression/props/costume/speech are simpler independent piecewise
  tracks. This is the module to touch if you're adding a new action
  type.
- **`scene.py`** — composites one scene per frame: background -> map
  annotations -> effects -> characters (sorted back-to-front by `y`)
  -> speech bubbles, all inside the camera transform; then text
  overlays and the fade-transition overlay outside it (fixed screen
  space). `SceneRenderer.draw_frame(ctx, t, w, h)` is the entry point
  `render.py` calls once per output frame.

`render.py` (project root) is the CLI: loads the storyboard, builds a
`SceneRenderer` per scene, and for a normal render maps global video
time -> (scene index, local time) each frame, calling that scene's
`draw_frame()`. `--frame`/`--scene`/`--preview` are handled here by
changing what gets rendered, not by engine-level flags.

## Design conventions worth preserving

- **Positions are always percent (0-100), never pixels**, at the
  storyboard/character/text/effect API level. Pixel conversion only
  happens right before drawing (`Character.resolve()`,
  `text.py`/`effects.py` multiplying by `w`/`h` internally).
- **Angles in `Pose` are absolute, not parent-relative.** This was a
  deliberate simplification over a "real" kinematic chain — it makes
  poses easy to hand-author and blend (each field interpolates
  independently), at the cost of not being physically hierarchical.
  Don't change this without updating every hand-authored pose in
  `poses.py`.
- **Auto-grounding.** `layout_points()` always shifts a pose so its
  lowest foot/toe point sits at local y=0. This is why poses don't
  need individually tuned hip heights to "stand on the ground" — rely
  on it rather than hand-adjusting `hip_y_offset` to fix ground
  contact.
- **Effects/poses must be deterministic in `t`.** No `random.random()`
  — always a seeded `random.Random(seed)` — so a `--frame` still
  matches the equivalent moment in a full video render.
- **`StoryboardError` only from `storyboard.py`.** Keep validation
  (and its friendly, specific messages) centralized there rather than
  letting bad input surface as an exception from deep in
  `timeline.py`/`scene.py`.
- **One place per extensible thing.** Adding a pose only touches
  `poses.py`; a prop only `props.py`; a costume only `costumes.py`; a
  background preset only `background.py`; an effect only
  `effects.py` (plus a small dispatch case in `scene.py`'s
  `_draw_effects()` if its call signature doesn't match the plain
  `(ctx, w, h, x, y, t, ...)` shape most effects use). If a change
  requires touching many files, it's probably not following this
  pattern — reconsider.
- **Render, then look.** This whole engine was built by rendering
  after every change (`render_still()` for a single pose/scene check,
  a short `render_video()` clip for motion/timing, contact sheets via
  PIL for comparing several frames at once) and visually inspecting
  the PNG/MP4. Keep doing that for new work — angle/color/timing bugs
  are much faster to catch by looking than by reasoning about the
  numbers.

## Known simplifications (fine for now, worth knowing about)

- The `map` background is a plain stylized landmass, not
  geographically accurate (explicitly out of scope for v1 — see
  `map_scene.py`'s docstring). Real maps go through
  `background: {image: ...}` instead.
- Costumes (toga/cape) don't cloth-simulate — they're a fixed shape
  relative to shoulder/hip joints, so they can look slightly odd
  during large/fast pose changes (e.g. a toga during a full walk
  cycle). Cosmetic, not a correctness bug.
- No automated visual regression tests — verification is manual
  render-and-look, as above. `tests/test_rig.py` only covers basic
  kinematics sanity checks.
