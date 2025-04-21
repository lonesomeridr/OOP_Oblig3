from __future__ import annotations
"""
ConfigTab – add new sensors + accelerometer calibration

• Add sensor entries (type, location, installation_date)
• Calibrate zero offset for accelerometer (stored in DB)
• Set deadband threshold (stored in DB)
"""

import datetime
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QPushButton, QLabel, QDoubleSpinBox, QGroupBox, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import QDate
from utils.logger import log

class ConfigTab(QWidget):
    def __init__(self, serial_reader, serial_conn, db):
        super().__init__()
        self.serial_reader = serial_reader
        self.serial_conn = serial_conn
        self.db = db

        # will be set to the accelerometer sensor_id if found
        self.accel_sensor_id: Optional[int] = None
        self.zero_offset: dict[str, float] = {'x':0.0,'y':0.0,'z':0.0}
        self.deadband: float = 0.1

        root = QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(24)

        # === Sensor registration form ===
        form_group = QGroupBox("Register new sensor")
        form_layout = QFormLayout()
        self.type_edit = QLineEdit()
        self.location_edit = QLineEdit()
        self.install_date = QDateEdit(calendarPopup=True)
        self.install_date.setDate(QDate.currentDate())
        form_layout.addRow("Type:", self.type_edit)
        form_layout.addRow("Location:", self.location_edit)
        form_layout.addRow("Installed on:", self.install_date)
        self.add_btn = QPushButton("Add Sensor")
        self.add_btn.clicked.connect(self._add_sensor)
        form_layout.addRow(self.add_btn)
        form_group.setLayout(form_layout)
        root.addWidget(form_group)

        # === Accelerometer calibration ===
        calib_group = QGroupBox("Accelerometer Calibration")
        calib_layout = QVBoxLayout()

        # zero offset
        zero_btn = QPushButton("Calibrate Zero")
        zero_btn.clicked.connect(self._calibrate_zero)
        calib_layout.addWidget(zero_btn)
        self.zero_label = QLabel("Zero offset: not set")
        calib_layout.addWidget(self.zero_label)

        # deadband
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

        root.addStretch(1)

        # — load existing sensors & accel config —
        if self.db:
            try:
                # find the accelerometer sensor_id
                for sid, stype, _, _ in self.db.get_sensors():
                    if 'accel' in stype.lower():
                        self.accel_sensor_id = sid
                        break

                # if we have an accel sensor, load its config
                if self.accel_sensor_id is not None:
                    cfg = self.db.get_accel_config(self.accel_sensor_id)
                    self.zero_offset = {
                        'x': cfg['zero_x'],
                        'y': cfg['zero_y'],
                        'z': cfg['zero_z']
                    }
                    self.deadband = cfg['deadband']
                    # update UI
                    self.zero_label.setText(
                        f"Zero offset: x={cfg['zero_x']:.2f}, "
                        f"y={cfg['zero_y']:.2f}, z={cfg['zero_z']:.2f}"
                    )
                    self.dead_spin.setValue(self.deadband)
            except Exception as e:
                log(f"ConfigTab init load error: {e}")

    def _add_sensor(self):
        """Called when user clicks Add Sensor."""
        if not self.db:
            QMessageBox.warning(self, "No DB", "Database connection not available.")
            return

        stype = self.type_edit.text().strip()
        loc   = self.location_edit.text().strip()
        date  = self.install_date.date().toPyDate()  # datetime.date

        if not stype or not loc:
            QMessageBox.information(self, "Incomplete", "Type and location are required.")
            return

        try:
            self.db.add_sensor(stype, loc, date)
            QMessageBox.information(self, "Success", f"Added sensor '{stype}'.")
            self.type_edit.clear()
            self.location_edit.clear()
        except Exception as exc:
            log(f"DB error adding sensor: {exc}")
            QMessageBox.critical(self, "DB Error", str(exc))

    def _calibrate_zero(self):
        """Capture the current accel sample as our zero offset and store it."""
        if not self.accel_sensor_id:
            QMessageBox.warning(self, "No Sensor", "No accelerometer sensor found in DB.")
            return

        pkt = getattr(self.serial_reader, 'last_packet', None)
        if not pkt or 'acceleration' not in pkt:
            QMessageBox.information(self, "No Data",
                "No acceleration packet yet — please start live data first.")
            return

        acc = pkt['acceleration']
        zx, zy, zz = acc['x'], acc['y'], acc['z']
        self.zero_offset = {'x':zx,'y':zy,'z':zz}

        # persist to DB
        try:
            self.db.upsert_accel_config(
                self.accel_sensor_id,
                zx, zy, zz,
                self.deadband
            )
            self.zero_label.setText(
                f"Zero offset: x={zx:.2f}, y={zy:.2f}, z={zz:.2f}"
            )
            QMessageBox.information(self, "Calibrated", "Zero offset stored.")
        except Exception as exc:
            log(f"DB error in calibrate_zero: {exc}")
            QMessageBox.critical(self, "DB Error", str(exc))

    def _set_deadband(self):
        """Store the chosen deadband into the DB so LiveTab will apply it."""
        if not self.accel_sensor_id:
            QMessageBox.warning(self, "No Sensor", "No accelerometer sensor found in DB.")
            return

        db_val = self.dead_spin.value()
        self.deadband = db_val

        try:
            # write back current zero_offset as well
            self.db.upsert_accel_config(
                self.accel_sensor_id,
                self.zero_offset['x'],
                self.zero_offset['y'],
                self.zero_offset['z'],
                self.deadband
            )
            QMessageBox.information(
                self, "Deadband Set",
                f"Deadband ±{db_val:.2f} m/s² saved."
            )
        except Exception as exc:
            log(f"DB error in set_deadband: {exc}")
            QMessageBox.critical(self, "DB Error", str(exc))
