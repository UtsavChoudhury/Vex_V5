# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       vision.py                                                    #
# 	Author:       utsavchoudhury                                               #
# 	Description:  AI Vision sensor -- cone recognition                         #
#                                                                              #
# ---------------------------------------------------------------------------- #

from vex import *
from config import *

# ---------------------------------------------------------------------------- #
#  AI VISION HELPERS
# ---------------------------------------------------------------------------- #

def find_cone():
    """Largest 'cone' colour code currently in view, or None.

    The returned AiVisionObject carries centerX / centerY (pixels from the top
    left), width, height, angle and score, so the same call works for aiming at
    the cone later -- centerX below 160 means it sits left of centre.
    """
    largest = None
    largest_area = 0

    for obj in ai_vision.take_snapshot(AiVision.ALL_CODES, VISION_MAX_OBJECTS):
        if obj.id != CONE_CODE_ID:
            continue
        if obj.width < VISION_MIN_WIDTH or obj.height < VISION_MIN_HEIGHT:
            continue
        area = obj.width * obj.height
        if area > largest_area:
            largest = obj
            largest_area = area

    return largest

def cone_detector():
    """Watch continuously and announce the cone each time it comes into view.

    Prints once on arrival rather than once per frame -- a 20 Hz loop shouting
    the same line 20 times a second tells you nothing about when it actually
    appeared.
    """
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("AI VISION  --  watching for cone")

    visible = False
    hits = 0
    misses = 0

    while True:
        cone = find_cone()

        if cone is not None:
            hits = hits + 1
            misses = 0
        else:
            misses = misses + 1
            hits = 0

        # `cone is not None` is redundant at runtime -- hits only climbs on a frame
        # that found one -- but it is what tells the type checker that the attribute
        # reads below are safe, instead of squiggling every cone.centerX as None.
        if cone is not None and not visible and hits >= VISION_CONFIRM_FRAMES:
            visible = True
            print("cone identified")
            brain.screen.clear_line(3)
            brain.screen.set_cursor(3, 1)
            brain.screen.print("cone identified")
            brain.screen.clear_line(4)
            brain.screen.set_cursor(4, 1)
            brain.screen.print("x %d  y %d   %d x %d" % (
                cone.centerX, cone.centerY, cone.width, cone.height))
            controller.rumble(".")

        elif visible and misses >= VISION_CONFIRM_FRAMES:
            visible = False
            print("cone lost")
            brain.screen.clear_line(3)
            brain.screen.set_cursor(3, 1)
            brain.screen.print("no cone")
            brain.screen.clear_line(4)

        wait(VISION_LOOP_MS, MSEC)

def vision_report(seconds=20):
    """Diagnostic: print every object the sensor returns, with its id.

    Run this first, hold the cone in front of the sensor and watch the console.
    A CODE line is the colour code -- the id on it is the number that belongs in
    CONE_CODE_ID. If you only ever see COLOR lines and never a CODE line, the
    sensor is seeing the two colours but not treating them as one object: the
    halves are too far apart, or one of the two colour ranges is too tight to
    match at the distance you are testing from.
    """
    end_ms = brain.timer.time(MSEC) + seconds * 1000

    while brain.timer.time(MSEC) < end_ms:
        codes = ai_vision.take_snapshot(AiVision.ALL_CODES, VISION_MAX_OBJECTS)
        colors = ai_vision.take_snapshot(AiVision.ALL_COLORS, VISION_MAX_OBJECTS)

        for obj in codes:
            print("CODE  id=%d  center=(%d,%d)  %dx%d" % (
                obj.id, obj.centerX, obj.centerY, obj.width, obj.height))
        for obj in colors:
            print("COLOR id=%d  center=(%d,%d)  %dx%d" % (
                obj.id, obj.centerX, obj.centerY, obj.width, obj.height))

        if len(codes) == 0 and len(colors) == 0:
            print("-- nothing in view")

        wait(500, MSEC)
