import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.logger import setup_logger

def main():
    # Setup Logging
    logger = setup_logger()
    logger.info("Application started")
    
    # Create Application
    app = QApplication(sys.argv)
    
    # Create and Show Window
    window = MainWindow()
    window.show()
    
    # Run Event Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
