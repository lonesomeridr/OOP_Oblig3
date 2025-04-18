from __future__ import annotations

"""
Live‑fanen: sanntidsvisning av verdier som kommer fra SerialReader.
Viser både numeriske labels og en Plotly‑graf som ruller.
DB‑objekt er valgfritt – hvis det gis logges data automatisk.
"""

import time
import json
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Qt‑signal type import for bedre type‑hints
from PyQt6.QtCore import pyqtSignal  # only for typing, not used directly


class LiveTab(QWidget):
    """Rask og enkel sanntids‑GUI‑fane."""

    # ---------------------------------------------------------------------
    # API
    # ---------------------------------------------------------------------
    def __init__(self, serial_reader, db: Optional[object] = None):
        super().__init__()
        self.serial_reader = serial_reader  # SerialReader‑instans med signalet data_ready
        self.db = db                        # DB‑wrapper (kan være None)

        # --------------------------------------------------
        # GUI‑layout
        # --------------------------------------------------
        main_layout = QVBoxLayout()

        # --- Dashboard (numeriske verdier) ---
        dashboard = QHBoxLayout()
        self.temp_label = QLabel("Temperature: -- °C")
        self.ax_label = QLabel("Accel X: -- m/s²")
        self.ay_label = QLabel("Accel Y: -- m/s²")
        self.az_label = QLabel("Accel Z: -- m/s²")
        for lbl in (self.temp_label, self.ax_label, self.ay_label, self.az_label):
            lbl.setStyleSheet("font-size:14pt; font-weight:bold;")
            dashboard.addWidget(lbl)

        # --- Checkboxes for hvilke spor som skal vises ---
        cb_layout = QHBoxLayout()
        self.cb_temp = QCheckBox("Temp"); self.cb_temp.setChecked(True)
        self.cb_ax = QCheckBox("Acc X"); self.cb_ax.setChecked(True)
        self.cb_ay = QCheckBox("Acc Y"); self.cb_ay.setChecked(True)
        self.cb_az = QCheckBox("Acc Z"); self.cb_az.setChecked(True)
        cb_layout.addWidget(QLabel("Show:"))
        for cb in (self.cb_temp, self.cb_ax, self.cb_ay, self.cb_az):
            cb_layout.addWidget(cb)

        # --- Plotly‑view ---
        self.plot_view = QWebEngineView()
        self._load_initial_chart()

        # Sammensett layout
        main_layout.addLayout(dashboard)
        main_layout.addLayout(cb_layout)
        main_layout.addWidget(self.plot_view)
        self.setLayout(main_layout)

        # --------------------------------------------------
        # Internt
        # --------------------------------------------------
        self.start_time = time.time()
        self.MAX_POINTS = 30  # antall punkt som beholdes i grafen

        # Koble signal → slot
        self.serial_reader.data_ready.connect(self._update_from_packet)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _load_initial_chart(self) -> None:
        """Første tomme Plotly‑graf med fire spor."""
        html = """
        <html>
        <head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>
        <body>
          <div id="plot"></div>
          <script>
            var data = [
              {x: [], y: [], mode:'lines+markers', name:'Temperature (°C)', visible:true},
              {x: [], y: [], mode:'lines+markers', name:'Acceleration X (m/s²)', visible:true},
              {x: [], y: [], mode:'lines+markers', name:'Acceleration Y (m/s²)', visible:true},
              {x: [], y: [], mode:'lines+markers', name:'Acceleration Z (m/s²)', visible:true}
            ];
            var layout = {
              title: 'Real‑Time Sensor Data',
              xaxis: {title: 'Time (s)'},
              yaxis: {title: 'Value'},
              template: 'plotly_dark'
            };
            Plotly.newPlot('plot', data, layout);
          </script>
        </body>
        </html>
        """
        self.plot_view.setHtml(html)

    # ------------------------------------------------------------------
    def _update_from_packet(self, pkt: dict) -> None:
        """Slot som kalles hver gang SerialReader emitterer data_ready."""
        now_s = round(time.time() - self.start_time, 1)

        # ----------------- Parse temperatur -----------------
        temp_v = None
        if (t := pkt.get("temperature")):
            temp_v = t.get("temperature")
            if temp_v is not None:
                self.temp_label.setText(f"Temperature: {temp_v:.2f} °C")
        else:
            self.temp_label.setText("Temperature: -- °C")

        # ----------------- Parse akselerasjon --------------
        ax = ay = az = None
        if (a := pkt.get("acceleration")):
            ax, ay, az = a.get("x"), a.get("y"), a.get("z")
        self.ax_label.setText(f"Accel X: {ax:.2f} m/s²" if ax is not None else "Accel X: -- m/s²")
        self.ay_label.setText(f"Accel Y: {ay:.2f} m/s²" if ay is not None else "Accel Y: -- m/s²")
        self.az_label.setText(f"Accel Z: {az:.2f} m/s²" if az is not None else "Accel Z: -- m/s²")

        # ----------------- Oppdater Plotly -----------------
        # Null‑safe verdier (Plotly aksepterer 'null')
        temp_js = json.dumps(temp_v)  # gir f.eks. "null" eller 23.4
        ax_js = json.dumps(ax)
        ay_js = json.dumps(ay)
        az_js = json.dumps(az)

        vis_temp = "true" if self.cb_temp.isChecked() and temp_v is not None else "legendonly"
        vis_ax = "true" if self.cb_ax.isChecked() and ax is not None else "legendonly"
        vis_ay = "true" if self.cb_ay.isChecked() and ay is not None else "legendonly"
        vis_az = "true" if self.cb_az.isChecked() and az is not None else "legendonly"

        js = f"""
        var t={now_s};
        Plotly.extendTraces('plot', {{
            x: [[t],[t],[t],[t]],
            y: [[{temp_js}],[{ax_js}],[{ay_js}],[{az_js}]]
        }}, [0,1,2,3], {self.MAX_POINTS});

        Plotly.restyle('plot', {{visible:'{vis_temp}'}}, [0]);
        Plotly.restyle('plot', {{visible:'{vis_ax}'}},  [1]);
        Plotly.restyle('plot', {{visible:'{vis_ay}'}},  [2]);
        Plotly.restyle('plot', {{visible:'{vis_az}'}},  [3]);
        """
        self.plot_view.page().runJavaScript(js)

        # ----------------- DB‑logging (valgfritt) ------------
        if self.db:
            if temp_v is not None:
                self.db.insert_temperature(pkt['temperature']['sensor_id'], temp_v)
            if ax is not None:
                self.db.insert_accel(pkt['acceleration']['sensor_id'], ax, ay, az)
