# vision.py -- AI Vision cone recognition.

from vex import *
from config import *


# --- AI Vision ---

def find_cone():
    """Largest 'cone' colour code currently in view, or None."""
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

def find_color(color_id):
    """Return the largest visible object with the requested colour id."""
    largest = None
    largest_area = 0

    for obj in ai_vision.take_snapshot(AiVision.ALL_COLORS, VISION_MAX_OBJECTS):
        if obj.id != color_id:
            continue
        if obj.width < VISION_MIN_WIDTH or obj.height < VISION_MIN_HEIGHT:
            continue
        area = obj.width * obj.height
        if area > largest_area:
            largest = obj
            largest_area = area

    return largest

def search_color_circle():
    """Find, center on, and approach the cone color code."""
    left_motor.set_stopping(BRAKE)
    right_motor.set_stopping(BRAKE)
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("searching for cone")

    hits = 0
    while True:
        target = find_cone()
        if target is not None:
            hits = hits + 1
        else:
            hits = 0

        if target is not None and hits >= VISION_CONFIRM_FRAMES:
            break

        left_motor.spin(FORWARD, SEARCH_INNER_POWER, PERCENT)
        right_motor.spin(FORWARD, SEARCH_OUTER_POWER, PERCENT)
        wait(VISION_LOOP_MS, MSEC)

    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("centering on cone")

    approach_ticks = 0
    while True:
        target = find_cone()
        if target is None:
            left_motor.stop()
            right_motor.stop()
            brain.screen.set_cursor(3, 1)
            brain.screen.print("cone lost - searching")
            hits = 0
            while hits < VISION_CONFIRM_FRAMES:
                target = find_cone()
                if target is not None:
                    hits = hits + 1
                else:
                    hits = 0
                left_motor.spin(FORWARD, SEARCH_INNER_POWER, PERCENT)
                right_motor.spin(FORWARD, SEARCH_OUTER_POWER, PERCENT)
                wait(VISION_LOOP_MS, MSEC)
            continue

        if approach_ticks >= APPROACH_MIN_TICKS and target.width >= APPROACH_TARGET_WIDTH:
            left_motor.stop()
            right_motor.stop()
            brain.screen.set_cursor(3, 1)
            brain.screen.print("TARGET FOUND!")
            brain.screen.set_cursor(4, 1)
            brain.screen.print("cone  x %d y %d" % (
                target.centerX, target.centerY))
            controller.rumble("...")
            return

        error = target.centerX - 160
        if abs(error) > APPROACH_CENTER_TOLERANCE:
            turn_direction = 1 if error > 0 else -1
            left_motor.spin(FORWARD, turn_direction * APPROACH_TURN_POWER, PERCENT)
            right_motor.spin(FORWARD, -turn_direction * APPROACH_TURN_POWER, PERCENT)
        else:
            left_motor.spin(FORWARD, APPROACH_FORWARD_POWER, PERCENT)
            right_motor.spin(FORWARD, APPROACH_FORWARD_POWER, PERCENT)
        approach_ticks = approach_ticks + 1
        wait(VISION_LOOP_MS, MSEC)

def cone_detector():
    """Watch continuously and announce the cone each time it comes into view."""
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

def vision_report():
    """On-screen AI Vision diagnostic. Brain screen, so no terminal is needed."""
    tick = 0

    while True:
        tick = tick + 1
        codes = ai_vision.take_snapshot(AiVision.ALL_CODES, VISION_MAX_OBJECTS)
        colors = ai_vision.take_snapshot(AiVision.ALL_COLORS, VISION_MAX_OBJECTS)

        brain.screen.clear_screen()
        brain.screen.set_cursor(1, 1)
        brain.screen.print("VISION DIAG   tick %d" % tick)
        brain.screen.set_cursor(2, 1)
        # installed False means wrong port or unplugged; a frozen timestamp means
        # the sensor is connected but not sending.
        brain.screen.print("installed %s   stamp %d" % (ai_vision.installed(), ai_vision.timestamp()))
        brain.screen.set_cursor(3, 1)
        brain.screen.print("codes %d   colors %d   want code id %d" % (len(codes), len(colors), CONE_CODE_ID))

        row = 4
        for obj in codes:
            if row > 11:
                break
            brain.screen.set_cursor(row, 1)
            brain.screen.print("CODE  id %d  %dx%d at %d,%d" % (
                obj.id, obj.width, obj.height, obj.centerX, obj.centerY))
            print("CODE  id=%d  %dx%d at %d,%d" % (
                obj.id, obj.width, obj.height, obj.centerX, obj.centerY))
            row = row + 1
        for obj in colors:
            if row > 11:
                break
            brain.screen.set_cursor(row, 1)
            brain.screen.print("COLOR id %d  %dx%d at %d,%d" % (
                obj.id, obj.width, obj.height, obj.centerX, obj.centerY))
            print("COLOR id=%d  %dx%d at %d,%d" % (
                obj.id, obj.width, obj.height, obj.centerX, obj.centerY))
            row = row + 1

        # Double buffered so the clear-and-repaint never shows blank. Safe because
        # this loop never returns; see AGENTS.md.
        brain.screen.render()
        wait(250, MSEC)

def scan_ports():
    """Show which smart port the AI Vision sensor answers on."""
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("scanning ports...")

    found = []
    for index in range(0, 21):
        try:
            probe = AiVision(index)
            first = probe.timestamp()
            wait(100, MSEC)
            # A real sensor keeps stamping packets; a dead port does not.
            if probe.installed() and probe.timestamp() != first:
                found.append(index + 1)
        except:
            pass

    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    if len(found) == 0:
        brain.screen.print("no AI Vision sensor on any port")
        print("no AI Vision sensor on any port")
    else:
        brain.screen.print("AI Vision on port(s): %s" % found)
        print("AI Vision on port(s): %s" % found)
    brain.screen.set_cursor(2, 1)
    brain.screen.print("config has PORT%d" % (AI_VISION_PORT + 1))
