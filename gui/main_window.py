"""
MainWindow class - Creates the main application window with tabs and status bar
Uses dark theme styling throughout the interface
"""
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
import os

from gui.tabs.live_tab import LiveTab
from gui.tabs.history_tab import HistoryTab
from gui.tabs.config_tab import ConfigTab
from gui.tabs.settings_tab import SettingsTab

# Dark theme color palette
DARK_BG = "#121212"  # Dark background matching header
DARKER_BG = "#0A0A0A"  # Slightly darker for contrast
LIGHT_TEXT = "#E0E0E0"  # Light grey text for readability
DIM_TEXT = "#9E9E9E"  # Dimmed text for secondary info
SUCCESS_COLOR = "#4CAF50"  # Green for success states
ERROR_COLOR = "#F44336"  # Red for error states
NEUTRAL_COLOR = "#757575"  # Medium gray
SEPARATOR_COLOR = "#2C2C2C"  # Subtle dark separator


class VerticalLine(QFrame):
    """Custom vertical line separator for dark theme"""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setStyleSheet(f"background-color: {SEPARATOR_COLOR}; max-width: 1px;")


class MainWindow(QMainWindow):
    """Main application window containing tabs and status information"""

    def __init__(self, serial_reader, serial_conn, db):
        super().__init__()
        self.setWindowTitle("Sensor Dashboard")
        self.resize(1200, 900)

        self.serial_conn = serial_conn
        self.db = db

        # Create tab widget with all app sections
        tabs = QTabWidget()
        tabs.addTab(LiveTab(serial_reader, db), "Live Data")
        tabs.addTab(HistoryTab(db), "Historical Data")
        tabs.addTab(ConfigTab(serial_reader, serial_conn, db), "Configuration")

        # Create settings tab and handle connection updates
        self.settings_tab = SettingsTab(serial_conn)
        tabs.addTab(self.settings_tab, "Settings")

        self.setCentralWidget(tabs)

        # Setup dark-themed status bar
        self.setup_status_bar()

        # Check initial connection state
        self.check_connection_state()

        # Update status every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def setup_status_bar(self):
        """Set up a dark theme status bar with connection info and time"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {DARK_BG}; 
                color: {LIGHT_TEXT};
                border-top: 1px solid {DARKER_BG};
            }}
            QStatusBar::item {{
                border: none;
                margin: 0px 6px;
            }}
        """)
        self.setStatusBar(self.status_bar)

        # Serial port status indicator
        self.com_label = QLabel("  Serial: Checking...  ")
        self.com_label.setStyleSheet(f"color: {DIM_TEXT}; padding: 0 8px;")
        self.status_bar.addWidget(self.com_label)

        # Visual separator
        self.status_bar.addWidget(VerticalLine())

        # Database connection status
        db_status = "Connected" if self.db is not None else "Disconnected"
        db_color = SUCCESS_COLOR if self.db is not None else ERROR_COLOR
        self.db_label = QLabel(f"  DB: {db_status}  ")
        self.db_label.setStyleSheet(f"color: {db_color}; padding: 0 8px;")
        self.status_bar.addWidget(self.db_label)

        # Right side information with separator
        self.status_bar.addPermanentWidget(VerticalLine())

        # User info display
        try:
            username = os.getlogin()
        except:
            username = "Unknown"

        user_label = QLabel(f"  User: {username}  ")
        user_label.setStyleSheet(f"color: {LIGHT_TEXT}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(user_label)

        # Final separator before time
        self.status_bar.addPermanentWidget(VerticalLine())

        # Current time display
        self.time_label = QLabel()
        self.time_label.setStyleSheet(f"color: {LIGHT_TEXT}; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.time_label)

    def check_connection_state(self):
        """Check and update the serial connection status indicator"""
        # Try to determine connection state from various possible attributes
        connected = False
        port_name = None

        if hasattr(self.serial_conn, 'port'):
            port_name = self.serial_conn.port
            connected = port_name is not None
        elif hasattr(self.serial_conn, 'ser') and hasattr(self.serial_conn.ser, 'port'):
            port_name = self.serial_conn.ser.port
            connected = self.serial_conn.ser.is_open
        elif hasattr(self.serial_conn, 'is_open'):
            connected = self.serial_conn.is_open
            port_name = self.serial_conn.port if hasattr(self.serial_conn, 'port') else "Unknown"

        # Check settings tab status label as fallback
        if hasattr(self.settings_tab, 'status_lbl'):
            status_text = self.settings_tab.status_lbl.text()
            if "Connected to" in status_text:
                connected = True
                if not port_name:
                    port_name = status_text.replace("Connected to ", "")

        # Update status indicator with appropriate color
        if connected and port_name:
            self.com_label.setText(f"  Serial: Connected to {port_name}  ")
            self.com_label.setStyleSheet(f"color: {SUCCESS_COLOR}; padding: 0 8px;")
        else:
            self.com_label.setText("  Serial: Not connected  ")
            self.com_label.setStyleSheet(f"color: {ERROR_COLOR}; padding: 0 8px;")

    def update_status(self):
        """Periodic update of status bar information"""
        # Update time display
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"  Time: {current_time}  ")

        # Check connection state
        self.check_connection_state()