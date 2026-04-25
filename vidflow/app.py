from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from vidflow.app_bridge import AppBridge


def qml_entrypoint() -> Path:
    project_qml = Path(__file__).resolve().parents[1] / "qml" / "Main.qml"
    if project_qml.is_file():
        return project_qml

    bundled_qml = Path(__file__).resolve().parent / "qml" / "Main.qml"
    if bundled_qml.is_file():
        return bundled_qml

    raise FileNotFoundError("No se encontró qml/Main.qml")


def main() -> None:
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    bridge = AppBridge()

    engine.rootContext().setContextProperty("appBridge", bridge)
    engine.load(str(qml_entrypoint()))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
