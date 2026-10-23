# Comp

VEX V5 competition robot. VEXcode Python, SDK `V5_1_0_1_25`, slot 2.

Two-motor drive with an arm and a claw, plus an AI Vision sensor that recognises
the yellow/blue cone.

## Build and download

A V5 brain runs **one** Python file, so the modules under `src/` are flattened
before download:

```
python3 build.py       # writes src/download.py
```

Then hit Download in VEXcode. The project is configured to send
`src/download.py`, which is generated — never edit it. Run `build.py` after
every change.

## Hardware

| Port | Device |
|------|--------|
| 1 | right drive motor (green 18:1) |
| 2 | left drive motor (green 18:1) |
| 4 | AI Vision sensor |
| 10 | arm motor (red 36:1) |
| 15 | claw motor (red 36:1) |
| 9 | VEXnet radio — managed by brain firmware, never declared in code |

Set `INVERT_DRIVE` in `src/config.py` if the robot drives backward when you push
the stick forward.

## Driver controls

| Control | Action |
|---------|--------|
| Left stick (axis 3 / 4) | drive and turn |
| Right stick (axis 2 / 1) | arm and claw |
| L1 or R1 | boost — full power, bypasses the turn taper |
| L2 or R2 | crawl — 25% power |
| nothing held | 50% power |

Throttle is deadbanded then squared, so small stick movements stay fine-grained.

## Selecting a mode

`main()` in `src/main.py` picks what runs. Uncomment exactly one:

| Call | Purpose |
|------|---------|
| `cone_detector()` | watch through the AI Vision sensor, announce the cone |
| `search_color_circle()` | slowly circle until `SEARCH_COLOR_ID` is found |
| `vision_report()` | diagnostic — what the sensor is seeing, on the brain screen |
| `scan_ports()` | diagnostic — which port the AI Vision sensor is on |
| `user_control()` | normal driving |
| `autonomous()` | wait 5 s, turn in 15° steps until the cone is found, align, approach, align again |
| `turn_tuner()` | on-robot turn calibration |

Field control switches between `autonomous()` and `user_control()` at a real
competition; until then, choose here.

## Turn calibration

Autonomous angles depend on geometry that has to be measured, not guessed. Set
these in `src/config.py`:

- `WHEEL_DIAMETER_MM` — across the tyre through the axle. VEX: 4" = 101.6,
  3.25" = 82.55, 2.75" = 69.85.
- `TRACK_WIDTH_MM` — left wheel contact patch to right wheel contact patch. The
  single biggest source of turn error.
- `EXTERNAL_GEAR_RATIO` — motor turns per wheel turn. Direct drive = 1.0; a 60t
  wheel gear driven by a 36t motor gear = 60/36 = 1.667.

Check the cartridge colour matches the `GearSetting`: green `RATIO_18_1`, blue
`RATIO_6_1`, red `RATIO_36_1`. Declaring green with a blue cartridge fitted
overshoots every move by exactly 3×.

Whatever error remains — mostly wheel scrub, which no formula predicts — is
absorbed by `TURN_SCALE`. Find it with `turn_tuner()`, which starts at
`SCAN_TURN_SPEED`, the speed the cone scan turns at.

1. Put tape on the floor, line the nose up with it.
2. **A** runs the test spin, **B** spins back.
3. Landed short → raise the scale. Went past → lower it.
4. **Up/Down** ±0.010, **R1/R2** ±0.001, **X** cycles 1→2→3 spins, **Y** cycles
   speed 25→50→75%.
5. Read the final number off the brain screen into `TURN_SCALE`.

Spinning whole revolutions means you never measure an angle — the target is just
"the nose came back to the tape". Use 3 spins: a 5% error misses by 54°, which
you can see, where at a quarter turn it is 4.5°, which you cannot.

Calibrate on the surface you compete on. Foam tiles and a classroom floor scrub
differently.

`TURN_SCALE` absorbs wheel diameter, track width, gear ratio and scrub together,
so you can fix the angle without ever measuring a distance, and `DRIVE_SCALE`
can stay at 1.0.

### Is it actually a scale error?

Run 1 spin, note the miss, then run 3.

- **Miss roughly triples** — proportional error. `TURN_SCALE` is the right fix
  and will hold at every angle.
- **Miss stays the same** — a fixed offset per move. Scaling would overcorrect
  small turns and undercorrect large ones; the fix is elsewhere (settling time,
  or a heading sensor).

An inertial sensor closing the loop on measured heading makes all of this
unnecessary — turns stop caring about track width and scrub entirely.

## AI Vision

