from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QFrame, QFileDialog, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from pathlib import Path

class NewSessionScreen(QWidget):
    back_clicked = pyqtSignal()
    session_created = pyqtSignal(dict) # Returns session data

    def __init__(self):
        super().__init__()
        self.load_stylesheet()
        self.init_ui()

    def load_stylesheet(self):
        style_path = Path("assets/style.qss")
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print("Warning: Style sheet not found!")

    def init_ui(self):
        # Global Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area to handle height
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background-color: #0E0E0F; border: none; }
            QScrollBar:vertical { width: 8px; background: #0E0E0F; }
            QScrollBar::handle:vertical { background: #333; border-radius: 4px; }
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #0E0E0F;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(20)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # --- Header (Back Button + Title) ---
        header_container = QWidget()
        header_container.setFixedWidth(600)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        back_btn = QPushButton()
        back_btn.setIcon(QIcon("assets/icons/arrow_left.svg"))
        back_btn.setIconSize(QSize(24, 24))
        back_btn.setFixedSize(30, 30)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("background: transparent; border: none;")
        back_btn.clicked.connect(self.back_clicked.emit)

        title = QLabel("Neue Session erstellen")
        title.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold; border: none;")

        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.content_layout.addWidget(header_container)

        # --- Main Form Card ---
        card = QFrame()
        card.setFixedWidth(600)
        # Background transparent to match main screen as requested
        card.setStyleSheet("""
            QFrame {
                background-color: transparent; 
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 20, 0, 20)
        card_layout.setSpacing(24) # Spacing between groups

        # 1. Quellordner
        self.source_input = self.create_line_edit("Ordner auswählen...")
        self.source_input.textChanged.connect(self.validate_form)
        self.source_btn = self.create_folder_button("Ordner wählen")
        self.source_btn.clicked.connect(lambda: self.browse_folder(self.source_input))
        
        source_input_layout = QHBoxLayout()
        source_input_layout.setSpacing(10)
        source_input_layout.addWidget(self.source_input)
        source_input_layout.addWidget(self.source_btn)
        
        self.add_input_group(card_layout, "Quellordner", "Der Ordner, aus dem alle unsortierten Medien geladen werden.", source_input_layout)
        
        # 2. Zielordner
        self.target_input = self.create_line_edit("Zielordner auswählen...")
        self.target_input.textChanged.connect(self.validate_form)
        self.target_btn = self.create_folder_button("Ordner wählen")
        self.target_btn.clicked.connect(lambda: self.browse_folder(self.target_input))

        target_input_layout = QHBoxLayout()
        target_input_layout.setSpacing(10)
        target_input_layout.addWidget(self.target_input)
        target_input_layout.addWidget(self.target_btn)
        
        self.add_input_group(card_layout, "Zielordner", "In diesem Ordner legt FotoSortierer alle sortierten Dateien und Unterordner ab.", target_input_layout)

        # 3. Sitzungsname
        self.name_input = self.create_line_edit("Name der Session eingeben...")
        self.name_input.textChanged.connect(self.validate_form)
        self.add_input_group(card_layout, "Sitzungsname", "Der Name dieser Session, unter dem Fortschritt und Einstellungen gespeichert werden.", self.name_input)

        # 4. Dublettenerkennung
        card_layout.addSpacing(10)
        dupe_row = QHBoxLayout()
        dupe_row.setSpacing(15)
        dupe_row.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.dupe_check = QCheckBox()
        self.dupe_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dupe_check.setFixedSize(24, 24)
        self.dupe_check.setStyleSheet("""
            QCheckBox { background: transparent; }
            QCheckBox::indicator { 
                width: 20px; height: 20px; 
                border: 1px solid #555; 
                border-radius: 4px; 
                background: #2A2A2C; 
            }
            QCheckBox::indicator:checked { 
                background-color: #2D7DFF; 
                border-color: #2D7DFF; 
                image: url(assets/icons/check.svg); 
            }
        """)
        
        dupe_text_layout = QVBoxLayout()
        dupe_text_layout.setSpacing(6) # Increased spacing as requested
        dupe_label = QLabel("Dublettenerkennung aktivieren")
        dupe_label.setStyleSheet("color: #FFF; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        dupe_desc = QLabel("Wenn aktiviert, führt FotoSortierer vor dem Start des Sortiervorgangs einen Dubletten-Scan durch.")
        dupe_desc.setStyleSheet("color: #888; font-size: 12px; border: none; background: transparent;")
        dupe_desc.setWordWrap(True)
        
        dupe_text_layout.addWidget(dupe_label)
        dupe_text_layout.addWidget(dupe_desc)
        
        dupe_row.addWidget(self.dupe_check)
        dupe_row.addLayout(dupe_text_layout, 1)
        card_layout.addLayout(dupe_row)

        # 5. Buttons
        card_layout.addSpacing(30)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        self.start_btn = QPushButton("Session starten")
        self.start_btn.setFixedHeight(45)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton { 
                background-color: #2D7DFF; 
                color: white; 
                border-radius: 6px; 
                font-weight: bold; 
                font-size: 14px; 
                border: none; 
            }
            QPushButton:hover { background-color: #3B82F6; }
            QPushButton:disabled { 
                background-color: #333333; 
                color: #888888; 
                cursor: default;
            }
        """)
        self.start_btn.clicked.connect(self.submit)

        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #333333; color: #E0E0E0; border-radius: 6px; font-weight: bold; font-size: 14px; border: none; }
            QPushButton:hover { background-color: #444444; }
        """)
        self.cancel_btn.clicked.connect(self.back_clicked.emit)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.cancel_btn)
        card_layout.addLayout(btn_row)

        self.content_layout.addWidget(card)

        # --- Info Box ---
        info_box = QFrame()
        info_box.setFixedWidth(600)
        info_box.setStyleSheet("""
            QFrame { background-color: #151517; border: 1px solid #333; border-radius: 8px; }
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        info_title_row = QHBoxLayout()
        info_icon = QLabel()
        info_icon.setPixmap(QIcon("assets/icons/info.svg").pixmap(20, 20))
        info_icon.setStyleSheet("border: none; background: transparent;")
        
        info_title = QLabel("Hinweise zur Session-Erstellung:")
        info_title.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        info_title_row.addWidget(info_icon)
        info_title_row.addWidget(info_title)
        info_title_row.addStretch()
        
        info_layout.addLayout(info_title_row)
        
        info_text = QLabel("• Der Quell- und Zielordner dürfen nicht identisch sein\n• Sessions können jederzeit pausiert und fortgesetzt werden")
        info_text.setStyleSheet("color: #888; font-size: 13px; margin-left: 28px; line-height: 1.4; border: none; background: transparent;")
        info_layout.addWidget(info_text)

        self.content_layout.addWidget(info_box)
        self.content_layout.addStretch()
        
        # Initial validation
        self.validate_form()

    def validate_form(self):
        name = self.name_input.text().strip()
        source = self.source_input.text().strip()
        target = self.target_input.text().strip()
        
        # Reset styles
        self.source_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2C;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                color: #FFF;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #2D7DFF; }
        """)
        self.target_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2C;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                color: #FFF;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #2D7DFF; }
        """)
        
        # Validation checks
        is_valid = True
        
        # Check if all fields are filled
        if not (name and source and target):
            is_valid = False
        
        # Check if source path exists and is a directory
        if source:
            source_path = Path(source)
            if not source_path.exists() or not source_path.is_dir():
                is_valid = False
                self.source_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #2A2A2C;
                        border: 1px solid #ff4444;
                        border-radius: 4px;
                        padding: 10px;
                        color: #FFF;
                        font-size: 14px;
                    }
                    QLineEdit:focus { border: 1px solid #ff4444; }
                """)
        
        # Check if target path exists and is a directory
        if target:
            target_path = Path(target)
            if not target_path.exists() or not target_path.is_dir():
                is_valid = False
                self.target_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #2A2A2C;
                        border: 1px solid #ff4444;
                        border-radius: 4px;
                        padding: 10px;
                        color: #FFF;
                        font-size: 14px;
                    }
                    QLineEdit:focus { border: 1px solid #ff4444; }
                """)
        
        # Check if source and target are not identical
        if source and target and is_valid:
            if Path(source).resolve() == Path(target).resolve():
                is_valid = False
                self.source_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #2A2A2C;
                        border: 1px solid #ff4444;
                        border-radius: 4px;
                        padding: 10px;
                        color: #FFF;
                        font-size: 14px;
                    }
                    QLineEdit:focus { border: 1px solid #ff4444; }
                """)
                self.target_input.setStyleSheet("""
                    QLineEdit {
                        background-color: #2A2A2C;
                        border: 1px solid #ff4444;
                        border-radius: 4px;
                        padding: 10px;
                        color: #FFF;
                        font-size: 14px;
                    }
                    QLineEdit:focus { border: 1px solid #ff4444; }
                """)
        
        self.start_btn.setEnabled(is_valid)

    def add_input_group(self, parent_layout, label_text, help_text, input_item):
        """Helper to group label, help text and input with tight spacing."""
        group_layout = QVBoxLayout()
        group_layout.setSpacing(6) # Tight spacing between label/help/input
        
        group_layout.addWidget(self.create_label(label_text))
        group_layout.addWidget(self.create_help_text(help_text))
        
        if isinstance(input_item, QWidget):
            group_layout.addWidget(input_item)
        elif isinstance(input_item, QHBoxLayout):
            group_layout.addLayout(input_item)
            
        parent_layout.addLayout(group_layout)

    def create_label(self, text):
        lbl = QLabel(f"{text} <span style='color:#ff4444;'>*</span>")
        lbl.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        return lbl

    def create_help_text(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #666; font-size: 11px; border: none; background: transparent;")
        return lbl

    def create_line_edit(self, placeholder):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setStyleSheet("""
            QLineEdit {
                background-color: #2A2A2C;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                color: #FFF;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #2D7DFF; }
        """)
        return le

    def create_folder_button(self, text):
        btn = QPushButton(f"  {text}")
        btn.setIcon(QIcon("assets/icons/folder.svg"))
        btn.setFixedSize(140, 42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: #333; color: #E0E0E0; border-radius: 4px; border: 1px solid #444; font-size: 13px; }
            QPushButton:hover { background-color: #444; }
        """)
        return btn

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        if folder:
            line_edit.setText(folder)

    def submit(self):
        data = {
            "name": self.name_input.text(),
            "source": self.source_input.text(),
            "target": self.target_input.text(),
            "detect_duplicates": self.dupe_check.isChecked()
        }
        self.session_created.emit(data)
