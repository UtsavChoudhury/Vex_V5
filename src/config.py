# config.py -- devices and tuning constants. See README.md and AGENTS.md.

from vex import *

brain = Brain()
controller = Controller()


# --- Hardware ---

RIGHT_PORT = Ports.PORT4
LEFT_PORT = Ports.PORT6
# Radio is on port 5; VEXos manages it, never declare it.

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
TURN_SCALE = 1.10        # field test: 90 still turning a little short

# Autonomous move settings.
AUTO_DRIVE_SPEED = 50     # percent
AUTO_TURN_SPEED = 25      # percent -- a slow turn coasts past its target far less
AUTO_LEG_MM = 1000        # S->A and A->B
AUTO_TURN_DEG = 90        # positive = right

WALL_SQUARE_SPEED = 30    # percent, backing into the wall
WALL_SQUARE_PUSH_MS = 200 # keep pushing once both bumpers are in, so both sides seat
WALL_SQUARE_MAX_MS = 4000 # no wall by then = stop and skip the rest of autonomous

AUTO_ARM_LIFT_DEG = 90    # motor degrees, "slightly up"
AUTO_ARM_SPEED = 100
ARM_MAX_DPS = 600.0       # red cartridge, 100 rpm; full arm travel is ~2000+ deg

# Override preload autonomous. Arm degrees are absolute from where the arm sits
# when autonomous starts; read them off the brain screen in user_control().
AUTO_SEAT_MS = 800        # max time to seat both bumpers on the start wall
# Start mid-wall; the goal is ~1 tile out and ~1 tile along. See README.md.
AUTO_LEG1_MM = 400        # goal-out distance minus wall -> robot turning centre
AUTO_LEG2_MM = 320        # after the turn; field test: was stopping short
AUTO_GOAL_SPEED = 30      # percent, slow so the pin doesn't swing
AUTO_ARM_CARRY_DEG = 900  # pin bottom clears the goal rim
AUTO_ARM_PLACE_DEG = 600  # pin bottom inside the goal
AUTO_CLAW_OPEN_PCT = 50   # sign = the claw direction that opens
AUTO_CLAW_OPEN_MS = 400
AUTO_BACKOFF_MM = 150

MOTOR_MAX_DPS = 1200.0

TIMEOUT_MARGIN = 2.0      # allow 2x the theoretical time...
TIMEOUT_FLOOR_MS = 1000   # ...plus this, to cover acceleration on short moves

dt = DriveTrain(left_motor, right_motor, WHEEL_TRAVEL_MM, TRACK_WIDTH_MM,
                WHEEL_BASE_MM, MM, EXTERNAL_GEAR_RATIO)


# Bumper switches: back left C, back right E, left side F.
bumper_left = Bumper(brain.three_wire_port.c)
bumper_right = Bumper(brain.three_wire_port.e)
bumper_side = Bumper(brain.three_wire_port.f)


# --- Manipulator hardware ---

ARM_PORT = Ports.PORT9
CLAW_PORT = Ports.PORT10

ARM_INVERT = False
CLAW_INVERT = True

arm_motor = Motor(ARM_PORT, GearSetting.RATIO_36_1, ARM_INVERT)
claw_motor = Motor(CLAW_PORT, GearSetting.RATIO_36_1, CLAW_INVERT)


# --- Driver tuning ---

LOOP_MS = 20

DEADBAND = 2

SPEED_BOOST = 1.00   # R1 held
SPEED_CRAWL = 0.25   # R2 held
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

ARM_SPEED = 1.00        # fraction of full power available to the arm
CLAW_SPEED = 0.60       # claws need less; extra power just stalls and heats

ARM_ACCEL_STEP = 6.0    # 0 -> 75% in ~250 ms
ARM_DECEL_STEP = 15.0

CLAW_TORQUE = 100

# Claw range: 0 = fully open (set at start), CLAW_MAX_DEG = fully closed.
CLAW_USE_LIMITS = True
CLAW_MAX_DEG = 120.0
CLAW_CLOSE_SIGN = -1      # closing takes the claw position negative (0 open, -100 closed)
CLAW_ZERO_SPEED = 0.30    # fraction of power for the stick while confirming

# Motor rotations, arm load and bumpers on the brain screen. Turn off for comp.
MOTOR_DIAGNOSTIC = True

ARM_USE_LIMITS = True
ARM_MIN_DEG = 0.0
ARM_MAX_DEG = 2020.0      # measured on the regeared arm

ARM_SLOW_ZONE_DEG = 250   # arm tapers to a crawl over the last this many degrees at either end
ARM_TORQUE = 90           # percent of max

# Zeroing: move the arm by hand with the stick, press A.
ARM_ZERO_SPEED = 0.25     # fraction of power for the stick while confirming


# --- AI Vision ---

AI_VISION_PORT = Ports.PORT7

BLUE_CONE_ID = 1                 # colour "bluecone", first in the utility list
YELLOW_CONE_ID = 2               # colour "yellowcone"
CONE_CODE_ID = 1                 # colour code "cone"
VISION_CENTER_X = 164            # centerX when the cone is dead ahead; shift if camera is off-centre

# Driver cone assist: spin until the cone is seen, then centre on it.
ASSIST_SEARCH_SPEED = 15         # percent while looking; slow so frames aren't blurred
ASSIST_STEER_KP = 0.12           # turn power per pixel of error
ASSIST_MIN_TURN = 4              # smallest turn power that actually moves the robot
ASSIST_MAX_TURN = 15
ASSIST_TOLERANCE_PX = 4
ASSIST_HOLD_FRAMES = 3           # centred this many frames in a row = done
ASSIST_LOST_FRAMES = 5           # misses in a row before searching again
ASSIST_STICK_CANCEL = 20         # stick past this cancels, as any button does

