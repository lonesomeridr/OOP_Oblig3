from __future__ import annotations
from datetime import datetime
import traceback

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from utils.logger import log

class HistoryTab(QWidget):
    """
    Simple history viewer using matplotlib.
    Select last N hours and click Load to plot Temperature & Acceleration.
    """
    def __init__(self, db):
        super().__init__()
        self.db = db

        # --- Controls ---
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Last"))
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 24)
        self.hours_spin.setValue(1)
        ctrl.addWidget(self.hours_spin)
        ctrl.addWidget(QLabel("hour(s)"))
        load_btn = QPushButton("Load")
        ctrl.addWidget(load_btn)
        ctrl.addStretch(1)

        # --- Figure for Temperature ---
        self.temp_fig = Figure(figsize=(5, 3))
        self.temp_ax  = self.temp_fig.add_subplot(111)
        self.temp_canvas = FigureCanvas(self.temp_fig)

        # --- Figure for Acceleration ---
        self.acc_fig = Figure(figsize=(5, 3))
        self.acc_ax  = self.acc_fig.add_subplot(111)
        self.acc_canvas = FigureCanvas(self.acc_fig)

        # --- Layout ---
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.addLayout(ctrl)

        root.addWidget(self.temp_canvas)
        root.addWidget(self.acc_canvas)

        load_btn.clicked.connect(self._load_history)

    def _load_history(self):
        if not self.db:
            log("HistoryTab: no DB connection")
            return

        hrs = self.hours_spin.value()
        try:
            # Fetch from your tables. Adjust the timestamp index if yours differs.
            temp_rows = self.db.fetch_last_hours("temperature_readings", hrs)
            acc_rows  = self.db.fetch_last_hours("acceleration_readings", hrs)

            # Extract data
            # Assumes temp_rows: (id, sensor_id, temperature, timestamp)
            times_t = [row[3] for row in temp_rows]
            vals_t  = [row[2] for row in temp_rows]

            # Assumes acc_rows: (id, sensor_id, x, y, z, timestamp)
            times_a = [row[5] for row in acc_rows]
            xs = [row[2] for row in acc_rows]
            ys = [row[3] for row in acc_rows]
            zs = [row[4] for row in acc_rows]

            # --- Plot Temperature ---
            self.temp_ax.clear()
            self.temp_ax.plot(times_t, vals_t, marker='o', linestyle='-', color='orange')
            self.temp_ax.set_title(f"Temperature (last {hrs}h)")
            self.temp_ax.set_xlabel("Time")
            self.temp_ax.set_ylabel("°C")
            self.temp_fig.autofmt_xdate()
            self.temp_canvas.draw()

            # --- Plot Acceleration ---
            self.acc_ax.clear()
            self.acc_ax.plot(times_a, xs, label='Ax', color='skyblue')
            self.acc_ax.plot(times_a, ys, label='Ay', color='limegreen')
            self.acc_ax.plot(times_a, zs, label='Az', color='salmon')
            self.acc_ax.set_title(f"Acceleration (last {hrs}h)")
            self.acc_ax.set_xlabel("Time")
            self.acc_ax.set_ylabel("m/s²")
            self.acc_ax.legend()
            self.acc_fig.autofmt_xdate()
            self.acc_canvas.draw()

        except Exception as exc:
            # catch everything so it doesn't crash the app
            tb = traceback.format_exc(limit=1)
            log(f"HistoryTab load error: {exc}\n{tb}")
