from __future__ import annotations
"""
SettingsTab v4 – signal‑block for single open, simple layout
• Live data controls (Start/Stop) øverst
• GatherFreq under
• COM‑port rett under GatherFreq
• Blocks dropdown signal when auto‑setting to avoid double-open
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QSpinBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from utils.logger import log

DEFAULT_PORT = "COM7"

class SettingsTab(QWidget):
    """Settingstab for SerialConnection med tre seksjoner i én kolonne."""
    def __init__(self, serial_conn):
        super().__init__()
        self.conn = serial_conn

        # Root layout: vertikal stub
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12,12,12,12)
        main_layout.setSpacing(20)

        # 1) Live-data controls
        live_layout = QHBoxLayout(); live_layout.setSpacing(10)
        lbl_live = QLabel("Live data:"); lbl_live.setFixedWidth(100)
        self.start_btn = QPushButton("Start"); self.start_btn.setFixedSize(80,30)
        self.stop_btn  = QPushButton("Stop");  self.stop_btn.setFixedSize(80,30)
        live_layout.addWidget(lbl_live)
        live_layout.addWidget(self.start_btn)
        live_layout.addWidget(self.stop_btn)
        live_layout.addStretch(1)
        main_layout.addLayout(live_layout)

        # 2) Gather frequency
        freq_layout = QHBoxLayout(); freq_layout.setSpacing(10)
        lbl_freq = QLabel("GatherFreq:"); lbl_freq.setFixedWidth(100)
        self.freq_spin = QSpinBox(); self.freq_spin.setRange(1,10); self.freq_spin.setValue(5)
        self.freq_spin.setFixedSize(60,30)
        self.set_btn = QPushButton("Set"); self.set_btn.setFixedSize(60,30)
        freq_layout.addWidget(lbl_freq)
        freq_layout.addWidget(self.freq_spin)
        freq_layout.addWidget(self.set_btn)
        freq_layout.addStretch(1)
        main_layout.addLayout(freq_layout)

        # 3) COM-port selector
        com_layout = QHBoxLayout(); com_layout.setSpacing(10)
        lbl_com = QLabel("COM-port:"); lbl_com.setFixedWidth(100)
        self.port_combo = QComboBox(); self.port_combo.setFixedSize(120,30)
        self.port_combo.addItems([f"COM{i}" for i in range(1,10)])
        self.port_combo.currentTextChanged.connect(self._on_port_change)
        self.status_lbl = QLabel("Not connected")
        com_layout.addWidget(lbl_com)
        com_layout.addWidget(self.port_combo)
        com_layout.addWidget(self.status_lbl)
        com_layout.addStretch(1)
        main_layout.addLayout(com_layout)

        # Signals
        self.start_btn.clicked.connect(lambda: self.conn.send_json({"Command":"START"}))
        self.stop_btn.clicked.connect(lambda: self.conn.send_json({"Command":"STOP"}))
        self.set_btn.clicked.connect(self._send_freq)

        # Auto-connect default port (block signal)
        ports = [self.port_combo.itemText(i) for i in range(self.port_combo.count())]
        default = DEFAULT_PORT if DEFAULT_PORT in ports else ports[0]
        self.port_combo.blockSignals(True)
        self.port_combo.setCurrentText(default)
        self.port_combo.blockSignals(False)
        self._on_port_change(default)

    def _on_port_change(self, port: str) -> None:
        if not port:
            self.status_lbl.setText("No port")
            return
        try:
            self.conn.open_port(port)
            self.status_lbl.setText(f"Connected to {port}")
            self.conn.send_json({"Command":"START"})
        except Exception as e:
            self.status_lbl.setText("Failed")
            log(f"Serial connect error: {e}")

    def _send_freq(self) -> None:
        self.conn.send_json({"GatherFreq": self.freq_spin.value()})
