# main.py -- entry point. Run build.py before downloading; see README.md.

from vex import *

from config import *
from autonomousroutine import autonomous, autonomous_s_path, turn_tuner, drive, turn
from drivercontrol import user_control
from vision import cone_detector, vision_report, find_cone, scan_ports


# --- Mode ---

def match():
    """Field control picks autonomous or driver. Use this at a competition."""
    global competition
    competition = Competition(user_control, autonomous)

def test_autonomous():
    """Run autonomous once, then hand over to the driver to reset the robot."""
    autonomous()
    user_control()

def main():
    # Arm degrees count from here, so start every program with the arm resting down.
    arm_motor.reset_position()

    # scan_ports()

    # vision_report()

    # cone_detector()
    # user_control()
    test_autonomous()
    # match()
    # turn_tuner()

main()
