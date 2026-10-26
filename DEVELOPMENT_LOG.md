# Development Log

How this VEX V5 robot program developed, one day at a time, worked out from the
git history (57 commits), commit messages, diffs and file metadata. Times are
local (UTC+2).

| Date | Commits | Focus |
|------|---------|-------|
| Mon 8 Sep 2026 | none | Project created in VEXcode |
| Mon 22 Sep 2026 | 9 | Accurate autonomous movement, modular code, AI Vision first light |
| Thu 25 Sep 2026 | 2 | Getting the AI Vision sensor to actually detect the cone |
| Thu 22 Oct 2026 | 20 | Autonomous that searches for the cone and drives to it |
| Fri 23 Oct 2026 | 19 | Making the cone approach reliable |
| Sun 25 Oct 2026 | 3 | Change of direction: fixed autonomous path, cone assist moved to the driver |
| Mon 26 Oct 2026 | 1 | Repo published |

---

## Mon 8 Sep 2026: project created

**What:** The VEXcode project was created (`creationDate` in
`.vscode/vex_project_settings.json` is 9/8/2026 7:09 PM) and the `.vscode` files
date from then. It was not under git yet.

**Before git:** The first commit later stored `src/main.py` (425 lines), which had
last been edited on 21 Sep, plus an older `src/main.py.bak` (177 lines). So
between 8 and 21 Sep the team wrote a working single-file program: arcade drive
with slew limiting and turn taper, an arm and claw, and a basic autonomous routine.

---

## Mon 22 Sep 2026: accuracy, structure, first vision work

### 1. Restore point (`4f76b82`)
**What:** The existing program was committed exactly as it was.
**Why:** So every later change could be undone.

### 2. Autonomous drive and turn accuracy (`eb032a0`)
**Challenge:** Every autonomous distance and angle was wrong.
**Cause:** `DriveTrain` was built with the SDK's default geometry (300/320/320
mm), which doesn't match this robot. There were two other problems:
- `BRAKE` stops resisting as soon as a move ends, so momentum overshoot carried
  through and the error built up over each segment.
- Every move had a flat 5 s timeout. That quietly cut long drives off at about
  half distance (`drive(5000)` at 50% needs 9.4 s).

**How it was fixed:**
- Wheel travel is now calculated from a stated wheel diameter, with track width
  and gear ratio kept as constants you can measure.
- `drive_for`/`turn_for` were replaced with explicit wheel-degree maths, plus
  `DRIVE_SCALE`/`TURN_SCALE` trims to absorb the remaining error.
- Autonomous uses `HOLD`, which keeps correcting back to the target after
  arriving.
- Timeouts scale with the move (2× theoretical time + 1 s).
- `turn_tuner()` was added so `TURN_SCALE` can be calibrated on the robot from
  the controller.

### 3. AI Vision cone detection (`78005ed`)
**What:** Detects the yellow/blue cone using the colour code set up in the AI
Vision Utility.
**Decision:** No colours were declared in code, to avoid overwriting the ranges
tuned in the utility. This was reversed on 25 Sep.

### 4. Split into modules with a build step (`0607385`)
**Challenge:** The V5 brain runs only one Python file.
`vex_project_settings.json` has a single `main` key, so `from config import *`
works in the editor but fails with `ImportError` on the robot.
**How it was fixed:** The code was split into `config.py`, `vision.py`,
`autonomousroutine.py`, `drivercontrol.py` and `main.py`. A new `build.py`
joins them into `src/download.py`, removes the editor-only imports, and
`compile()`s the result so mistakes show up when you build, not on the robot.

### 5. Documentation and comment cleanup (`165d475`, `7043f53`)
**What:** Added README (how to operate the robot) and AGENTS (architecture and
gotchas). Long code comments were moved into those docs. For example,
`config.py` went from 308 to 146 lines. A docstring-stripped AST comparison
confirmed that no code changed.

### 6. Turn tuner flicker (`2e1cf54`)
**Challenge:** The tuner screen flickered constantly.
**Cause:** It cleared and redrew the screen every 50 ms.
**How it was fixed:** The screen only redraws when a button changes something,
and `render()` (double buffering) shows each new frame in one go.

