"""
QThread som leser fra SerialConnection og sender signaler:
    data_ready(dict)  – gyldig JSON‑pakke
    error(str)        – tekst med feilmelding
"""

from __future__ import annotations
import json, time, traceback
from PyQt6.QtCore import QThread, pyqtSignal

class SerialReader(QThread):
    data_ready = pyqtSignal(dict)
    error      = pyqtSignal(str)

    def __init__(self, conn):
        super().__init__(daemon=True)
        self.conn = conn
        self._run = True

    def run(self):
        while self._run:
            try:
                raw = self.conn.readline()
                if raw and raw.startswith("{"):
                    try:
                        pkt = json.loads(raw)
                        self.data_ready.emit(pkt)
                    except json.JSONDecodeError:
                        # Ignorer linjer som ikke er komplett JSON
                        continue
                time.sleep(0.02)
            except Exception as exc:
                tb = traceback.format_exc(limit=1)
                self.error.emit(f"{exc}\\n{tb}")
                time.sleep(0.2)   # kort pause før ny runde

    def stop(self):
        self._run = False
