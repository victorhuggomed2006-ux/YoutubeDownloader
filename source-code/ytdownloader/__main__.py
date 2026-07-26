"""Permite executar o aplicativo com ``python -m ytdownloader``."""

from __future__ import annotations

from .app import main

if __name__ == "__main__":
    raise SystemExit(main())
