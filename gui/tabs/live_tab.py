"""
Sanntidsvisning: mottar Qt‑signal fra SerialReader og oppdaterer labels + Plotly.
Flyttet hele gamle sensor_dashboard_real_data‑koden hit (det meste kan beholdes).
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
# + resten av importene fra den gamle filen

class LiveTab(QWidget):
    def __init__(self, serial_reader, db):
        super().__init__()
        # TODO: kopier inn eksisterende layout‑kode
        #  * kutt ut COM‑port‑knapper (flyttes til settings_tab)
        #  * kall db.insert(packet) hvis du vil logge her

        # Koble signal
        serial_reader.data_ready.connect(self.update_from_packet)

    def update_from_packet(self, pkt: dict):
        """Oppdater GUI + send til Plotly."""
        # TODO: gjenbruk update_plot‑logikk fra gammel fil
