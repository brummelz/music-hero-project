"""Horn Hero entry point: wires storage, audio and UI together."""

from __future__ import annotations

import argparse
import logging
import sys

from PySide6.QtWidgets import QApplication

from audio.sources import AudioSource, MicrophoneSource, SimulatedSource
from storage.store import ProfileStore, default_profile_path, load_levels
from ui.main_window import MainWindow
from ui.theme import STYLESHEET, body_font


def main() -> int:
    parser = argparse.ArgumentParser(description="Horn Hero: learn to play in tune.")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="use the keyboard instead of the microphone (Space = in tune, Up = sharp, Down = flat)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    app = QApplication(sys.argv)
    app.setApplicationName("Horn Hero")
    app.setStyleSheet(STYLESHEET)
    app.setFont(body_font(16))

    source: AudioSource = SimulatedSource() if args.simulate else MicrophoneSource()
    window = MainWindow(ProfileStore(default_profile_path()), load_levels(), source)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
