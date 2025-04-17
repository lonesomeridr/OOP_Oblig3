"""
QThread som leser linjer kontinuerlig, parser JSON, og emitterer 'data_ready'.
"""
import json, time
from PyQt6.QtCore import QThread, pyqtSignal

class SerialReader(QThread):
    data_ready = pyqtSignal(dict)

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self._run = True

    def run(self):
        while self._run:
            raw = self.conn.readline()
            if raw and raw.startswith("{"):
                try:
                    pkt = json.loads(raw)
                    self.data_ready.emit(pkt)
                except json.JSONDecodeError:
                    pass
            time.sleep(0.05)  # liten pause

    def stop(self):
        self._run = False
