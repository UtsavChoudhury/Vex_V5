# autonomousroutine.py -- movement, calibration and the autonomous routine.

from vex import *
from config import *


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

def free_drive_timeouts():
    """move_wheels leaves a short time limit on the motors; spin() moves need it lifted."""
    left_motor.set_timeout(600000, MSEC)
    right_motor.set_timeout(600000, MSEC)

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
    free_drive_timeouts()

def drive(distance_mm, speed=AUTO_DRIVE_SPEED):
    """Drive straight. Positive = forward, negative = backward."""
    degrees = wheel_degrees_for_distance(distance_mm)
    move_wheels(degrees, degrees, speed)

def turn(degrees, speed=AUTO_TURN_SPEED):
    """Turn in place. Positive = right, negative = left."""
    wheel_deg = wheel_degrees_for_turn(degrees)
    move_wheels(wheel_deg, -wheel_deg, speed)

def settle(timeout_ms=150):
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


# --- Routine ---

def bumper_status(text):
    """Bumper state on brain row 1 and the controller, so a dead switch is obvious."""
    line = "%s  C %s  E %s" % (text, bumper_left.pressing(), bumper_right.pressing())
    brain.screen.clear_line(1)
    brain.screen.set_cursor(1, 1)
    brain.screen.print(line)
    controller.screen.clear_screen()
    controller.screen.set_cursor(1, 1)
    controller.screen.print(line)

def square_to_wall(max_ms=WALL_SQUARE_MAX_MS):
    """Back up until both bumpers are pressed, then keep pushing for WALL_SQUARE_PUSH_MS."""
    free_drive_timeouts()
    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    bumper_status("wall")
    left_motor.spin(REVERSE, WALL_SQUARE_SPEED, PERCENT)
    right_motor.spin(REVERSE, WALL_SQUARE_SPEED, PERCENT)
    start = brain.timer.time(MSEC)
    while not (bumper_left.pressing() and bumper_right.pressing()):
        if max_ms > 0 and brain.timer.time(MSEC) - start > max_ms:
            left_motor.stop()
            right_motor.stop()
            bumper_status("NO WALL")
            return False
        wait(10, MSEC)
    bumper_status("pushing wall")
    push_start = brain.timer.time(MSEC)
    while brain.timer.time(MSEC) - push_start < WALL_SQUARE_PUSH_MS:
        left_motor.spin(REVERSE, WALL_SQUARE_SPEED, PERCENT)
        right_motor.spin(REVERSE, WALL_SQUARE_SPEED, PERCENT)
        wait(10, MSEC)
    left_motor.stop()
    right_motor.stop()
    bumper_status("square")
    return True

def lift_arm(degrees=AUTO_ARM_LIFT_DEG, speed=AUTO_ARM_SPEED):
    """Raise the arm by motor degrees and hold it there."""
    arm_motor.set_stopping(HOLD)
    arm_motor.spin_for(FORWARD, degrees, DEGREES, speed, PERCENT)

def release_arm():
    """Stop holding the arm so it drops."""
    arm_motor.set_stopping(COAST)
    arm_motor.stop()

def arm_to(degrees, speed=AUTO_ARM_SPEED, wait=True):
    """Move the arm to an absolute position and hold it there."""
    degrees = max(ARM_MIN_DEG, min(ARM_MAX_DEG, degrees))
    travel = abs(degrees - arm_motor.position(DEGREES))
    dps = max(1.0, (speed / 100.0) * ARM_MAX_DPS)
    arm_motor.set_stopping(HOLD)
    arm_motor.set_timeout(int((travel / dps) * 1000.0 * TIMEOUT_MARGIN) + TIMEOUT_FLOOR_MS, MSEC)
    arm_motor.spin_to_position(degrees, DEGREES, speed, PERCENT, wait)

def arm_wait():
    """Block until an arm_to(..., wait=False) move finishes or times out."""
    while arm_motor.is_spinning():
        wait(10, MSEC)

def open_claw():
    """Drive the claw open for AUTO_CLAW_OPEN_MS, whatever its encoder says."""
    claw_motor.set_stopping(HOLD)
    claw_motor.spin(FORWARD, AUTO_CLAW_OPEN_PCT, PERCENT)
    wait(AUTO_CLAW_OPEN_MS, MSEC)
    claw_motor.stop()

