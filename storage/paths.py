"""File locations that work both from source and inside a PyInstaller bundle."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "HornHero"


def user_data_dir() -> Path:
    """Per-user data folder, e.g. %APPDATA%/HornHero."""
    base = os.environ.get("APPDATA")
    return (Path(base) if base else Path.home()) / APP_DIR_NAME


def resource_path(relative: str) -> Path:
    """A file under ``resources/``, also when bundled (PyInstaller sets ``sys._MEIPASS``)."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    root = Path(bundle_root) if bundle_root else Path(__file__).resolve().parent.parent
    return root / "resources" / relative
