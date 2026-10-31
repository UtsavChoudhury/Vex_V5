# drivercontrol.py -- arcade drive, slew limiting, manipulator, toggle motor.

from vex import *
from config import *


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

def screen_line(row, text):
    brain.screen.clear_line(row)
    brain.screen.set_cursor(row, 1)
    brain.screen.print(text)

def show_motor_diagnostic():
    """Every motor's rotation, the arm's load and the bumpers, on the brain screen."""
    try:
        arm_deg = arm_motor.position(DEGREES)
        screen_line(3, "L drive %6d deg   R drive %6d deg" % (
            left_motor.position(DEGREES), right_motor.position(DEGREES)))
        screen_line(4, "ARM %5d deg  %.2f rev  %4d dps" % (
            arm_deg, arm_deg / 360.0, arm_motor.velocity(DPS)))
        screen_line(5, "arm %.2f A%s" % (
            arm_motor.current(), "" if arm_state["homed"] else "  NOT ZEROED"))
        screen_line(6, "CLAW %5d deg  %.2f A" % (claw_motor.position(DEGREES), claw_motor.current()))
        screen_line(7, "bump C%d E%d F%d   (X = re-zero arm)" % (
            bumper_left.pressing(), bumper_right.pressing(), bumper_side.pressing()))
    except:
        # Never let a diagnostic take the drive down mid-match.
        screen_line(5, "diagnostic error")

def show_controller_line(row):
    """One of three short lines on the controller; one per call, as its screen is slow."""
    try:
        if row == 1:
            text = "ARM %d %.1fr %s" % (arm_motor.position(DEGREES), arm_motor.position(DEGREES) / 360.0,
                                       "" if arm_state["homed"] else "NO ZERO")
        elif row == 2:
            text = "L%d R%d" % (left_motor.position(DEGREES), right_motor.position(DEGREES))
        else:
            text = "CLAW %d" % claw_motor.position(DEGREES)
        controller.screen.clear_line(row)
        controller.screen.set_cursor(row, 1)
        controller.screen.print(text[:19])
    except:
        pass


# --- Driver loop ---

def user_control():
    brain.screen.clear_screen()
    brain.screen.print("Slow Drive / Fast Turn")
    brain.screen.next_row()
    brain.screen.print("L=port6  R=port4  invert=" + str(INVERT_DRIVE))

    left_motor.set_stopping(BRAKE)
    right_motor.set_stopping(BRAKE)
    manipulator_init()
    toggle_motor.set_stopping(BRAKE)
    toggle_motor.set_max_torque(100, PERCENT)

    forward_power = 0.0
    turn_power = 0.0
    reverse_mode = False
    turn_sign = 1.0
    arm_power = 0.0
    diag_tick = 0
    ctrl_row = 0
    controller.screen.clear_screen()

    while True:
        if controller.buttonX.pressing():
            while controller.buttonX.pressing():
                wait(20, MSEC)
            confirm_arm_zero()
            brain.screen.clear_screen()
            arm_power = 0.0

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

        # Refuse to drive further into either end, taper near them, always allow coming back.
        arm_hold = False
        arm_deg = arm_motor.position(DEGREES)
        if ARM_USE_LIMITS and arm_state["homed"] and arm_power != 0:
            if arm_power > 0:
                room = ARM_MAX_DEG - arm_deg
            else:
                room = arm_deg - ARM_MIN_DEG
            if room <= 0:
                arm_power = 0.0
                arm_hold = True
            elif room < ARM_SLOW_ZONE_DEG:
                cap = max(8.0, 100.0 * ARM_SPEED * room / ARM_SLOW_ZONE_DEG)
                arm_power = max(-cap, min(cap, arm_power))

        claw_power = claw_raw * CLAW_SPEED
        claw_hold = False
        if CLAW_USE_LIMITS and claw_state["zeroed"] and claw_power != 0:
            closed = claw_motor.position(DEGREES) * CLAW_CLOSE_SIGN
            closing = claw_power * CLAW_CLOSE_SIGN > 0
            if (closing and closed >= CLAW_MAX_DEG) or (not closing and closed <= 0):
                claw_power = 0.0
                claw_hold = True

        if arm_hold:
            arm_motor.stop()    # HOLD brakes; spin at 0 would coast
        else:
            arm_motor.spin(FORWARD, arm_power, PERCENT)
        if claw_hold:
            claw_motor.stop()
        else:
            claw_motor.spin(FORWARD, claw_power, PERCENT)

        # Toggle motor: L1 (top) forward, L2 (bottom) backward, full power, no limits.
        if controller.buttonL1.pressing():
            toggle_motor.spin(FORWARD, 100, PERCENT)
        elif controller.buttonL2.pressing():
            toggle_motor.spin(REVERSE, 100, PERCENT)
        else:
            toggle_motor.stop()

        if MOTOR_DIAGNOSTIC:
            diag_tick = diag_tick + 1
            if diag_tick >= 10:          # ~5 Hz, slow enough to read
                diag_tick = 0
                show_motor_diagnostic()
                ctrl_row = ctrl_row % 3 + 1
                show_controller_line(ctrl_row)

        wait(LOOP_MS, MSEC)
