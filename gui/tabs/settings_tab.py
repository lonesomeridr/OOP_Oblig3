from __future__ import annotations
"""
Innstillings‑fane: velg COM‑port, Start/Stop og sett GatherFreq.
Kobler automatisk til **COM7** (hvis den finnes) ellers første tilgjengelige
port – og sender «START» umiddelbart, slik at LiveTab mottar data uten
brukerklikk. Brukeren kan fortsatt velge andre porter fra dropdownen.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QPushButton, QSpinBox
)
from utils.logger import log

DEFAULT_PORT = "COM7"  # endre her om du får nytt kort / portnummer


class SettingsTab(QWidget):
    """Brukes mot en felles SerialConnection‑instans."""

    def __init__(self, serial_conn):
        super().__init__()
        self.conn = serial_conn

        # --------------------------------------------------
        # COM‑port‑velger
        # --------------------------------------------------
        com_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        ports = self._refresh_ports()          # fyll dropdown
        self.port_combo.currentTextChanged.connect(self._on_port_change)
        self.status_lbl = QLabel("Not connected")
        com_layout.addWidget(self.port_combo)
        com_layout.addWidget(self.status_lbl)

        # --------------------------------------------------
        # Kontrollknapper
        # --------------------------------------------------
        ctl_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        ctl_layout.addWidget(self.start_btn)
        ctl_layout.addWidget(self.stop_btn)

        # GatherFreq‑kontroll
        freq_lbl = QLabel("GatherFreq:")
        self.freq_spin = QSpinBox(); self.freq_spin.setRange(1, 10); self.freq_spin.setValue(5)
        set_freq_btn = QPushButton("Set")
        ctl_layout.addWidget(freq_lbl)
        ctl_layout.addWidget(self.freq_spin)
        ctl_layout.addWidget(set_freq_btn)

        # --------------------------------------------------
        # Signals
        # --------------------------------------------------
        self.start_btn.clicked.connect(lambda: self.conn.send_json({"Command": "START"}))
        self.stop_btn.clicked.connect(lambda: self.conn.send_json({"Command": "STOP"}))
        set_freq_btn.clicked.connect(self._send_freq)

        # --------------------------------------------------
        # Hoved‑layout
        # --------------------------------------------------
        main_lay = QVBoxLayout()
        main_lay.addLayout(com_layout)
        main_lay.addLayout(ctl_layout)
        self.setLayout(main_lay)

        # --------------------------------------------------
        # Auto‑connect + auto‑start
        # --------------------------------------------------
        chosen = None
        if DEFAULT_PORT in ports:
            chosen = DEFAULT_PORT
        elif ports:
            chosen = ports[0]

        if chosen:
            # setCurrentText triggerer signal, men bare hvis teksten endres;
            # for sikkerhets skyld kaller vi _on_port_change manuelt etterpå.
            self.port_combo.setCurrentText(chosen)
            self._on_port_change(chosen)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _refresh_ports(self):
        """Returnerer liste over tilgjengelige porter og fyller dropdown."""
        ports = self.conn.list_ports() or []
        self.port_combo.clear()
        self.port_combo.addItems(ports or ["<ingen>"])
        return ports

    def _on_port_change(self, port: str):
        if "<ingen>" in port:
            return
        try:
            self.conn.open_port(port)
            self.status_lbl.setText(f"Connected to {port}")
            # Start datainnsamling umiddelbart for LiveTab
            self.conn.send_json({"Command": "START"})
        except Exception as exc:
            self.status_lbl.setText("Failed")
            log(f"Serial connect error: {exc}")

    def _send_freq(self):
        self.conn.send_json({"GatherFreq": self.freq_spin.value()})
