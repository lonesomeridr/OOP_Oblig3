from __future__ import annotations
"""
LiveTab v3 – polish per 2025‑04‑19 notes (composite tile fix)
• Wider, fixed‑width value tiles
• Combined Acceleration tile with x/y/z sub‑values
• Temperature y‑axis fixed 15–30 °C, axes labelled
• Graphs scroll smoothly (sliding window 60 s)
"""

import time
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

DARK_BG  = "#121212"
CARD_BG  = "#1e1e1e"
TEMP_COL = "#ffcc00"
ACC_COLS = {"x": "#3fa7d6", "y": "#bada55", "z": "#f17c67"}
WINDOW_SECONDS = 60  # seconds

class LiveTab(QWidget):
    def __init__(self, serial_reader, db: Optional[object] = None):
        super().__init__()
        self.db = db
        self.last_js = 0.0
        self.start = time.time()
        self.MAX_POINTS = 300

        root = QVBoxLayout(self)
        root.setContentsMargins(8,8,8,8)
        self.setStyleSheet(f"background:{DARK_BG};color:#e0e0e0;")

        # --------------- value tiles ---------------
        tile_row = QHBoxLayout()
        tile_row.setSpacing(16)
        self.tiles: dict[str, QLabel] = {}

        # Temperature tile
        temp_frame, temp_lbl = self._make_tile('Temperature', TEMP_COL, fixed_w=200)
        self.tiles['Temperature'] = temp_lbl
        tile_row.addWidget(temp_frame)

        # Acceleration composite tile
        acc_frame = QFrame()
        acc_frame.setFixedWidth(300)
        acc_frame.setStyleSheet(f"background:{CARD_BG};border-radius:10px;")
        acc_layout = QVBoxLayout(acc_frame)
        acc_layout.setContentsMargins(8,8,8,8)
        title = QLabel("Acceleration", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:11pt; margin:0px; padding-bottom:2px;")
        acc_layout.addWidget(title)
        # sub-values row
        sub_row = QHBoxLayout()
        sub_row.setSpacing(8)
        for axis in ('x', 'y', 'z'):
            lbl = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size:22pt; font-weight:600; color:{ACC_COLS[axis]};")
            self.tiles[axis] = lbl
            sub_row.addWidget(lbl)
        acc_layout.addLayout(sub_row)
        tile_row.addWidget(acc_frame)

        tile_row.addStretch(1)
        root.addLayout(tile_row)

        # --------------- plots ---------------
        plot_row = QHBoxLayout()
        plot_row.setSpacing(8)
        self.temp_view = QWebEngineView()
        self.acc_view  = QWebEngineView()
        for widget in (self.temp_view, self.acc_view):
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            plot_row.addWidget(widget)
        root.addLayout(plot_row)

        self._init_plots()
        serial_reader.data_ready.connect(self._update)

    def _make_tile(self, label: str, color: str, fixed_w: int) -> Tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setFixedWidth(fixed_w)
        frame.setStyleSheet(f"background:{CARD_BG};border-radius:10px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8,8,8,8)
        title_lbl = QLabel(label, alignment=Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size:11pt;")
        val_lbl = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"font-size:24pt;font-weight:600;color:{color}; margin-top:2px;")
        layout.addWidget(title_lbl)
        layout.addWidget(val_lbl)
        return frame, val_lbl

    def _html(self, body: str) -> str:
        return (
            f"<html><head><script src='https://cdn.plot.ly/plotly-2.31.1.min.js'></script></head>"
            f"<body style='margin:0;background:{DARK_BG};'>{body}</body></html>"
        )

    def _init_plots(self):
        temp_body = f"""
        <div id='t' style='width:100%;height:100%'></div>
        <script>
        var layout={{template:'plotly_dark',paper_bgcolor:'{DARK_BG}',plot_bgcolor:'{DARK_BG}',
                     margin:{{l:50,r:10,t:40,b:40}},title:'Temperature',
                     xaxis:{{title:'Time (s)'}}, yaxis:{{title:'°C',range:[15,30]}}}};
        Plotly.newPlot('t', [{{x:[],y:[],name:'Temp',line:{{color:'{TEMP_COL}'}}}}], layout);
        </script>
        """
        self.temp_view.setHtml(self._html(temp_body))

        accel_body = f"""
        <div id='a' style='width:100%;height:100%'></div>
        <script>
        var layout={{template:'plotly_dark',paper_bgcolor:'{DARK_BG}',plot_bgcolor:'{DARK_BG}',
                     margin:{{l:50,r:10,t:40,b:40}},title:'Acceleration',
                     xaxis:{{title:'Time (s)'}}, yaxis:{{title:'m/s²'}}}};
        Plotly.newPlot('a', [
          {{x:[],y:[],name:'Ax',line:{{color:'{ACC_COLS['x']}'}}}},
          {{x:[],y:[],name:'Ay',line:{{color:'{ACC_COLS['y']}'}}}},
          {{x:[],y:[],name:'Az',line:{{color:'{ACC_COLS['z']}'}}}}
        ], layout);
        </script>
        """
        self.acc_view.setHtml(self._html(accel_body))

    def _update(self, pkt: dict):
        t = round(time.time() - self.start, 2)
        temp = pkt.get('temperature', {}).get('temperature')
        ax = pkt.get('acceleration', {}).get('x')
        ay = pkt.get('acceleration', {}).get('y')
        az = pkt.get('acceleration', {}).get('z')

        if temp is not None:
            self.tiles['Temperature'].setText(f"{temp:.1f}°C")
        if ax is not None:
            self.tiles['x'].setText(f"{ax:.2f}")
        if ay is not None:
            self.tiles['y'].setText(f"{ay:.2f}")
        if az is not None:
            self.tiles['z'].setText(f"{az:.2f}")

        # throttle
        if time.time() - self.last_js < 0.15:
            return
        self.last_js = time.time()

        # Extend and slide temp
        if temp is not None:
            js = (
                f"Plotly.extendTraces('t',{{x:[[{round(time.time()-self.start,2)}]],y:[[{temp}]]}},[0],{self.MAX_POINTS});"
                f"Plotly.relayout('t',{{xaxis:{{range:[Math.max({round(time.time()-self.start,2)}-{WINDOW_SECONDS},0),{round(time.time()-self.start,2)}]}}}});"
            )
            self.temp_view.page().runJavaScript(js)

        # Extend and slide accel
        if None not in (ax, ay, az):
            js = (
                f"Plotly.extendTraces('a',{{x:[[{round(time.time()-self.start,2)}],[{round(time.time()-self.start,2)}],[{round(time.time()-self.start,2)}]],"
                f"y:[[{ax}],[{ay}],[{az}]]}},[0,1,2],{self.MAX_POINTS});"
                f"Plotly.relayout('a',{{xaxis:{{range:[Math.max({round(time.time()-self.start,2)}-{WINDOW_SECONDS},0),{round(time.time()-self.start,2)}]}}}});"
            )
            self.acc_view.page().runJavaScript(js)

        # optional DB log
        if self.db:
            try:
                if temp is not None:
                    self.db.insert_temperature(pkt['temperature']['sensor_id'], temp)
                if None not in (ax, ay, az):
                    self.db.insert_accel(pkt['acceleration']['sensor_id'], ax, ay, az)
            except Exception as exc:
                print(f"DB error: {exc}")
