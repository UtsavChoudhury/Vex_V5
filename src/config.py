# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       config.py                                                    #
# 	Author:       utsavchoudhury                                               #
# 	Description:  Hardware, geometry and tuning shared by all modules          #
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
#  SHARED SETUP
#
#  Lives here rather than with the driver code because autonomous() needs it
#  too -- both modes want the manipulator in the same state before they start.
# ---------------------------------------------------------------------------- #

def manipulator_init():
    """
    HOLD rather than BRAKE: a braked motor still creeps under load, so an arm
    left holding a game object would sag over a match. Capping claw torque lets
    it stay clamped shut indefinitely without drawing stall current.
    """
    arm_motor.set_stopping(HOLD)
    claw_motor.set_stopping(HOLD)
    claw_motor.set_max_torque(CLAW_TORQUE, PERCENT)
