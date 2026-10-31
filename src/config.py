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
TURN_SCALE = 1.155       # 90 was ~5 degrees short at 1.10

# Autonomous move settings.
AUTO_DRIVE_SPEED = 50     # percent
AUTO_TURN_SPEED = 25      # percent -- a slow turn coasts past its target far less
AUTO_LEG_MM = 1000        # S->A and A->B
AUTO_TURN_DEG = 90        # positive = right
AUTO_GOAL_TURN_DEG = 90.5  # the turn towards the goal in autonomous (was 88.5; +2 deg)

WALL_SQUARE_SPEED = 30    # percent, backing into the wall
WALL_SQUARE_PUSH_MS = 300  # keep pushing once both bumpers are in, so both sides seat
WALL_SQUARE_MAX_MS = 4000 # no wall by then = stop and skip the rest of autonomous

AUTO_ARM_LIFT_DEG = 90    # motor degrees, "slightly up"
AUTO_ARM_SPEED = 100
ARM_MAX_DPS = 600.0       # red cartridge, 100 rpm; full arm travel is ~2000+ deg

# Override preload autonomous. Arm degrees are absolute from where the arm sits
# when autonomous starts; read them off the brain screen in user_control().
AUTO_SEAT_MS = 800        # max time to seat both bumpers on the start wall
# Start mid-wall; the goal is ~1 tile out and ~1 tile along. See README.md.
AUTO_LEG1_MM = 400        # goal-out distance minus wall -> robot turning centre
AUTO_LEG2_MM = 390        # after the turn; +20 mm so the claw is over the goal
AUTO_GOAL_SPEED = 30      # percent, slow so the pin doesn't swing
AUTO_ARM_CARRY_DEG = 900  # pin bottom clears the goal rim
AUTO_ARM_PLACE_DEG = 300  # first guess for "20 cm lower"; set from the ARM number once measured
AUTO_CLAW_OPEN_PCT = 50   # sign = the claw direction that opens
AUTO_CLAW_OPEN_MS = 800
AUTO_BACKOFF_MM = 150

# Front collision handling
COLLISION_BACKOFF_MM = 75  # 7.5cm back when front bumper hits
COLLISION_MAX_MS = 6000    # wait this long for the front bumper before giving up (time, not distance)

MOTOR_MAX_DPS = 1200.0

TIMEOUT_MARGIN = 2.0      # allow 2x the theoretical time...
TIMEOUT_FLOOR_MS = 1000   # ...plus this, to cover acceleration on short moves

dt = DriveTrain(left_motor, right_motor, WHEEL_TRAVEL_MM, TRACK_WIDTH_MM,
                WHEEL_BASE_MM, MM, EXTERNAL_GEAR_RATIO)


# Bumper switches: back left C, back right E, left side F, front H.
bumper_left = Bumper(brain.three_wire_port.c)
bumper_right = Bumper(brain.three_wire_port.e)
bumper_side = Bumper(brain.three_wire_port.f)
bumper_front = Bumper(brain.three_wire_port.h)


# --- Manipulator hardware ---

ARM_PORT = Ports.PORT9
CLAW_PORT = Ports.PORT10

ARM_INVERT = False
CLAW_INVERT = True

arm_motor = Motor(ARM_PORT, GearSetting.RATIO_36_1, ARM_INVERT)
claw_motor = Motor(CLAW_PORT, GearSetting.RATIO_36_1, CLAW_INVERT)

# Toggle spinner: no limits. L1 spins it forward, L2 backward, at full power.
TOGGLE_PORT = Ports.PORT8
TOGGLE_INVERT = False      # flip if L1 spins it the wrong way
toggle_motor = Motor(TOGGLE_PORT, GearSetting.RATIO_18_1, TOGGLE_INVERT)
TOGGLE_AUTO_SPEED = 80     # percent in autonomous (manual L1/L2 stay at 100): less kick on the chassis
TOGGLE_WALL_PUSH_PCT = 20  # drive pressed into the wall while the toggle spins, so the robot can't swing
TOGGLE_AUTO_TURNS = 2      # autonomous spins it backward (like L2) this many motor rotations before moving


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
