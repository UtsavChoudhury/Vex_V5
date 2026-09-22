# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       utsavchoudhury                                               #
# 	Created:      9/9/2026                                                     #
# 	Description:  Slow Driving with Aggressive High-Speed Turning              #
#                                                                              #
# ---------------------------------------------------------------------------- #

from vex import *

brain = Brain()
controller = Controller()

# ---------------------------------------------------------------------------- #
#  HARDWARE
#
#    PORT1  right drive motor
#    PORT2  left drive motor
#    PORT9  VEXnet radio -- handled by brain firmware, never declared in code
# ---------------------------------------------------------------------------- #

RIGHT_PORT = Ports.PORT1
LEFT_PORT = Ports.PORT2

# Flip if the robot drives backward when you push the stick forward.
INVERT_DRIVE = False

left_motor = Motor(LEFT_PORT, GearSetting.RATIO_18_1, INVERT_DRIVE)
right_motor = Motor(RIGHT_PORT, GearSetting.RATIO_18_1, not INVERT_DRIVE)

dt = DriveTrain(left_motor, right_motor, 300, 320, 320, MM)

# ---------------------------------------------------------------------------- #
#  MANIPULATOR HARDWARE
#
#    PORT3  arm motor   -- driven by the right stick, up/down   (axis2)
#    PORT4  claw motor  -- driven by the right stick, left/right (axis1)
#
#  The drive uses axis3/axis4, which on a V5 controller are the LEFT stick, so
#  the right stick was free. Change the ports to match your robot. If a mechanism
#  runs the wrong way, flip its INVERT flag rather than negating it in the loop.
#
#  Red 36:1 cartridges are the usual pick for a lift and a grip -- slow, strong,
#  and they back-drive far less under load.
# ---------------------------------------------------------------------------- #

ARM_PORT = Ports.PORT10
CLAW_PORT = Ports.PORT15

ARM_INVERT = False
CLAW_INVERT = False

arm_motor = Motor(ARM_PORT, GearSetting.RATIO_36_1, ARM_INVERT)
claw_motor = Motor(CLAW_PORT, GearSetting.RATIO_36_1, CLAW_INVERT)

# ---------------------------------------------------------------------------- #
#  DRIVER TUNING
#
#  Fractions of full motor power. The built-in Drive program runs at 1.00, which
#  is why it feels so much quicker than this project -- these are the only thing
#  setting the difference.
# ---------------------------------------------------------------------------- #

LOOP_MS = 20

DEADBAND = 2

SPEED_BOOST = 1.00   # L1/R1 held
SPEED_CRAWL = 0.25   # L2/R2 held
SPEED_NORMAL = 0.50  # nothing held

TURN_NORMAL = 0.8

# ---------------------------------------------------------------------------- #
#  ACCELERATION LIMITING
#
#  Largest change in output power allowed per loop tick. Anything gentler than
#  these passes through untouched, so fine stick work is exactly as before --
#  only a floored stick gets ramped. Returning toward zero is allowed to be much
#  quicker than leaving it, so stopping never feels mushy.
# ---------------------------------------------------------------------------- #

FWD_ACCEL_STEP = 4.0    # 0 -> 100 in ~500 ms
FWD_DECEL_STEP = 12.0   # 100 -> 0 in ~170 ms

TURN_ACCEL_STEP = 8.0   # 0 -> 40 in ~100 ms, so turns stay aggressive
TURN_DECEL_STEP = 20.0

# ---------------------------------------------------------------------------- #
#  REVERSE TURN HANDLING
#
#  Two ways to read the turn stick when the robot is backing up:
#
#    HEADING-RELATIVE (MIRROR_TURN_IN_REVERSE = False, what we use)
#      The nose always rotates the way the stick points. The whole right half of
#      the stick -- 1.5 o'clock through 3 to 4.5 -- rotates right, and the whole
#      left half rotates left, so sweeping the stick from top to bottom down one
#      side never reverses which way the robot is coming around.
#
#    PATH-RELATIVE (MIRROR_TURN_IN_REVERSE = True)
#      Car-like: while reversing the stick is mirrored so the robot's *path*
#      curves the way the stick points, at the cost of the nose flipping
#      direction as the stick crosses 3 o'clock.
#
#  The constants below only do anything in the mirrored mode. ENTER/EXIT form a
#  hysteresis band so the mirror cannot chatter around zero throttle, and the
#  sign is blended rather than snapped so it cannot jolt.
# ---------------------------------------------------------------------------- #