# RGB sampled from the utility swatches; hue and saturation ranges as set there.
# Declared here rather than relied on from the sensor -- see AGENTS.md.
BLUE_CONE = Colordesc(BLUE_CONE_ID, 74, 126, 169, 40.0, 1.00)
YELLOW_CONE = Colordesc(YELLOW_CONE_ID, 194, 194, 123, 40.0, 1.00)
CONE = Codedesc(CONE_CODE_ID, BLUE_CONE, YELLOW_CONE)

ai_vision = AiVision(AI_VISION_PORT, BLUE_CONE, YELLOW_CONE, CONE)
# Colour and code processing is off until asked for; without this every
# snapshot comes back empty even though the sensor is streaming.
ai_vision.color_detection(True)

# Every Override goal carries an AprilTag (manual Appendix A16). Alliance goals
# are tag 2 (alliance-station side quadrant) and tag 3; neutrals 1 and 4; centre 0.
TAG_FAMILY = AiVision.TAG_CIRCLE21H7   # notched-square tags on the goals; check with tag_report()
try:
    ai_vision.set_tag_family(TAG_FAMILY)
    ai_vision.tag_detection(True)
except:
    pass

TAG_FOR_SIDE = {1: 2, -1: 3}     # arrow pressed -> goal tag; see README.md
TAG_CENTER_X = 160               # tag centerX when the claw lines up with the goal
TAG_STOP_WIDTH = 40              # tag width (px) where vision hands over to the final drive
TAG_FINAL_MM = 80                # drive from there until the claw is over the goal
TAG_STEER_KP = 0.10              # turn power per pixel
TAG_MAX_TURN = 12
TAG_MIN_SPEED = 8                # percent forward while closing in
TAG_MAX_SPEED = 25
TAG_SPEED_KP = 0.8               # forward power per pixel of width still to close
TAG_TOLERANCE_PX = 6
TAG_FIND_MS = 1200               # never seen by then = fall back to distances
TAG_LOST_FRAMES = 6              # misses in a row after seeing it = fall back
TAG_MAX_MS = 5000

VISION_MIN_WIDTH = 6             # a cone across the field is only ~15 px wide
VISION_MIN_HEIGHT = 6

VISION_CONFIRM_FRAMES = 3

VISION_LOOP_MS = 50
VISION_MAX_OBJECTS = 8


# --- Shared setup ---

arm_state = {"homed": False}
claw_state = {"zeroed": False}

def log(text):
    """Timed line in the VS Code terminal (print goes nowhere if not tethered)."""
    print("[%6d ms] %s" % (brain.timer.time(MSEC), text))

def say(text, second=""):
    """A line (and optional second line) on the brain and the controller."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print(text)
    controller.screen.clear_screen()
    controller.screen.set_cursor(1, 1)
    controller.screen.print(text)
    if second:
        brain.screen.set_cursor(2, 1)
        brain.screen.print(second)
        controller.screen.set_cursor(2, 1)
        controller.screen.print(second)

def release_buttons():
    while controller.buttonA.pressing() or controller.buttonB.pressing():
        wait(20, MSEC)

def zero_arm_here():
    arm_motor.stop()
    wait(100, MSEC)
    arm_motor.reset_position()
    arm_state["homed"] = True

def confirm_arm_zero():
    """Move the arm with the right stick, then press A to call that position 0."""
    say("Arm at bottom? A=yes", "Rstick^v=move")
    arm_motor.set_stopping(HOLD)
    arm_motor.set_max_torque(ARM_TORQUE, PERCENT)
    while True:
        if controller.buttonA.pressing():
            release_buttons()
            zero_arm_here()
            say("arm zeroed")
            return True
        stick = controller.axis2.position()
        if abs(stick) < ARM_DEADBAND:
            arm_motor.stop()
        else:
            arm_motor.spin(FORWARD, stick * ARM_ZERO_SPEED, PERCENT)
        wait(20, MSEC)

def confirm_claw_zero():
    """Ask whether the claw is fully open. A = yes (that is 0); right stick moves it meanwhile."""
    say("Claw fully open? A=yes", "Rstick<>=move")
    claw_motor.set_stopping(HOLD)
    claw_motor.set_max_torque(CLAW_TORQUE, PERCENT)
    while True:
        if controller.buttonA.pressing():
            release_buttons()
            claw_motor.stop()
            wait(100, MSEC)
            claw_motor.reset_position()
            claw_state["zeroed"] = True
            say("claw zeroed")
            return True
        stick = controller.axis1.position()
        if abs(stick) < CLAW_DEADBAND:
            claw_motor.stop()
        else:
            claw_motor.spin(FORWARD, stick * CLAW_ZERO_SPEED, PERCENT)
        wait(20, MSEC)

def confirm_zero():
    """Start-of-program checks: arm at the bottom, then claw fully open."""
    confirm_arm_zero()
    confirm_claw_zero()

def manipulator_init():
    """Put the arm and claw in their start-of-match state. HOLD stops them creeping."""
    arm_motor.set_stopping(HOLD)
    arm_motor.set_max_torque(ARM_TORQUE, PERCENT)
    claw_motor.set_stopping(HOLD)
    claw_motor.set_max_torque(CLAW_TORQUE, PERCENT)
