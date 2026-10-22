# config.py -- devices and tuning constants. See README.md and AGENTS.md.

from vex import *

brain = Brain()
controller = Controller()


# --- Hardware ---

RIGHT_PORT = Ports.PORT1
LEFT_PORT = Ports.PORT2

# Flip if the robot drives backward when you push the stick forward.
INVERT_DRIVE = False

left_motor = Motor(LEFT_PORT, GearSetting.RATIO_18_1, INVERT_DRIVE)
right_motor = Motor(RIGHT_PORT, GearSetting.RATIO_18_1, not INVERT_DRIVE)


# --- Drive geometry ---

PI = 3.141592653589793

WHEEL_DIAMETER_MM = 101.6     # 4" VEX wheel
TRACK_WIDTH_MM = 320.0        # left contact patch to right contact patch
WHEEL_BASE_MM = 320.0         # front axle to rear axle; unused by in-place turns
EXTERNAL_GEAR_RATIO = 1.0     # motor revolutions per wheel revolution

WHEEL_TRAVEL_MM = PI * WHEEL_DIAMETER_MM

DRIVE_SCALE = 1.00
TURN_SCALE = 1.00

# Autonomous move settings.
AUTO_DRIVE_SPEED = 50     # percent
AUTO_TURN_SPEED = 25      # percent -- a slow turn coasts past its target far less

MOTOR_MAX_DPS = 1200.0

TIMEOUT_MARGIN = 2.0      # allow 2x the theoretical time...
TIMEOUT_FLOOR_MS = 1000   # ...plus this, to cover acceleration on short moves

dt = DriveTrain(left_motor, right_motor, WHEEL_TRAVEL_MM, TRACK_WIDTH_MM,
                WHEEL_BASE_MM, MM, EXTERNAL_GEAR_RATIO)


# --- Manipulator hardware ---

ARM_PORT = Ports.PORT10
CLAW_PORT = Ports.PORT15

ARM_INVERT = False
CLAW_INVERT = False

arm_motor = Motor(ARM_PORT, GearSetting.RATIO_36_1, ARM_INVERT)
claw_motor = Motor(CLAW_PORT, GearSetting.RATIO_36_1, CLAW_INVERT)


# --- Driver tuning ---

LOOP_MS = 20

DEADBAND = 2

SPEED_BOOST = 1.00   # L1/R1 held
SPEED_CRAWL = 0.25   # L2/R2 held
SPEED_NORMAL = 0.50  # nothing held

TURN_NORMAL = 0.8


# --- Acceleration limiting ---

FWD_ACCEL_STEP = 4.0    # 0 -> 100 in ~500 ms
FWD_DECEL_STEP = 12.0   # 100 -> 0 in ~170 ms

TURN_ACCEL_STEP = 8.0   # 0 -> 40 in ~100 ms, so turns stay aggressive
TURN_DECEL_STEP = 20.0


# --- Reverse turn handling ---

MIRROR_TURN_IN_REVERSE = False

REVERSE_ENTER = 12.0    # forward power below -this counts as reversing
REVERSE_EXIT = 4.0      # forward power above -this leaves reverse
TURN_FLIP_STEP = 0.2    # sign blend per tick -- ~200 ms to swap over


# --- Forward vs turn balance ---

TURN_GAIN_REST = 1.00   # turn authority with the throttle centred
TURN_GAIN_FULL = 0.35   # turn authority at full throttle
TURN_TAPER_SHAPE = 1.0  # 1 = linear; >1 holds authority up through low speeds

FORWARD_PRIORITY = 0.8  # 0.0 = old clipping, 1.0 = forward never yields at all


# --- Manipulator tuning ---

ARM_DEADBAND = 5
CLAW_DEADBAND = 5

ARM_SPEED = 0.75        # fraction of full power available to the arm
CLAW_SPEED = 0.60       # claws need less; extra power just stalls and heats

ARM_ACCEL_STEP = 6.0    # 0 -> 75% in ~250 ms
ARM_DECEL_STEP = 15.0

CLAW_TORQUE = 100

# Prints the claw stick and motor load to the brain screen. Turn off for comp.
CLAW_DIAGNOSTIC = True

ARM_USE_LIMITS = False
ARM_MIN_DEG = 0.0
ARM_MAX_DEG = 900.0


# --- AI Vision ---

AI_VISION_PORT = Ports.PORT4     # <-- set to the port the sensor is plugged into

BLUE_CONE_ID = 1                 # colour "bluecone", first in the utility list
YELLOW_CONE_ID = 2               # colour "yellowcone"
CONE_CODE_ID = 1                 # colour code "cone"
SEARCH_COLOR_ID = YELLOW_CONE_ID # colour to find while circling
SEARCH_INNER_POWER = 5
SEARCH_OUTER_POWER = 10
VISION_CENTER_X = 164            # centerX when the cone is dead ahead; shift if camera is off-centre
APPROACH_FORWARD_POWER = 25      # forward power when the cone is far
APPROACH_MIN_FORWARD = 8         # forward power as the cone fills the frame
APPROACH_STEER_KP = 0.12         # turn power per pixel of error
APPROACH_MIN_TURN = 4            # smallest turn power that actually moves the robot
APPROACH_MAX_TURN = 15
APPROACH_DRIVE_ERROR = 40        # beyond this many px, turn in place instead of driving
APPROACH_CENTER_TOLERANCE = 3
APPROACH_TARGET_WIDTH = 250
VISION_DEG_PER_PX = 74.0 / 320  # horizontal FOV over frame width; see README.md
ALIGN_TOLERANCE_PX = 2           # final aim accuracy, about half a degree
ALIGN_SAMPLES = 7                # frames per median measurement
ALIGN_SETTLE_MS = 250            # let the robot stop rocking before measuring
ALIGN_MIN_TURN_DEG = 0.5
ALIGN_MAX_STEPS = 8
ALIGN_TURN_SPEED = 10

# RGB sampled from the utility swatches; hue and saturation ranges as set there.
# Declared here rather than relied on from the sensor -- see AGENTS.md.
BLUE_CONE = Colordesc(BLUE_CONE_ID, 74, 126, 169, 40.0, 1.00)
YELLOW_CONE = Colordesc(YELLOW_CONE_ID, 194, 194, 123, 40.0, 1.00)
CONE = Codedesc(CONE_CODE_ID, BLUE_CONE, YELLOW_CONE)

ai_vision = AiVision(AI_VISION_PORT, BLUE_CONE, YELLOW_CONE, CONE)
# Colour and code processing is off until asked for; without this every
# snapshot comes back empty even though the sensor is streaming.
ai_vision.color_detection(True)

VISION_MIN_WIDTH = 20
VISION_MIN_HEIGHT = 20

VISION_CONFIRM_FRAMES = 3

VISION_LOOP_MS = 50
VISION_MAX_OBJECTS = 8


# --- Shared setup ---

def manipulator_init():
    """Put the arm and claw in their start-of-match state. HOLD stops them creeping."""
    arm_motor.set_stopping(HOLD)
    claw_motor.set_stopping(HOLD)
    claw_motor.set_max_torque(CLAW_TORQUE, PERCENT)
