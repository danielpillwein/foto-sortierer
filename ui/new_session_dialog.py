from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QFileDialog, QCheckBox, QMessageBox, QWidget)
from PyQt6.QtCore import Qt

class NewSessionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neue Session")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.result_data = None
        self.init_ui()

    def init_ui(self):
        # Main Container with Border
        container = QWidget(self)
        container.setGeometry(0, 0, 600, 500)
        container.setStyleSheet("""
            QWidget {
                background-color: #0E0E0F;
                border: 1px solid #333333;
                border-radius: 12px;
                color: #FFFFFF;
                font-family: "Segoe UI", sans-serif;
            }
            QLabel {
                border: none;
                font-size: 14px;
                color: #E0E0E0;
                margin-bottom: 4px;
            }
            QLineEdit {
                background-color: #1A1A1C;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 10px;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2D7DFF;
            }
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QPushButton#secondary {
                background-color: #333333;
                color: #E0E0E0;
            }
            QPushButton#secondary:hover {
                background-color: #444444;
            }
            QCheckBox {
                spacing: 8px;
                font-size: 14px;
                color: #E0E0E0;
                border: none;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #555555;
                border-radius: 4px;
                background: #1A1A1C;
            }
            QCheckBox::indicator:checked {
                background-color: #2D7DFF;
                border-color: #2D7DFF;
                image: url(assets/icons/check.svg); /* Fallback if icon missing */
            }
        """)

        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        title = QLabel("Neue Session")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;")
        layout.addWidget(title)

        # Session Name
        layout.addWidget(QLabel("Name der Session"))
        self.name_input = QLineEdit()
        self.name_input.setText("Katze") # Default from mockup? Or empty. Let's keep empty or placeholder.
        self.name_input.setPlaceholderText("z.B. Urlaub 2023")
        layout.addWidget(self.name_input)

        # Source Path
        layout.addWidget(QLabel("Quellordner (Unsortiert)"))
        source_layout = QHBoxLayout()
        source_layout.setSpacing(10)
        self.source_input = QLineEdit()
        self.source_input.setReadOnly(True)
        browse_source_btn = QPushButton("...")
        browse_source_btn.setFixedSize(50, 40)
        browse_source_btn.clicked.connect(lambda: self.browse_folder(self.source_input))
        source_layout.addWidget(self.source_input)
        source_layout.addWidget(browse_source_btn)
        layout.addLayout(source_layout)

        # Target Path
        layout.addWidget(QLabel("Zielordner (Sortiert)"))
        target_layout = QHBoxLayout()
        target_layout.setSpacing(10)
        self.target_input = QLineEdit()
        self.target_input.setReadOnly(True)
        browse_target_btn = QPushButton("...")
        browse_target_btn.setFixedSize(50, 40)
        browse_target_btn.clicked.connect(lambda: self.browse_folder(self.target_input))
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(browse_target_btn)
        layout.addLayout(target_layout)

        # Options
        layout.addSpacing(10)
        self.dupe_check = QCheckBox("Automatische Dublettenerkennung durchführen")
        layout.addWidget(self.dupe_check)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setFixedHeight(45)
        cancel_btn.clicked.connect(self.reject)
        
        start_btn = QPushButton("Session starten")
        start_btn.setFixedHeight(45)
        start_btn.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        if folder:
            line_edit.setText(folder)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        source = self.source_input.text().strip()
        target = self.target_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte gib einen Namen für die Session ein.")
            return
        if not source:
            QMessageBox.warning(self, "Fehler", "Bitte wähle einen Quellordner aus.")
            return
        if not target:
            QMessageBox.warning(self, "Fehler", "Bitte wähle einen Zielordner aus.")
            return
        if source == target:
            QMessageBox.warning(self, "Fehler", "Quell- und Zielordner dürfen nicht identisch sein.")
            return

        self.result_data = {
            "name": name,
            "source": source,
            "target": target,
            "detect_duplicates": self.dupe_check.isChecked()
        }
        self.accept()
