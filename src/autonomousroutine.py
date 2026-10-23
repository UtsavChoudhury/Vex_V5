# autonomousroutine.py -- movement, calibration and the autonomous routine.

from vex import *
from config import *
from vision import find_cone


# --- Movement ---

def wheel_degrees_for_distance(distance_mm):
    """Motor shaft degrees needed to roll the robot `distance_mm` along the floor."""
    return (distance_mm / WHEEL_TRAVEL_MM) * 360.0 * EXTERNAL_GEAR_RATIO * DRIVE_SCALE

def wheel_degrees_for_turn(robot_degrees):
    """Motor shaft degrees, per side, to rotate the robot `robot_degrees` in place."""
    arc_mm = PI * TRACK_WIDTH_MM * (robot_degrees / 360.0)
    return (arc_mm / WHEEL_TRAVEL_MM) * 360.0 * EXTERNAL_GEAR_RATIO * TURN_SCALE

def move_timeout_ms(wheel_deg, speed):
    """How long to give a move before calling it jammed."""
    dps = max(1.0, (abs(speed) / 100.0) * MOTOR_MAX_DPS)
    return int((abs(wheel_deg) / dps) * 1000.0 * TIMEOUT_MARGIN) + TIMEOUT_FLOOR_MS

def move_wheels(left_deg, right_deg, speed, timeout_ms=None):
    """Spin both sides through a set number of shaft degrees and wait for both."""
    if timeout_ms is None:
        timeout_ms = move_timeout_ms(max(abs(left_deg), abs(right_deg)), speed)

    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    left_motor.set_timeout(timeout_ms, MSEC)
    right_motor.set_timeout(timeout_ms, MSEC)

    left_motor.spin_for(FORWARD, left_deg, DEGREES, speed, PERCENT, wait=False)
    right_motor.spin_for(FORWARD, right_deg, DEGREES, speed, PERCENT, wait=False)

    while left_motor.is_spinning() or right_motor.is_spinning():
        wait(10, MSEC)

def drive(distance_mm, speed=AUTO_DRIVE_SPEED):
    """Drive straight. Positive = forward, negative = backward."""
    degrees = wheel_degrees_for_distance(distance_mm)
    move_wheels(degrees, degrees, speed)

def turn(degrees, speed=AUTO_TURN_SPEED):
    """Turn in place. Positive = right, negative = left."""
    wheel_deg = wheel_degrees_for_turn(degrees)
    move_wheels(wheel_deg, -wheel_deg, speed)

def settle(timeout_ms=300):
    """Brief pause after a move so momentum doesn't bleed into the next segment."""
    wait(timeout_ms, MSEC)


# --- Calibration ---

def tuner_screen(spins, speed):
    """Current state of the tuner, redrawn after every keypress."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("TURN TUNER   scale %.3f" % TURN_SCALE)
    brain.screen.set_cursor(2, 1)
    brain.screen.print("test %d spin(s) = %d deg @ %d%%" % (spins, spins * 360, speed))
    brain.screen.set_cursor(3, 1)
    brain.screen.print("A run   B unwind   X spins   Y speed")
    brain.screen.set_cursor(4, 1)
    brain.screen.print("up/down .010   R1/R2 .001")
    brain.screen.set_cursor(5, 1)
    brain.screen.print("short: raise    long: lower")
    # Double buffered from here on, so the clear-and-repaint never reaches the
    # glass half done. Only turn_tuner() draws after this, and it never returns.
    brain.screen.render()

def wait_release():
    """Hold here until every tuner button is let go, so one press counts once."""
    while (controller.buttonA.pressing() or controller.buttonB.pressing() or
           controller.buttonX.pressing() or controller.buttonY.pressing() or
           controller.buttonUp.pressing() or controller.buttonDown.pressing() or
           controller.buttonR1.pressing() or controller.buttonR2.pressing()):
        wait(20, MSEC)

def turn_tuner():
    """Tune TURN_SCALE from the controller. Procedure in README.md."""
    global TURN_SCALE

    spins = 1
    speed = AUTO_TURN_SPEED
    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    tuner_screen(spins, speed)

    while True:
        changed = True

        if controller.buttonA.pressing():
            wait_release()
            turn(spins * 360, speed)
            settle(300)
        elif controller.buttonB.pressing():
            wait_release()
            turn(-spins * 360, speed)
            settle(300)
        elif controller.buttonUp.pressing():
            wait_release()
            TURN_SCALE = TURN_SCALE + 0.010
        elif controller.buttonDown.pressing():
            wait_release()
            TURN_SCALE = max(0.010, TURN_SCALE - 0.010)
        elif controller.buttonR1.pressing():
            wait_release()
            TURN_SCALE = TURN_SCALE + 0.001
        elif controller.buttonR2.pressing():
            wait_release()
            TURN_SCALE = max(0.010, TURN_SCALE - 0.001)
        elif controller.buttonX.pressing():
            wait_release()
            spins = spins + 1 if spins < 3 else 1
        elif controller.buttonY.pressing():
            wait_release()
            # Scrub depends on speed, so tune at the speed you will drive at.
            speed = speed + 25 if speed < 75 else 25
        else:
            changed = False

        if changed:
            tuner_screen(spins, speed)
        wait(50, MSEC)

def calibrate_turn(degrees=360, speed=AUTO_TURN_SPEED):
    """One-shot turn calibration: TURN_SCALE = TURN_SCALE * degrees / measured."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("turn cal: asking for %d deg" % degrees)
    brain.screen.next_row()
    brain.screen.print("TURN_SCALE now %.3f" % TURN_SCALE)
    settle(2000)
    turn(degrees, speed)
    brain.screen.next_row()
    brain.screen.print("new = %.3f * %d / measured" % (TURN_SCALE, degrees))

