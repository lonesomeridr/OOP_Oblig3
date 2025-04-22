"""
Serial Reader Worker - Reads and parses JSON data from serial port in background thread
"""

import json
import traceback
from PyQt6.QtCore import QThread, pyqtSignal
import serial.serialutil


class SerialReader(QThread):
    """Background thread that continuously reads and parses data from serial port"""
    data_ready = pyqtSignal(dict)  # Emitted when valid data is received
    error = pyqtSignal(Exception)  # Emitted on error conditions

    def __init__(self, conn):
        """Initialize reader with connection object"""
        super().__init__()
        self.conn = conn
        self.last_packet: dict | None = None
        self._running = True

    def run(self):
        """Main thread loop - reads, parses and emits data"""
        while self._running:
            try:
                # Try to read data
                raw = self.conn.readline()
                if not raw:
                    continue

                # Parse JSON data
                try:
                    pkt = json.loads(raw.decode("utf-8").strip())
                except Exception:
                    # Skip invalid JSON data
                    continue

                self.last_packet = pkt
                self.data_ready.emit(pkt)

            except serial.serialutil.SerialException as ex:
                # Windows-specific error that can be ignored
                if "ClearCommError" in str(ex):
                    continue
                # Other serial errors are reported and cause thread to exit
                self.error.emit(ex)
                break
            except Exception as ex:
                # Unexpected errors are reported and cause thread to exit
                self.error.emit(ex)
                break

    def stop(self):
        """Stop the thread gracefully"""
        self._running = False
        self.wait()