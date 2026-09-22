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

# ---------------------------------------------------------------------------- #
#  DRIVE GEOMETRY  --  every autonomous distance and angle is derived from these
#
#  The previous numbers (300, 320, 320) were the SDK's own defaults, not this
#  robot. A turn is converted into wheel travel with
#
#      arc per wheel (mm) = PI * TRACK_WIDTH_MM * angle / 360
#
#  PI * TRACK_WIDTH_MM is the circle the wheels trace when the robot spins once
#  in place; the two wheels split that circle by running opposite ways, so the
#  formula already accounts for both of them moving and is NOT doubled. An angle
#  that comes out too big therefore means one of the numbers below is wrong:
#  every mm TRACK_WIDTH_MM is too large is angle the robot turns too far, and
#  every mm WHEEL_DIAMETER_MM is too small does the same again.
#
#  MEASURE these, do not guess:
#    WHEEL_DIAMETER_MM    across the tyre through the axle. VEX: 4" = 101.6,
#                         3.25" = 82.55, 2.75" = 69.85.
#    TRACK_WIDTH_MM       left wheel contact patch to right wheel contact patch.
#                         This is the single biggest source of turn error.
#    EXTERNAL_GEAR_RATIO  motor turns per wheel turn. Direct drive = 1.0; a 60t
#                         wheel gear driven by a 36t motor gear = 60/36 = 1.667.
#
#  CHECK THE CARTRIDGE TOO: the GearSetting above has to match the physical
#  cartridge colour -- green RATIO_18_1, blue RATIO_6_1, red RATIO_36_1.
#  Declaring green with a blue cartridge fitted overshoots every move by exactly
#  3x, and drives and turns overshoot together. If drive(1000) also travels far
#  too far, suspect the cartridge or the wheel size, not the track width.
# ---------------------------------------------------------------------------- #

PI = 3.141592653589793

WHEEL_DIAMETER_MM = 101.6     # 4" VEX wheel
TRACK_WIDTH_MM = 320.0        # left contact patch to right contact patch
WHEEL_BASE_MM = 320.0         # front axle to rear axle; unused by in-place turns
EXTERNAL_GEAR_RATIO = 1.0     # motor revolutions per wheel revolution

WHEEL_TRAVEL_MM = PI * WHEEL_DIAMETER_MM

# Empirical trims applied on top of the geometry. Leave both at 1.0 until the
# measurements above are real, then run calibrate_turn() / calibrate_drive():
#
#     SCALE = commanded / actually_achieved
#
# A robot asked for 180 that swung all the way to 360 wants TURN_SCALE = 0.5.
DRIVE_SCALE = 1.00
TURN_SCALE = 1.00

# Autonomous move settings.
AUTO_DRIVE_SPEED = 50     # percent
AUTO_TURN_SPEED = 25      # percent -- a slow turn coasts past its target far less

# Free speed of the drive cartridge, in shaft degrees per second. Green 18:1 is
# 200 rpm = 1200 dps; blue 6:1 is 600 rpm = 3600 dps; red 36:1 is 100 rpm = 600
# dps. Only used to size move timeouts, so a rough value is fine -- but it has to
# match the GearSetting above or long moves get cut short.
MOTOR_MAX_DPS = 1200.0

# A move is abandoned once it has taken this much longer than it should have.
# Proportional, never flat: a flat timeout silently truncates any move that
# legitimately takes longer, which looks exactly like under-travel.
TIMEOUT_MARGIN = 2.0      # allow 2x the theoretical time...
TIMEOUT_FLOOR_MS = 1000   # ...plus this, to cover acceleration on short moves

