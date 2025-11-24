from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from pathlib import Path

class DuplicateReviewScreen(QWidget):
    keep_left = pyqtSignal()
    keep_right = pyqtSignal()
    keep_both = pyqtSignal()
    review_completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_pair = None
        self.load_stylesheet()
        self.init_ui()
        
    def load_stylesheet(self):
        style_path = Path("assets/style.qss")
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Header with progress
        header_layout = QHBoxLayout()
        
        title = QLabel("Manuelle Dublettenprüfung")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF;")
        
        self.progress_label = QLabel("0 von 0 Paaren")
        self.progress_label.setStyleSheet("font-size: 14px; color: #AAAAAA;")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        
        layout.addLayout(header_layout)
        
        # Image comparison container
        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(30)
        
        # Left image panel
        self.left_panel = self.create_image_panel()
        comparison_layout.addWidget(self.left_panel)
        
        # Right image panel
        self.right_panel = self.create_image_panel()
        comparison_layout.addWidget(self.right_panel)
        
        layout.addLayout(comparison_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.left_btn = QPushButton("Linkes Bild behalten")
        self.left_btn.setFixedHeight(45)
        self.left_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
        self.left_btn.clicked.connect(self.keep_left.emit)
        
        self.both_btn = QPushButton("Beide behalten")
        self.both_btn.setFixedHeight(45)
        self.both_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.both_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #16A34A;
            }
        """)
        self.both_btn.clicked.connect(self.keep_both.emit)
        
        self.right_btn = QPushButton("Rechtes Bild behalten")
        self.right_btn.setFixedHeight(45)
        self.right_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
        self.right_btn.clicked.connect(self.keep_right.emit)
        
        button_layout.addWidget(self.left_btn)
        button_layout.addWidget(self.both_btn)
        button_layout.addWidget(self.right_btn)
        
        layout.addLayout(button_layout)
    
    def create_image_panel(self):
        """Create a panel for displaying one image with metadata."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1A1A1C;
                border-radius: 8px;
                border: 1px solid #2A2A2C;
            }
        """)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)
        
        # Image display
        image_label = QLabel()
        image_label.setFixedSize(500, 400)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background-color: #0E0E0F; border-radius: 4px;")
        image_label.setScaledContents(False)
        panel_layout.addWidget(image_label)
        
        # Metadata container
        metadata_layout = QVBoxLayout()
        metadata_layout.setSpacing(8)
        
        # Filename
        filename_label = QLabel("Dateiname: --")
        filename_label.setStyleSheet("color: #E0E0E0; font-size: 13px; font-weight: bold;")
        metadata_layout.addWidget(filename_label)
        
        # Date
        date_label = QLabel("Datum: --")
        date_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        metadata_layout.addWidget(date_label)
        
        # Time
        time_label = QLabel("Uhrzeit: --")
        time_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        metadata_layout.addWidget(time_label)
        
        # Camera
        camera_label = QLabel("Kamera: --")
        camera_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        metadata_layout.addWidget(camera_label)
        
        panel_layout.addLayout(metadata_layout)
        
        # Store references
        panel.image_label = image_label
        panel.filename_label = filename_label
        panel.date_label = date_label
        panel.time_label = time_label
        panel.camera_label = camera_label
        
        return panel
    
    def load_pair(self, left_path: Path, right_path: Path, left_metadata: dict, right_metadata: dict):
        """Load a pair of images for comparison."""
        self.current_pair = (left_path, right_path)
        
        # Load left image
        self.load_image_to_panel(self.left_panel, left_path, left_metadata)
        
        # Load right image
        self.load_image_to_panel(self.right_panel, right_path, right_metadata)
    
    def load_image_to_panel(self, panel, image_path: Path, metadata: dict):
        """Load an image and its metadata into a panel."""
        # Load image
        pixmap = QPixmap(str(image_path))
        if not pixmap.isNull():
            # Scale to fit while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                panel.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            panel.image_label.setPixmap(scaled_pixmap)
        else:
            panel.image_label.setText("Bild konnte nicht geladen werden")
        
        # Update metadata
        panel.filename_label.setText(f"Dateiname: {metadata.get('filename', '--')}")
        panel.date_label.setText(f"Datum: {metadata.get('date', '--')}")
        panel.time_label.setText(f"Uhrzeit: {metadata.get('time', '--')}")
        panel.camera_label.setText(f"Kamera: {metadata.get('camera', '--')}")
    
    def update_progress(self, current: int, total: int):
        """Update progress display."""
        self.progress_label.setText(f"{current} von {total} Paaren")
