"""
Enkel klasse som håndterer åpning/lukking av serial‑port + sending av JSON.
"""
import json, serial, serial.tools.list_ports
from utils.logger import log

BAUD = 9600

class SerialConnection:
    def __init__(self):
        self.ser = None

    # ---------- PUBLIC API ---------- #
    def list_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def open_port(self, port: str):
        if self.ser:
            self.ser.close()
        self.ser = serial.Serial(port, BAUD, timeout=1)
        log(f"Opened {port}")

    def send_json(self, obj: dict):
        if self.ser and self.ser.is_open:
            self.ser.write((json.dumps(obj) + "\n").encode())

    def readline(self) -> str | None:
        if self.ser and self.ser.in_waiting:
            return self.ser.readline().decode(errors="ignore").strip()
        return None