### 7. Vision diagnostics on the brain screen (`b4624fd`)
**Challenge:** The cone was never reported, and it was impossible to tell why.
`print()` only goes to the VEXcode console, so with no tether a sensor that sees
nothing looks exactly like a program that isn't running.
**How it was fixed:** `vision_report()` now draws on the brain screen: a tick
counter, `installed()`, the packet timestamp, snapshot counts and object ids.

### 8. Enable colour detection (`91a2514`)
**Challenge:** The new screen showed the sensor connected and streaming, but
with zero colours and zero codes even with the cone in view.
**Cause:** Colour processing is off until `color_detection(True)` is called.
**How it was fixed:** That call was added to `config.py`.

---

## Thu 25 Sep 2026: making detection actually work

### 1. Declare the colours in code (`08c26bb`)
**Challenge:** Even with colour detection on, every snapshot came back empty.
**Cause:** A screenshot of the AI Vision Utility showed *"No AI Vision Sensor
Connected"*. The colours had been set up while the sensor was disconnected, so
they never reached the sensor.
**How it was fixed:** The colours are now declared in `config.py` and passed to
`AiVision()`, which loads them onto the sensor at startup. RGB values came from
the utility's swatches and hue/saturation from its sliders. This also fixed the
index order: `bluecone` is 1, not `yellowcone` as previously guessed.

### 2. Port scanner (`a2bfc94`)
**Challenge:** `AI_VISION_PORT` was a guess.
**How it was solved:** `scan_ports()` checks every smart port and reports which
one has a sensor sending data, all on the brain screen with no laptop needed.

---

## Thu 22 Oct 2026: autonomous cone search and approach

After about four weeks with no commits, the goal changed: autonomous should find
the cone and drive to it. These commits were made in a fast loop of test, tweak
and download, with GitHub Copilot (16:46–17:28) and then Claude (17:32 onward).

### Phase 1: search (`3bf3746` → `cb78f60`)
- Added `find_color()` and `search_color_circle()`, so the robot drives in a
  slow circle until it sees the target colour, then made autonomous do only this.
- **Challenge: speed.** Search power was tried at 30/60 (too fast to see the
  cone), then 1/2 (barely moved), and settled at 5/10.
- **Challenge: what to look for.** The target went from the yellow colour, to the
  blue+yellow code (`88daab7`), back to yellow alone (`cb78f60`), and finally to
  the code again (`4e0d8ed`). The code is more specific to the cone but harder
  to detect.

### Phase 2: approach (`b5cc2be` → `7ea5cea`)
- The robot turns to centre the cone, then drives until the cone looks
  `APPROACH_TARGET_WIDTH` pixels wide.
- **Challenge:** It stopped too early. It sometimes believed it had arrived
  straight away (`f05e383` added a minimum drive time), and it stopped too far
  from the cone (the target width was raised 100 → 180 → 250).
- **Challenge:** It drove off-centre, because steering while driving forward
  drifted. The fix was turning to centre first and driving second (`dc63501`),
  with the centring tolerance tightened from 20 to 5 px.
- **Challenge:** The image moved too much while driving to get accurate
  readings. The robot was changed to drive in short pulses (`3559957`) and to
  confirm it was centred over several frames before moving (`7ea5cea`).

### Phase 3: measure while still (`5bffee1` → `e4c1567`)
- `5bffee1` tried proportional steering (`STEER_KP`), a minimum turn power, and
  turning in place when the cone was far off-centre.
- **Key change (`2ea38be`):** The robot now stops, takes the median `centerX`
  over several still frames, converts the pixel error to degrees, and turns by
  encoder. Readings taken while moving were the cause of the jitter.
- **Challenge:** The robot always ended up aiming slightly right, because the
  camera isn't exactly centred. `VISION_CENTER_X` was moved from 160 to 164
  (`be39e7a`).
- Every alignment step is now logged on the brain screen (`e4c1567`), so a run
  can be checked without a laptop.

---

## Fri 23 Oct 2026: making the approach reliable

The full sequence became: wait → scan → approach → final align. Each commit
fixed a problem seen in the previous test run.

