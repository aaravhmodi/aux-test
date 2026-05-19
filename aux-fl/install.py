"""Install the Aux FL Studio MIDI Controller Script."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

FL_SCRIPT_FILES = [
    "device_Aux.py",
    "server.py",
    "api.py",
    "dispatcher.py",
]

FL_SCRIPT_INI = """[Ini]
Version=2
"""


def default_fl_hardware_path() -> Path:
    # Use the shell's registered Documents path so OneDrive-redirected folders work.
    try:
        import ctypes, ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # CSIDL_PERSONAL = 5
        documents = Path(buf.value)
    except Exception:
        documents = Path.home() / "Documents"
    return documents / "Image-Line" / "FL Studio" / "Settings" / "Hardware"


def install(destination: Path | None = None) -> Path:
    root = Path(__file__).resolve().parent
    source = root / "fl_script"
    destination = destination or default_fl_hardware_path() / "Aux"
    destination.mkdir(parents=True, exist_ok=True)

    for filename in FL_SCRIPT_FILES:
        shutil.copy2(source / filename, destination / filename)
        print(f"Copied {filename} to {destination}")

    ini_path = destination.parent / f"{destination.name}.ini"
    ini_path.write_text(FL_SCRIPT_INI, encoding="utf-8")
    print(f"Wrote {ini_path}")

    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Override FL Studio Hardware script destination.",
    )
    args = parser.parse_args()

    destination = install(args.dest)
    print()
    print("Installed Aux FL script.")
    print("In FL Studio: Options > MIDI Settings > Controller type > Aux > Enable")
    print("Expected FL log: [Aux] Bridge started on localhost:9001")
    print(f"Script folder: {destination}")


if __name__ == "__main__":
    main()