MIRROR_TURN_IN_REVERSE = False

REVERSE_ENTER = 12.0    # forward power below -this counts as reversing
REVERSE_EXIT = 4.0      # forward power above -this leaves reverse
TURN_FLIP_STEP = 0.2    # sign blend per tick -- ~200 ms to swap over

# ---------------------------------------------------------------------------- #
#  FORWARD vs TURN BALANCE
#
#  A flat arcade mix hands the turn stick the same absolute authority at 5%
#  throttle as at full throttle. At speed that drags the inner wheel way down,
#  so the robot scrubs and pivots instead of arcing, and it sheds the forward
#  momentum you had built up. Two things correct the bias toward turning:
#
#    1. TAPER -- turn authority falls off as forward speed rises, so a turn at
#       speed is a wide arc. At a standstill it stays at full, leaving
#       spin-in-place exactly as it was.
#    2. PRIORITY -- when the mix would clip past 100%, the turn gives way
#       instead of the forward, so finishing a turn never costs you speed.
#
#  Holding L1/R1 bypasses both, so a deliberate aggressive turn is still there
#  on demand -- that is what makes it the "fast turn" button.
# ---------------------------------------------------------------------------- #

TURN_GAIN_REST = 1.00   # turn authority with the throttle centred
TURN_GAIN_FULL = 0.35   # turn authority at full throttle
TURN_TAPER_SHAPE = 1.0  # 1 = linear; >1 holds authority up through low speeds

FORWARD_PRIORITY = 0.8  # 0.0 = old clipping, 1.0 = forward never yields at all

# ---------------------------------------------------------------------------- #
#  MANIPULATOR TUNING
#
#  Both sticks are read the same way the drive stick is: deadband, then squared
#  for fine control near centre. The arm is ramped like the drive so a loaded
#  lift cannot slam into its hard stops; the claw is left linear because you
#  usually want it to bite the moment you ask.
#
#  The arm stick deadband is deliberately wider than the drive's -- a drifting
#  arm stick creeps the lift up or down all match, which is far more annoying
#  than a little drive creep.
# ---------------------------------------------------------------------------- #

ARM_DEADBAND = 5
CLAW_DEADBAND = 5

ARM_SPEED = 0.75        # fraction of full power available to the arm
CLAW_SPEED = 0.60       # claws need less; extra power just stalls and heats

ARM_ACCEL_STEP = 6.0    # 0 -> 75% in ~250 ms
ARM_DECEL_STEP = 15.0

# Torque available to the claw, as a percent. This caps BOTH directions, so if
# your claw is held shut by rubber bands the motor has to beat them to open and
# too low a number here looks exactly like "opening is broken". V5 motors have
# their own thermal protection, so start at 100 and only dial back if the claw
# motor runs hot after holding a grip for a whole match.
CLAW_TORQUE = 100

# Prints the claw stick and motor load to the brain screen. Turn off for comp.
CLAW_DIAGNOSTIC = True

# Soft travel limits. Off until you have measured your own range: drive the arm
# to each end by hand, read arm_motor.position(DEGREES), and put the numbers in.
ARM_USE_LIMITS = False
ARM_MIN_DEG = 0.0
ARM_MAX_DEG = 900.0

# ---------------------------------------------------------------------------- #
#  AUTONOMOUS HELPERS
# ---------------------------------------------------------------------------- #

def drive(distance_mm, speed=50):
    """Drive straight. Positive = forward, negative = backward."""
    direction = FORWARD if distance_mm >= 0 else REVERSE
    dt.drive_for(direction, abs(distance_mm), MM, speed, PERCENT)

def turn(degrees, speed=50):
    """Turn in place. Positive = right, negative = left."""
    direction = RIGHT if degrees >= 0 else LEFT
    dt.turn_for(direction, abs(degrees), DEGREES, speed, PERCENT)

def settle(timeout_ms=300):
    """Brief pause after a move so momentum doesn't bleed into the next segment."""
    wait(timeout_ms, MSEC)

def run_path(path):
    """
    path = list of tuples:
      ("drive", distance_mm, speed)
      ("turn", degrees, speed)
      ("wait", ms)                 # pause without moving -- useful at pickup/drop points
    """
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

# ---------------------------------------------------------------------------- #
#  DRIVER HELPERS
# ---------------------------------------------------------------------------- #

