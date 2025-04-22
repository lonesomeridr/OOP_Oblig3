from __future__ import annotations

"""
SettingsTab – Application Configuration Interface

• Live data controls (Start/Stop)
• Gather Frequency setting
• COM-port selection with auto-connect
• Modern UI matching Configuration tab styling
• Status feedback for user actions
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QComboBox, QPushButton, QSpinBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from utils.logger import log

DEFAULT_PORT = "COM7"
CARD_BG = "#1e1e1e"  # Match color from other tabs
BUTTON_COLOR = "#9e9e9e"  # Light grey for buttons
STATUS_GREEN = "#4CAF50"  # Green for success status
STATUS_RED = "#F44336"  # Red for stopped status


class SettingsTab(QWidget):
    """Settings panel for controlling real-time data collection and serial connection."""

    def __init__(self, serial_conn):
        super().__init__()
        self.conn = serial_conn

        # Root layout: vertical structure with consistent spacing
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("Application Settings")
        title.setFont(QFont(title.font().family(), 14, QFont.Weight.DemiBold))
        main_layout.addWidget(title)

        # Settings cards container
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)

        # 1) Live-data controls card
        live_card, live_layout = self._create_card("Live Data Controls")
        live_layout.setSpacing(10)

        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedSize(80, 30)
        self.start_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: black; border-radius: 4px;")

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(80, 30)
        self.stop_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: black; border-radius: 4px;")

        # Add status label for live data
        self.live_status = QLabel("Stopped")
        self.live_status.setStyleSheet(f"color: {STATUS_RED}; font-weight: bold;")

        live_layout.addWidget(self.start_btn)
        live_layout.addWidget(self.stop_btn)
        live_layout.addSpacing(20)
        live_layout.addWidget(self.live_status)
        live_layout.addStretch(1)
        settings_layout.addWidget(live_card)

        # 2) Data Collection Settings card
        data_card, data_layout = self._create_card("Data Collection Settings")
        data_layout.setSpacing(10)

        # Gather frequency row
        freq_row = QHBoxLayout()
        lbl_freq = QLabel("Gather Frequency:")
        lbl_freq.setMinimumWidth(120)

        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 10)
        self.freq_spin.setValue(5)
        self.freq_spin.setFixedSize(60, 30)
        # Make the spinner arrows visible with lighter colors
        self.freq_spin.setStyleSheet("""
            QSpinBox {
                background-color: #424242;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding-right: 15px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #666666;
                border: none;
                width: 16px;
                border-radius: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #888888;
            }
            QSpinBox::up-arrow {
                image: url(none);
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid white;
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow {
                image: url(none);
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid white;
                width: 0px;
                height: 0px;
            }
        """)

        self.set_btn = QPushButton("Set")
        self.set_btn.setFixedSize(60, 30)
        self.set_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: black; border-radius: 4px;")

        # Add status label for frequency updates
        self.freq_status = QLabel("")

        freq_row.addWidget(lbl_freq)
        freq_row.addWidget(self.freq_spin)
        freq_row.addWidget(self.set_btn)
        freq_row.addSpacing(10)
        freq_row.addWidget(self.freq_status)
        freq_row.addStretch(1)
        data_layout.addLayout(freq_row)

        # COM-port selector row
        com_row = QHBoxLayout()
        lbl_com = QLabel("COM-port:")
        lbl_com.setMinimumWidth(120)

        self.port_combo = QComboBox()
        self.port_combo.setFixedHeight(30)
        self.port_combo.setMinimumWidth(120)
        self.port_combo.addItems([f"COM{i}" for i in range(1, 10)])
        self.port_combo.currentTextChanged.connect(self._on_port_change)
        # Make the combo box more visible too
        self.port_combo.setStyleSheet("""
            QComboBox {
                background-color: #424242;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #555555;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #666666;
            }
            QComboBox::down-arrow {
                image: url(none);
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid white;
                width: 0px;
                height: 0px;
            }
        """)

        self.status_lbl = QLabel("Not connected")

        com_row.addWidget(lbl_com)
        com_row.addWidget(self.port_combo)
        com_row.addSpacing(10)
        com_row.addWidget(self.status_lbl)
        com_row.addStretch(1)
        data_layout.addLayout(com_row)

        settings_layout.addWidget(data_card)
        main_layout.addLayout(settings_layout)

        # Add stretch at the end to push everything to the top
        main_layout.addStretch(1)

        # Create timer for temporary status messages
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self._clear_freq_status)

        # Connect signals
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.set_btn.clicked.connect(self._on_set_freq)

        # Auto-connect default port (block signal)
        ports = [self.port_combo.itemText(i) for i in range(self.port_combo.count())]
        default = DEFAULT_PORT if DEFAULT_PORT in ports else ports[0]
        self.port_combo.blockSignals(True)
        self.port_combo.setCurrentText(default)
        self.port_combo.blockSignals(False)
        self._on_port_change(default)

    def _create_card(self, title):
        """Create a styled card with a title for grouping settings.
        Returns the frame widget and its content layout for adding controls."""
        # Create the main frame
        frame = QFrame()
        frame.setStyleSheet(f"background: {CARD_BG}; border-radius: 8px;")
        frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Create the main layout for the frame
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Add the header with title
        header = QLabel(f" {title}")
        header.setStyleSheet("background: rgba(0,0,0,0.2); border-radius: 8px 8px 0 0; padding: 6px;")
        header.setFont(QFont(header.font().family(), 11, QFont.Weight.Medium))
        frame_layout.addWidget(header)

        # Create a layout for the content area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(12, 12, 12, 12)

        # Add the content layout to the frame
        frame_layout.addLayout(content_layout)

        # Return both the frame and its content layout
        return frame, content_layout

    def _on_start(self):
        """Handle start button click with status update"""
        self.conn.send_json({"Command": "START"})
        self.live_status.setText("Active")
        self.live_status.setStyleSheet(f"color: {STATUS_GREEN}; font-weight: bold;")

    def _on_stop(self):
        """Handle stop button click with status update"""
        self.conn.send_json({"Command": "STOP"})
        self.live_status.setText("Stopped")
        self.live_status.setStyleSheet(f"color: {STATUS_RED}; font-weight: bold;")

    def _on_set_freq(self):
        """Send the gather frequency setting to the device with status feedback"""
        freq = self.freq_spin.value()
        self.conn.send_json({"GatherFreq": freq})
        self.freq_status.setText(f"Set to {freq}Hz")
        self.freq_status.setStyleSheet(f"color: {STATUS_GREEN};")

        # Clear the status message after 3 seconds
        self.status_timer.start(3000)

    def _clear_freq_status(self):
        """Clear the frequency status message"""
        self.freq_status.setText("")

    def _on_port_change(self, port: str) -> None:
        """Handle COM port selection and connection."""
        if not port:
            self.status_lbl.setText("No port")
            return
        try:
            self.conn.open_port(port)
            self.status_lbl.setText(f"Connected to {port}")
            self.conn.send_json({"Command": "START"})

            # Update live status to Active when connected
            self.live_status.setText("Active")
            self.live_status.setStyleSheet(f"color: {STATUS_GREEN}; font-weight: bold;")
        except Exception as e:
            self.status_lbl.setText("Failed")
            log(f"Serial connect error: {e}")