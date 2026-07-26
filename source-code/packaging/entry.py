"""Script de entrada usado pelo PyInstaller para gerar o executável."""

from __future__ import annotations

import sys

from ytdownloader.app import main

if __name__ == "__main__":
    sys.exit(main())
