# main.py -- entry point. Run build.py before downloading; see README.md.

from vex import *

from config import *
from autonomousroutine import autonomous, turn_tuner, drive, turn
from drivercontrol import user_control
from vision import cone_detector, vision_report, find_cone, scan_ports


# --- Mode ---

def main():
    # scan_ports()

    # vision_report()

    # cone_detector()
    # user_control()
    autonomous()
    # turn_tuner()

main()
