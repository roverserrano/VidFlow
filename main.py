import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from bridge import AppBridge


def main():
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    bridge = AppBridge()

    engine.rootContext().setContextProperty("appBridge", bridge)

    qml_file = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(str(qml_file))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()