The cone is a colour code: two colours that only match when found adjacent to
each other, which is exactly the half-yellow half-blue cone. The code drops out
at range, so `find_cone()` falls back to a yellow blob with a blue blob right
beside it (`find_color_pair()`), merged into one box (`ConeBox`) so width and
centre cover the whole cone, not just the yellow half. A plain yellow object alone still cannot
trigger it. Blobs under `VISION_MIN_WIDTH` x `VISION_MIN_HEIGHT` px are ignored;
a cone across the field is only about 15 px wide.

`scan_for_cone()` logs one row per stop: the angle, how many of the 7 frames
saw the cone, and its widest width. It needs `SCAN_MIN_HITS` frames to stop.

| Kind | Index | Name |
|------|-------|------|
| colour | 1 | `bluecone` |
| colour | 2 | `yellowcone` |
| colour code | 1 | `cone` |

These are **declared in `src/config.py`**, not read from the sensor. Relying on
what the AI Vision Utility stored does not work — see AGENTS.md.

If the code matches things that are not the cone, narrow the hue range (40) and
saturation range (1.00) in the `Colordesc` lines. To re-sample the colours
properly: connect the brain over USB, open the AI Vision Utility, press
**Connect**, point the sensor at the real cone and use **Set Color** on each
half, then copy the values back into `config.py`.

`cone_detector()` prints `cone identified` once on arrival, not once per frame,
and `cone lost` on the way out. Three consecutive agreeing frames are required
in each direction (150 ms), which rides out a dropped frame without lag.

### Aligning to the cone

Autonomous waits `AUTO_START_DELAY_MS` showing live AI Vision status (sensor
installed, timestamp, code and colour counts, cone position), then `scan_for_cone()` looks, turns
`SCAN_STEP_DEG` in place at `SCAN_TURN_SPEED`, and looks again, forever until
the cone is found. It does not track total angle, so `TURN_SCALE` only affects
how far each step goes. It only looks while stopped, because the colour code is
unreliable on blurred frames mid-turn.
Once the cone is seen it runs
`align_to_cone()`. That step repeats: wait for the robot to settle, take the
median `centerX` over 7 frames, convert the pixel error to degrees
(`VISION_DEG_PER_PX`), and turn that far by encoder. It finishes when the error
is within `ALIGN_TOLERANCE_PX`. Row 5 of the brain screen shows each step.

`approach_cone()` then runs whether or not that first alignment converged. Each
step it settles and measures (looking twice before calling the cone lost),
turns to face it if `centerX` is more than `APPROACH_REAIM_PX` off, and drives
straight. The step scales from `APPROACH_STEP_MAX_MM` down to
`APPROACH_STEP_MIN_MM` as the cone's width nears `APPROACH_TARGET_WIDTH`, which
is the "close enough" setting: raise it to stop closer. Past half the target
width, two drive steps in a row that grow the cone by less than
`APPROACH_MIN_GROWTH_PX` also end the approach: the robot is touching or pushing
it. The reason it ended is shown on the controller screen. A final `align_to_cone(FINAL_ALIGN_TOLERANCE_PX)` squares up at the
end with a looser tolerance, because the centre jitters close up. The controller gives
one long rumble each time it loses the cone and goes back to scanning, and three
short rumbles once it has reached the cone.

If it reports `err 0` but the robot is visibly angled, the camera is not on the
robot's centreline. Aim the robot at the cone by hand, read `x` from
`vision_report()`, and put that number in `VISION_CENTER_X`.

If each step overshoots (the error flips sign), lower `VISION_DEG_PER_PX`. If
it creeps towards centre over many steps, raise it.

### Nothing happens at all

1. **Did you run `python3 build.py`?** The brain runs `src/download.py`. Editing
   a module and hitting Download sends the previous build.
2. **`print()` does not appear on the brain** — it goes to the VEXcode console
   over USB. `vision_report()` reports on the brain screen instead, so use that
   when you are not tethered.
3. **Blank brain screen** means the program is not running: wrong slot, a failed
   download, or it stopped on an error.

### If detection never fires

Run `vision_report()` and watch the console with the cone in front of the sensor.

- **A `CODE` line appears** — read the id off it into `CONE_CODE_ID`.
- **Only `COLOR` lines, never `CODE`** — the sensor sees both halves but will not
  merge them. Either they are too far apart at your test distance, or one colour
  range is too tight. Fix it in the utility.
- **Nothing at all** — wrong port, or the lighting is far from where the colours
  were tuned.

`VISION_MIN_WIDTH` / `VISION_MIN_HEIGHT` discard matches under 20×20 px in the
320×240 frame. Raise them to shorten detection range.
