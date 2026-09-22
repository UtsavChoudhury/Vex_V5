# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       utsavchoudhury                                               #
# 	Description:  Entry point -- picks which mode to run                       #
#                                                                              #
# ---------------------------------------------------------------------------- #
#
#  READ THIS BEFORE YOU DOWNLOAD
#
#  A V5 brain runs ONE python file. vex_project_settings.json has a single
#  "main" key, described by VEXcode as "Path to python file to download to
#  brain" -- there is no file list, so `import config` works in the editor and
#  raises ImportError on the robot.
#
#  So the split below is real, and build.py glues it back together:
#
#      python3 build.py        ->  writes src/download.py
#
#  src/download.py is what the project now downloads, and it is generated --
#  never edit it. Run build.py after every change, before you hit Download.
#
# ---------------------------------------------------------------------------- #

from vex import *

from config import *
from autonomousroutine import autonomous, turn_tuner, drive, turn
from drivercontrol import user_control
from vision import cone_detector, vision_report, find_cone

# ---------------------------------------------------------------------------- #
#  MODE
#
#  Exactly one of these should be uncommented.
#
#    cone_detector()   watch through the AI Vision sensor, announce the cone
#    vision_report()   diagnostic -- print every object the sensor returns
#    user_control()    normal driving
#    autonomous()      the autonomous routine
#    turn_tuner()      on-robot TURN_SCALE tuning from the controller
#
#  In a real competition the field control switches between autonomous() and
#  user_control() for you; until then, pick one here.
# ---------------------------------------------------------------------------- #

def main():
    cone_detector()

    # vision_report()
    # user_control()
    # autonomous()
    # turn_tuner()

main()
