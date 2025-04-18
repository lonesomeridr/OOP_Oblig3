from __future__ import annotations
"""
Robust SerialReader‑tråd som ikke krasjer hoved‐prosessen.
• Ingen daemon‑argument (QThread støtter det ikke)
• All unntakshåndtering inni løkken – sender error‑signal istedenfor "exit 0xC0000409"
• Non‑blocking polling via 50 ms sleep
"""

import json
import time
import traceback
from PyQt6.QtCore import QThread, pyqtSignal


class SerialReader(QThread):
    data_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self._run = True

    # --------------------------------------------------
    def run(self):
        while self._run:
            try:
                raw = self.conn.readline()
                if raw and raw.startswith("{"):
                    try:
                        pkt = json.loads(raw)
                        self.data_ready.emit(pkt)
                    except json.JSONDecodeError:
                        continue  # ignorer ufullstendig linje
                time.sleep(0.05)  # non‑blocking poll
            except Exception as exc:
                tb = traceback.format_exc(limit=1)
                self.error.emit(f"SerialReader error: {exc}\n{tb}")
                time.sleep(0.2)

    def stop(self):
        self._run = False
