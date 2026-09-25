# AGENTS.md

Context for anyone — human or agent — working on this repo. Read this and
`README.md` first; together with a skim of `src/config.py` they are the whole
picture.

## What this is

A VEX V5 competition robot program. VEXcode VS Code extension, Python, SDK
`V5_1_0_1_25`, downloads to slot 2.

`README.md` covers operation: ports, controls, calibration procedure, AI Vision
setup. This file covers how the code is put together and what will bite you.

## Conventions

**Comments stay short.** No block comments explaining rationale, no tutorial
docstrings. If something needs explaining at length it goes in this file or
`README.md`, with at most a one-line pointer in the code. One-line docstrings on
functions are fine; paragraphs are not.

**Commit as you go**, in logically scoped commits, without being asked.

## The single-file constraint

A V5 brain runs one Python file. `.vscode/vex_project_settings.json` has a single
`python.main` key — VEXcode's own schema calls it "Path to python file to
download to brain" — and no file list. So `from config import *` resolves in the
editor and raises `ImportError` on the robot.

`build.py` works around this by concatenating the modules in dependency order,
dropping the editor-only imports, and writing `src/download.py`. It `compile()`s
the result before writing, so a mistake surfaces as a build error rather than a
line number pointing into a generated file.

```
python3 build.py       # before every download
```

`src/download.py` is generated and committed (so a fresh clone is immediately
downloadable at a competition). Never edit it; its diffs are noise.

## Layout

| File | Contents |
|------|----------|
| `src/config.py` | every device object and every tunable constant; `manipulator_init()` |
| `src/vision.py` | `find_cone`, `cone_detector`, `vision_report` |
| `src/autonomousroutine.py` | wheel-degree maths, `drive`, `turn`, calibration, `turn_tuner`, `autonomous()` |
| `src/drivercontrol.py` | `slew`, `turn_taper`, `fit_turn`, `user_control()` |
| `src/main.py` | imports the above; `main()` selects the mode |
| `build.py` | flattens `src/` into `src/download.py` |

`MODULES` in `build.py` is the dependency order. A new module must be added
there, after the modules it reads from.

`manipulator_init()` lives in `config.py` rather than with the driver code
because both modes call it.

`.vscode/settings.json` puts `src` on `python.analysis.extraPaths` so the editor
resolves the sibling imports.

## Autonomous movement

`drive()` and `turn()` compute wheel degrees explicitly rather than calling
`DriveTrain.drive_for` / `turn_for`, so the maths is visible and tunable.

A point turn is `arc_mm = PI * TRACK_WIDTH_MM * angle / 360`. `PI * TRACK_WIDTH`
is the circle the wheels trace when the robot spins once in place; the two sides
split that circle by counter-rotating. **The formula is not doubled** — there is
no hidden factor of two to remove, and this has been mistaken for one before.

`DRIVE_SCALE` and `TURN_SCALE` are multiplicative trims at the end of each
conversion. They absorb every error source at once, which is why turns can be
calibrated without ever measuring a distance.

Autonomous sets `HOLD` on both drive motors; `user_control()` sets `BRAKE`.
`HOLD` keeps servoing to the target after arrival, pulling back momentum
overshoot. `BRAKE` stops resisting the moment the command ends, which bakes the
overshoot in and compounds it across segments. This distinction mattered: it was
most of the original turn error.

Move timeouts are proportional (`2×` theoretical time `+ 1 s`), not flat. A flat
5 s was silently truncating `drive(5000)` — which needs 9.4 s at 50% — to
roughly half distance.

## AI Vision

The colour and code descriptions are **declared in `config.py` and passed to
`AiVision()`**, which pushes them to the sensor at construction.

The obvious alternative — declare nothing and rely on what the AI Vision Utility
stored on the sensor — does not work here, and the failure is silent: the sensor
reports `installed()` True with a moving `timestamp()` while every snapshot comes
back empty. The utility screenshot showed "No AI Vision Sensor Connected", so the
colours were configured against a disconnected utility and never reached any
sensor. Declaring them in code sidesteps the question entirely.

`ai_vision.color_detection(True)` is then required to turn colour and code
processing on.

Indices follow the utility's list order: `bluecone` 1, `yellowcone` 2, code
`cone` 1. The RGB values were sampled from the utility's colour swatches, and
the hue (40) and saturation (1.00) ranges copied from its sliders. Those are
wide tolerances — if the code matches things that are not the cone, narrow them.

A colour code only matches when both member colours are found adjacent to each
other, which is exactly the half-yellow half-blue cone.

`find_cone()` returns the full `AiVisionObject`, so aiming at the cone later is
the same call — `centerX` under 160 is left of centre in the 320x240 frame.

## Gotchas

- **Cartridge mismatch.** Declaring `RATIO_18_1` with a blue cartridge fitted
  overshoots every move by exactly 3×, drives and turns alike. If `drive(1000)`
  also overshoots badly, suspect the cartridge or wheel size, not track width.
- **`right_motor` is declared reversed**, so `FORWARD` on it means robot-forward.
  The sign flip in `turn()` is what makes the sides oppose. Positive angle =
  right turn.
- **Wheel scrub under-rotates** in-place turns: the encoders reach target while
  the robot slides through part of the motion. Not predictable from geometry;
  absorb it into `TURN_SCALE`.
- **`TURN_SCALE` is rebound by `turn_tuner()`** via `global`. That works because
  the tuner and `wheel_degrees_for_turn` are in the same module, and stays true
  after flattening. Moving either one breaks it.
- **Type checker and `AiVisionObject | None`.** Narrow with `is not None` before
  attribute reads even where it is redundant at runtime.
- **`ai_vision.color_detection(True)` is required.** Colour and code processing
  is off by default. The sensor still reports `installed()` True and a moving
  `timestamp()`, so the failure looks like "sees nothing" rather than
  "misconfigured". `config.py` enables it right after constructing the sensor.
- **The brain screen is static pixels.** `brain.screen.print()` paints once and
  has no link to the variable it formatted; redraw to update. It also does not
  blank the rest of the row, so a shorter string leaves the tail of the old one
  behind — `clear_line()` first. Redraw only when something changed; repainting
  every loop pass flickers.
- **`brain.screen.render()` switches the screen to double buffering globally.**
  After the first call nothing reaches the glass until the next `render()`, so
  any other code that draws must call it too. Currently only `tuner_screen()`
  uses it, which is safe because `turn_tuner()` never returns.
- **`print()` goes to the VEXcode console, not the brain.** Output is lost
  unless the robot is tethered with the terminal open.
- **`src/main.py.bak`** predates this work and is kept only in git history.

## Not yet done

Closed-loop heading turns with the `Inertial` class (present in the SDK at
`vex.py:2191` — `heading()`, `rotation()`, `calibrate()`, `is_calibrating()`).
That would make `TURN_SCALE`, track width and scrub irrelevant for turns. Not
built because it is unknown whether the sensor is on the robot.
