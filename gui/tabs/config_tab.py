from __future__ import annotations
"""
ConfigTab – add new sensors to DB + accelerometer calibration
• Add sensor entries (type, location, installation_date)
• Calibrate zero offset for accelerometer
• Set deadband threshold
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QPushButton, QLabel, QDoubleSpinBox, QGroupBox, QHBoxLayout
)
from PyQt6.QtCore import QDate
from typing import Optional
from utils.logger import log

class ConfigTab(QWidget):
    def __init__(self, serial_reader, serial_conn, db):
        super().__init__()
        self.serial_reader = serial_reader
        self.serial_conn = serial_conn
        self.db = db
        self.zero_offset: Optional[dict[str, float]] = None
        self.deadband: float = 0.1

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(24)

        # --- Sensor registration form ---
        form_group = QGroupBox("Register new sensor")
        form_layout = QFormLayout()
        self.type_edit = QLineEdit()
        self.location_edit = QLineEdit()
        self.install_date = QDateEdit()
        self.install_date.setCalendarPopup(True)
        self.install_date.setDate(QDate.currentDate())
        form_layout.addRow("Type:", self.type_edit)
        form_layout.addRow("Location:", self.location_edit)
        form_layout.addRow("Installed on:", self.install_date)
        self.add_btn = QPushButton("Add Sensor")
        self.add_btn.clicked.connect(self._add_sensor)
        form_layout.addRow(self.add_btn)
        form_group.setLayout(form_layout)
        root.addWidget(form_group)

        # --- Accelerometer calibration ---
        calib_group = QGroupBox("Accelerometer Calibration")
        calib_layout = QVBoxLayout()
        # Zero offset button
        zero_btn = QPushButton("Calibrate Zero")
        zero_btn.clicked.connect(self._calibrate_zero)
        calib_layout.addWidget(zero_btn)
        self.zero_label = QLabel("Zero offset: not set")
        calib_layout.addWidget(self.zero_label)
        # Deadband setting
        dead_layout = QHBoxLayout()
        dead_layout.addWidget(QLabel("Deadband (m/s²):"))
        self.dead_spin = QDoubleSpinBox()
        self.dead_spin.setRange(0.0, 5.0)
        self.dead_spin.setSingleStep(0.1)
        self.dead_spin.setValue(self.deadband)
        dead_layout.addWidget(self.dead_spin)
        dead_btn = QPushButton("Set Deadband")
        dead_btn.clicked.connect(self._set_deadband)
        dead_layout.addWidget(dead_btn)
        calib_layout.addLayout(dead_layout)
        calib_group.setLayout(calib_layout)
        root.addWidget(calib_group)

        # Spacer
        root.addStretch(1)

    def _add_sensor(self):
        if not self.db:
            log("No database connection")
            return
        stype = self.type_edit.text().strip()
        loc = self.location_edit.text().strip()
        date = self.install_date.date().toString("yyyy-MM-dd")
        if not stype or not loc:
            log("Type and location required")
            return
        try:
            self.db.add_sensor(stype, loc, date)
            log(f"Added sensor: {stype} at {loc}")
            self.type_edit.clear()
            self.location_edit.clear()
        except Exception as e:
            log(f"DB error adding sensor: {e}")

    def _calibrate_zero(self):
        pkt = getattr(self.serial_reader, 'last_packet', None)
        if not pkt or 'acceleration' not in pkt:
            log("No acceleration data to calibrate")
            return
        acc = pkt['acceleration']
        self.zero_offset = {'x': acc['x'], 'y': acc['y'], 'z': acc['z']}
        self.zero_label.setText(
            f"Zero offset: x={acc['x']:.2f}, y={acc['y']:.2f}, z={acc['z']:.2f}"
        )
        log("Accelerometer zero calibrated")

    def _set_deadband(self):
        self.deadband = self.dead_spin.value()
        log(f"Deadband set to ±{self.deadband:.2f} m/s²")

    # You can apply offsets/deadband in LiveTab by subtracting zero_offset and
    # ignoring values within ±deadband
