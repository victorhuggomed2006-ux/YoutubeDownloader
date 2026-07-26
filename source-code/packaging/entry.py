"""The entry script PyInstaller uses to build the executable."""

from __future__ import annotations

import sys

from ytdownloader.app import main

if __name__ == "__main__":
    sys.exit(main())
