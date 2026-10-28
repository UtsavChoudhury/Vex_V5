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
TURN_SCALE = 1.05        # field test: 90 was turning a little short

# Autonomous move settings.
AUTO_DRIVE_SPEED = 50     # percent
AUTO_TURN_SPEED = 25      # percent -- a slow turn coasts past its target far less
AUTO_LEG_MM = 1000        # S->A and A->B
AUTO_TURN_DEG = 90        # positive = right

WALL_SQUARE_SPEED = 30    # percent, backing into the wall
WALL_SQUARE_PUSH_MS = 200 # keep pushing once both bumpers are in, so both sides seat
WALL_SQUARE_MAX_MS = 4000 # no wall by then = stop and skip the rest of autonomous

AUTO_ARM_LIFT_DEG = 90    # motor degrees, "slightly up"
AUTO_ARM_SPEED = 80
ARM_MAX_DPS = 600.0       # red cartridge, 100 rpm; full arm travel is ~2000+ deg

# Override preload autonomous. Arm degrees are absolute from where the arm sits
# when autonomous starts; read them off the brain screen in user_control().
AUTO_SEAT_MS = 800        # max time to seat both bumpers on the start wall
# Start mid-wall; the goal is ~1 tile out and ~1 tile along. See README.md.
AUTO_LEG1_MM = 400        # goal-out distance minus wall -> robot turning centre
AUTO_LEG2_MM = 250        # goal-along distance minus turning centre -> claw centre
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


# Back bumper switches, 3-wire ports B and E.
bumper_b = Bumper(brain.three_wire_port.b)
bumper_e = Bumper(brain.three_wire_port.e)

# Every 3-wire port, so a new switch can be found by pressing it. See show_claw_diagnostic().
probe_a = Bumper(brain.three_wire_port.a)
probe_c = Bumper(brain.three_wire_port.c)
probe_d = Bumper(brain.three_wire_port.d)
probe_f = Bumper(brain.three_wire_port.f)
probe_g = Bumper(brain.three_wire_port.g)
probe_h = Bumper(brain.three_wire_port.h)

# Pressed when the arm is fully down.
arm_switch = probe_g


# --- Manipulator hardware ---

ARM_PORT = Ports.PORT10
CLAW_PORT = Ports.PORT4

ARM_INVERT = True
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

ARM_SPEED = 0.75        # fraction of full power available to the arm
CLAW_SPEED = 0.60       # claws need less; extra power just stalls and heats

ARM_ACCEL_STEP = 6.0    # 0 -> 75% in ~250 ms
ARM_DECEL_STEP = 15.0

CLAW_TORQUE = 100

# Prints the claw stick and motor load to the brain screen. Turn off for comp.
CLAW_DIAGNOSTIC = True

ARM_USE_LIMITS = True
ARM_MIN_DEG = 0.0
ARM_MAX_DEG = 1025.0      # measured top is 1040; keep a margin

ARM_SLOW_ZONE_DEG = 250   # arm tapers to a crawl over the last this many degrees of travel
ARM_HOME_SPEED = 30      # percent, lowering onto the switch
ARM_HOME_MAX_MS = 10000   # no switch by then = give up


# --- AI Vision ---

AI_VISION_PORT = Ports.PORT15    # <-- set to the port the sensor is plugged into

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

VISION_MIN_WIDTH = 6             # a cone across the field is only ~15 px wide
VISION_MIN_HEIGHT = 6

VISION_CONFIRM_FRAMES = 3

VISION_LOOP_MS = 50
VISION_MAX_OBJECTS = 8


# --- Shared setup ---

arm_state = {"homed": False}

def say(text):
    """One line on the brain and the controller."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print(text)
    controller.screen.clear_screen()
    controller.screen.set_cursor(1, 1)
    controller.screen.print(text)

def home_arm():
    """Wait for A, lower the arm onto the switch and call that 0. False if it never arrives."""
    say("ARM HOME: clear? A")
    while not controller.buttonA.pressing():
        wait(20, MSEC)
    while controller.buttonA.pressing():
        wait(20, MSEC)
    arm_motor.set_stopping(HOLD)
    if not arm_switch.pressing():
        say("arm homing...")
        arm_motor.spin(REVERSE, ARM_HOME_SPEED, PERCENT)
        start = brain.timer.time(MSEC)
        while not arm_switch.pressing():
            if brain.timer.time(MSEC) - start > ARM_HOME_MAX_MS:
                arm_motor.stop()
                arm_state["homed"] = False
                say("ARM HOME FAILED")
                return False
            wait(10, MSEC)
    arm_motor.stop()
    wait(100, MSEC)
    arm_motor.reset_position()
    arm_state["homed"] = True
    say("arm homed")
    return True

def manipulator_init():
    """Put the arm and claw in their start-of-match state. HOLD stops them creeping."""
    arm_motor.set_stopping(HOLD)
    claw_motor.set_stopping(HOLD)
    claw_motor.set_max_torque(CLAW_TORQUE, PERCENT)
