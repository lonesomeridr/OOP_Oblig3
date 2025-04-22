"""
Serial Connection Module - Handles device communication over serial ports
"""

import json
import serial
import serial.tools.list_ports

BAUD_RATE = 9600  # Standard communication speed


class SerialConnection:
    """Manages serial port connections with external devices"""

    def __init__(self):
        self.ser: serial.Serial | None = None  # Active connection
        self.current_port: str | None = None  # Current port name

    def list_ports(self) -> list[str]:
        """Return list of available serial ports"""
        return [p.device for p in serial.tools.list_ports.comports()]

    def open_port(self, port: str) -> None:
        """Open connection to specified port (if not already connected)"""
        # Skip if already connected to this port
        if port == self.current_port and self.ser and self.ser.is_open:
            return

        # Close existing connection if any
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass

        # Open new connection
        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=1)
            self.current_port = port
            print(f"Opened {port}")
        except serial.SerialException as ex:
            print(f"Failed to open {port}: {ex}")
            raise

    def send_json(self, payload: dict) -> None:
        """Send JSON command to device"""
        if not (self.ser and self.ser.is_open):
            raise serial.SerialException("Serial port not open")
        raw = json.dumps(payload) + "\n"  # Add newline terminator
        self.ser.write(raw.encode("utf-8"))

    def readline(self) -> bytes:
        """Read available data from device (non-blocking)"""
        if not (self.ser and self.ser.in_waiting):
            return b""  # No data available
        return self.ser.readline()