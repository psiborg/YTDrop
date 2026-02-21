#!/usr/bin/env python3
"""
ytdrop.py — backward-compatible launcher shim.

Allows ``python ytdrop.py`` to keep working after the codebase was
restructured into the ``ytdrop/`` package.  All real logic lives in
the package; this file is just an entry point.
"""

import sys
from pathlib import Path

# Ensure the directory containing this file is on sys.path so that the
# ``ytdrop`` package folder next to it is importable.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from ytdrop.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