def drive_until_collision(speed=AUTO_GOAL_SPEED, max_ms=COLLISION_MAX_MS):
    """Drive straight until the front bumper is pressed (waits up to max_ms), then back off with the arm lowering."""
    start = brain.timer.time(MSEC)

    free_drive_timeouts()
    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    bumper_status("driving to the button")
    log("driving forward until the front bumper hits (waits up to %d ms), front pressed now: %s" % (max_ms, bumper_front.pressing()))

    left_motor.spin(FORWARD, speed, PERCENT)
    right_motor.spin(FORWARD, speed, PERCENT)

    while True:
        if bumper_front.pressing():
            log("FRONT COLLISION DETECTED after %d ms" % (brain.timer.time(MSEC) - start))
            bumper_status("HIT")
            break
        if brain.timer.time(MSEC) - start > max_ms:
            log("NO COLLISION in %d ms, carrying on" % max_ms)
            break
        wait(10, MSEC)

    # Straight into the reverse, no stop in between; the arm lowers while backing off.
    arm_to(AUTO_ARM_PLACE_DEG, wait=False)
    drive(-COLLISION_BACKOFF_MM, AUTO_GOAL_SPEED)
    arm_wait()
    log("backed off, arm lowered")

AUTO_SIDE = 1               # +1 goal on the right, -1 on the left

def set_auto_side(side):
    """Called by the selector; lives here so the global is this module's."""
    global AUTO_SIDE
    AUTO_SIDE = side

def auto_side_text():
    """Which way autonomous will go, for the screens."""
    return "RIGHT >" if AUTO_SIDE > 0 else "< LEFT"

def toggle_start(rotations=TOGGLE_AUTO_TURNS):
    """Spin the toggle motor backward (L2 direction) a set number of rotations, without waiting."""
    toggle_motor.set_stopping(HOLD)      # servo to the target, so it can't coast on past a rotation
    toggle_motor.set_max_torque(TOGGLE_AUTO_TORQUE, PERCENT)
    toggle_motor.set_timeout(4000, MSEC)
    toggle_motor.reset_position()
    log("toggle start: target %.2f rev, speed %d%%, torque %d%%" % (rotations, TOGGLE_AUTO_SPEED, TOGGLE_AUTO_TORQUE))
    toggle_motor.spin_for(REVERSE, rotations, TURNS, TOGGLE_AUTO_SPEED, PERCENT, wait=False)

def toggle_wait():
    """Block until the toggle motor has finished (or timed out), logging its position every 100 ms."""
    start = brain.timer.time(MSEC)
    last = -1000
    while toggle_motor.is_spinning():
        now = brain.timer.time(MSEC)
        if now - last >= 100:
            last = now
            log("toggle %.2f rev  %d dps  %.2f A" % (
                toggle_motor.position(TURNS), toggle_motor.velocity(DPS), toggle_motor.current()))
        wait(10, MSEC)
    log("toggle stopped at %.2f rev after %d ms" % (
        toggle_motor.position(TURNS), brain.timer.time(MSEC) - start))

def autonomous():
    """Override: mid-wall start, flip the toggle, out a tile, turn, drive in, place the preload."""
    log("AUTO start, side %d" % AUTO_SIDE)
    manipulator_init()
    claw_motor.stop()
    # Already on the wall by the start rule; this only seats it square.
    log("squared to wall: %s" % square_to_wall())
    # Step 1 cm off the wall so nothing is pressing on the robot, then flip the toggle
    # (arm lifting meanwhile) with the wheels still.
    drive(TOGGLE_STANDOFF_MM, AUTO_GOAL_SPEED)
    log("stepped off the wall")
    toggle_start()
    arm_to(AUTO_ARM_CARRY_DEG, wait=False)
    toggle_wait()
    # Then back all the way again until both back bumpers are in, whatever the toggle did.
    log("re-squared after toggle: %s" % square_to_wall())
    log("toggle now at %.2f rev (did it settle, drift or get pulled back?)" % toggle_motor.position(TURNS))
    drive(AUTO_LEG1_MM, AUTO_GOAL_SPEED)
    log("leg 1 done, arm %d" % arm_motor.position(DEGREES))
    arm_wait()
    log("arm at carry, %d" % arm_motor.position(DEGREES))
    settle()
    turn(AUTO_GOAL_TURN_DEG * AUTO_SIDE)
    log("turned")
    settle()
    drive_until_collision()
    log("arm at place, %d" % arm_motor.position(DEGREES))
    open_claw()
    log("claw open, %d" % claw_motor.position(DEGREES))
    arm_to(AUTO_ARM_CARRY_DEG)
    drive(-AUTO_BACKOFF_MM, AUTO_GOAL_SPEED)
    log("AUTO done")

def autonomous_s_path():
    """S -> wall square -> lift arm -> A -> turn right -> B -> release arm."""
    manipulator_init()
    if not square_to_wall():
        return
    settle()
    lift_arm()
    drive(AUTO_LEG_MM)
    settle()
    turn(AUTO_TURN_DEG)
    settle()
    drive(AUTO_LEG_MM)
    settle()
    release_arm()
