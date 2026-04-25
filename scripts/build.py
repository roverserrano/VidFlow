from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    separator = ";" if os.name == "nt" else ":"
    qml_data = f"{root / 'qml'}{separator}qml"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "VidFlow",
        "--windowed",
        "--add-data",
        qml_data,
        str(root / "main.py"),
    ]
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
