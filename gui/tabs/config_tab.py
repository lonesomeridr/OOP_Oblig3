"""
Registrer nye sensorer + send {"SensorConfiguration": {...}} til Pico.
"""
from PyQt6.QtWidgets import QWidget, QFormLayout, QLineEdit, QPushButton

class ConfigTab(QWidget):
    def __init__(self, serial_conn):
        super().__init__()
        # TODO: felter: type, sensor_id, etc.
        #       knappen kaller serial_conn.send_json(cfg_dict)
