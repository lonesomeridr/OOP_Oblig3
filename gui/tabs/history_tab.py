"""
Henter historiske data fra MySQL og plott­er dem (ikke sanntid).
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
# + QWebEngineView / Plotly

class HistoryTab(QWidget):
    def __init__(self, db):
        super().__init__()
        # TODO: knapp "Last siste 1t", dropdown sensor‑id, etc.
        #       bruk db.fetch_temperature(...), db.fetch_accel(...)
        #       render Plotly én gang per klikk