def calibrate_drive(distance_mm=1000, speed=AUTO_DRIVE_SPEED):
    """One-shot drive calibration: DRIVE_SCALE = distance_mm / measured."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("drive cal: asking for %d mm" % distance_mm)
    brain.screen.next_row()
    brain.screen.print("DRIVE_SCALE now %.3f" % DRIVE_SCALE)
    settle(2000)
    drive(distance_mm, speed)
    brain.screen.next_row()
    brain.screen.print("new = %d / measured" % distance_mm)

def run_path(path):
    """Run a list of ("drive", mm, speed) / ("turn", deg, speed) / ("wait", ms) steps."""
    for step in path:
        action = step[0]
        if action == "drive":
            drive(step[1], step[2])
            settle()
        elif action == "turn":
            turn(step[1], step[2])
            settle()
        elif action == "wait":
            wait(step[1], MSEC)


# --- Cone alignment ---

def measure_cone():
    """Median centerX, x spread and median width over stationary frames, or None."""
    xs = []
    widths = []
    for i in range(ALIGN_SAMPLES):
        target = find_cone()
        if target is not None:
            xs.append(target.centerX)
            widths.append(target.width)
        wait(VISION_LOOP_MS, MSEC)
    if len(xs) < SCAN_MIN_HITS:
        return None
    xs.sort()
    widths.sort()
    return xs[len(xs) // 2], xs[-1] - xs[0], widths[len(widths) // 2]

def align_to_cone(tolerance=ALIGN_TOLERANCE_PX):
    """Stop, measure, turn by encoder; repeat until centred. Logs each step from row 5."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("ALIGN  centre %d  tol %d  deg/px %.3f" % (
        VISION_CENTER_X, tolerance, VISION_DEG_PER_PX))
    for step in range(ALIGN_MAX_STEPS):
        settle(ALIGN_SETTLE_MS)
        reading = measure_cone()
        brain.screen.set_cursor(step + 3, 1)
        if reading is None:
            brain.screen.print("%d  cone not seen" % (step + 1))
            return False
        x, spread, width = reading
        error = x - VISION_CENTER_X
        if abs(error) <= tolerance:
            brain.screen.print("%d  x %d  err %d  spr %d  w %d  DONE" % (
                step + 1, x, error, spread, width))
            return True
        angle = error * VISION_DEG_PER_PX
        if abs(angle) < ALIGN_MIN_TURN_DEG:
            angle = ALIGN_MIN_TURN_DEG if angle > 0 else -ALIGN_MIN_TURN_DEG
        start_left = left_motor.position(DEGREES)
        turn(angle, ALIGN_TURN_SPEED)
        moved = left_motor.position(DEGREES) - start_left
        brain.screen.print("%d  x %d  err %d  spr %d  w %d  t %.1f  mv %.1f" % (
            step + 1, x, error, spread, width, angle, moved))
    brain.screen.set_cursor(ALIGN_MAX_STEPS + 3, 1)
    brain.screen.print("gave up")
    return False


