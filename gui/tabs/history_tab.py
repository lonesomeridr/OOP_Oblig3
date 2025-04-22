from __future__ import annotations
import json, time, traceback
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QPushButton, QFrame
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from utils.logger import log

# Match LiveTab styling
DARK_BG = "#121212"
CARD_BG = "#1e1e1e"
BUTTON_BG = "#3d3d3d"  # Matching gray for button
BUTTON_HOVER = "#4d4d4d"
BUTTON_PRESSED = "#2d2d2d"
TEMP_COL = "#ffcc00"
ACC_COLS = {"x": "#3fa7d6", "y": "#bada55", "z": "#f17c67"}


class HistoryTab(QWidget):
    """
    History view using Plotly inside QWebEngineView with stacked plots layout.
    """

    def __init__(self, db: Optional[object]):
        super().__init__()
        self.db = db

        # Set minimum height for better plot visibility
        self.setMinimumHeight(800)

        # --- Controls ---
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(f"""
            background: {CARD_BG};
            border-radius: 8px;
        """)
        ctrl_layout = QHBoxLayout(ctrl_frame)
        # Keep it compact with smaller margins
        ctrl_layout.setContentsMargins(12, 8, 12, 8)
        ctrl_layout.setSpacing(8)

        # "Last" label
        last_label = QLabel("Last")
        last_label.setStyleSheet("font-size: 13px;")
        ctrl_layout.addWidget(last_label)

        # Hours spinbox with visible arrows
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 24)
        self.hours_spin.setValue(1)
        self.hours_spin.setMinimumWidth(50)
        self.hours_spin.setFixedHeight(26)  # More compact
        self.hours_spin.setStyleSheet("""
            QSpinBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 2px 2px 2px 4px;
                font-size: 13px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                background-color: #3d3d3d;
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #5d5d5d;
            }
            QSpinBox::up-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTYgMyBMMTAgNyBMMiA3IFoiIGZpbGw9IiNlMGUwZTAiLz48L3N2Zz4=);
                width: 10px;
                height: 6px;
            }
            QSpinBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTYgOSBMMTAgNSBMMiA1IFoiIGZpbGw9IiNlMGUwZTAiLz48L3N2Zz4=);
                width: 10px;
                height: 6px;
            }
        """)
        ctrl_layout.addWidget(self.hours_spin)

        # "hour(s)" label
        hours_label = QLabel("hour(s)")
        hours_label.setStyleSheet("font-size: 13px;")
        ctrl_layout.addWidget(hours_label)

        # Spacer for better button placement
        ctrl_layout.addSpacing(10)

        # Load button with gray color scheme to match GUI
        load_btn = QPushButton("Load History")
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.setMinimumWidth(100)
        load_btn.setFixedHeight(26)  # Compact height
        load_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_BG};
                color: white;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BUTTON_PRESSED};
            }}
        """)
        ctrl_layout.addWidget(load_btn)

        # Add stretch to push controls to the left
        ctrl_layout.addStretch(1)

        # --- Plot widgets ---
        self.temp_view = QWebEngineView()
        self.acc_x_view = QWebEngineView()
        self.acc_y_view = QWebEngineView()
        self.acc_z_view = QWebEngineView()

        # Set minimum heights for all plots
        self.temp_view.setMinimumHeight(180)
        self.acc_x_view.setMinimumHeight(180)
        self.acc_y_view.setMinimumHeight(180)
        self.acc_z_view.setMinimumHeight(180)

        # --- Layout ---
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)
        self.setStyleSheet(f"background:{DARK_BG};color:#e0e0e0;")

        # Add control frame at top
        root.addWidget(ctrl_frame)

        # Create vertical layout for stacked plots
        plots_layout = QVBoxLayout()
        plots_layout.setSpacing(8)

        plots_layout.addWidget(self.temp_view)
        plots_layout.addWidget(self.acc_x_view)
        plots_layout.addWidget(self.acc_y_view)
        plots_layout.addWidget(self.acc_z_view)

        root.addLayout(plots_layout)

        # Connect signals
        load_btn.clicked.connect(self._load_history)

        # Initialize with blank displays
        self._set_blank_all()

    def _set_blank_all(self):
        """Set blank content for all views"""
        for view in [self.temp_view, self.acc_x_view, self.acc_y_view, self.acc_z_view]:
            self._set_blank(view)

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
            acc_rows = self.db.fetch_last_hours("acceleration_readings", hrs)

            # --- Temperature plot ---
            # temp_rows: id, sensor_id, temperature, created_at
            times_t = [int(time.mktime(r[3].timetuple()) * 1000) for r in temp_rows]
            vals_t = [r[2] for r in temp_rows]

            # Generate HTML+JS for temp
            temp_html = self._create_plot_html(
                "plot_temp",
                "Temperature History",
                "Time", "°C",
                [{"times": times_t, "values": vals_t, "name": "Temperature", "color": TEMP_COL}],
                hrs
            )
            self.temp_view.setHtml(temp_html)

            # --- Acceleration plots (separate X, Y, Z) ---
            # acc_rows: id, sensor_id, x, y, z, created_at
            times_a = [int(time.mktime(r[5].timetuple()) * 1000) for r in acc_rows]
            xs = [r[2] for r in acc_rows]
            ys = [r[3] for r in acc_rows]
            zs = [r[4] for r in acc_rows]

            # X-axis acceleration
            acc_x_html = self._create_plot_html(
                "plot_acc_x",
                "Acceleration X-Axis History",
                "Time", "m/s²",
                [{"times": times_a, "values": xs, "name": "X", "color": ACC_COLS['x']}],
                hrs
            )
            self.acc_x_view.setHtml(acc_x_html)

            # Y-axis acceleration
            acc_y_html = self._create_plot_html(
                "plot_acc_y",
                "Acceleration Y-Axis History",
                "Time", "m/s²",
                [{"times": times_a, "values": ys, "name": "Y", "color": ACC_COLS['y']}],
                hrs
            )
            self.acc_y_view.setHtml(acc_y_html)

            # Z-axis acceleration
            acc_z_html = self._create_plot_html(
                "plot_acc_z",
                "Acceleration Z-Axis History",
                "Time", "m/s²",
                [{"times": times_a, "values": zs, "name": "Z", "color": ACC_COLS['z']}],
                hrs
            )
            self.acc_z_view.setHtml(acc_z_html)

        except Exception as exc:
            tb = traceback.format_exc(limit=1)
            log(f"HistoryTab load error: {exc}\n{tb}")

    def _create_plot_html(self, div_id, title, x_title, y_title, data_series, hours):
        """Create HTML for a plot with common styling"""
        traces_json = []

        for series in data_series:
            trace = {
                "x": series["times"],
                "y": series["values"],
                "mode": "lines",
                "name": series["name"],
                "line": {"color": series["color"]}
            }
            traces_json.append(json.dumps(trace))

        traces_str = ",".join(traces_json)

        html = f"""
        <html>
        <head>
          <script src="https://cdn.plot.ly/plotly-2.31.1.min.js"></script>
        </head>
        <body style="margin:0;background:{DARK_BG};">
          <div id="{div_id}" style="width:100%;height:100%;"></div>
          <script>
            var layout = {{
              template:'plotly_dark',
              paper_bgcolor:'{DARK_BG}',
              plot_bgcolor:'{DARK_BG}',
              margin: {{l:50,r:10,t:40,b:40}},
              title: '{title} ({hours}h)',
              xaxis: {{title:'{x_title}', type:'date'}},
              yaxis: {{title:'{y_title}'}}
            }};
            Plotly.newPlot('{div_id}',[{traces_str}],layout);
          </script>
        </body>
        </html>
        """
        return html