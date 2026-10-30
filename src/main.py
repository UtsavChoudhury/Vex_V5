# main.py -- entry point. Run build.py before downloading; see README.md.

from vex import *

from config import *
from autonomousroutine import autonomous, autonomous_s_path, set_auto_side, turn_tuner, drive, turn
from drivercontrol import user_control
from vision import cone_detector, vision_report, find_cone, scan_ports, tag_report


# --- Programs ---
# Arm degrees count from where confirm_arm_zero() is answered.

def driver():
    """Slot 1: manual control only."""
    confirm_zero()
    user_control()

def show_both(row, text):
    """One line on the brain and the controller."""
    brain.screen.clear_line(row)
    brain.screen.set_cursor(row, 1)
    brain.screen.print(text)
    controller.screen.clear_line(row)
    controller.screen.set_cursor(row, 1)
    controller.screen.print(text)

def read_side():
    """+1 for the right arrow, -1 for the left, 0 for neither."""
    if controller.buttonRight.pressing():
        return 1
    if controller.buttonLeft.pressing():
        return -1
    return 0

def auto_on_button():
    """Slot 2: arrow towards the goal starts autonomous, then the driver takes over."""
    confirm_zero()
    brain.screen.clear_screen()
    controller.screen.clear_screen()
    show_both(1, "AUTO: < or > goal")
    side = 0
    while side == 0:
        side = read_side()
        wait(20, MSEC)
    while read_side() != 0:
        wait(20, MSEC)
    set_auto_side(side)
    show_both(1, "AUTO running")
    autonomous()
    show_both(1, "AUTO done")
    user_control()

def match():
    """Slot 3: pick the goal side with an arrow before the match; field control does the rest."""
    global competition
    confirm_zero()
    competition = Competition(user_control, autonomous)
    brain.screen.clear_screen()
    controller.screen.clear_screen()
    show_both(1, "goal side: RIGHT >")
    while not competition.is_enabled():
        side = read_side()
        if side != 0:
            set_auto_side(side)
            show_both(1, "goal side: RIGHT >" if side > 0 else "goal side: < LEFT")
        wait(20, MSEC)


# --- Mode ---

def main():
    # scan_ports()
    # tag_report()
    # vision_report()
    # cone_detector()
    # turn_tuner()
    # match()
    # driver()
    auto_on_button()

main()
