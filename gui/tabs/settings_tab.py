"""
Velg COM‑port, start/stop, gatherFreq.
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton, QSpinBox, QLabel

class SettingsTab(QWidget):
    def __init__(self, serial_conn):
        super().__init__()
        # TODO: bygg UI som i gammel topp‑bar
        #       bruk serial_conn.list_ports(), open_port(), send_json({...})