# Kept in sync with the constants above so dt.drive_for/turn_for agree with the
# helpers below, in case anything reaches for the drivetrain object directly.
dt = DriveTrain(left_motor, right_motor, WHEEL_TRAVEL_MM, TRACK_WIDTH_MM,
                WHEEL_BASE_MM, MM, EXTERNAL_GEAR_RATIO)

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
#  AI VISION  --  cone detection
#
#  The sensor already holds the configuration you built in the AI Vision
#  Utility:
#
#      colour        1   yellowcone
#      colour        2   bluecone
#      colour code   1   cone   ( yellowcone + bluecone )
#
#  So this file deliberately declares NO Colordesc or Codedesc objects. Passing
#  them to AiVision() writes new RGB values down to the sensor and overwrites
#  what you tuned in the utility. Instead it asks the sensor for every colour
#  code it can see and matches on the code's index.
#
#  Those indices come from the order things were created in the utility, which
#  makes "cone" -- the first and only colour code -- id 1. If detection never
#  fires, run vision_report(): it prints the id of everything the sensor is
#  actually returning, and that is how you confirm the number below.
#
#  A colour code only matches when BOTH of its colours are found adjacent to
#  each other, which is exactly the yellow-over-blue cone and is why a code is
#  the right tool here -- a plain yellow object cannot trigger it.
# ---------------------------------------------------------------------------- #

AI_VISION_PORT = Ports.PORT4     # <-- set to the port the sensor is plugged into

CONE_CODE_ID = 1                 # colour code "cone"
YELLOW_CONE_ID = 1               # colour "yellowcone"
BLUE_CONE_ID = 2                 # colour "bluecone"

ai_vision = AiVision(AI_VISION_PORT)

# The camera frame is 320 x 240. A code match a handful of pixels wide is noise
# rather than a cone, so anything smaller than this is thrown away. Raise both
# numbers if the sensor reports the cone from further away than you want.
VISION_MIN_WIDTH = 20
VISION_MIN_HEIGHT = 20

# Frames the cone has to be steadily present, or steadily gone, before the
# message changes. At the 50 ms loop below that is 150 ms of agreement: long
# enough to ride out a dropped frame, short enough to still feel instant.
VISION_CONFIRM_FRAMES = 3

VISION_LOOP_MS = 50
VISION_MAX_OBJECTS = 8

# ---------------------------------------------------------------------------- #
#  AI VISION HELPERS
# ---------------------------------------------------------------------------- #

def find_cone():
    """Largest 'cone' colour code currently in view, or None.

    The returned AiVisionObject carries centerX / centerY (pixels from the top
    left), width, height, angle and score, so the same call works for aiming at
    the cone later -- centerX below 160 means it sits left of centre.
    """
    largest = None
    largest_area = 0

    for obj in ai_vision.take_snapshot(AiVision.ALL_CODES, VISION_MAX_OBJECTS):
        if obj.id != CONE_CODE_ID:
            continue
        if obj.width < VISION_MIN_WIDTH or obj.height < VISION_MIN_HEIGHT:
            continue
        area = obj.width * obj.height
        if area > largest_area:
            largest = obj
            largest_area = area

    return largest

def cone_detector():
    """Watch continuously and announce the cone each time it comes into view.

    Prints once on arrival rather than once per frame -- a 20 Hz loop shouting
    the same line 20 times a second tells you nothing about when it actually
    appeared.
    """
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("AI VISION  --  watching for cone")

    visible = False
    hits = 0
    misses = 0

    while True:
        cone = find_cone()

        if cone is not None:
            hits = hits + 1
            misses = 0
        else:
            misses = misses + 1
            hits = 0

        if not visible and hits >= VISION_CONFIRM_FRAMES:
            visible = True
            print("cone identified")
            brain.screen.clear_line(3)
            brain.screen.set_cursor(3, 1)
            brain.screen.print("cone identified")
            brain.screen.clear_line(4)
            brain.screen.set_cursor(4, 1)
            brain.screen.print("x %d  y %d   %d x %d" % (
                cone.centerX, cone.centerY, cone.width, cone.height))
            controller.rumble(".")

        elif visible and misses >= VISION_CONFIRM_FRAMES:
            visible = False
            print("cone lost")
            brain.screen.clear_line(3)
            brain.screen.set_cursor(3, 1)
            brain.screen.print("no cone")
            brain.screen.clear_line(4)

        wait(VISION_LOOP_MS, MSEC)

