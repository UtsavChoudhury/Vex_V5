# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       autonomousroutine.py                                         #
# 	Author:       utsavchoudhury                                               #
# 	Description:  Autonomous movement, calibration and routine                 #
#                                                                              #
# ---------------------------------------------------------------------------- #

from vex import *
from config import *

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
#  THE ROUTINE
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
