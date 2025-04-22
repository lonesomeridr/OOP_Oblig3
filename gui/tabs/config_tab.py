from __future__ import annotations

"""
ConfigTab – Sensor Management and Configuration

• View, edit, and delete sensors
• Configure sensor alarm thresholds
• Accelerometer calibration
• Alarm history display
"""

import datetime
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit,
    QPushButton, QLabel, QDoubleSpinBox, QGroupBox, QHBoxLayout,
    QMessageBox, QTabWidget, QComboBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QFrame, QHeaderView, QDialog
)
from PyQt6.QtCore import QDate, Qt, QTimer
from PyQt6.QtGui import QColor
from utils.logger import log

# UI Colors
DARK_BG = "#121212"
CARD_BG = "#1e1e1e"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
WARN_COLOR = "#FFC107"
ALARM_COLOR = "#FF5722"

# Sensor types
SENSOR_TYPES = {
    "TMP102": {
        "name": "Temperature Sensor (TMP102)",
        "parameter": "temperature",
        "units": "°C"
    },
    "ADXL345": {
        "name": "Accelerometer (ADXL345)",
        "parameter": "vibration",
        "units": "m/s²"
    }
}


class SensorEditDialog(QDialog):
    """Dialog for editing sensor details and alarm thresholds"""

    def __init__(self, parent=None, sensor_data=None, alarm_thresholds=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Sensor")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"background: {DARK_BG}; color: #e0e0e0;")

        layout = QVBoxLayout(self)

        # Sensor details section
        details_group = QGroupBox("Sensor Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        form = QFormLayout(details_group)

        # Type field
        self.type_edit = QLineEdit(sensor_data.get('type', ''))
        self.type_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        form.addRow("Type:", self.type_edit)

        # Location field
        self.location_edit = QLineEdit(sensor_data.get('location', ''))
        self.location_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        form.addRow("Location:", self.location_edit)

        # Installation date
        self.date_edit = QDateEdit(calendarPopup=True)
        date = sensor_data.get('installed', datetime.date.today())
        if isinstance(date, datetime.date):
            self.date_edit.setDate(QDate(date.year, date.month, date.day))
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        form.addRow("Installed on:", self.date_edit)

        layout.addWidget(details_group)

        # Alarm thresholds section
        self.alarm_group = QGroupBox("Alarm Thresholds")
        self.alarm_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        alarm_form = QFormLayout(self.alarm_group)

        # Determine sensor type and add appropriate fields
        sensor_type = sensor_data.get('type', '').upper()
        self.alarm_params = {}

        if 'TMP' in sensor_type or 'TEMP' in sensor_type:
            # Temperature sensor
            self.parameter_type = 'temperature'

            # Low alarm
            self.min_value = QDoubleSpinBox()
            self.min_value.setRange(-50, 150)
            self.min_value.setValue(alarm_thresholds.get('min_value', 10.0) if alarm_thresholds else 10.0)
            self.min_value.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            alarm_form.addRow("Low Temperature Alarm (°C):", self.min_value)
            self.alarm_params['min_value'] = self.min_value

            # High alarm
            self.max_value = QDoubleSpinBox()
            self.max_value.setRange(-50, 150)
            self.max_value.setValue(alarm_thresholds.get('max_value', 40.0) if alarm_thresholds else 40.0)
            self.max_value.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            alarm_form.addRow("High Temperature Alarm (°C):", self.max_value)
            self.alarm_params['max_value'] = self.max_value

        elif 'ADXL' in sensor_type or 'ACCEL' in sensor_type:
            # Accelerometer
            self.parameter_type = 'vibration'

            # Vibration threshold
            self.max_value = QDoubleSpinBox()
            self.max_value.setRange(0, 20)
            self.max_value.setValue(alarm_thresholds.get('max_value', 5.0) if alarm_thresholds else 5.0)
            self.max_value.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            alarm_form.addRow("Vibration Threshold (m/s²):", self.max_value)
            self.alarm_params['max_value'] = self.max_value
            self.alarm_params['min_value'] = None  # Not used for accelerometer
        else:
            # Unknown sensor type
            alarm_form.addRow("Unknown sensor type, alarm thresholds not available", QLabel())
            self.parameter_type = None

        layout.addWidget(self.alarm_group)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3176b0;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #3d8dd6;
            }
        """)
        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_data(self):
        """Return the edited sensor data"""
        return {
            'type': self.type_edit.text(),
            'location': self.location_edit.text(),
            'installed': self.date_edit.date().toPyDate()
        }

    def get_alarm_data(self):
        """Return the edited alarm thresholds"""
        if not hasattr(self, 'parameter_type') or not self.parameter_type:
            return None

        data = {
            'parameter': self.parameter_type
        }

        if 'min_value' in self.alarm_params and self.alarm_params['min_value'] is not None:
            data['min_value'] = self.alarm_params['min_value'].value()
        else:
            data['min_value'] = None

        if 'max_value' in self.alarm_params:
            data['max_value'] = self.alarm_params['max_value'].value()

        return data


class ConfigTab(QWidget):
    def __init__(self, serial_reader, serial_conn, db):
        super().__init__()
        self.serial_reader = serial_reader
        self.serial_conn = serial_conn
        self.db = db
        self.setStyleSheet(f"background: {DARK_BG}; color: #e0e0e0;")

        # will be set to the accelerometer sensor_id if found
        self.accel_sensor_id = None
        self.zero_offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.deadband = 0.1
        self.sensors_data = []

        # Track alarm state to avoid duplicates
        self.temp_alarm_active = False
        self.accel_alarm_active = False
        self.last_alarm_time = None

        # Store column widths
        self.column_widths = [50, 100, 150, 100, 200, 150]  # Default widths

        # Main layout
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        # Create tabbed interface
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2d2d2d;
                background: #1e1e1e;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: #b0b0b0;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3d3d3d;
                color: #ffffff;
            }
        """)

        # Create tabs
        self._create_sensor_overview_tab()
        self._create_add_sensor_tab()
        self._create_alarm_config_tab()
        self._create_calibration_tab()

        root.addWidget(self.tabs)

        # Activity log
        self._create_log_section(root)

        # Initialize
        self._init_load()
        self._log_message("ConfigTab initialized", "INFO")

        # Start alarm check timer
        self.alarm_timer = QTimer()
        self.alarm_timer.timeout.connect(self._check_for_alarms)
        self.alarm_timer.start(10000)  # Check every 10 seconds

    def _create_sensor_overview_tab(self):
        """Create the sensor overview tab with sensor list"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Table showing existing sensors
        self.sensor_table = QTableWidget()
        self.sensor_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 6px;
                border: none;
            }
        """)
        self.sensor_table.setColumnCount(6)
        self.sensor_table.setHorizontalHeaderLabels(["ID", "Type", "Location", "Installed", "Alarm Limits", "Actions"])
        self.sensor_table.setAlternatingRowColors(True)

        # Set initial column widths
        for i, width in enumerate(self.column_widths):
            self.sensor_table.setColumnWidth(i, width)

        # Make the alarm limits column stretch
        self.sensor_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.sensor_table)

        # Refresh button
        refresh_btn = QPushButton("Refresh Sensors")
        refresh_btn.setStyleSheet(self._get_button_style())
        refresh_btn.clicked.connect(self._refresh_sensors)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.tabs.addTab(tab, "Sensor Overview")

    def _create_add_sensor_tab(self):
        """Create the add sensor tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Sensor type selection with wider layout
        type_layout = QHBoxLayout()
        label = QLabel("Sensor Type:")
        label.setFixedWidth(100)  # Fixed width for label
        type_layout.addWidget(label)

        self.sensor_type_combo = QComboBox()
        self.sensor_type_combo.setMinimumWidth(250)  # Make the combo box wider
        for sensor_type, info in SENSOR_TYPES.items():
            self.sensor_type_combo.addItem(info["name"], sensor_type)
        type_layout.addWidget(self.sensor_type_combo)
        type_layout.addStretch()  # Add stretch to align left
        layout.addLayout(type_layout)

        # Registration form
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        self.location_edit = QLineEdit()
        self.location_edit.setMinimumWidth(250)
        self.install_date = QDateEdit(calendarPopup=True)
        self.install_date.setDate(QDate.currentDate())
        form_layout.addRow("Location:", self.location_edit)
        form_layout.addRow("Installed on:", self.install_date)
        layout.addLayout(form_layout)

        # Add button
        self.add_btn = QPushButton("Add Sensor")
        self.add_btn.setStyleSheet(self._get_button_style())
        self.add_btn.clicked.connect(self._add_sensor)
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addWidget(self.add_btn)
        add_btn_layout.addStretch()
        layout.addLayout(add_btn_layout)
        layout.addStretch(1)

        self.tabs.addTab(tab, "Register New Sensor")

    def _create_alarm_config_tab(self):
        """Create the alarm configuration tab with alarm log"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Top section - Alarm configuration
        config_layout = QVBoxLayout()

        # Sensor selection with wider layout
        alarm_select_layout = QHBoxLayout()
        label = QLabel("Select Sensor:")
        label.setFixedWidth(100)  # Fixed width for label
        alarm_select_layout.addWidget(label)

        self.alarm_sensor_combo = QComboBox()
        self.alarm_sensor_combo.setMinimumWidth(250)  # Make the combo box wider
        self.alarm_sensor_combo.currentIndexChanged.connect(self._update_alarm_params)
        alarm_select_layout.addWidget(self.alarm_sensor_combo)
        alarm_select_layout.addStretch()  # Add stretch to align left
        config_layout.addLayout(alarm_select_layout)

        # Alarm parameters frame
        self.alarm_params_frame = QFrame()
        self.alarm_params_frame.setStyleSheet(f"background: {CARD_BG}; border-radius: 4px; padding: 10px;")
        self.alarm_params_layout = QFormLayout(self.alarm_params_frame)
        config_layout.addWidget(self.alarm_params_frame)

        # Save button
        save_alarms_btn = QPushButton("Save Alarm Settings")
        save_alarms_btn.setStyleSheet(self._get_button_style())
        save_alarms_btn.clicked.connect(self._save_alarm_settings)
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_alarms_btn)
        button_layout.addStretch()
        config_layout.addLayout(button_layout)
        layout.addLayout(config_layout)

        # Alarm history section
        alarm_group = QGroupBox("Alarm History")
        alarm_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 20px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        alarm_layout = QVBoxLayout(alarm_group)

        self.alarm_table = QTableWidget()
        self.alarm_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 6px;
                border: none;
            }
        """)
        self.alarm_table.setColumnCount(5)
        self.alarm_table.setHorizontalHeaderLabels(["Sensor", "Value", "Threshold", "Time", "Parameter"])
        self.alarm_table.setAlternatingRowColors(True)
        self.alarm_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        alarm_layout.addWidget(self.alarm_table)

        # Buttons for alarm management
        alarm_btn_layout = QHBoxLayout()
        clear_alarms_btn = QPushButton("Clear All Alarms")
        clear_alarms_btn.setStyleSheet(self._get_button_style(ALARM_COLOR))
        clear_alarms_btn.clicked.connect(self._clear_alarms)
        alarm_btn_layout.addWidget(clear_alarms_btn)

        refresh_alarms_btn = QPushButton("Refresh Alarms")
        refresh_alarms_btn.setStyleSheet(self._get_button_style())
        refresh_alarms_btn.clicked.connect(self._refresh_alarms)
        alarm_btn_layout.addWidget(refresh_alarms_btn)

        alarm_layout.addLayout(alarm_btn_layout)
        layout.addWidget(alarm_group)

        self.tabs.addTab(tab, "Alarm Configuration")

    def _create_calibration_tab(self):
        """Create accelerometer calibration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        calib_group = QGroupBox("Accelerometer Calibration")
        calib_group.setStyleSheet(f"""
            QGroupBox {{
                background: {CARD_BG};
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
                color: #e0e0e0;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        calib_layout = QVBoxLayout()

        # zero offset
        zero_btn = QPushButton("Calibrate Zero")
        zero_btn.setStyleSheet(self._get_button_style())
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
        self.dead_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-radius: 4px;
                padding: 2px 4px;
            }
        """)
        dead_layout.addWidget(self.dead_spin)
        dead_btn = QPushButton("Set Deadband")
        dead_btn.setStyleSheet(self._get_button_style())
        dead_btn.clicked.connect(self._set_deadband)
        dead_layout.addWidget(dead_btn)
        calib_layout.addLayout(dead_layout)

        calib_group.setLayout(calib_layout)
        layout.addWidget(calib_group)
        layout.addStretch(1)

        self.tabs.addTab(tab, "Calibration")

    def _create_log_section(self, parent_layout):
        """Create activity log section"""
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet(f"""
            QGroupBox {{
                background: {CARD_BG};
                border-radius: 6px;
                margin-top: 12px;
                font-weight: bold;
                color: #e0e0e0;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: none;
                font-family: Consolas, monospace;
                font-size: 12px;
            }}
        """)
        self.log_text.setMaximumHeight(120)
        log_layout.addWidget(self.log_text)

        # Clear log button
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.setStyleSheet(self._get_button_style())
        clear_log_btn.clicked.connect(self._clear_log)
        log_layout.addWidget(clear_log_btn)

        parent_layout.addWidget(log_group)

    def _get_button_style(self, bg_color="#3d3d3d"):
        """Return common button style"""
        hover_color = self._lighten_color(bg_color, 20)
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    def _lighten_color(self, color, amount=20):
        """Lighten a hex color by a percentage"""
        if color.startswith('#'):
            color = color[1:]

        # Convert to RGB
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        # Lighten
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _init_load(self):
        """Load initial data from database"""
        if not self.db:
            return

        try:
            # Load sensors
            self._refresh_sensors()

            # Find accelerometer sensor_id
            for sensor in self.sensors_data:
                if 'accel' in sensor['type'].lower() or 'ADXL345' in sensor['type']:
                    self.accel_sensor_id = sensor['id']
                    break

            # Load acceleration calibration if available
            if self.accel_sensor_id is not None and self.db:
                cfg = self.db.get_accel_config(self.accel_sensor_id)
                if cfg:
                    self.zero_offset = {
                        'x': cfg['zero_x'],
                        'y': cfg['zero_y'],
                        'z': cfg['zero_z']
                    }
                    self.deadband = cfg['deadband']
                    # Update UI
                    self.zero_label.setText(
                        f"Zero offset: x={cfg['zero_x']:.2f}, y={cfg['zero_y']:.2f}, z={cfg['zero_z']:.2f}"
                    )
                    self.dead_spin.setValue(self.deadband)

            # Load alarm history
            self._refresh_alarms()

        except Exception as e:
            self._log_message(f"Error loading configuration: {e}", "INFO")

    def _refresh_sensors(self):
        """Refresh the sensor list table and combo boxes"""
        if not self.db:
            return

        try:
            # Store column widths before refresh
            self._save_column_widths()

            # Get all sensors
            sensors = self.db.get_sensors()
            self.sensors_data = []

            # Clear existing UI elements
            self.sensor_table.setRowCount(0)
            self.alarm_sensor_combo.clear()

            # Populate data
            for sensor_id, stype, location, installed in sensors:
                # Add to internal data structure
                sensor_data = {
                    'id': sensor_id,
                    'type': stype,
                    'location': location,
                    'installed': installed
                }
                self.sensors_data.append(sensor_data)

                # Add to table
                row = self.sensor_table.rowCount()
                self.sensor_table.insertRow(row)
                self.sensor_table.setItem(row, 0, QTableWidgetItem(str(sensor_id)))
                self.sensor_table.setItem(row, 1, QTableWidgetItem(stype))
                self.sensor_table.setItem(row, 2, QTableWidgetItem(location))
                self.sensor_table.setItem(row, 3, QTableWidgetItem(installed.strftime("%Y-%m-%d")))

                # Add alarm limits cell
                thresholds = self._get_alarm_thresholds(sensor_id)
                limits_text = "Not set"
                if thresholds:
                    if thresholds['parameter'] == 'temperature':
                        min_val = thresholds.get('min_value', 'N/A')
                        max_val = thresholds.get('max_value', 'N/A')
                        limits_text = f"Temp: {min_val}°C - {max_val}°C"
                    elif thresholds['parameter'] == 'vibration':
                        max_val = thresholds.get('max_value', 'N/A')
                        limits_text = f"Vibration: {max_val} m/s²"

                limits_item = QTableWidgetItem(limits_text)
                self.sensor_table.setItem(row, 4, limits_item)

                # Add actions cell with buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(6)

                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("padding: 4px 8px; background: #3176b0; color: white; border-radius: 3px;")
                edit_btn.clicked.connect(lambda checked, s_id=sensor_id: self._edit_sensor(s_id))
                actions_layout.addWidget(edit_btn)

                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("padding: 4px 8px; background: #d32f2f; color: white; border-radius: 3px;")
                delete_btn.clicked.connect(lambda checked, s_id=sensor_id: self._delete_sensor(s_id))
                actions_layout.addWidget(delete_btn)

                self.sensor_table.setCellWidget(row, 5, actions_widget)

                # Add to combo box for alarm config
                display_text = f"{stype} - {location} (ID: {sensor_id})"
                self.alarm_sensor_combo.addItem(display_text, sensor_id)

            # Restore column widths
            self._restore_column_widths()

            self._log_message(f"Found {len(sensors)} sensors", "INFO")

        except Exception as e:
            self._log_message(f"Error refreshing sensors: {e}", "INFO")

    def _save_column_widths(self):
        """Save the current column widths"""
        for i in range(self.sensor_table.columnCount()):
            if i < len(self.column_widths):
                self.column_widths[i] = self.sensor_table.columnWidth(i)

    def _restore_column_widths(self):
        """Restore the saved column widths"""
        for i, width in enumerate(self.column_widths):
            if i < self.sensor_table.columnCount():
                self.sensor_table.setColumnWidth(i, width)

        # Always make the alarm limits column stretch
        self.sensor_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

    def _edit_sensor(self, sensor_id):
        """Edit a sensor's details"""
        # Find sensor data
        sensor_data = None
        for sensor in self.sensors_data:
            if sensor['id'] == sensor_id:
                sensor_data = sensor
                break

        if not sensor_data:
            return

        # Get current alarm thresholds
        alarm_thresholds = self._get_alarm_thresholds(sensor_id)

        # Show edit dialog
        dialog = SensorEditDialog(self, sensor_data, alarm_thresholds)
        if dialog.exec():
            # Get updated data
            updated_data = dialog.get_data()
            alarm_data = dialog.get_alarm_data()

            try:
                # Update sensor in database
                self.db.cur.execute(
                    "UPDATE sensors SET type = %s, location = %s, installation_date = %s WHERE sensor_id = %s",
                    (updated_data['type'], updated_data['location'], updated_data['installed'], sensor_id)
                )

                # Update alarm thresholds if available
                if alarm_data:
                    parameter = alarm_data['parameter']
                    min_value = alarm_data['min_value']
                    max_value = alarm_data['max_value']

                    # Check if alarm thresholds already exist
                    self.db.cur.execute(
                        "SELECT COUNT(*) FROM alarm_thresholds WHERE sensor_id = %s AND parameter = %s",
                        (sensor_id, parameter)
                    )

                    if self.db.cur.fetchone()[0] > 0:
                        # Update existing thresholds
                        self.db.cur.execute(
                            "UPDATE alarm_thresholds SET min_value = %s, max_value = %s WHERE sensor_id = %s AND parameter = %s",
                            (min_value, max_value, sensor_id, parameter)
                        )
                    else:
                        # Insert new thresholds
                        self.db.cur.execute(
                            "INSERT INTO alarm_thresholds (sensor_id, parameter, min_value, max_value) VALUES (%s, %s, %s, %s)",
                            (sensor_id, parameter, min_value, max_value)
                        )

                try:
                    # Try to commit, but don't worry if it fails
                    if hasattr(self.db, 'conn') and self.db.conn:
                        self.db.conn.commit()
                except:
                    pass

                self._log_message(f"Updated sensor ID {sensor_id}", "SUCCESS")
                self._refresh_sensors()

            except Exception as e:
                self._log_message(f"Error updating sensor: {e}", "INFO")

    def _delete_sensor(self, sensor_id):
        """Delete a sensor"""
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete sensor ID {sensor_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            # Delete from alarm_thresholds
            self.db.cur.execute("DELETE FROM alarm_thresholds WHERE sensor_id = %s", (sensor_id,))

            # Delete from acceleration_config if it exists
            self.db.cur.execute("DELETE FROM acceleration_config WHERE sensor_id = %s", (sensor_id,))

            # Finally delete the sensor
            self.db.cur.execute("DELETE FROM sensors WHERE sensor_id = %s", (sensor_id,))

            try:
                # Try to commit, but don't worry if it fails
                if hasattr(self.db, 'conn') and self.db.conn:
                    self.db.conn.commit()
            except:
                pass

            self._log_message(f"Deleted sensor ID {sensor_id}", "SUCCESS")
            self._refresh_sensors()

            # If this was the accelerometer, clear the ID
            if self.accel_sensor_id == sensor_id:
                self.accel_sensor_id = None

        except Exception as e:
            self._log_message(f"Error deleting sensor: {e}", "INFO")
            # Don't show error message as per request

    def _update_alarm_params(self):
        """Update alarm parameters form based on selected sensor"""
        # Clear existing form items
        while self.alarm_params_layout.count():
            item = self.alarm_params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get selected sensor ID
        if self.alarm_sensor_combo.count() == 0:
            return

        index = self.alarm_sensor_combo.currentIndex()
        if index < 0:
            return

        selected_id = self.alarm_sensor_combo.itemData(index)
        selected_sensor = None

        # Find the sensor data
        for sensor in self.sensors_data:
            if sensor['id'] == selected_id:
                selected_sensor = sensor
                break

        if not selected_sensor:
            return

        # Determine sensor type and create parameters
        sensor_type = self._get_sensor_type(selected_sensor['type'])
        thresholds = self._get_alarm_thresholds(selected_id)

        # Create form fields based on sensor type
        header = QLabel(f"<b>{selected_sensor['type']} Alarm Settings</b>")
        header.setStyleSheet("color: #ffffff; margin-top: 10px;")
        self.alarm_params_layout.addRow(header)

        self.alarm_params = {}  # Store spinboxes for retrieval later

        if sensor_type == "TMP102":
            # Temperature sensor settings
            low_spin = QDoubleSpinBox()
            low_spin.setRange(-50, 150)
            low_spin.setValue(
                thresholds.get('min_value', 10.0) if thresholds and thresholds.get('min_value') is not None else 10.0)
            low_spin.setStyleSheet("background-color: #2d2d2d; color: #e0e0e0; border-radius: 4px; padding: 4px;")
            self.alarm_params_layout.addRow("Low Temperature Alarm (°C):", low_spin)
            self.alarm_params['min_value'] = low_spin

            high_spin = QDoubleSpinBox()
            high_spin.setRange(-50, 150)
            high_spin.setValue(
                thresholds.get('max_value', 40.0) if thresholds and thresholds.get('max_value') is not None else 40.0)
            high_spin.setStyleSheet("background-color: #2d2d2d; color: #e0e0e0; border-radius: 4px; padding: 4px;")
            self.alarm_params_layout.addRow("High Temperature Alarm (°C):", high_spin)
            self.alarm_params['max_value'] = high_spin
            self.alarm_params_parameter = 'temperature'

        elif sensor_type == "ADXL345":
            # Accelerometer settings
            vib_spin = QDoubleSpinBox()
            vib_spin.setRange(0, 20)
            vib_spin.setValue(
                thresholds.get('max_value', 5.0) if thresholds and thresholds.get('max_value') is not None else 5.0)
            vib_spin.setStyleSheet("background-color: #2d2d2d; color: #e0e0e0; border-radius: 4px; padding: 4px;")
            self.alarm_params_layout.addRow("Vibration Threshold (m/s²):", vib_spin)
            self.alarm_params['max_value'] = vib_spin
            self.alarm_params_parameter = 'vibration'

        # Store the sensor ID for saving later
        self.current_alarm_sensor_id = selected_id

    def _get_sensor_type(self, type_string):
        """Determine sensor type from string"""
        if 'TMP' in type_string.upper() or 'TEMP' in type_string.upper():
            return "TMP102"
        elif 'ADXL' in type_string.upper() or 'ACCEL' in type_string.upper():
            return "ADXL345"
        return "TMP102"  # Default to temperature sensor

    def _get_alarm_thresholds(self, sensor_id):
        """Get alarm thresholds for a sensor from database"""
        if not self.db:
            return {}

        try:
            self.db.cur.execute(
                "SELECT parameter, min_value, max_value FROM alarm_thresholds WHERE sensor_id = %s",
                (sensor_id,)
            )

            result = self.db.cur.fetchone()
            if result:
                parameter, min_value, max_value = result
                return {
                    'parameter': parameter,
                    'min_value': min_value,
                    'max_value': max_value
                }
            return {}

        except Exception as e:
            self._log_message(f"Database error getting thresholds: {e}", "INFO")
            return {}

    def _save_alarm_settings(self):
        """Save the current alarm settings to the database"""
        if not self.db or not hasattr(self, 'current_alarm_sensor_id') or not self.alarm_params:
            return

        # Collect settings from form
        settings = {}
        for key, spinbox in self.alarm_params.items():
            settings[key] = spinbox.value()

        try:
            # Save to alarm_thresholds table
            parameter = getattr(self, 'alarm_params_parameter', 'temperature')
            min_value = settings.get('min_value')
            max_value = settings.get('max_value')

            # Check if record exists
            self.db.cur.execute(
                "SELECT COUNT(*) FROM alarm_thresholds WHERE sensor_id = %s AND parameter = %s",
                (self.current_alarm_sensor_id, parameter)
            )

            count = self.db.cur.fetchone()[0]

            if count > 0:
                # Update existing record
                self.db.cur.execute(
                    "UPDATE alarm_thresholds SET min_value = %s, max_value = %s WHERE sensor_id = %s AND parameter = %s",
                    (min_value, max_value, self.current_alarm_sensor_id, parameter)
                )
            else:
                # Insert new record
                self.db.cur.execute(
                    "INSERT INTO alarm_thresholds (sensor_id, parameter, min_value, max_value) VALUES (%s, %s, %s, %s)",
                    (self.current_alarm_sensor_id, parameter, min_value, max_value)
                )

            try:
                # Try to commit, but don't worry if it fails
                if hasattr(self.db, 'conn') and self.db.conn:
                    self.db.conn.commit()
            except:
                pass

            # Log success and refresh display
            self._log_message(f"Saved alarm thresholds for sensor {self.current_alarm_sensor_id}", "SUCCESS")
            self._refresh_sensors()

            QMessageBox.information(self, "Settings Saved", "Alarm settings have been saved.")

        except Exception as e:
            self._log_message(f"Error saving alarm settings: {e}", "INFO")

    def _add_sensor(self):
        """Called when user clicks Add Sensor."""
        if not self.db:
            QMessageBox.warning(self, "No DB", "Database connection not available.")
            return

        # Get the sensor data
        index = self.sensor_type_combo.currentIndex()
        sensor_type = self.sensor_type_combo.itemData(index)
        display_type = self.sensor_type_combo.currentText()
        loc = self.location_edit.text().strip()
        date = self.install_date.date().toPyDate()

        if not loc:
            QMessageBox.information(self, "Incomplete", "Location is required.")
            return

        try:
            # Add sensor to database
            new_id = self.db.add_sensor(sensor_type, loc, date)

            self._log_message(f"Added new sensor: {display_type} at {loc}", "SUCCESS")
            QMessageBox.information(self, "Success", f"Added new {display_type} sensor.")
            self.location_edit.clear()
            self._refresh_sensors()

            # If this is an accelerometer and we don't have one yet, set it
            if 'accel' in sensor_type.lower() and self.accel_sensor_id is None:
                self.accel_sensor_id = new_id

        except Exception as exc:
            self._log_message(f"Database error while adding sensor: {exc}", "INFO")
            QMessageBox.warning(self, "Error", "Could not add sensor.")

    def _calibrate_zero(self):
        """Capture the current accel sample as our zero offset and store it."""
        if not self.accel_sensor_id:
            QMessageBox.warning(self, "No Sensor", "No accelerometer sensor found in DB.")
            return

        pkt = getattr(self.serial_reader, 'last_packet', None)
        if not pkt or 'acceleration' not in pkt:
            QMessageBox.information(self, "No Data", "No acceleration packet yet — please start live data first.")
            return

        acc = pkt['acceleration']
        zx, zy, zz = acc['x'], acc['y'], acc['z']
        self.zero_offset = {'x': zx, 'y': zy, 'z': zz}

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

            self._log_message(f"Calibrated zero offset for sensor ID {self.accel_sensor_id}", "SUCCESS")
            QMessageBox.information(self, "Calibrated", "Zero offset stored.")
        except Exception as exc:
            self._log_message(f"Database error during calibration: {exc}", "INFO")

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

            self._log_message(f"Set deadband to ±{db_val:.2f} m/s²", "SUCCESS")
            QMessageBox.information(self, "Deadband Set", f"Deadband ±{db_val:.2f} m/s² saved.")
        except Exception as exc:
            self._log_message(f"Database error while setting deadband: {exc}", "INFO")

    def _check_for_alarms(self):
        """Check for alarm conditions in the latest readings"""
        if not self.db:
            return

        try:
            # Get the latest temperature reading
            self.db.cur.execute("""
                SELECT t.id, t.sensor_id, t.temperature, t.created_at, s.type, s.location
                FROM temperature_readings t
                JOIN sensors s ON t.sensor_id = s.sensor_id
                ORDER BY t.created_at DESC
                LIMIT 1
            """)

            temp_reading = self.db.cur.fetchone()
            if temp_reading:
                reading_id, sensor_id, temp_value, timestamp, sensor_type, location = temp_reading

                # Check against thresholds
                thresholds = self._get_alarm_thresholds(sensor_id)
                if thresholds and thresholds.get('parameter') == 'temperature':
                    min_value = thresholds.get('min_value')
                    max_value = thresholds.get('max_value')

                    # Check for alarm condition
                    is_high_alarm = max_value is not None and temp_value > max_value
                    is_low_alarm = min_value is not None and temp_value < min_value

                    if (is_high_alarm or is_low_alarm) and not self.temp_alarm_active:
                        # Create an alarm entry and prevent duplicates
                        parameter = 'low_temp' if is_low_alarm else 'high_temp'
                        self._create_alarm('temperature', reading_id, timestamp, parameter)

                        # Set alarm state
                        self.temp_alarm_active = True
                        self.last_alarm_time = datetime.datetime.now()

                        # Show alarm notification
                        threshold = min_value if is_low_alarm else max_value
                        self._log_message(
                            f"Temperature {temp_value}°C is {'below' if is_low_alarm else 'above'} threshold ({threshold}°C)",
                            "ALARM"
                        )
                    elif not is_high_alarm and not is_low_alarm:
                        # Reset alarm state when temperature returns to normal
                        self.temp_alarm_active = False

            # Try to get acceleration readings (handle different column names)
            try:
                # Check column names
                self.db.cur.execute("SHOW COLUMNS FROM acceleration_readings")
                columns = [col[0] for col in self.db.cur.fetchall()]

                # Determine column names for acceleration
                x_col = 'acceleration_x' if 'acceleration_x' in columns else 'x'
                y_col = 'acceleration_y' if 'acceleration_y' in columns else 'y'
                z_col = 'acceleration_z' if 'acceleration_z' in columns else 'z'

                # Get latest reading
                self.db.cur.execute(f"""
                    SELECT a.id, a.sensor_id, a.{x_col}, a.{y_col}, a.{z_col}, 
                           a.created_at, s.type, s.location
                    FROM acceleration_readings a
                    JOIN sensors s ON a.sensor_id = s.sensor_id
                    ORDER BY a.created_at DESC
                    LIMIT 1
                """)

                acc_reading = self.db.cur.fetchone()
                if acc_reading:
                    reading_id, sensor_id, acc_x, acc_y, acc_z, timestamp, sensor_type, location = acc_reading

                    # Calculate magnitude
                    magnitude = (acc_x ** 2 + acc_y ** 2 + acc_z ** 2) ** 0.5

                    # Check against thresholds
                    thresholds = self._get_alarm_thresholds(sensor_id)
                    if thresholds and thresholds.get('parameter') == 'vibration':
                        max_value = thresholds.get('max_value')

                        # Check for alarm condition
                        if max_value is not None and magnitude > max_value and not self.accel_alarm_active:
                            # Create an alarm entry
                            self._create_alarm('acceleration', reading_id, timestamp, 'high_vibration')

                            # Set alarm state
                            self.accel_alarm_active = True
                            self.last_alarm_time = datetime.datetime.now()

                            # Show alarm notification
                            self._log_message(
                                f"Vibration {magnitude:.2f} m/s² exceeds threshold ({max_value} m/s²)",
                                "ALARM"
                            )
                        elif max_value is not None and magnitude <= max_value:
                            # Reset alarm state when vibration returns to normal
                            self.accel_alarm_active = False

            except Exception:
                # Silently ignore acceleration reading errors
                pass

            # Refresh the alarm display
            self._refresh_alarms()

        except Exception:
            # Silently ignore errors in alarm checking
            pass

    def _create_alarm(self, alarm_type, reading_id, timestamp, parameter):
        """Create an alarm entry in the database"""
        try:
            if alarm_type == 'temperature':
                # Check if this reading already has an alarm
                self.db.cur.execute(
                    "SELECT COUNT(*) FROM temperature_alarms WHERE reading_id = %s",
                    (reading_id,)
                )
                if self.db.cur.fetchone()[0] == 0:
                    # Only insert if no alarm exists for this reading
                    self.db.cur.execute(
                        "INSERT INTO temperature_alarms (reading_id, timestamp, parameter) VALUES (%s, %s, %s)",
                        (reading_id, timestamp, parameter)
                    )
            else:  # acceleration
                # Check if this reading already has an alarm
                self.db.cur.execute(
                    "SELECT COUNT(*) FROM acceleration_alarms WHERE reading_id = %s",
                    (reading_id,)
                )
                if self.db.cur.fetchone()[0] == 0:
                    # Only insert if no alarm exists for this reading
                    self.db.cur.execute(
                        "INSERT INTO acceleration_alarms (reading_id, timestamp, parameter) VALUES (%s, %s, %s)",
                        (reading_id, timestamp, parameter)
                    )

            # Try to commit but don't worry if it fails
            try:
                if hasattr(self.db, 'conn') and self.db.conn:
                    self.db.conn.commit()
            except:
                pass

        except Exception:
            # Silently ignore errors in alarm creation
            pass

    def _refresh_alarms(self):
        """Refresh the alarm table with alarm history"""
        if not self.db:
            return

        try:
            self.alarm_table.setRowCount(0)

            # Get temperature alarms
            try:
                self.db.cur.execute("""
                    SELECT s.type, s.location, ta.parameter, ta.timestamp, tr.temperature,
                           at.min_value, at.max_value
                    FROM temperature_alarms ta
                    JOIN temperature_readings tr ON ta.reading_id = tr.id
                    JOIN sensors s ON tr.sensor_id = s.sensor_id
                    LEFT JOIN alarm_thresholds at ON s.sensor_id = at.sensor_id AND at.parameter = 'temperature'
                    ORDER BY ta.timestamp DESC
                    LIMIT 50
                """)

                for stype, location, parameter, timestamp, temperature, min_val, max_val in self.db.cur.fetchall():
                    threshold = min_val if parameter == 'low_temp' else max_val
                    self._add_alarm_row(
                        f"{stype} at {location}",
                        f"{temperature:.1f}°C",
                        f"{threshold}°C",
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Low Temperature" if parameter == 'low_temp' else "High Temperature"
                    )
            except Exception:
                # Silently ignore temperature alarm errors
                pass

            # Get acceleration alarms - check column names
            try:
                # Determine column names
                self.db.cur.execute("SHOW COLUMNS FROM acceleration_readings")
                columns = [col[0] for col in self.db.cur.fetchall()]

                x_col = 'acceleration_x' if 'acceleration_x' in columns else 'x'
                y_col = 'acceleration_y' if 'acceleration_y' in columns else 'y'
                z_col = 'acceleration_z' if 'acceleration_z' in columns else 'z'

                self.db.cur.execute(f"""
                    SELECT s.type, s.location, aa.parameter, aa.timestamp,
                           SQRT(POWER(ar.{x_col}, 2) + POWER(ar.{y_col}, 2) + POWER(ar.{z_col}, 2)) as magnitude,
                           at.max_value
                    FROM acceleration_alarms aa
                    JOIN acceleration_readings ar ON aa.reading_id = ar.id
                    JOIN sensors s ON ar.sensor_id = s.sensor_id
                    LEFT JOIN alarm_thresholds at ON s.sensor_id = at.sensor_id AND at.parameter = 'vibration'
                    ORDER BY aa.timestamp DESC
                    LIMIT 50
                """)

                for stype, location, parameter, timestamp, magnitude, max_val in self.db.cur.fetchall():
                    self._add_alarm_row(
                        f"{stype} at {location}",
                        f"{magnitude:.2f} m/s²",
                        f"{max_val} m/s²",
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "High Vibration"
                    )
            except Exception:
                # Silently ignore acceleration alarm errors
                pass

        except Exception:
            # Silently ignore errors in alarm refresh
            pass

    def _add_alarm_row(self, sensor, value, threshold, time, parameter):
        """Add a row to the alarm table"""
        row = self.alarm_table.rowCount()
        self.alarm_table.insertRow(row)

        sensor_item = QTableWidgetItem(sensor)
        sensor_item.setForeground(QColor(ALARM_COLOR))
        self.alarm_table.setItem(row, 0, sensor_item)

        self.alarm_table.setItem(row, 1, QTableWidgetItem(value))
        self.alarm_table.setItem(row, 2, QTableWidgetItem(str(threshold)))
        self.alarm_table.setItem(row, 3, QTableWidgetItem(time))
        self.alarm_table.setItem(row, 4, QTableWidgetItem(parameter))

    def _clear_alarms(self):
        """Clear all alarm entries from the database"""
        if not self.db:
            return

        confirm = QMessageBox.question(
            self, "Confirm Clear Alarms",
            "Are you sure you want to clear all alarm history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            # Clear alarm tables
            self.db.cur.execute("DELETE FROM temperature_alarms")
            self.db.cur.execute("DELETE FROM acceleration_alarms")

            # Try to commit but don't worry if it fails
            try:
                if hasattr(self.db, 'conn') and self.db.conn:
                    self.db.conn.commit()
            except:
                pass

            # Clear the alarm table UI and reset alarm state
            self.alarm_table.setRowCount(0)
            self.temp_alarm_active = False
            self.accel_alarm_active = False

            self._log_message("Cleared all alarm history", "SUCCESS")

        except Exception:
            # Silently ignore errors
            pass

    def _log_message(self, message, level="INFO"):
        """Add a message to the activity log with timestamp"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Color coding based on level
        color = "#e0e0e0"  # Default light gray
        if level == "ERROR":
            color = ERROR_COLOR
        elif level == "WARNING":
            color = WARN_COLOR
        elif level == "SUCCESS":
            color = SUCCESS_COLOR
        elif level == "ALARM":
            color = ALARM_COLOR

        html_message = f'<span style="color:{color}"><b>[{timestamp}] [{level}]</b> {message}</span>'

        # Insert at the beginning (newest messages on top)
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.log_text.setTextCursor(cursor)
        self.log_text.insertHtml(html_message + "<br>")

        # Also log to system log if it's an ERROR or SUCCESS
        if level in ["ERROR", "SUCCESS"] and level != "INFO":
            log(f"ConfigTab: {message}")

    def _clear_log(self):
        """Clear the activity log"""
        self.log_text.clear()
        self._log_message("Log cleared")