def slew(current, target, accel_step, decel_step):
    """
    Move `current` toward `target` by at most one step. Growing the command away
    from zero -- or swinging it through zero into the other direction -- is the
    case that breaks traction, so it gets the small step; shrinking it back
    toward zero gets the large one.
    """
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
    """
    How much of the requested turn to keep at this forward speed. Full authority
    when stopped, tapering to TURN_GAIN_FULL flat out so fast turns become arcs
    rather than pivots.
    """
    x = min(1.0, abs(forward) / 100.0) ** TURN_TAPER_SHAPE
    return TURN_GAIN_REST + (TURN_GAIN_FULL - TURN_GAIN_REST) * x

def fit_turn(forward, turn, priority):
    """
    A wheel peaks at abs(forward) + abs(turn). When that would clip past 100 the
    plain mix trims both sides equally, which quietly eats forward speed. Here
    the turn is what gives way, by `priority`, so the forward command survives.
    """
    if abs(forward) + abs(turn) <= 100.0:
        return turn
    room = 100.0 - min(abs(forward), 100.0)
    wanted = abs(turn)
    allowed = wanted + (room - wanted) * priority
    return allowed if turn >= 0 else -allowed

def show_claw_diagnostic(stick, power):
    """
    Three lines that separate the possible causes of a claw that will not open:

      stick stays 0 when you push    -> the controller axis is not reaching us
      stick moves, amps near 0       -> nothing is wired to CLAW_PORT
      stick moves, amps high, no move-> jammed, or CLAW_TORQUE is too low to
                                        beat the rubber bands
      temp climbing toward 100%      -> motor is throttling itself back
    """
    brain.screen.set_cursor(4, 1)
    brain.screen.clear_line(4)
    brain.screen.print("claw stick %d  pwr %d" % (int(stick), int(power)))
    brain.screen.set_cursor(5, 1)
    brain.screen.clear_line(5)
    try:
        brain.screen.print("amps %.2f  temp %d%%" % (claw_motor.current(),
                                                     claw_motor.temperature()))
    except:
        # Never let a diagnostic take the drive down mid-match.
        brain.screen.print("amps n/a on this SDK")

def manipulator_init():
    """
    HOLD rather than BRAKE: a braked motor still creeps under load, so an arm
    left holding a game object would sag over a match. Capping claw torque lets
    it stay clamped shut indefinitely without drawing stall current.
    """
    arm_motor.set_stopping(HOLD)
    claw_motor.set_stopping(HOLD)
    claw_motor.set_max_torque(CLAW_TORQUE, PERCENT)

# ---------------------------------------------------------------------------- #
#  COMPETITION MODES
# ---------------------------------------------------------------------------- #

def autonomous():
    dt.set_stopping(BRAKE)
    manipulator_init()
    for _ in range(3):
        settle(3000)
        drive(2000)
        turn(180)
        drive(5000)

def user_control():
    brain.screen.clear_screen()
    brain.screen.print("Slow Drive / Fast Turn")
    brain.screen.next_row()
    brain.screen.print("L=port2  R=port1  invert=" + str(INVERT_DRIVE))

    dt.set_stopping(BRAKE)
    manipulator_init()

    forward_power = 0.0
    turn_power = 0.0
    reverse_mode = False
    turn_sign = 1.0
    arm_power = 0.0
    diag_tick = 0

    while True:
        forward_raw = controller.axis3.position()
        turn_raw = controller.axis4.position()

        if abs(forward_raw) < DEADBAND:
            forward_raw = 0
        if abs(turn_raw) < DEADBAND:
            turn_raw = 0

        fast_turn = controller.buttonL1.pressing() or controller.buttonR1.pressing()
        crawl = controller.buttonL2.pressing() or controller.buttonR2.pressing()

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

        # Car-like reversing, off by default. When on, decide whether we are
        # travelling backward from the ramped value so it tracks what the robot
        # is actually doing rather than the raw stick. When off turn_sign stays
        # at 1.0 and the nose simply follows the stick in both directions.
        if MIRROR_TURN_IN_REVERSE:
            if forward_power < -REVERSE_ENTER:
                reverse_mode = True
            elif forward_power > -REVERSE_EXIT:
                reverse_mode = False

            turn_sign = approach(turn_sign, -1.0 if reverse_mode else 1.0,
                                 TURN_FLIP_STEP)

        # Bias the mix toward holding forward speed, unless L1/R1 asks otherwise.
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

# ---------------------------------------------------------------------------- #

autonomous()
