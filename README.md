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
| 3-wire B, C | back bumper switches |
| 9 | VEXnet radio — managed by brain firmware, never declared in code |

Set `INVERT_DRIVE` in `src/config.py` if the robot drives backward when you push
the stick forward.

## Driver controls

| Control | Action |
|---------|--------|
| Left stick (axis 3 / 4) | drive and turn |
| Right stick (axis 2 / 1) | arm and claw |
| R1 | fast — full power, bypasses the turn taper |
| R2 | slow — 25% power |
| nothing held | 50% power |
| Left arrow | cone assist: spin left until the cone is seen, then centre on it |
| Right arrow | cone assist: spin right until the cone is seen, then centre on it |

While cone assist runs, **any** button or a stick pushed past
`ASSIST_STICK_CANCEL` stops it and hands control straight back. The controller
screen shows `searching`, `aligning`, `centred` (two short rumbles) or
`cancelled`.

Throttle is deadbanded then squared, so small stick movements stay fine-grained.

## Selecting a mode

`main()` in `src/main.py` picks what runs. Uncomment exactly one:

| Call | Purpose |
|------|---------|
| `cone_detector()` | watch through the AI Vision sensor, announce the cone |
| `vision_report()` | diagnostic — what the sensor is seeing, on the brain screen |
| `scan_ports()` | diagnostic — which port the AI Vision sensor is on |
| `user_control()` | normal driving |
| `autonomous()` | square on the wall, lift arm, drive the S→A→B path, release arm |
| `turn_tuner()` | on-robot turn calibration |

Field control switches between `autonomous()` and `user_control()` at a real
competition; until then, choose here.

## Autonomous

```
A - - - B
|
|
S
```

Start at S with the back bumper towards the wall and the nose pointing at A.

1. `square_to_wall()` backs into the wall at `WALL_SQUARE_SPEED` until **both**
   back bumper switches (3-wire ports B and C) are pressed, pushes
   `WALL_SQUARE_PUSH_MS` longer, then stops. Both sides keep driving while only
   one bumper is in, so the robot swings flat against the wall. Nothing else
   runs until both are pressed; if that hasn't happened within
   `WALL_SQUARE_MAX_MS` it stops and skips the rest of autonomous. The brain and
   controller show `B`/`C` bumper state and `square` or `NO WALL`.
2. `lift_arm()` raises the arm `AUTO_ARM_LIFT_DEG` motor degrees and holds.
3. Drives `AUTO_LEG_MM` (1 m) to A.
4. Turns `AUTO_TURN_DEG` (90, right) in place.
5. Drives `AUTO_LEG_MM` to B.
6. `release_arm()` switches the arm to coast so it drops.

If the arm goes down instead of up in step 2, flip `ARM_INVERT` or make
`AUTO_ARM_LIFT_DEG` negative. Distances and the 90° depend on `DRIVE_SCALE` and
`TURN_SCALE`; see below.

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
`AUTO_TURN_SPEED`, the speed autonomous turns at.

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

### Cone assist

`cone_assist()` in `drivercontrol.py` spins at `ASSIST_SEARCH_SPEED` until the
cone is seen `VISION_CONFIRM_FRAMES` frames in a row, then turns towards it with
power proportional to the pixel error (`ASSIST_STEER_KP`, clamped between
`ASSIST_MIN_TURN` and `ASSIST_MAX_TURN`). It stops once `centerX` is within
`ASSIST_TOLERANCE_PX` for `ASSIST_HOLD_FRAMES` frames. If the cone drops out for
`ASSIST_LOST_FRAMES` it searches again, turning the way the cone was last seen.

If it oscillates either side of the cone, lower `ASSIST_STEER_KP` or
`ASSIST_MAX_TURN`. If it stalls just short of centre, raise `ASSIST_MIN_TURN`.

If it reports centred but the robot is visibly angled, the camera is not on the
robot's centreline. Aim the robot at the cone by hand, read `x` from
`vision_report()`, and put that number in `VISION_CENTER_X`.

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
# Vex_V5
