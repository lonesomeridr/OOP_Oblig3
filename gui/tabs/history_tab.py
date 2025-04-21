from __future__ import annotations
import json, time, traceback
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from utils.logger import log

DARK_BG  = "#121212"
TEMP_COL = "#ffcc00"
ACC_COLS = {"x":"#3fa7d6","y":"#bada55","z":"#f17c67"}

class HistoryTab(QWidget):
    """
    History view using Plotly inside QWebEngineView.
    """
    def __init__(self, db: Optional[object]):
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

        # --- Plot widgets ---
        self.temp_view = QWebEngineView()
        self.acc_view  = QWebEngineView()

        # --- Layout ---
        root = QVBoxLayout(self)
        root.setContentsMargins(8,8,8,8)
        root.setSpacing(8)
        root.addLayout(ctrl)
        plots = QHBoxLayout()
        plots.setSpacing(8)
        plots.addWidget(self.temp_view,1)
        plots.addWidget(self.acc_view,1)
        root.addLayout(plots)

        load_btn.clicked.connect(self._load_history)
        # initial blank pages
        self._set_blank(self.temp_view)
        self._set_blank(self.acc_view)

    def _set_blank(self, view: QWebEngineView):
        html = f"<html><body style='margin:0;background:{DARK_BG};'></body></html>"
        view.setHtml(html)

    def _load_history(self):
        if not self.db:
            log("HistoryTab: no DB connection")
            return

        hrs = self.hours_spin.value()
        try:
            # fetch rows
            temp_rows = self.db.fetch_last_hours("temperature_readings", hrs)
            acc_rows  = self.db.fetch_last_hours("acceleration_readings", hrs)

            # build JS arrays
            # temp_rows: id, sensor_id, temperature, created_at
            times_t = [int(time.mktime(r[3].timetuple())*1000) for r in temp_rows]
            vals_t  = [r[2] for r in temp_rows]

            # acc_rows: id, sensor_id, x, y, z, created_at
            times_a = [int(time.mktime(r[5].timetuple())*1000) for r in acc_rows]
            xs      = [r[2] for r in acc_rows]
            ys      = [r[3] for r in acc_rows]
            zs      = [r[4] for r in acc_rows]

            # generate HTML+JS for Temp
            temp_html = f"""
            <html>
            <head>
              <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body style="margin:0;background:{DARK_BG};">
              <div id="plot_temp" style="width:100%;height:100%;"></div>
              <script>
                var trace = {{
                  x: {json.dumps(times_t)},
                  y: {json.dumps(vals_t)},
                  mode: 'lines+markers',
                  name: 'Temperature (°C)',
                  line: {{color:'{TEMP_COL}'}}
                }};
                var layout = {{
                  template:'plotly_dark',
                  paper_bgcolor:'{DARK_BG}',
                  plot_bgcolor:'{DARK_BG}',
                  margin: {{l:40,r:10,t:40,b:40}},
                  title: 'Temperature History ({hrs}h)',
                  xaxis: {{title:'Time', type:'date'}},
                  yaxis: {{title:'°C'}}
                }};
                Plotly.newPlot('plot_temp',[trace],layout);
              </script>
            </body>
            </html>
            """
            self.temp_view.setHtml(temp_html)

            # generate HTML+JS for Accel
            acc_html = f"""
            <html>
            <head>
              <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body style="margin:0;background:{DARK_BG};">
              <div id="plot_acc" style="width:100%;height:100%;"></div>
              <script>
                var t1 = {{x:{json.dumps(times_a)}, y:{json.dumps(xs)}, mode:'lines', name:'Ax', line:{{color:'{ACC_COLS['x']}'}}}};
                var t2 = {{x:{json.dumps(times_a)}, y:{json.dumps(ys)}, mode:'lines', name:'Ay', line:{{color:'{ACC_COLS['y']}'}}}};
                var t3 = {{x:{json.dumps(times_a)}, y:{json.dumps(zs)}, mode:'lines', name:'Az', line:{{color:'{ACC_COLS['z']}'}}}};
                var layout = {{
                  template:'plotly_dark',
                  paper_bgcolor:'{DARK_BG}',
                  plot_bgcolor:'{DARK_BG}',
                  margin: {{l:40,r:10,t:40,b:40}},
                  title: 'Acceleration History ({hrs}h)',
                  xaxis: {{title:'Time', type:'date'}},
                  yaxis: {{title:'m/s²'}}
                }};
                Plotly.newPlot('plot_acc',[t1,t2,t3],layout);
              </script>
            </body>
            </html>
            """
            self.acc_view.setHtml(acc_html)

        except Exception as exc:
            tb = traceback.format_exc(limit=1)
            log(f"HistoryTab load error: {exc}\n{tb}")
