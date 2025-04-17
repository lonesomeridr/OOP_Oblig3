"""
Starter programmet og setter opp avhengigheter (GUI + seriell‑tråd + DB‑tilkobling).
"""
import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from serial_io.connection import SerialConnection
from serial_io.worker import SerialReader
from database.db import DB

def main():
    # 1) Init Qt
    app = QApplication(sys.argv)

    # 2) Init database (kan evt. flyttes inn i history_tab)
    db = DB()  # TODO: legg inn passord i utils/config.py

    # 3) Init serial connection + reader‑tråd
    serial_conn = SerialConnection()      # åpner ikke port ennå
    serial_reader = SerialReader(serial_conn)
    serial_reader.start()

    # 4) Send shared refs inn i MainWindow
    win = MainWindow(serial_reader, serial_conn, db)
    win.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
