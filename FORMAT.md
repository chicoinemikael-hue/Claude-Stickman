# Storyboard format reference

This document fully describes the storyboard YAML format used by
`render.py`. It's written so you can paste this whole file into a
Claude chat along with a description of the video you want ("write me
a storyboard about the Punic Wars") and get back a working
`.yaml` file.

If you're a person reading this instead: see `README.md` for how to
actually install and run things. This file is just the format spec.

## The big picture

A storyboard file is one YAML file describing one video. It has two
top-level parts:

- **`characters`**: the cast, and what each one looks like.
- **`scenes`**: a list of scenes, played back to back. Each scene has
  a background, camera moves, on-screen text, effects, and a list of
  timed actions for each character appearing in it.

All positions (`x`, `y`) are **percent of the screen, 0-100** — not
pixels. `x: 0` is the left edge, `x: 100` is the right edge, `y: 0` is
the top, `y: 100` is the bottom. For a character, `x`/`y` is where
their **feet** touch the ground.

Keep important text and action out of **`y` 0-15 and `y` 85-100** —
Shorts/TikTok draw their own UI over the top and bottom ~15% of the
screen. The built-in text elements (title, date stamp, caption)
already default to safe positions, so you mostly only need to think
about this for where you place characters and props.

## Minimal example

```yaml
characters:
  marcus:
    color: "#2E5AA8"
    label: Marcus

scenes:
  - duration: 4
    background: rome_city
    text:
      - {type: title, text: "Marcus Says Hello"}
    characters:
      marcus:
        start: {x: 50, y: 80}
        actions:
          - {t: 0.5, type: pose, pose: wave}
          - {t: 1.0, type: say, text: "Hello, Rome!"}
```

Run it with `python render.py your_file.yaml`.

## Top level fields

```yaml
fps: 30                    # optional, default 30
resolution: [1080, 1920]   # optional, default [1080, 1920] (vertical)

audio:                     # optional
  voiceover: audio/voice.mp3      # optional path to a narration track
  music: audio/music.mp3          # optional path to background music (loops)
  music_volume: 0.55              # music volume when there's no voiceover (0-1)
  duck_volume: 0.16               # music volume while the voiceover plays (0-1)

characters:                # required: the cast (see below)
  ...

scenes:                    # required: at least one scene (see below)
  - ...
```

Audio file paths are relative to wherever you run `python render.py`
from (normally the project folder).

## Characters (the cast)

Every character who appears anywhere needs an entry here first:

```yaml
characters:
  marcus:
    color: "#2E5AA8"     # hex code, or [r, g, b] with each 0-1
    scale: 1.0            # optional, default 1.0. Use e.g. 0.6 for a kid, 1.4 for a giant
    facing: right         # optional, default "right". Starting facing direction
    label: Marcus         # optional. Shown above their head. Omit for no label.
```

The character name (`marcus` here) is just an internal ID you'll use
in scenes — it's never shown on screen. The `label` is what's shown
(or nothing, if you leave it out).

## Scenes

```yaml
scenes:
  - duration: 5                    # required, seconds
    background: rome_city          # required, see "Backgrounds" below
    transition_in: cut             # optional: "cut" (default) or "fade"
    transition_out: cut            # optional: "cut" (default) or "fade"
    camera: [...]                  # optional, see "Camera" below
    text: [...]                    # optional, see "Text" below
    effects: [...]                 # optional, see "Effects" below
    map_labels: [...]              # optional, only meaningful with background: map
    map_arrows: [...]              # optional, only meaningful with background: map
    characters:                    # optional: who appears + what they do
      marcus:
        start: {...}
        actions: [...]
```

### Backgrounds

Either a built-in preset name:

```yaml
background: rome_city
```

Available presets: `rome_city`, `throne_room`, `battlefield`,
`barbarian_camp`, and `map` (a simple stylized territory map — see
"Map labels and arrows" below).

Or your own image, scaled to fill the frame:

```yaml
background: {image: my_backgrounds/senate.png}
```

### Camera

A list of keyframes; the camera smoothly moves between them. `x`/`y`
are what point of the scene the camera centers on (percent, same
0-100 system). `zoom` 1.0 is normal, bigger numbers zoom in. `shake`
0-1 adds a shaky-camera effect (0 = none).

```yaml
camera:
  - {t: 0, x: 50, y: 50, zoom: 1.0}
  - {t: 3, x: 40, y: 45, zoom: 1.3, shake: 0.3}
```

If you don't include a `camera` list, the scene uses a static camera
(centered, no zoom). You don't need a keyframe at `t: 0` — the camera
holds at the first keyframe's values until its `t`.

### Text

Three kinds, each a list item with a `t` (when it appears, seconds
into the scene) and optional `duration` (how long it stays; if you
leave it out, a title/date_stamp stays for the rest of the scene, and
a caption stays until the next caption starts, or the scene ends):

```yaml
text:
  - {type: title, text: "The Fall of Rome", t: 0, duration: 2.5}
  - {type: date_stamp, text: "410 AD", t: 0.3}
  - {type: caption, text: "The Visigoths storm the city.", t: 0.6}
  - {type: caption, text: "Rome falls for the first time in 800 years.", t: 3.5}
```

- `title`: a big title card, centered high on screen.
- `date_stamp`: a small badge, e.g. "410 AD" — keep it short (a few
  words); it shrinks to fit but isn't meant for full sentences.
- `caption`: a bottom caption line, for narration-style text.

### Effects

Each has a `type`, a position, a `t` (when it starts, seconds into
the scene), and a `duration`:

```yaml
effects:
  - {type: fire, x: 20, y: 80, t: 0, duration: 3, scale: 1.2}
  - {type: smoke, x: 20, y: 78, t: 0, duration: 3, scale: 1.2}
  - {type: dust_cloud, x: 50, y: 82, t: 1.0, duration: 1.5, scale: 1.5}
  - {type: falling_coins, x: 50, y: 30, t: 0.5, duration: 2, count: 12}
  - {type: flying_arrows, x: 10, y: 55, to_x: 90, to_y: 60, t: 0.5, duration: 1.0, count: 6}
  - {type: crumbling_building, x: 50, y: 80, t: 0.5, duration: 2.5, width_pct: 30, height_pct: 32}
```

- `fire`, `smoke`, `dust_cloud`: `scale` (default 1.0) makes them
  bigger/smaller.
- `falling_coins`: `count` (default 10).
- `flying_arrows`: needs `to_x`/`to_y` (where they fly to); `count`
  (default 5).
- `crumbling_building`: `width_pct`/`height_pct` (default 26/30) size
  the building; it shakes, then breaks apart.

### Map labels and arrows

Only meaningful when `background: map`. Labels are plain text at a
spot; arrows animate drawing themselves from one point to another
(handy for showing an invasion or migration):

```yaml
background: map
map_labels:
  - {text: "ROME", x: 30, y: 60}
  - {text: "GOTHS", x: 55, y: 45}
map_arrows:
  - {from_x: 76, from_y: 42, to_x: 54, to_y: 50, t: 0.5, duration: 1.4}
```

`map_arrows` fields: `from_x`/`from_y`/`to_x`/`to_y` required, `t`
(default 0) and `duration` (default 1.5) control when/how fast it
draws.

The built-in map is a plain stylized landmass (this project doesn't
aim for geographic accuracy) — if you want a real map, use
`background: {image: my_map.png}` instead and place `map_labels`/
`map_arrows` to match your image.

### Characters in a scene

For each character who appears in a scene:

```yaml
characters:
  marcus:
    start:
      x: 50                  # optional, default 50
      y: 80                  # optional, default 80
      facing: right          # optional, default "right"
      pose: stand             # optional, default "stand"
      expression: neutral     # optional, default "neutral"
      props: [laurel_wreath]  # optional, default []
      costume: toga            # optional, default none
    actions:
      - {t: 0.5, type: pose, pose: cheer}
      - ...
```

`start` is where/how they look at the very beginning of the scene
(before any actions kick in). If a character doesn't need a `start`
override, you can skip it entirely and they'll start at the defaults
above.

`actions` is a list of timed things that happen to them. Each needs a
`t` (seconds into the scene) and a `type`:

| type | fields | what it does |
|---|---|---|
| `enter` | `side` (left/right), `x`, `y` (optional), `duration` (default 1.0) | Walks/runs in from off-screen to position `x`,`y`. |
| `exit` | `side` (left/right), `duration` (default 1.0) | Walks/runs off-screen to that side. |
| `move_to` | `x`, `y` (optional, keeps current), `duration` (default 1.0) | Walks (or runs, if fast) to a new position. |
| `pose` | `pose`, `duration` (default 0.4) | Smoothly blends into a new held pose. |
| `expression` | `expression` | Changes facial expression (instant). |
| `say` | `text`, `duration` (default: auto, based on text length) | Shows a speech bubble above their head. |
| `pickup` | `prop` | Adds a prop (from then on, until dropped). |
| `drop` | `prop` | Removes a prop. |
| `costume` | `costume` (or omit/null to remove), `color` (optional) | Puts on/takes off a torso costume. |
| `fall_down` | `duration` (default 0.6) | Blends into the "fall_over" pose. |

Notes:
- During `enter`/`exit`/`move_to`, the character automatically plays
  a walking (or running, for fast/long moves) animation and faces the
  direction they're moving — you don't pick this yourself.
- Actions don't need to be in time order in the file — they get
  sorted by `t` automatically. But it's easier to read if you write
  them in order.
- Multiple characters' action lists all use scene-local time (seconds
  since that scene started, not the whole video).

