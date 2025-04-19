"""
En enkel wrapper rundt pyserial – én port om gangen.
"""

from __future__ import annotations
import json
import serial, serial.tools.list_ports
from utils.logger import log

BAUD = 9600

class SerialConnection:
    def __init__(self) -> None:
        self.ser: serial.Serial | None = None

    # ---------- Public API ---------- #
    @staticmethod
    def list_ports() -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]

    def open_port(self, port: str) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()
        # non‑blocking with 50 ms timeout
        self.ser = serial.Serial(port=port, baudrate=BAUD, timeout=0.05)
        log(f"Opened {port}")

    def send_json(self, obj: dict) -> None:
        if self.ser and self.ser.is_open:
            self.ser.write((json.dumps(obj) + "\n").encode())

    def readline(self) -> str | None:
        if self.ser and self.ser.in_waiting:
            return self.ser.readline().decode(errors="ignore").strip()
        return None
