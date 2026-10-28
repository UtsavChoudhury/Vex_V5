# drivercontrol.py -- arcade drive, slew limiting, manipulator, cone assist.

from vex import *
from config import *
from vision import find_cone


# --- Driver helpers ---

def slew(current, target, accel_step, decel_step):
    """Move `current` toward `target` by at most one accel or decel step."""
    if target * current < 0 or abs(target) <= abs(current):
        limit = decel_step
    else:
        limit = accel_step

    delta = target - current
    if delta > limit:
        return current + limit
    if delta < -limit:
        return current - limit
    return target

def approach(current, target, step):
    """Move a blend factor toward a target without overshooting it."""
    if current < target:
        return min(target, current + step)
    if current > target:
        return max(target, current - step)
    return target

def turn_taper(forward):
    """Fraction of the requested turn to keep at this forward speed."""
    x = min(1.0, abs(forward) / 100.0) ** TURN_TAPER_SHAPE
    return TURN_GAIN_REST + (TURN_GAIN_FULL - TURN_GAIN_REST) * x

def fit_turn(forward, turn, priority):
    """Scale forward and turn so a wheel cannot clip past 100, favouring forward."""
    if abs(forward) + abs(turn) <= 100.0:
        return turn
    room = 100.0 - min(abs(forward), 100.0)
    wanted = abs(turn)
    allowed = wanted + (room - wanted) * priority
    return allowed if turn >= 0 else -allowed

def show_claw_diagnostic(stick, power):
    """Print claw stick position and motor load to the brain screen."""
    brain.screen.set_cursor(4, 1)
    brain.screen.clear_line(4)
    brain.screen.print("claw stick %d  pwr %d  arm %d" % (int(stick), int(power),
                                                         int(arm_motor.position(DEGREES))))
    brain.screen.set_cursor(7, 1)
    brain.screen.clear_line(7)
    brain.screen.print("A%d B%d C%d D%d E%d F%d G%d H%d" % (
        probe_a.pressing(), bumper_b.pressing(), probe_c.pressing(),
        probe_d.pressing(), bumper_e.pressing(), probe_f.pressing(),
        probe_g.pressing(), probe_h.pressing()))
    brain.screen.set_cursor(5, 1)
    brain.screen.clear_line(5)
    try:
        brain.screen.print("amps %.2f  temp %d%%" % (claw_motor.current(),
                                                     claw_motor.temperature()))
    except:
        # Never let a diagnostic take the drive down mid-match.
        brain.screen.print("amps n/a on this SDK")


# --- Cone assist ---

BUTTON_NAMES = ["buttonL1", "buttonL2", "buttonR1", "buttonR2", "buttonUp", "buttonDown",
                "buttonLeft", "buttonRight", "buttonA", "buttonB", "buttonX", "buttonY"]

def sticks_moved():
    return (abs(controller.axis1.position()) > ASSIST_STICK_CANCEL or
            abs(controller.axis2.position()) > ASSIST_STICK_CANCEL or
            abs(controller.axis3.position()) > ASSIST_STICK_CANCEL or
            abs(controller.axis4.position()) > ASSIST_STICK_CANCEL)

def spin_in_place(power):
    """Positive = right."""
    left_motor.spin(FORWARD, power, PERCENT)
    right_motor.spin(FORWARD, -power, PERCENT)

def assist_steer(error):
    """Proportional turn power for a centerX error, with a floor to beat friction."""
    power = ASSIST_STEER_KP * error
    if abs(power) < ASSIST_MIN_TURN:
        power = ASSIST_MIN_TURN if error > 0 else -ASSIST_MIN_TURN
    return max(-ASSIST_MAX_TURN, min(ASSIST_MAX_TURN, power))

def assist_report(text):
    controller.screen.clear_screen()
    controller.screen.set_cursor(1, 1)
    controller.screen.print(text)

def cone_assist(direction, start_name):
    """Spin `direction` (1 right, -1 left) until the cone is seen, then centre; any input cancels."""
    arm_motor.stop()
    claw_motor.stop()
    assist_report("cone: searching")
    released = False
    hits = 0
    misses = 0
    centred = 0
    found = False
    while True:
        if not getattr(controller, start_name).pressing():
            released = True
        for name in BUTTON_NAMES:
            if getattr(controller, name).pressing() and (name != start_name or released):
                left_motor.stop()
                right_motor.stop()
                assist_report("cone: cancelled")
                return False
        if sticks_moved():
            left_motor.stop()
            right_motor.stop()
            assist_report("cone: cancelled")
            return False

        cone = find_cone()
        if cone is None:
            hits = 0
            centred = 0
            misses = misses + 1
            if found and misses >= ASSIST_LOST_FRAMES:
                found = False
                assist_report("cone: searching")
        else:
            misses = 0
            hits = hits + 1
            if not found and hits >= VISION_CONFIRM_FRAMES:
                found = True
                assist_report("cone: aligning")

        if found and cone is not None:
            error = cone.centerX - VISION_CENTER_X
            direction = 1 if error > 0 else -1
            if abs(error) <= ASSIST_TOLERANCE_PX:
                centred = centred + 1
                left_motor.stop()
                right_motor.stop()
                if centred >= ASSIST_HOLD_FRAMES:
                    assist_report("cone: centred")
                    controller.rumble("..")
                    return True
            else:
                centred = 0
                spin_in_place(assist_steer(error))
        elif found:
            left_motor.stop()
            right_motor.stop()
        else:
            spin_in_place(direction * ASSIST_SEARCH_SPEED)

        wait(VISION_LOOP_MS, MSEC)