def vision_report(seconds=20):
    """Diagnostic: print every object the sensor returns, with its id.

    Run this first, hold the cone in front of the sensor and watch the console.
    A CODE line is the colour code -- the id on it is the number that belongs in
    CONE_CODE_ID. If you only ever see COLOR lines and never a CODE line, the
    sensor is seeing the two colours but not treating them as one object: the
    halves are too far apart, or one of the two colour ranges is too tight to
    match at the distance you are testing from.
    """
    end_ms = brain.timer.time(MSEC) + seconds * 1000

    while brain.timer.time(MSEC) < end_ms:
        codes = ai_vision.take_snapshot(AiVision.ALL_CODES, VISION_MAX_OBJECTS)
        colors = ai_vision.take_snapshot(AiVision.ALL_COLORS, VISION_MAX_OBJECTS)

        for obj in codes:
            print("CODE  id=%d  center=(%d,%d)  %dx%d" % (
                obj.id, obj.centerX, obj.centerY, obj.width, obj.height))
        for obj in colors:
            print("COLOR id=%d  center=(%d,%d)  %dx%d" % (
                obj.id, obj.centerX, obj.centerY, obj.width, obj.height))

        if len(codes) == 0 and len(colors) == 0:
            print("-- nothing in view")

        wait(500, MSEC)


# ---------------------------------------------------------------------------- #
#  AUTONOMOUS HELPERS
# ---------------------------------------------------------------------------- #

def wheel_degrees_for_distance(distance_mm):
    """Motor shaft degrees needed to roll the robot `distance_mm` along the floor."""
    return (distance_mm / WHEEL_TRAVEL_MM) * 360.0 * EXTERNAL_GEAR_RATIO * DRIVE_SCALE

def wheel_degrees_for_turn(robot_degrees):
    """
    Motor shaft degrees, per side, to rotate the robot `robot_degrees` in place.

    The wheels sit TRACK_WIDTH_MM/2 out from the centre of rotation, so a full
    360 spin rolls each wheel PI * TRACK_WIDTH_MM along the floor. The two sides
    cover that arc in opposite directions -- they do not each have to travel the
    whole circle -- so there is no factor of two hiding in here.
    """
    arc_mm = PI * TRACK_WIDTH_MM * (robot_degrees / 360.0)
    return (arc_mm / WHEEL_TRAVEL_MM) * 360.0 * EXTERNAL_GEAR_RATIO * TURN_SCALE

def move_timeout_ms(wheel_deg, speed):
    """
    How long to give a move before calling it jammed: twice the time it should
    take at the commanded speed, plus a second for acceleration.

    Scaled to the move rather than fixed, because a fixed timeout is a trap --
    a long drive or a multi-revolution calibration spin runs past it and gets
    cut off part-way, which on the floor is indistinguishable from the geometry
    being wrong.
    """
    dps = max(1.0, (abs(speed) / 100.0) * MOTOR_MAX_DPS)
    return int((abs(wheel_deg) / dps) * 1000.0 * TIMEOUT_MARGIN) + TIMEOUT_FLOOR_MS

def move_wheels(left_deg, right_deg, speed, timeout_ms=None):
    """
    Spin both sides through a set number of shaft degrees and wait for both.

    HOLD rather than BRAKE: the motors keep servoing to the target after they
    arrive, so whatever the robot coasts past under its own momentum gets pulled
    back. BRAKE only stops resisting once the command ends, which leaves the
    overshoot baked in and carries each segment's error into the next one.

    The timeout means a wheel that jams against a wall ends the move instead of
    stalling there for the rest of the match.
    """
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
    """
    Turn in place. Positive = right, negative = left.

    Right turn = left side forward, right side backward. right_motor is already
    declared reversed, so FORWARD on it means robot-forward and the sign flip
    here is the only thing that makes the sides oppose each other.
    """
    wheel_deg = wheel_degrees_for_turn(degrees)
    move_wheels(wheel_deg, -wheel_deg, speed)

def settle(timeout_ms=300):
    """Brief pause after a move so momentum doesn't bleed into the next segment."""
    wait(timeout_ms, MSEC)

