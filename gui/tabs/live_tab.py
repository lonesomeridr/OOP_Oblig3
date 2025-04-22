from __future__ import annotations

"""
LiveTab – Real-time Sensor Monitoring

• Live visualization of temperature and acceleration values
• Time-based sliding window plots (60 seconds history)
• Acceleration zero calibration and deadband filtering
• Visual alarm indicators for sensor threshold violations
"""

import time
from typing import Optional, Tuple, Dict
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# UI Colors
DARK_BG = "#121212"
CARD_BG = "#1e1e1e"
TEMP_COL = "#ffcc00"
ACC_COLS = {"x": "#3fa7d6", "y": "#bada55", "z": "#f17c67"}
CAL_COL = "#8080ff"
ALARM_COLOR = "#FF5722"  # Alarm color (vibrant orange-red)
WINDOW_SECONDS = 60  # Seconds to display in plots
ALARM_DISPLAY_SECONDS = 5  # How long to show vibration alarms


class LiveTab(QWidget):
    def __init__(self, serial_reader, db: Optional[object] = None):
        super().__init__()
        self.db = db
        self.last_js = 0.0
        self.start = time.time()
        self.MAX_POINTS = 300
        self.last_calib_check = 0  # Track when we last checked for calibration updates

        # Initialize calibration values with defaults
        self.calibration = {
            'zero_x': 0.0,
            'zero_y': 0.0,
            'zero_z': 0.0,
            'deadband': 0.0
        }

        # Track alarm states
        self.temp_alarm_active = False
        self.accel_alarm_active = False

        # Track latest values for threshold checking
        self.latest_temp = None
        self.latest_accel = {"x": None, "y": None, "z": None}
        self.thresholds = {"temp_min": None, "temp_max": None, "accel_max": None}

        # Load calibration values if DB is available
        self.accel_sensor_id = None
        self.temp_sensor_id = None

        # Timer for auto-hiding vibration alarm
        self.vib_alarm_timer = QTimer(self)
        self.vib_alarm_timer.setSingleShot(True)
        self.vib_alarm_timer.timeout.connect(self._hide_vibration_alarm)

        # Timer for checking calibration updates
        self.calib_timer = QTimer(self)
        self.calib_timer.timeout.connect(self._check_calibration_updates)
        self.calib_timer.start(2000)  # Check for calibration updates every 2 seconds

        # UI Setup
        self.setMinimumHeight(800)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(12)
        self.setStyleSheet(f"background:{DARK_BG};color:#e0e0e0;")

        # --------------- value tiles ---------------
        tile_row = QHBoxLayout()
        tile_row.setSpacing(16)
        tile_row.addStretch(1)  # Add stretch before tiles for centering
        self.tiles: dict[str, QLabel] = {}
        self.alarm_labels: dict[str, QLabel] = {}

        # Temperature tile - now with fixed height
        temp_frame = self._make_temp_tile('Temperature', TEMP_COL, fixed_w=200)
        tile_row.addWidget(temp_frame)

        # Acceleration composite tile with integrated calibration status
        acc_frame = QFrame()
        acc_frame.setFixedWidth(300)
        acc_frame.setFixedHeight(85)  # REDUCED FROM 100 TO 85
        acc_frame.setStyleSheet(f"background:{CARD_BG};border-radius:10px;")
        acc_layout = QVBoxLayout(acc_frame)
        acc_layout.setContentsMargins(8, 8, 8, 8)
        acc_layout.setSpacing(2)  # Reduced spacing for layout

        # Title row with calibration status
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        # Add the cal status to the left with invisible spacer to maintain centering
        self.cal_status = QLabel("cal", alignment=Qt.AlignmentFlag.AlignLeft)
        self.cal_status.setStyleSheet(f"font-size:8pt; color:{CAL_COL}; margin:0; padding:0;")
        title_row.addWidget(self.cal_status)

        # Add title in the center
        title = QLabel("Acceleration", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:11pt; margin:0; padding:0;")
        title_row.addWidget(title, 1)  # Give it stretch factor

        # Add invisible spacer on the right to balance the cal indicator
        right_spacer = QLabel()
        right_spacer.setFixedWidth(self.cal_status.sizeHint().width())
        title_row.addWidget(right_spacer)

        acc_layout.addLayout(title_row)

        # Sub-values row
        sub_row = QHBoxLayout()
        sub_row.setSpacing(8)
        for axis in ('x', 'y', 'z'):
            lbl = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size:22pt; font-weight:600; color:{ACC_COLS[axis]};")
            self.tiles[axis] = lbl
            sub_row.addWidget(lbl)
        acc_layout.addLayout(sub_row)

        # REMOVED STRETCH - Changed from 1 to 0
        acc_layout.addStretch(0)

        # Alarm label for acceleration (at bottom)
        self.accel_alarm_lbl = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        # Set a smaller fixed height for the alarm label - REDUCED FROM 14 TO 12
        self.accel_alarm_lbl.setFixedHeight(12)
        self.accel_alarm_lbl.setStyleSheet(
            f"color:{ALARM_COLOR}; font-weight:bold; font-size:8pt; margin:0; padding:0;")
        # Make it invisible initially
        self.accel_alarm_lbl.setVisible(False)
        acc_layout.addWidget(self.accel_alarm_lbl)
        self.alarm_labels['Acceleration'] = self.accel_alarm_lbl

        tile_row.addWidget(acc_frame)

        tile_row.addStretch(1)  # Add stretch after tiles for centering
        root.addLayout(tile_row)

        # --------------- plots ---------------
        plots_layout = QVBoxLayout()
        plots_layout.setSpacing(8)

        # Temperature plot
        self.temp_view = QWebEngineView()
        self.temp_view.setMinimumHeight(180)
        plots_layout.addWidget(self.temp_view)

        # Acceleration plots - separate for each axis
        self.acc_x_view = QWebEngineView()
        self.acc_y_view = QWebEngineView()
        self.acc_z_view = QWebEngineView()

        # Set minimum heights for acceleration plots
        self.acc_x_view.setMinimumHeight(180)
        self.acc_y_view.setMinimumHeight(180)
        self.acc_z_view.setMinimumHeight(180)

        plots_layout.addWidget(self.acc_x_view)
        plots_layout.addWidget(self.acc_y_view)
        plots_layout.addWidget(self.acc_z_view)

        root.addLayout(plots_layout)

        # Initialize plots and load thresholds
        self._init_plots()
        self._load_thresholds()
        serial_reader.data_ready.connect(self._update)

    def _make_temp_tile(self, label: str, color: str, fixed_w: int) -> QFrame:
        """Create a temperature tile with fixed layout and proper alignment"""
        frame = QFrame()
        frame.setFixedWidth(fixed_w)
        frame.setFixedHeight(85)  # REDUCED FROM 100 TO 85
        frame.setStyleSheet(f"background:{CARD_BG};border-radius:10px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)  # Zero spacing to control exact positioning

        # Title label (fixed at top)
        title_lbl = QLabel(label, alignment=Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size:11pt; margin:0; padding:0;")
        title_lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(title_lbl)

        # Value label with vertical alignment to match acceleration values
        temp_val_lbl = QLabel("--", alignment=Qt.AlignmentFlag.AlignCenter)
        temp_val_lbl.setStyleSheet(f"font-size:22pt; font-weight:600; color:{color}; margin-top:0px; padding-top:0px;")
        layout.addWidget(temp_val_lbl)
        self.tiles['Temperature'] = temp_val_lbl

        # REMOVED STRETCH - Changed from 1 to 0
        layout.addStretch(0)

        # Alarm label at bottom with fixed height - REDUCED FROM 14 TO 12
        alarm_lbl = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        alarm_lbl.setFixedHeight(12)
        alarm_lbl.setStyleSheet(f"color:{ALARM_COLOR}; font-weight:bold; font-size:8pt; margin:0; padding:0;")
        alarm_lbl.setVisible(False)  # Hidden initially
        layout.addWidget(alarm_lbl)
        self.alarm_labels['Temperature'] = alarm_lbl

        return frame

    def _html(self, body: str) -> str:
        """Create HTML wrapper for Plotly charts"""
        return (
            f"<html><head><script src='https://cdn.plot.ly/plotly-2.31.1.min.js'></script></head>"
            f"<body style='margin:0;background:{DARK_BG};'>{body}</body></html>"
        )

    def _init_plots(self):
        """Initialize all plots"""
        # Temperature plot
        temp_body = f"""
        <div id='temp' style='width:100%;height:100%'></div>
        <script>
        var layout={{template:'plotly_dark',paper_bgcolor:'{DARK_BG}',plot_bgcolor:'{DARK_BG}',
                     margin:{{l:50,r:10,t:40,b:40}},title:'Temperature',
                     xaxis:{{title:'Time (s)'}}, yaxis:{{title:'°C'}}}};
        Plotly.newPlot('temp', [{{x:[],y:[],name:'Temp',line:{{color:'{TEMP_COL}'}}}}], layout);
        </script>
        """
        self.temp_view.setHtml(self._html(temp_body))

        # X-axis acceleration
        acc_x_body = f"""
        <div id='accx' style='width:100%;height:100%'></div>
        <script>
        var layout={{template:'plotly_dark',paper_bgcolor:'{DARK_BG}',plot_bgcolor:'{DARK_BG}',
                     margin:{{l:50,r:10,t:40,b:40}},title:'Acceleration X-Axis',
                     xaxis:{{title:'Time (s)'}}, yaxis:{{title:'m/s²'}}}};
        Plotly.newPlot('accx', [{{x:[],y:[],name:'X',line:{{color:'{ACC_COLS['x']}'}}}}], layout);
        </script>
        """
        self.acc_x_view.setHtml(self._html(acc_x_body))

        # Y-axis acceleration
        acc_y_body = f"""
        <div id='accy' style='width:100%;height:100%'></div>
        <script>
        var layout={{template:'plotly_dark',paper_bgcolor:'{DARK_BG}',plot_bgcolor:'{DARK_BG}',
                     margin:{{l:50,r:10,t:40,b:40}},title:'Acceleration Y-Axis',
                     xaxis:{{title:'Time (s)'}}, yaxis:{{title:'m/s²'}}}};
        Plotly.newPlot('accy', [{{x:[],y:[],name:'Y',line:{{color:'{ACC_COLS['y']}'}}}}], layout);
        </script>
        """
        self.acc_y_view.setHtml(self._html(acc_y_body))

        # Z-axis acceleration
        acc_z_body = f"""
        <div id='accz' style='width:100%;height:100%'></div>
        <script>
        var layout={{template:'plotly_dark',paper_bgcolor:'{DARK_BG}',plot_bgcolor:'{DARK_BG}',
                     margin:{{l:50,r:10,t:40,b:40}},title:'Acceleration Z-Axis',
                     xaxis:{{title:'Time (s)'}}, yaxis:{{title:'m/s²'}}}};
        Plotly.newPlot('accz', [{{x:[],y:[],name:'Z',line:{{color:'{ACC_COLS['z']}'}}}}], layout);
        </script>
        """
        self.acc_z_view.setHtml(self._html(acc_z_body))

    def _check_calibration_updates(self):
        """Periodically check for updated calibration values"""
        if not self.db or not self.accel_sensor_id:
            return

        try:
            # Get fresh calibration data
            config = self.db.get_accel_config(self.accel_sensor_id)

            if config:
                # Update calibration if values have changed
                new_calib = {
                    'zero_x': config.get('zero_x', 0.0) or 0.0,
                    'zero_y': config.get('zero_y', 0.0) or 0.0,
                    'zero_z': config.get('zero_z', 0.0) or 0.0,
                    'deadband': config.get('deadband', 0.0) or 0.0
                }

                # If deadband has changed, update it
                if new_calib['deadband'] != self.calibration['deadband']:
                    self.calibration = new_calib
                    self.cal_status.setText("cal")
                    self.cal_status.setStyleSheet(f"font-size:8pt; color:{CAL_COL}; margin:0; padding:0;")
        except Exception:
            pass  # Silent fail for calibration updates

    def _load_calibration(self, sensor_id: int) -> None:
        """Load calibration values from database for accelerometer"""
        if not self.db:
            return

        try:
            config = self.db.get_accel_config(sensor_id)

            if config:
                self.calibration = {
                    'zero_x': config.get('zero_x', 0.0) or 0.0,
                    'zero_y': config.get('zero_y', 0.0) or 0.0,
                    'zero_z': config.get('zero_z', 0.0) or 0.0,
                    'deadband': config.get('deadband', 0.0) or 0.0
                }
                self.cal_status.setText("cal")
                self.cal_status.setStyleSheet(f"font-size:8pt; color:{CAL_COL}; margin:0; padding:0;")
            else:
                self.cal_status.setText("cal")
                self.cal_status.setStyleSheet("font-size:8pt; color:red; margin:0; padding:0;")
        except Exception:
            self.cal_status.setText("cal")
            self.cal_status.setStyleSheet("font-size:8pt; color:red; margin:0; padding:0;")

    def _load_thresholds(self):
        """Load alarm thresholds from the database"""
        if not self.db:
            return

        # We'll load thresholds on first data receipt when we have sensor IDs
        pass

    def _check_alarm_thresholds(self, sensor_id: int, sensor_type: str):
        """Load alarm thresholds for a specific sensor"""
        if not self.db:
            return

        try:
            # Query threshold data
            self.db.cur.execute(
                "SELECT parameter, min_value, max_value FROM alarm_thresholds WHERE sensor_id = %s",
                (sensor_id,)
            )

            result = self.db.cur.fetchone()
            if result:
                parameter, min_value, max_value = result

                # Store thresholds based on parameter type
                if parameter == 'temperature':
                    self.thresholds["temp_min"] = min_value
                    self.thresholds["temp_max"] = max_value
                elif parameter == 'vibration':
                    self.thresholds["accel_max"] = max_value
        except Exception:
            pass  # Silently continue if there's an error

    def _hide_vibration_alarm(self):
        """Hide the vibration alarm after timer expires"""
        # Make sure this actually hides the label
        self.alarm_labels['Acceleration'].setVisible(False)
        self.accel_alarm_active = False

    def _apply_calibration(self, values: Dict[str, float]) -> Dict[str, float]:
        """Apply zero offset and deadband to acceleration values"""
        if not values:
            return {}

        result = {}
        for axis in ('x', 'y', 'z'):
            if axis in values:
                # Apply zero offset
                calibrated = values[axis] - self.calibration[f'zero_{axis}']

                # Apply deadband (if value is within deadband range of zero, set to zero)
                if abs(calibrated) <= self.calibration['deadband']:
                    calibrated = 0.0

                result[axis] = calibrated

        return result

    def _check_alarms(self):
        """Check for alarm conditions and update display"""
        # Check temperature alarms
        if self.latest_temp is not None and self.thresholds["temp_max"] is not None:
            # Check for high alarm
            if self.thresholds["temp_max"] is not None and self.latest_temp > self.thresholds["temp_max"]:
                self.alarm_labels['Temperature'].setText(f"ALARM: HIGH TEMPERATURE")
                self.alarm_labels['Temperature'].setVisible(True)
                self.temp_alarm_active = True
            # Check for low alarm
            elif self.thresholds["temp_min"] is not None and self.latest_temp < self.thresholds["temp_min"]:
                self.alarm_labels['Temperature'].setText(f"ALARM: LOW TEMPERATURE")
                self.alarm_labels['Temperature'].setVisible(True)
                self.temp_alarm_active = True
            # Temperature normal - hide alarm
            else:
                self.alarm_labels['Temperature'].setVisible(False)
                self.temp_alarm_active = False

        # Check vibration alarms
        if (self.latest_accel["x"] is not None and
                self.latest_accel["y"] is not None and
                self.latest_accel["z"] is not None and
                self.thresholds["accel_max"] is not None):

            # Calculate magnitude
            magnitude = (self.latest_accel["x"] ** 2 +
                         self.latest_accel["y"] ** 2 +
                         self.latest_accel["z"] ** 2) ** 0.5

            # Check for high vibration
            if magnitude > self.thresholds["accel_max"]:
                self.alarm_labels['Acceleration'].setText(f"ALARM: HIGH VIBRATION")
                self.alarm_labels['Acceleration'].setVisible(True)
                self.accel_alarm_active = True

                # Start/restart the timer to auto-hide after 5 seconds
                self.vib_alarm_timer.stop()  # Stop any existing timer
                self.vib_alarm_timer.start(ALARM_DISPLAY_SECONDS * 1000)

    def _update(self, pkt: dict):
        """Update displays with new data"""
        t = round(time.time() - self.start, 2)

        # Get temperature data and sensor ID
        temp_data = pkt.get('temperature', {})
        temp = temp_data.get('temperature')

        # Store latest temperature for alarm checking
        if temp is not None:
            self.latest_temp = temp

            # Check if this is a new temperature sensor
            if 'sensor_id' in temp_data and self.temp_sensor_id != temp_data['sensor_id']:
                self.temp_sensor_id = temp_data['sensor_id']
                self._check_alarm_thresholds(self.temp_sensor_id, 'temperature')

        # Get acceleration data and sensor ID
        accel_data = pkt.get('acceleration', {})
        if accel_data and 'sensor_id' in accel_data:
            # Check if this is a new sensor ID or first reading
            if self.accel_sensor_id != accel_data['sensor_id']:
                self.accel_sensor_id = accel_data['sensor_id']
                self._load_calibration(self.accel_sensor_id)
                self._check_alarm_thresholds(self.accel_sensor_id, 'acceleration')

        # Extract raw acceleration values
        raw_values = {}
        for axis in ('x', 'y', 'z'):
            if axis in accel_data:
                raw_values[axis] = accel_data[axis]

        # Apply calibration if we have values
        calibrated_values = self._apply_calibration(raw_values) if raw_values else {}

        # Store latest acceleration for alarm checking
        for axis in ('x', 'y', 'z'):
            if axis in calibrated_values:
                self.latest_accel[axis] = calibrated_values[axis]

        # Update temperature display
        if temp is not None:
            self.tiles['Temperature'].setText(f"{temp:.1f}°C")

        # Update acceleration display with calibrated values
        for axis in ('x', 'y', 'z'):
            if axis in calibrated_values:
                self.tiles[axis].setText(f"{calibrated_values[axis]:.2f}")

        # Check and update alarm status
        self._check_alarms()

        # Throttle plot updates for performance
        if time.time() - self.last_js < 0.15:
            return
        self.last_js = time.time()

        # Extend and slide temp
        if temp is not None:
            js = (
                f"Plotly.extendTraces('temp',{{x:[[{t}]],y:[[{temp}]]}},[0],{self.MAX_POINTS});"
                f"Plotly.relayout('temp',{{xaxis:{{range:[Math.max({t}-{WINDOW_SECONDS},0),{t}]}}}});"
            )
            self.temp_view.page().runJavaScript(js)

        # Update individual acceleration plots
        if 'x' in calibrated_values:
            js_x = (
                f"Plotly.extendTraces('accx',{{x:[[{t}]],y:[[{calibrated_values['x']}]]}},[0],{self.MAX_POINTS});"
                f"Plotly.relayout('accx',{{xaxis:{{range:[Math.max({t}-{WINDOW_SECONDS},0),{t}]}}}});"
            )
            self.acc_x_view.page().runJavaScript(js_x)

        if 'y' in calibrated_values:
            js_y = (
                f"Plotly.extendTraces('accy',{{x:[[{t}]],y:[[{calibrated_values['y']}]]}},[0],{self.MAX_POINTS});"
                f"Plotly.relayout('accy',{{xaxis:{{range:[Math.max({t}-{WINDOW_SECONDS},0),{t}]}}}});"
            )
            self.acc_y_view.page().runJavaScript(js_y)

        if 'z' in calibrated_values:
            js_z = (
                f"Plotly.extendTraces('accz',{{x:[[{t}]],y:[[{calibrated_values['z']}]]}},[0],{self.MAX_POINTS});"
                f"Plotly.relayout('accz',{{xaxis:{{range:[Math.max({t}-{WINDOW_SECONDS},0),{t}]}}}});"
            )
            self.acc_z_view.page().runJavaScript(js_z)

        # Optional DB logging - store the ORIGINAL (uncalibrated) values
        if self.db:
            try:
                if temp is not None and 'sensor_id' in temp_data:
                    self.db.insert_temperature(temp_data['sensor_id'], temp)
                if all(axis in raw_values for axis in ('x', 'y', 'z')) and 'sensor_id' in accel_data:
                    self.db.insert_accel(accel_data['sensor_id'],
                                         raw_values['x'], raw_values['y'], raw_values['z'])
            except Exception:
                pass  # Silent error handling for DB operations