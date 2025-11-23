from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FotoSortierer")
        self.resize(1280, 720)
        
        # Load global style
        self.load_stylesheet()
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Placeholder Content
        label = QLabel("FotoSortierer - Phase 1 Ready")
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2D7DFF;")
        layout.addWidget(label)
        
        info_label = QLabel("Basic Structure Initialized")
        layout.addWidget(info_label)

    def load_stylesheet(self):
        style_path = Path("assets/style.qss")
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print("Warning: Style sheet not found!")
