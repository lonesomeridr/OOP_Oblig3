import json
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
import serial.serialutil

class SerialReader(QThread):
    data_ready = pyqtSignal(dict)
    error      = pyqtSignal(Exception)

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.last_packet: dict | None = None
        self._running = True

    def run(self):
        while self._running:
            try:
                raw = self.conn.readline()
                if not raw:
                    continue
                try:
                    pkt = json.loads(raw.decode("utf-8").strip())
                except Exception:
                    # skip bad lines
                    continue

                self.last_packet = pkt
                self.data_ready.emit(pkt)

            except serial.serialutil.SerialException as ex:
                # on Windows you sometimes get ClearCommError handle invalid
                if "ClearCommError" in str(ex):
                    # just swallow it
                    continue
                # all other serial errors bubble up
                self.error.emit(ex)
                break
            except Exception as ex:
                # any other surprise
                self.error.emit(ex)
                break

    def stop(self):
        self._running = False
        self.wait()
