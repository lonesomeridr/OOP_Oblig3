import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget)
from PyQt6.QtCore import pyqtSlot

from gui.tabs.live_tab import LiveTab
from gui.tabs.history_tab import HistoryTab
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.config_tab import ConfigTab

# Corrected import path for DB and DEFAULT_SENSOR_ID
from database.db import DB, DEFAULT_SENSOR_ID
from serial_io.connection import SerialConnection
from serial_io.worker import SerialReader
from utils.logger import log


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        log("MainWindow init")
        self.setWindowTitle("Sensor Dashboard")
        self.setGeometry(100, 100, 1000, 700) # Adjusted default size

        # --- Core components ---
        self.db = DB()
        self.conn = Connection()
        self.reader = SerialReader(self.conn)

        # --- UI Setup ---
        self.tabs = QTabWidget()
        self.live_tab = LiveTab(self.reader) # Pass reader if needed for direct plot updates
        self.history_tab = HistoryTab(self.db) # Pass db instance
        self.settings_tab = SettingsTab(self.conn, self.reader, self.db) # Pass necessary components
        self.config_tab = ConfigTab(self.db) # Pass db instance

        self.tabs.addTab(self.live_tab, "Live")
        self.tabs.addTab(self.history_tab, "History")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.config_tab, "Config")

        self.setCentralWidget(self.tabs)

        # --- Connect Signals ---
        self._connect_signals()

        # Start reader thread
        self.reader.start()

    def _connect_signals(self):
        # Connect serial reader signals to the main window's slots
        self.reader.data_ready.connect(self._on_data_ready)
        self.reader.error.connect(self._on_serial_error)

        # Connect settings tab signals that affect the reader/connection
        self.settings_tab.com_port_changed.connect(self.conn.set_port)
        self.settings_tab.status_update.connect(self.statusBar().showMessage) # Example status update

        # Connect other signals as needed (e.g., History tab load button)
        # self.history_tab.load_button.clicked.connect(self.history_tab.load_data)

    @pyqtSlot(dict)
    def _on_data_ready(self, data: dict):
        """Handles incoming data packets from the serial reader."""
        # 1. Update Live Tab (pass data directly)
        self.live_tab.update_plots(data)

        # 2. Insert into Database
        try:
            # Use the DEFAULT_SENSOR_ID defined in db.py
            sensor_id = DEFAULT_SENSOR_ID

            # Insert temperature if present
            if "temperature" in data:
                self.db.insert_temperature(sensor_id, data["temperature"])

            # Insert acceleration if present
            if all(k in data for k in ("accel_x", "accel_y", "accel_z")):
                accel_x = data["accel_x"]
                accel_y = data["accel_y"]
                accel_z = data["accel_z"]

                # --- THE FIX: Get diff values safely, defaulting to 0.0 ---
                diff_x = data.get("diff_accel_x", 0.0)
                diff_y = data.get("diff_accel_y", 0.0)
                diff_z = data.get("diff_accel_z", 0.0)

                # Call insert_accel with *all* required arguments
                self.db.insert_accel(sensor_id, accel_x, accel_y, accel_z, diff_x, diff_y, diff_z)

        except Exception as e:
            log(f"Error inserting data into DB: {e}") # Log DB insertion errors

    @pyqtSlot(str)
    def _on_serial_error(self, error_message: str):
        """Handles errors reported by the serial reader thread."""
        log(f"Serial Error: {error_message}")
        self.statusBar().showMessage(f"Serial Error: {error_message.splitlines()[0]}", 5000) # Show brief error

    def closeEvent(self, event):
        """Ensure threads and connections are closed cleanly."""
        log("Closing application...")
        self.reader.stop() # Signal the reader thread to stop
        self.reader.wait(2000) # Wait for thread to finish (max 2 seconds)
        if self.reader.isRunning():
            log("Reader thread did not stop gracefully, terminating.")
            self.reader.terminate() # Force terminate if needed
        self.conn.close()
        self.db.close()
        log("Connections closed.")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Apply dark theme or other styling if desired
    # app.setStyleSheet(...)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())