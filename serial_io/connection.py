import json
import serial
import serial.tools.list_ports

BAUD_RATE = 9600

class SerialConnection:
    def __init__(self):
        self.ser: serial.Serial | None = None
        self.current_port: str | None = None

    def list_ports(self) -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]

    def open_port(self, port: str) -> None:
        # only re‑open (and print) if port really changes
        if port == self.current_port and self.ser and self.ser.is_open:
            return

        # close old if needed
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass

        # open new
        try:
            self.ser = serial.Serial(port, BAUD_RATE, timeout=1)
            self.current_port = port
            print(f"Opened {port}")
        except serial.SerialException as ex:
            print(f"Failed to open {port}: {ex}")
            raise

    def send_json(self, payload: dict) -> None:
        if not (self.ser and self.ser.is_open):
            raise serial.SerialException("Serial port not open")
        raw = json.dumps(payload) + "\n"
        self.ser.write(raw.encode("utf-8"))

    def readline(self) -> bytes:
        if not (self.ser and self.ser.in_waiting):
            return b""
        return self.ser.readline()
