#!/usr/bin/env python3
"""Flatten the src/ modules into the single file a V5 brain can run.

A V5 brain runs one python file: vex_project_settings.json has one "main" key,
"Path to python file to download to brain", and no file list. So `import config`
resolves in the editor and raises ImportError on the robot.

This script concatenates the modules in dependency order, dropping the imports
that only existed to make the editor happy, and writes src/download.py -- which
is what the project downloads. Run it after every change:

    python3 build.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
OUT = os.path.join(SRC, "download.py")

# Dependency order. config is first because every other module reads its
# constants at import time; main is last because it calls into all of them.
MODULES = ["config", "vision", "autonomousroutine", "drivercontrol", "main"]

# `from config import *`, `from vision import cone_detector`, `import config`...
LOCAL_IMPORT = re.compile(r"^\s*(?:from|import)\s+(?:%s)\b" % "|".join(MODULES))

# Kept once, at the very top, rather than repeated per module.
VEX_IMPORT = re.compile(r"^\s*from\s+vex\s+import\s+\*\s*$")

HEADER = """\
# ---------------------------------------------------------------------------- #
#                                                                              #
# \tModule:       download.py                                                  #
# \tAuthor:       utsavchoudhury                                               #
# \tDescription:  GENERATED FILE -- DO NOT EDIT                                #
#                                                                              #
# ---------------------------------------------------------------------------- #
#
#  Built by build.py from, in order:
#
#      %s
#
#  Edit those, then re-run `python3 build.py` before downloading. Anything you
#  type in here is lost the next time the script runs.
#
# ---------------------------------------------------------------------------- #

from vex import *
"""


def flatten():
    missing = [m for m in MODULES if not os.path.exists(os.path.join(SRC, m + ".py"))]
    if missing:
        sys.exit("build.py: missing module(s): %s" % ", ".join(missing))

    parts = [HEADER % "\n#      ".join(m + ".py" for m in MODULES)]

    for name in MODULES:
        path = os.path.join(SRC, name + ".py")
        kept = []
        for line in open(path).read().split("\n"):
            if LOCAL_IMPORT.match(line) or VEX_IMPORT.match(line):
                continue
            kept.append(line)

        body = "\n".join(kept).strip("\n")
        parts.append(
            "\n\n# ============================================================================ #\n"
            "#  %s\n"
            "# ============================================================================ #\n\n%s\n"
            % (name + ".py", body)
        )

    source = "".join(parts)

    # A syntax error here means the flattened file would fail on the brain with
    # nothing but a line number from a file you never wrote -- catch it now.
    try:
        compile(source, OUT, "exec")
    except SyntaxError as err:
        sys.exit("build.py: flattened output does not parse: line %s: %s"
                 % (err.lineno, err.msg))

    open(OUT, "w").write(source)
    print("build.py: wrote %s (%d lines) from %s"
          % (os.path.relpath(OUT, HERE), len(source.split("\n")), ", ".join(MODULES)))
    print("build.py: now hit Download in VEXcode.")


if __name__ == "__main__":
    flatten()