def scan_for_cone():
    """Turn in SCAN_STEP_DEG steps through a full circle, looking only while stopped."""
    steps = int(360 / SCAN_STEP_DEG)
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("SCAN  need %d/%d  min %dpx" % (SCAN_MIN_HITS, ALIGN_SAMPLES, VISION_MIN_WIDTH))
    for step in range(steps + 1):
        settle(ALIGN_SETTLE_MS)
        hits = 0
        width = 0
        for i in range(ALIGN_SAMPLES):
            target = find_cone()
            if target is not None:
                hits = hits + 1
                width = max(width, target.width)
            wait(VISION_LOOP_MS, MSEC)
        brain.screen.set_cursor(step + 2, 1)
        brain.screen.print("%3d deg  seen %d/%d  w %d" % (step * SCAN_STEP_DEG, hits, ALIGN_SAMPLES, width))
        if hits >= SCAN_MIN_HITS:
            return True
        if step < steps:
            turn(SCAN_STEP_DEG, SCAN_TURN_SPEED)
    return False


def approach_cone():
    """Stop, measure, re-aim if needed, drive a step that shrinks as the cone grows."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("APPROACH  target w %d" % APPROACH_TARGET_WIDTH)
    last_drive_width = None
    for step in range(APPROACH_MAX_STEPS):
        settle(ALIGN_SETTLE_MS)
        reading = measure_cone()
        brain.screen.set_cursor(2 + step % 10, 1)
        brain.screen.clear_line()
        if reading is None:
            brain.screen.print("%d  cone not seen" % (step + 1))
            return False
        x, spread, width = reading
        error = x - VISION_CENTER_X
        if width >= APPROACH_TARGET_WIDTH:
            brain.screen.print("%d  x %d  w %d  DONE" % (step + 1, x, width))
            return True
        close = last_drive_width is not None and last_drive_width >= APPROACH_TARGET_WIDTH // 2
        if close and width < last_drive_width + APPROACH_MIN_GROWTH_PX:
            brain.screen.print("%d  x %d  w %d  not growing, DONE" % (step + 1, x, width))
            return True
        if abs(error) > APPROACH_REAIM_PX:
            angle = error * VISION_DEG_PER_PX
            brain.screen.print("%d  x %d  w %d  aim %.1f" % (step + 1, x, width, angle))
            turn(angle, ALIGN_TURN_SPEED)
            continue
        remaining = 1.0 - width / float(APPROACH_TARGET_WIDTH)
        distance = max(APPROACH_STEP_MIN_MM, APPROACH_STEP_MAX_MM * remaining)
        brain.screen.print("%d  x %d  w %d  drive %d" % (step + 1, x, width, distance))
        last_drive_width = width
        drive(distance, APPROACH_SPEED)
    return False


def start_wait_report(ms):
    """Wait out the start delay showing live AI Vision status, so a dead sensor shows up."""
    brain.screen.clear_screen()
    end = brain.timer.time(MSEC) + ms
    while brain.timer.time(MSEC) < end:
        codes = ai_vision.take_snapshot(AiVision.ALL_CODES, VISION_MAX_OBJECTS)
        colors = ai_vision.take_snapshot(AiVision.ALL_COLORS, VISION_MAX_OBJECTS)
        cone = find_cone()
        brain.screen.clear_line(1)
        brain.screen.set_cursor(1, 1)
        brain.screen.print("START  installed %s  stamp %d" % (ai_vision.installed(), ai_vision.timestamp()))
        brain.screen.clear_line(2)
        brain.screen.set_cursor(2, 1)
        brain.screen.print("codes %d  colours %d" % (len(codes), len(colors)))
        brain.screen.clear_line(3)
        brain.screen.set_cursor(3, 1)
        if cone is not None:
            brain.screen.print("cone x %d y %d  %dx%d" % (cone.centerX, cone.centerY, cone.width, cone.height))
        else:
            brain.screen.print("cone none")
        wait(250, MSEC)


# --- Routine ---

def autonomous():
    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    manipulator_init()
    start_wait_report(AUTO_START_DELAY_MS)
    if not scan_for_cone():
        controller.rumble("-")
        return
    align_to_cone()
    if approach_cone() and align_to_cone(FINAL_ALIGN_TOLERANCE_PX):
        controller.rumble("...")
    else:
        controller.rumble("-")
