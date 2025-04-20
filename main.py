#!/usr/bin/env python3
"""
Main entry point for the Sensor Dashboard application.
"""

import sys
from PyQt6.QtWidgets import QApplication

# Import the main window class - it will handle creating its components
from gui.main_window import MainWindow
from utils.logger import log

# --- Optional Styling ---
# If you have a stylesheet (e.g., for a dark theme), you can define it here
# DARK_STYLESHEET = """
# QWidget {
#     background-color: #333;
#     color: #EEE;
# }
# QPushButton {
#     background-color: #555;
#     border: 1px solid #777;
#     padding: 5px;
#     min-width: 80px;
# }
# QPushButton:hover {
#     background-color: #666;
# }
# QTabWidget::pane {
#     border-top: 2px solid #555;
# }
# QTabBar::tab {
#     background: #444;
#     border: 1px solid #555;
#     padding: 6px 10px;
# }
# QTabBar::tab:selected {
#     background: #555;
#     margin-bottom: -1px; /* Make selected tab look connected to pane */
# }
# /* Add more specific styles as needed */
# """

def main():
    """Sets up and runs the PyQt application."""
    log("Application starting...")
    app = QApplication(sys.argv)

    # --- Apply Styling (Uncomment if you have a stylesheet) ---
    # app.setStyleSheet(DARK_STYLESHEET)

    # --- Create and Show the Main Window ---
    # MainWindow's __init__ method now handles creating the DB connection,
    # serial connection, and serial reader thread.
    try:
        main_window = MainWindow()
        main_window.show()
    except Exception as e:
        log(f"FATAL: Failed to initialize MainWindow: {e}")
        # Optionally show a critical error message box to the user here
        # from PyQt6.QtWidgets import QMessageBox
        # QMessageBox.critical(None, "Application Error", f"Failed to start:\n{e}")
        sys.exit(1) # Exit if the main window fails to initialize

    # --- Start the Qt Event Loop ---
    log("Starting Qt event loop...")
    exit_code = app.exec()
    log(f"Application finished with exit code {exit_code}")
    sys.exit(exit_code)


if __name__ == '__main__':
    # This ensures the main() function runs only when the script is executed directly
    main()