## Available poses

Static (held) poses — use with `type: pose, pose: <name>`, or as a
character's starting `pose`:

`stand`, `point`, `cheer`, `kneel`, `bow`, `sit`, `sword_swing`,
`block`, `fall_over`, `lie_down`, `shrug`, `facepalm`, `arms_crossed`

Looping poses (automatically used during movement, or you can select
them directly the same way): `walk`, `run`, `wave`, `talk`

## Available expressions

`neutral`, `happy`, `angry`, `sad`, `shocked`, `scared`

## Available props

Head props (`attach` automatically to the head): `crown`,
`laurel_wreath`, `roman_helmet`, `barbarian_helmet`

Hand props (automatically held in a sensible hand): `sword`, `spear`,
`round_shield`, `rect_shield`, `torch`, `scroll`, `gold_bag`, `banner`

## Available costumes

`toga`, `cape`

## Everything in one bigger example

```yaml
fps: 30
resolution: [1080, 1920]

characters:
  alaric:
    color: "#3E6B2E"
    label: Alaric
  citizen:
    color: "#C97A3D"
    label: Citizen

scenes:
  - duration: 6
    background: rome_city
    transition_in: fade
    transition_out: fade
    camera:
      - {t: 0, x: 50, y: 55, zoom: 1.0}
      - {t: 6, x: 50, y: 50, zoom: 1.2, shake: 0.3}
    text:
      - {type: date_stamp, text: "410 AD", t: 0.2}
      - {type: caption, text: "The Visigoths storm the city.", t: 0.5}
      - {type: caption, text: "Rome falls for the first time in 800 years.", t: 3.5}
    effects:
      - {type: fire, x: 82, y: 82, t: 2.0, duration: 4, scale: 1.2}
      - {type: smoke, x: 82, y: 80, t: 2.0, duration: 4, scale: 1.4}
    characters:
      alaric:
        start: {x: -10, y: 84, facing: right, props: [barbarian_helmet, sword]}
        actions:
          - {t: 0, type: enter, side: left, x: 35, duration: 1.4}
          - {t: 1.6, type: pose, pose: sword_swing, duration: 0.4}
          - {t: 2.2, type: expression, expression: angry}
      citizen:
        start: {x: 60, y: 83, facing: left, expression: scared}
        actions:
          - {t: 1.0, type: pose, pose: facepalm, duration: 0.5}
          - {t: 2.4, type: exit, side: right, duration: 1.6}
```

## If something doesn't validate

`render.py` checks the whole file before rendering anything, and
prints an error that names the exact scene/character/action and what
was wrong — e.g. `Scene 3, character "marcus", action 2: unknown pose
"cheeer". Available poses: ...`. Fix the file and run it again.
