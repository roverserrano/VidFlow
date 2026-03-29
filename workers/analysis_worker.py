import json

from PySide6.QtCore import QObject, Signal, Slot

from services.ytdlp_service import analyze_media


class AnalysisWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    @Slot()
    def run(self):
        try:
            data = analyze_media(self.url)
            self.finished.emit(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            self.failed.emit(str(e))