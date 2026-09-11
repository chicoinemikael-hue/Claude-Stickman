# Claude Stickman

A tool for turning a simple text file (a "storyboard") into a finished
stickman-animated video — the kind of thing you'd use for a history
Short/TikTok. You write what happens in plain YAML, run one command,
and get an MP4 ready to upload.

This README explains how to install it, render a video, add your own
poses/props, and fix the most common problems — written for someone
who isn't a programmer.

## What you need installed

Two things, and they're both free:

1. **Python 3.9 or newer**
2. **ffmpeg** (turns the frames this tool draws into an actual video file)

### Windows

1. Install Python: go to [python.org/downloads](https://python.org/downloads),
   download the installer, run it. **Important:** on the first
   install screen, check the box that says "Add python.exe to PATH"
   before clicking Install.
2. Install ffmpeg: open PowerShell and run:
   ```
   winget install ffmpeg
   ```
   (If `winget` isn't available, download ffmpeg from
   [ffmpeg.org/download.html](https://ffmpeg.org/download.html),
   unzip it somewhere like `C:\ffmpeg`, and add `C:\ffmpeg\bin` to
   your PATH — search "Edit environment variables" in the Start Menu.)
3. Open a new PowerShell window (so the PATH changes take effect) and
   check both worked:
   ```
   python --version
   ffmpeg -version
   ```

### macOS

1. Install [Homebrew](https://brew.sh) if you don't have it (one
   command, shown on that page).
2. Then in Terminal:
   ```
   brew install python ffmpeg
   ```
3. Check it worked:
   ```
   python3 --version
   ffmpeg -version
   ```

### Linux

Use your distro's package manager, e.g. on Ubuntu/Debian:
```
sudo apt update
sudo apt install python3 python3-pip ffmpeg
```

## Setting up the project

Once Python and ffmpeg are installed, open a terminal in this
project's folder and run:

```
pip install -r requirements.txt
```

(On macOS/Linux you may need `pip3` instead of `pip`.)

This installs two small Python libraries: `pycairo` (draws the smooth
stickman artwork) and `PyYAML` (reads storyboard files). That's it —
no other setup needed.

**If `pip install pycairo` fails** with an error mentioning `cairo.h`
or a missing compiler, your system needs Cairo's development files
first:
- **macOS:** `brew install cairo pkg-config`
- **Ubuntu/Debian:** `sudo apt install libcairo2-dev pkg-config python3-dev`
- **Windows:** this is rare with modern Python, but if it happens,
  install [MSYS2](https://www.msys2.org/) and follow the pycairo
  Windows install notes at [pycairo's docs](https://pycairo.readthedocs.io/en/latest/getting_started.html).

Then run `pip install -r requirements.txt` again.

## Rendering a video

```
python render.py storyboards/fall_of_rome_demo.yaml
```

This reads that storyboard file and writes a finished MP4 to the
`output/` folder — 1080x1920 (vertical), 30fps, H.264, ready to drop
into CapCut or upload directly.

Useful options:

```
python render.py storyboards/my_video.yaml --preview
```
Renders fast at low resolution, so you can check timing/pacing
quickly before doing a full-quality render.

```
python render.py storyboards/my_video.yaml --frame 12.5
```
Instead of a video, saves one PNG image of what the video looks like
at the 12.5-second mark. Great for checking a specific pose or layout
without waiting for a full render.

```
python render.py storyboards/my_video.yaml --scene 3
```
Renders just scene 3 (scenes are numbered from 1), so you can iterate
on one part of a longer video quickly.

You can combine `--scene` and `--frame`/`--preview` too.

## Writing your own storyboard

See **`FORMAT.md`** for the full format reference with examples. The
easiest way to write a new one: open a chat with Claude, paste in
`FORMAT.md`, and describe the video you want ("write me a storyboard
about the Punic Wars, about 45 seconds, 4 scenes") — Claude can write
a working `.yaml` file for you directly.

Save your storyboard as a new file under `storyboards/`, e.g.
`storyboards/punic_wars.yaml`, and render it the same way:

```
python render.py storyboards/punic_wars.yaml
```

## Adding a new pose

All poses live in one place: `engine/poses.py`. Each one is a set of
joint angles (the file has a cheat sheet at the top explaining what
each angle does).

1. Open `engine/poses.py` and find a pose that's roughly similar to
   what you want.
2. Copy it, give it a new name, and tweak the angle numbers.
3. Add it to the `POSES` dictionary at the bottom of the file.
4. Check how it looks:
   ```
   python -c "
   from engine.character import Character
   from engine.poses import POSES
   from engine.renderer import render_still
   c = Character(name='test', pose=POSES['your_new_pose_name'])
   render_still([c], 'output/pose_check.png')
   "
   ```
   Then open `output/pose_check.png` and see how it looks. Repeat
   until it looks right — this is much easier than trying to imagine
   angles in your head.

For a *looping* pose (like `walk`), see how `WALK`/`RUN`/`WAVE` are
built near the bottom of `engine/poses.py` — they're a few keyframe
poses wrapped in a `PoseCycle`.

## Adding a new prop

Props live in `engine/props.py`. Each is a small function that draws
the item at a given point (a hand or the head).

1. Open `engine/props.py` and copy a function similar to what you
   want (e.g. copy `draw_sword` for another hand-held weapon).
2. Write your drawing code — it's plain [pycairo](https://pycairo.readthedocs.io/)
   calls (rectangles, arcs, lines).
3. Add an entry to `HEAD_PROPS` or `HAND_PROPS` at the bottom of the
   file with your prop's name.
4. Use it in a storyboard with `props: [your_prop_name]`.

## Project structure

See `CLAUDE.md` for a full map of the codebase (mainly aimed at future
Claude Code sessions working on this project, but useful for anyone
poking around the code).

## Common problems

**"Storyboard problem: ... unknown pose/prop/background ..."**
The error message tells you exactly which scene and character/action
has the typo, and lists the valid names. Fix the file and run again.

**`ModuleNotFoundError: No module named 'cairo'` (or `yaml`)**
Run `pip install -r requirements.txt` again — a dependency didn't
install. If pycairo specifically won't install, see the Cairo
dev-files note above.

**`ffmpeg was not found on your system`**
ffmpeg isn't installed, or isn't on your PATH. Revisit the install
steps above for your OS, then open a *new* terminal window (PATH
changes don't apply to already-open terminals).

**The video renders but has no sound**
Check the `audio:` section of your storyboard — `voiceover`/`music`
paths must point to real files, relative to wherever you run
`python render.py` from (usually the project folder itself).

**Text is cut off at the edges of the phone screen**
Shorts/TikTok apps cover roughly the top and bottom 15% of the video
with their own UI. Keep captions/titles (which already default to
safe positions) and important character action out of that zone —
see the "safe zone" note near the top of `FORMAT.md`.

**A render is slow**
Use `--preview` while you're iterating — it's much faster since it
renders at a lower resolution and frame rate. Do your final full-
quality render once you're happy with the timing.

**Characters overlap oddly / a pose looks wrong**
Stick figures are simple 2D rigs — very close characters with big
gestures (arms fully extended, etc.) can visually overlap. Try
spacing characters a bit further apart (`x` values further apart) or
using a less extreme pose in a crowded shot.