# --- Driver loop ---

def user_control():
    brain.screen.clear_screen()
    brain.screen.print("Slow Drive / Fast Turn")
    brain.screen.next_row()
    brain.screen.print("L=port2  R=port1  invert=" + str(INVERT_DRIVE))

    left_motor.set_stopping(BRAKE)
    right_motor.set_stopping(BRAKE)
    manipulator_init()

    forward_power = 0.0
    turn_power = 0.0
    reverse_mode = False
    turn_sign = 1.0
    arm_power = 0.0
    diag_tick = 0
    was_left = False
    was_right = False

    while True:
        # Edge-triggered so a button held through cancelling doesn't restart it.
        left_now = controller.buttonLeft.pressing()
        right_now = controller.buttonRight.pressing()
        if (left_now and not was_left) or (right_now and not was_right):
            if left_now and not was_left:
                cone_assist(-1, "buttonLeft")
            else:
                cone_assist(1, "buttonRight")
            forward_power = 0.0
            turn_power = 0.0
            arm_power = 0.0
            left_now = controller.buttonLeft.pressing()
            right_now = controller.buttonRight.pressing()
        was_left = left_now
        was_right = right_now

        forward_raw = controller.axis3.position()
        turn_raw = controller.axis4.position()

        if abs(forward_raw) < DEADBAND:
            forward_raw = 0
        if abs(turn_raw) < DEADBAND:
            turn_raw = 0

        fast_turn = controller.buttonR1.pressing()
        crawl = controller.buttonR2.pressing()

        if fast_turn:
            forward_multiplier = SPEED_BOOST
        elif crawl:
            forward_multiplier = SPEED_CRAWL
        else:
            forward_multiplier = SPEED_NORMAL

        # Squared for fine control near centre, sign preserved.
        forward_target = ((forward_raw * abs(forward_raw)) / 100.0) * forward_multiplier
        turn_target = (turn_raw * abs(turn_raw)) / 200.0

        if not fast_turn:
            turn_target = turn_target * TURN_NORMAL

        # Ramp toward the request rather than stepping straight to it.
        forward_power = slew(forward_power, forward_target,
                             FWD_ACCEL_STEP, FWD_DECEL_STEP)
        turn_power = slew(turn_power, turn_target,
                          TURN_ACCEL_STEP, TURN_DECEL_STEP)

        if MIRROR_TURN_IN_REVERSE:
            if forward_power < -REVERSE_ENTER:
                reverse_mode = True
            elif forward_power > -REVERSE_EXIT:
                reverse_mode = False

            turn_sign = approach(turn_sign, -1.0 if reverse_mode else 1.0,
                                 TURN_FLIP_STEP)

        # Bias the mix toward holding forward speed, unless R1 asks otherwise.
        turn_applied = turn_power
        if not fast_turn:
            turn_applied = turn_applied * turn_taper(forward_power)
            turn_applied = fit_turn(forward_power, turn_applied, FORWARD_PRIORITY)
        turn_applied = turn_applied * turn_sign

        left_power = forward_power + turn_applied
        right_power = forward_power - turn_applied

        left_power = max(-100, min(100, left_power))
        right_power = max(-100, min(100, right_power))

        left_motor.spin(FORWARD, left_power, PERCENT)
        right_motor.spin(FORWARD, right_power, PERCENT)

        # ---- Right stick: arm (vertical) and claw (horizontal) ------------- #
        arm_raw = controller.axis2.position()
        claw_raw = controller.axis1.position()

        if abs(arm_raw) < ARM_DEADBAND:
            arm_raw = 0
        if abs(claw_raw) < CLAW_DEADBAND:
            claw_raw = 0

        arm_target = ((arm_raw * abs(arm_raw)) / 100.0) * ARM_SPEED
        arm_power = slew(arm_power, arm_target, ARM_ACCEL_STEP, ARM_DECEL_STEP)

        # Refuse to drive further into a limit, but always allow coming back.
        if ARM_USE_LIMITS:
            arm_position = arm_motor.position(DEGREES)
            if arm_position <= ARM_MIN_DEG and arm_power < 0:
                arm_power = 0.0
            elif arm_position >= ARM_MAX_DEG and arm_power > 0:
                arm_power = 0.0

        claw_power = claw_raw * CLAW_SPEED

        arm_motor.spin(FORWARD, arm_power, PERCENT)
        claw_motor.spin(FORWARD, claw_power, PERCENT)

        if CLAW_DIAGNOSTIC:
            diag_tick = diag_tick + 1
            if diag_tick >= 10:          # ~5 Hz, slow enough to read
                diag_tick = 0
                show_claw_diagnostic(claw_raw, claw_power)

        wait(LOOP_MS, MSEC)
