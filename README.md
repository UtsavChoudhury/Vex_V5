# Comp

VEX V5 competition robot. VEXcode Python, SDK `V5_1_0_1_25`, slot 2.

Two-motor drive with an arm, a claw and a toggle motor. The AI Vision camera code
was removed; the sensor is not used.

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
| 4 | right drive motor (green 18:1) |
| 6 | left drive motor (green 18:1) |
| 8 | toggle motor (L1 forward, L2 backward, full power) |
| 9 | arm motor (red 36:1), lifts the arm by tracks |
| 10 | claw motor (red 36:1) |
| 3-wire C, E | back bumper switches, left and right |
| 3-wire F | left side bumper switch |
| 5 | VEXnet radio — managed by brain firmware, never declared in code |

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
| L1 / L2 | toggle motor forward / backward at full power |
| X | re-zero the arm: move it with the right stick, press A |

### Arm and claw zero, limits

Every program starts with `Arm at bottom? A=yes`: move the arm up or down with the
right stick, then press **A** to call that position 0. Then `Claw fully open?
A=yes` does the same for the claw (0 = open, closing goes negative).

Once zeroed, the arm stops at `ARM_MIN_DEG` and `ARM_MAX_DEG` and slows over the
last `ARM_SLOW_ZONE_DEG` at each end; the claw stops at 0 and `CLAW_MAX_DEG`
(`CLAW_CLOSE_SIGN` = -1). Re-measure the arm limits on each new build.

There is no stall or slip detection: the motor's own speed and current cannot tell
a slack chain from a free arm, so nothing is guessed from them.

The brain screen shows every motor's rotation, the arm's speed and current, the
bumpers and the slip count (`MOTOR_DIAGNOSTIC`).

Throttle is deadbanded then squared, so small stick movements stay fine-grained.

## Selecting a mode

`main()` in `src/main.py` picks what runs. Uncomment exactly one:

| Call | Purpose |
|------|---------|
| `user_control()` | normal driving |
| `test_autonomous()` | runs `autonomous()` immediately on Run, then driver control |
| `match()` | **competitions** — field control picks `autonomous()` or `user_control()` |
| `turn_tuner()` | on-robot turn calibration |

Every mode starts with the arm-zero question; see above.

## Autonomous (Override)

From the Override game manual (`<SG1>`, `<SG5>`, `<SG9>`): start touching the
perimeter on your side of the Autonomous Line, in your own Quadrant, not touching
a Goal, Toggle, Loader or Load Zone, holding one Preload (blue/yellow Pin for
blue, red/yellow for red). Each Alliance Quadrant has a low (82.5 mm) Alliance
Goal about one tile (≈610 mm) out from the side wall and two tiles from the
corner, which opponents may not touch.

Cups and Pins sit against the wall in line with every goal, so the only clear
start is the **middle of a side wall**, under the Toggle. From there the goal is
about one tile out and one tile along. See `start_positions.png`.

Setup: back bumpers on the wall, centred on the wall, preload Pin gripped upright
in the claw, arm zeroed.

0. Spins the toggle motor backward `TOGGLE_AUTO_TURNS` (2) rotations, with the arm lifting at the same time.
1. Seats both bumpers on the wall (`AUTO_SEAT_MS`; carries on either way).
2. Arm to `AUTO_ARM_CARRY_DEG`, drives `AUTO_LEG1_MM` out from the wall.
3. Turns 90° towards the goal (`AUTO_SIDE`, chosen with the arrow buttons).
4. Drives `AUTO_LEG2_MM`, then forward until the front bumper hits, backs off, arm down to
   `AUTO_ARM_PLACE_DEG`, opens the claw, arm back up, backs off.

### Slots

`build.py` writes one file per slot; download each with VEXcode or `vexcom`.

| Slot | Name | File | Does |
|---|---|---|---|
| 1 | Driver | `download_driver.py` | manual control |
| 2 | Auto | `download_auto.py` | waits for Left/Right arrow, runs autonomous, then manual |
| 3 | Match | `download.py` | competitions: arrow picks the side before the match, field control runs the rest |

Tuning, in `user_control()` (the brain screen shows `arm` degrees):

- `AUTO_LEG1_MM` = wall → goal centre (out) minus wall → robot turning centre.
- `AUTO_LEG2_MM` = middle of the wall → goal centre (along) minus turning centre
  → claw centre. 90° accuracy matters here: run `turn_tuner()` first.
- Raise the arm until the Pin clears the goal rim: `AUTO_ARM_CARRY_DEG`. Lower
  it until the Pin sits in the goal: `AUTO_ARM_PLACE_DEG`.
- `AUTO_CLAW_OPEN_PCT`: positive if pushing the right stick right opens the
  claw, negative if it closes it.

`autonomous_s_path()` is the old S→A→B test path below.

```
A - - - B
|
|
S
```

Start at S with the back bumper towards the wall and the nose pointing at A.

1. `square_to_wall()` backs into the wall at `WALL_SQUARE_SPEED` until **both**
   back bumper switches (3-wire ports C and E) are pressed, pushes
   `WALL_SQUARE_PUSH_MS` longer, then stops. Both sides keep driving while only
   one bumper is in, so the robot swings flat against the wall. Nothing else
   runs until both are pressed; if that hasn't happened within
   `WALL_SQUARE_MAX_MS` it stops and skips the rest of autonomous. The brain and
   controller show `B`/`E` bumper state and `square` or `NO WALL`.
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