| Problem seen | Fix |
|--------------|-----|
| Needed a start routine | Wait 5 s, spin 180°, then align. Then a full 360° (`d2678a2`, `c236978`) |
| Continuous spin went past the cone | Slower spin that stops when the cone is seen (`c287574`), then "stop and look" steps instead of continuous spinning (`0165a87`) |
| Cone not detected at a distance | Treat a yellow+blue pair as the cone when the code doesn't match, lower the minimum size, log the scan (`6c3a1b7`) |
| Overshooting while closing in | Approach in measured steps that get shorter, re-aiming between steps (`c0304ef`), and stop further back (`19ec8f4`) |
| No way to tell if the sensor was working at the start | Live AI Vision status shown during the 5 s start delay (`08bd56b`) |
| Whole run gave up if the first alignment failed | Approach anyway (`d0aad44`) |
| Close up, the robot kept turning left and right and pushing into the cone | Merge the colour pair into one box, end when the cone stops getting bigger (touching), use a looser final tolerance (`8471b29`) |
| Merged box in the wrong place | Build it from centre and size, not origin fields (`f1f4d77`) |
| Scan slow or gave up too soon | Smaller, faster steps: 15° steps that loop until the cone is found (`fb5d896`, `c38d16b`, `b9f0267`) |
| Calibrating turns at scan speed was awkward | Hold L1 at startup to run the turn tuner (`88896a1`). Removed again a few minutes later (`b9f0267`) |
| Cone lost partway through the approach | Go back to scanning (`86d01a7`) |
| Couldn't see why the approach ended | Aim on every step, and show the reason on the controller screen (`a9a325f`) |
| First alignment was redundant | Skipped it; the approach aims as it goes (`ac6f254`) |
| Brief detection dropouts stopped the approach | Drive toward where the scan last saw the cone, and keep going through a few missed frames (`2c93591`) |
| False readings close up (cone suddenly looks much wider) | Ignore any width jump above `APPROACH_MAX_GROWTH` (`ce2e710`) |

**Overall challenge of the day:** The vision readings were noisy and
inconsistent. The cone code was sometimes lost at a distance, the box size
changed suddenly close up, and readings blurred while moving. The team worked
around this with still-frame medians, rejecting outliers, driving short
distances without vision through dropouts, and lots of on-screen logging.

---

## Sun 25 Oct 2026: change of strategy

### 1. Download slot (`76b036f`)
The program now downloads to slot 3 instead of 2. README and AGENTS still say
slot 2.

### 2. Fixed path replaces the cone hunt (`cf781d1`, `cc730b7`)
**Decision:** Even with all the fixes, the vision-driven autonomous wasn't
reliable enough for a competition run. Autonomous was replaced with a
predictable path using only the encoders:

```
A - - - B
|
S          (start with the back against the wall, facing A)
```

1. `square_to_wall()` backs into the wall until both drive motors stall, pushes
   a moment longer so both sides sit flat against it, then stops. This gives a
   repeatable starting position and heading.
2. Lift the arm 90 motor degrees and hold.
3. Drive 1 m to A, turn 90° right, drive 1 m to B.
4. Release the arm (coast) so it drops.

**What happened to the vision work:** The cone alignment was moved into driver
control as a **cone assist**. The left/right arrows spin until the cone is seen
and then centre on it. Any button or stick movement cancels it. R1 and R2 became
fast (100%) and slow (25%) drive modes.
**Challenge:** The button that starts the assist would immediately cancel it.
**How it was fixed:** The start is edge-triggered and ignored until the button
is released. The assist uses `spin()` with live frames instead of blocking
`spin_for`, so it can check for cancel on every loop. This removed 622 lines and
added 350.

---

## Mon 26 Oct 2026: published

`448d4f1` "first commit" added `# Vex_V5` to the README, which marks the repo
being pushed to its remote.

---

## Recurring themes

- **Silent failures were the hardest problems:** the wrong default geometry,
  colour detection off by default, colours never reaching the sensor, and
  console-only output. Each one was solved by adding diagnostics that show on
  the robot itself.
- **Measurement over guessing:** encoder maths with calibration trims, the port
  scanner, the camera-centre offset, and median readings.
- **Knowing when to simplify:** after two days of tuning the vision approach,
  the team chose a reliable fixed autonomous and kept vision as a driver aid.

## Still open

- Closed-loop turns using the Inertial sensor (in AGENTS "Not yet done"). This
  would make `TURN_SCALE` and track-width tuning unnecessary.
- README and AGENTS still say slot 2; the project downloads to slot 3.
