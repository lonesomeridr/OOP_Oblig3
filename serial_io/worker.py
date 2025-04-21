import json, time, traceback
import serial
from PyQt6.QtCore import QThread, pyqtSignal

class SerialReader(QThread):
    data_ready = pyqtSignal(dict)
    error      = pyqtSignal(str)

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self._run = True

    def run(self):
        while self._run:
            try:
                raw = self.conn.readline()
                if not raw:
                    time.sleep(0.01)
                    continue
                pkt = json.loads(raw)
                self.data_ready.emit(pkt)
            except Exception as exc:
                # quietly ignore invalid-handle ClearCommError
                if isinstance(exc, serial.SerialException) and "ClearCommError" in str(exc):
                    time.sleep(0.05)
                    continue
                tb = traceback.format_exc(limit=1)
                self.error.emit(f"SerialReader error: {exc}\n{tb}")
                time.sleep(0.2)

    def stop(self):
        self._run = False
