# vision.py -- AI Vision cone recognition.

from vex import *
from config import *


# --- AI Vision ---

def find_cone():
    """Largest 'cone' colour code in view, else a yellow blob beside a blue one, or None."""
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

    if largest is not None:
        return largest
    return find_color_pair()

class ConeBox:
    """Bounding box with the AiVisionObject fields the cone code reads."""
    def __init__(self, left, top, right, bottom):
        self.width = right - left
        self.height = bottom - top
        self.centerX = (left + right) // 2
        self.centerY = (top + bottom) // 2

def find_color_pair():
    """Yellow and blue blobs side by side, merged into one box, for when the code drops out."""
    yellow = None
    blue = None
    for obj in ai_vision.take_snapshot(AiVision.ALL_COLORS, VISION_MAX_OBJECTS):
        if obj.width < VISION_MIN_WIDTH or obj.height < VISION_MIN_HEIGHT:
            continue
        if obj.id == YELLOW_CONE_ID and (yellow is None or obj.width * obj.height > yellow.width * yellow.height):
            yellow = obj
        elif obj.id == BLUE_CONE_ID and (blue is None or obj.width * obj.height > blue.width * blue.height):
            blue = obj
    if yellow is None or blue is None:
        return None
    gap = max(yellow.width, yellow.height, blue.width, blue.height)
    if abs(yellow.centerX - blue.centerX) > gap or abs(yellow.centerY - blue.centerY) > gap:
        return None
    left = min(yellow.centerX - yellow.width // 2, blue.centerX - blue.width // 2)
    right = max(yellow.centerX + yellow.width // 2, blue.centerX + blue.width // 2)
    top = min(yellow.centerY - yellow.height // 2, blue.centerY - blue.height // 2)
    bottom = max(yellow.centerY + yellow.height // 2, blue.centerY + blue.height // 2)
    return ConeBox(left, top, right, bottom)

# --- Goal AprilTags ---

def find_tag(tag_id):
    """Largest AprilTag with this id in view, or None."""
    best = None
    for obj in ai_vision.take_snapshot(AiVision.ALL_TAGS, VISION_MAX_OBJECTS):
        if obj.id == tag_id and (best is None or obj.width > best.width):
            best = obj
    return best

def set_drive(forward, turn):
    """Percent power; positive turn = right."""
    left_motor.spin(FORWARD, forward + turn, PERCENT)
    right_motor.spin(FORWARD, forward - turn, PERCENT)

def drive_position():
    return (left_motor.position(DEGREES) + right_motor.position(DEGREES)) / 2.0

def approach_tag(tag_id):
    """Steer onto the tag and close in until it is TAG_STOP_WIDTH wide.
    Returns (reached, motor degrees driven) so a fallback can finish the distance."""
    start = brain.timer.time(MSEC)
    start_pos = drive_position()
    seen = False
    misses = 0
    centred = 0
    while brain.timer.time(MSEC) - start < TAG_MAX_MS:
        tag = find_tag(tag_id)
        if tag is None:
            misses = misses + 1
            set_drive(0, 0)
            if (not seen and brain.timer.time(MSEC) - start > TAG_FIND_MS) or (seen and misses >= TAG_LOST_FRAMES):
                break
        else:
            if not seen:
                log("tag %d first seen: x %d w %d" % (tag_id, tag.centerX, tag.width))
            seen = True
            misses = 0
            error = tag.centerX - TAG_CENTER_X
            turn = max(-TAG_MAX_TURN, min(TAG_MAX_TURN, TAG_STEER_KP * error))
            to_close = TAG_STOP_WIDTH - tag.width
            if to_close <= 0:
                set_drive(0, turn if abs(error) > TAG_TOLERANCE_PX else 0)
                centred = centred + 1 if abs(error) <= TAG_TOLERANCE_PX else 0
                if centred >= 3:
                    set_drive(0, 0)
                    log("tag centred: x %d w %d" % (tag.centerX, tag.width))
                    return (True, drive_position() - start_pos)
            else:
                centred = 0
                forward = max(TAG_MIN_SPEED, min(TAG_MAX_SPEED, TAG_SPEED_KP * to_close))
                set_drive(forward, turn)
        wait(VISION_LOOP_MS, MSEC)
    set_drive(0, 0)
    log("tag not reached, seen=%s" % seen)
    return (False, drive_position() - start_pos)

def tag_report():
    """What the camera sees: AprilTags (for calibrating TAG_*) and any AI model objects."""
    try:
        ai_vision.model_detection(True)
    except:
        pass
    while True:
        tags = ai_vision.take_snapshot(AiVision.ALL_TAGS, VISION_MAX_OBJECTS)
        try:
            models = ai_vision.take_snapshot(AiVision.ALL_AIOBJS, VISION_MAX_OBJECTS)
        except:
            models = ()
        brain.screen.clear_screen()
        brain.screen.set_cursor(1, 1)
        brain.screen.print("TAGS %d  AI %d  installed %s" % (len(tags), len(models), ai_vision.installed()))
        row = 2
        for obj in tags:
            if row > 7:
                break
            brain.screen.set_cursor(row, 1)
            brain.screen.print("TAG %d  x %d y %d  w %d h %d  ang %d" % (
                obj.id, obj.centerX, obj.centerY, obj.width, obj.height, obj.angle))
            row = row + 1
        for obj in models:
            if row > 11:
                break
            brain.screen.set_cursor(row, 1)
            brain.screen.print("AI %s  x %d  w %d  score %d" % (obj.classname, obj.centerX, obj.width, obj.score))
            row = row + 1
        brain.screen.render()
        wait(200, MSEC)

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
