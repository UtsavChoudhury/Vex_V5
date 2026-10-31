# main.py -- entry point. Run build.py before downloading; see README.md.

from vex import *

from config import *
from autonomousroutine import autonomous, autonomous_s_path, set_auto_side, turn_tuner, drive, turn
from drivercontrol import user_control


# --- Programs ---
# Arm degrees count from where confirm_arm_zero() is answered.

def driver():
    """Slot 1: manual control only."""
    confirm_zero()
    user_control()

def show_both(row, text, second=""):
    """One line (and an optional line below it) on the brain and the controller."""
    for r, t in ((row, text), (row + 1, second)):
        if t:
            brain.screen.clear_line(r)
            brain.screen.set_cursor(r, 1)
            brain.screen.print(t)
            controller.screen.clear_line(r)
            controller.screen.set_cursor(r, 1)
            controller.screen.print(t)

def claw_by_stick():
    """Right stick moves the claw, for loading a pin before the start."""
    stick = controller.axis1.position()
    if abs(stick) < CLAW_DEADBAND:
        claw_motor.stop()
    else:
        claw_motor.spin(FORWARD, stick * CLAW_SPEED, PERCENT)

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
    show_both(1, "AUTO: < or > goal", "Rstick<> = claw")
    claw_motor.set_stopping(HOLD)
    side = 0
    while side == 0:
        claw_by_stick()
        side = read_side()
        wait(20, MSEC)
    claw_motor.stop()
    while read_side() != 0:
        wait(20, MSEC)
    set_auto_side(side)
    show_both(1, "AUTO running")
    autonomous()
    show_both(1, "AUTO done")
    user_control(True)

def match():
    """Slot 3: pick the goal side with an arrow before the match; field control does the rest."""
    global competition
    confirm_zero()
    competition = Competition(user_control, autonomous)
    brain.screen.clear_screen()
    controller.screen.clear_screen()
    show_both(1, "goal side: RIGHT >")
    claw_motor.set_stopping(HOLD)
    while not competition.is_enabled():
        claw_by_stick()
        side = read_side()
        if side != 0:
            set_auto_side(side)
            show_both(1, "goal side: RIGHT >" if side > 0 else "goal side: < LEFT")
        wait(20, MSEC)


# --- Mode ---

def main():
    # turn_tuner()
    # match()
    # driver()
    auto_on_button()

main()
