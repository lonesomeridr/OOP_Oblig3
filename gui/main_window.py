"""
QMainWindow som bygger opp et QTabWidget og kobler til SerialReader‑signaler.
"""
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from gui.tabs.live_tab import LiveTab
from gui.tabs.history_tab import HistoryTab
from gui.tabs.config_tab import ConfigTab
from gui.tabs.settings_tab import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self, serial_reader, serial_conn, db):
        super().__init__()
        self.setWindowTitle("Sensor Dashboard")

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(LiveTab(serial_reader, db),     "Live")
        tabs.addTab(HistoryTab(db),                 "Historikk")
        tabs.addTab(ConfigTab(serial_conn),         "Konfig")
        tabs.addTab(SettingsTab(serial_conn),       "Innstillinger")

        self.setCentralWidget(tabs)

        # TODO: statusbar, global shortcuts osv.