# ---------------------------------------------------------------------------- #
#  CALIBRATION
#
#  THE TURN CALIBRATES ON ITS OWN. TURN_SCALE is a single multiplier on the end
#  of the turn maths, so it absorbs every error at once -- wheel diameter, track
#  width, gear ratio, and the wheel scrub that no geometry can predict. Nothing
#  about it depends on the drive being right, so you never have to measure a
#  distance to fix an angle, and DRIVE_SCALE can stay at 1.0 meanwhile.
#
#  Better still, you never have to measure an ANGLE either. Spin the robot a
#  whole number of revolutions and the target is not a protractor reading, it is
#  "the nose came back to the tape". Whole revolutions also multiply the error
#  into view: at 3 spins a 5% scale error misses by 54 degrees, which anyone can
#  see; at a quarter turn it is 4.5 degrees, which nobody can.
#
#  Calibrate on the surface you compete on. Foam tiles and a classroom floor do
#  not scrub the same, and scrub is most of what is left once the geometry is
#  right. Under-rotation especially is usually scrub: the wheels turn the
#  degrees they were told to and the robot slides through part of it.
# ---------------------------------------------------------------------------- #

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

def wait_release():
    """Hold here until every tuner button is let go, so one press counts once."""
    while (controller.buttonA.pressing() or controller.buttonB.pressing() or
           controller.buttonX.pressing() or controller.buttonY.pressing() or
           controller.buttonUp.pressing() or controller.buttonDown.pressing() or
           controller.buttonR1.pressing() or controller.buttonR2.pressing()):
        wait(20, MSEC)

def turn_tuner():
    """
    Find TURN_SCALE on the robot, without a protractor and without ever
    measuring a distance. Call this instead of autonomous() at the bottom of the
    file, download once, and tune from the controller -- no rebuild per guess.

    Lay a strip of tape on the floor and line the nose up against it. Press A.
    The robot spins whole revolutions, so it is right when the nose lands back on
    the tape.

        landed SHORT of the tape  ->  raise the scale (up / R1)
        went PAST the tape        ->  lower it        (down / R2)

    Each run starts from where the last one stopped, so re-align to the tape
    between runs -- or press B to spin the same amount back the other way, which
    returns the robot to the mark and unwinds the cable dressing at the same
    time.

    Halve the step size as you close in. When it lands on the tape at 3 spins,
    read the number off the brain screen, put it in TURN_SCALE at the top of the
    file, and set the bottom of the file back to autonomous().
    """
    global TURN_SCALE

    spins = 1
    speed = AUTO_TURN_SPEED
    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    tuner_screen(spins, speed)

    while True:
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

        tuner_screen(spins, speed)
        wait(50, MSEC)

def calibrate_turn(degrees=360, speed=AUTO_TURN_SPEED):
    """
    One-shot version of the above, for when you would rather read an angle than
    iterate. Mark the nose, run it, measure what the robot actually swept, then

        TURN_SCALE = TURN_SCALE * degrees / measured_degrees

    Note the multiply: the scale you already have is baked into what you just
    watched, so this refines it rather than replacing it.
    """
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
    """
    Same idea for straight-line travel: measure how far the robot really went and
    set DRIVE_SCALE = distance_mm / measured_mm.

    Not needed to fix the turn -- TURN_SCALE stands alone. Worth running when you
    can, though: if the drive turns out to be off by roughly the factor the turn
    was, the fault is shared (wheel diameter, gear ratio, or a cartridge that
    isn't the colour the code claims) and it is better fixed at the source than
    papered over by two separate scale factors.
    """
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
    # HOLD so each move ends on its target instead of coasting past it; the
    # driver gets BRAKE back in user_control().
    left_motor.set_stopping(HOLD)
    right_motor.set_stopping(HOLD)
    manipulator_init()
    for _ in range(3):
        settle(3000)
        drive(2000)
        turn(180)

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

# Cone detection. If it never fires, run vision_report() instead: it prints what
# the sensor is really returning so you can confirm CONE_CODE_ID.
# vision_report()
cone_detector()

# autonomous()
# user_control()
