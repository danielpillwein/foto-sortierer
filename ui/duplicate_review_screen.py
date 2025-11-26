from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QByteArray, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QKeySequence, QShortcut, QMovie
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
        layout.setContentsMargins(60, 50, 60, 50)  # Larger margins for fullscreen
        layout.setSpacing(40)  # More breathing room
        
        # Header with progress
        header_layout = QHBoxLayout()
        
        title = QLabel("Manuelle Duplikatprüfung")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")  # Larger for fullscreen
        
        self.progress_label = QLabel("0 von 0 Paaren")
        self.progress_label.setStyleSheet("font-size: 16px; color: #AAAAAA;")  # Larger for fullscreen
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.progress_label)
        
        layout.addLayout(header_layout)
        
        # Image comparison container
        comparison_layout = QHBoxLayout()
        comparison_layout.setSpacing(40)  # More space between images
        
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
        
        # Left Button (Keep Left)
        self.left_btn = self.create_action_button(
            "Linkes Bild behalten", 
            "arrow-left.svg", 
            "←", 
            "#2D7DFF", 
            self.keep_left.emit
        )
        
        # Both Button (Keep Both)
        self.both_btn = self.create_action_button(
            "Beide behalten", 
            "check.svg", 
            "Leerzeichen", 
            "#22C55E", 
            self.keep_both.emit
        )
        
        # Right Button (Keep Right)
        self.right_btn = self.create_action_button(
            "Rechtes Bild behalten", 
            "arrow-right.svg", 
            "→", 
            "#2D7DFF", 
            self.keep_right.emit
        )
        
        button_layout.addWidget(self.left_btn)
        button_layout.addWidget(self.both_btn)
        button_layout.addWidget(self.right_btn)
        
        layout.addLayout(button_layout)
        
        # Setup Shortcuts
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for actions."""
        # Left Arrow -> Keep Left
        self.shortcut_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.shortcut_left.activated.connect(self.trigger_left)
        
        # Right Arrow -> Keep Right
        self.shortcut_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.shortcut_right.activated.connect(self.trigger_right)
        
        # Space -> Keep Both
        self.shortcut_space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        self.shortcut_space.activated.connect(self.trigger_both)
    
    def trigger_left(self):
        if self.left_btn.isEnabled():
            self.left_btn.animateClick()
            
    def trigger_right(self):
        if self.right_btn.isEnabled():
            self.right_btn.animateClick()
            
    def trigger_both(self):
        if self.both_btn.isEnabled():
            self.both_btn.animateClick()

    def create_action_button(self, text, icon_name, shortcut_text, color, callback):
        """Create a styled action button with icon and shortcut badge."""
        btn = QPushButton()
        btn.setMinimumHeight(50)  # Minimum height, can grow
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        
        # Store original text for restoring after loading
        btn.original_text = text
        btn.original_icon_name = icon_name
        
        # Layout for content
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel()
        icon_label.setStyleSheet("background: transparent; border: none;")
        icon_path = Path(f"assets/icons/{icon_name}")
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            icon_label.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            # Fallback if icon missing
            icon_label.setText("")
            icon_label.setStyleSheet("color: white; font-weight: bold;")
        
        layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel(text)
        text_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(text_label)
        
        layout.addStretch()
        
        # Shortcut Badge
        badge = QLabel(shortcut_text)
        badge.setFixedSize(40 if len(shortcut_text) > 1 else 24, 24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("background-color: rgba(0,0,0,0.2); color: #EEE; border-radius: 4px; font-size: 11px; border: none;")
        layout.addWidget(badge)
        
        # Store references
        btn.icon_label = icon_label
        btn.text_label = text_label
        btn.badge = badge
        
        # Set Button Style
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: 6px;
                border: none;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.adjust_color(color, 1.1)};
            }}
            QPushButton:disabled {{
                background-color: #333333;
                color: #888888;
            }}
        """)
        
        return btn
    
    def adjust_color(self, hex_color, factor):
        """Adjust color brightness (simple approximation)."""
        # This is a placeholder for color adjustment logic
        # For now, just return the color or a hardcoded lighter variant
        if hex_color == "#2D7DFF": return "#3B82F6"
        if hex_color == "#22C55E": return "#16A34A"
        return hex_color

    def set_processing(self, active_btn):
        """Disable all buttons and show animated spinner in the active one."""
        for btn in [self.left_btn, self.both_btn, self.right_btn]:
            btn.setEnabled(False)
            # Dim the badge
            btn.badge.setStyleSheet("background-color: rgba(0,0,0,0.1); color: #666; border-radius: 4px; font-size: 11px; border: none;")
        
        # Hide content in active button
        active_btn.icon_label.hide()
        active_btn.text_label.hide()
        active_btn.badge.hide()
        
        # Create spinner label if not exists
        if not hasattr(active_btn, 'spinner_label'):
            active_btn.spinner_label = QLabel("wird verarbeitet")
            active_btn.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            active_btn.spinner_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent; border: none;")
            # Insert at index 1 (middle)
            active_btn.layout().insertWidget(1, active_btn.spinner_label)
        
        active_btn.spinner_label.show()
        
        # Setup animation timer
        if not hasattr(active_btn, 'spinner_timer'):
            active_btn.spinner_timer = QTimer(self)
            active_btn.spinner_timer.timeout.connect(lambda: self.update_spinner_animation(active_btn))
        
        active_btn.spinner_dots = 0
        active_btn.spinner_label.setText("wird verarbeitet")
        active_btn.spinner_timer.start(100) # Update every 100ms

    def update_spinner_animation(self, btn):
        """Update the dots animation."""
        if hasattr(btn, 'spinner_dots'):
            btn.spinner_dots = (btn.spinner_dots + 1) % 4
            btn.spinner_label.setText("wird verarbeitet" + "." * btn.spinner_dots)

    def reset_processing(self):
        """Reset buttons to normal state."""
        for btn in [self.left_btn, self.both_btn, self.right_btn]:
            btn.setEnabled(True)
            btn.badge.setStyleSheet("background-color: rgba(0,0,0,0.2); color: #EEE; border-radius: 4px; font-size: 11px; border: none;")
            
            # Restore content
            btn.icon_label.show()
            btn.text_label.show()
            btn.badge.show()
            
            # Stop and hide spinner
            if hasattr(btn, 'spinner_timer'):
                btn.spinner_timer.stop()
            
            if hasattr(btn, 'spinner_label'):
                btn.spinner_label.hide()
    
    def create_image_panel(self):
        """Create a panel for displaying one image with metadata."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #1A1A1C;
                border-radius: 12px;
                border: 1px solid #2A2A2C;
            }
        """)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)
        
        # Image display - use minimum size and let it grow
        image_label = QLabel()
        image_label.setMinimumSize(400, 300)  # Minimum size
        image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background: transparent; border: none;")  # Transparent background
        image_label.setScaledContents(False)
        panel_layout.addWidget(image_label, 1)  # Stretch factor 1
        
        # Metadata container
        metadata_layout = QVBoxLayout()
        metadata_layout.setSpacing(8)
        
        # Filename
        filename_label = QLabel("Dateiname: --")
        filename_label.setStyleSheet("color: #E0E0E0; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        metadata_layout.addWidget(filename_label)
        
        # Date
        date_label = QLabel("Datum: --")
        date_label.setStyleSheet("color: #AAAAAA; font-size: 13px; background: transparent; border: none;")
        metadata_layout.addWidget(date_label)
        
        # Time
        time_label = QLabel("Uhrzeit: --")
        time_label.setStyleSheet("color: #AAAAAA; font-size: 13px; background: transparent; border: none;")
        metadata_layout.addWidget(time_label)
        
        # Camera
        camera_label = QLabel("Kamera: --")
        camera_label.setStyleSheet("color: #AAAAAA; font-size: 13px; background: transparent; border: none;")
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
            # Scale to fit the available space in the label
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
    
    def resizeEvent(self, event):
        """Handle resize events to rescale images."""
        super().resizeEvent(event)
        if hasattr(self, 'current_pair') and self.current_pair:
            # Reload current pair to rescale images
            left_path, right_path = self.current_pair
            # Get current metadata from labels
            left_meta = {
                'filename': self.left_panel.filename_label.text().replace('Dateiname: ', ''),
                'date': self.left_panel.date_label.text().replace('Datum: ', ''),
                'time': self.left_panel.time_label.text().replace('Uhrzeit: ', ''),
                'camera': self.left_panel.camera_label.text().replace('Kamera: ', '')
            }
            right_meta = {
                'filename': self.right_panel.filename_label.text().replace('Dateiname: ', ''),
                'date': self.right_panel.date_label.text().replace('Datum: ', ''),
                'time': self.right_panel.time_label.text().replace('Uhrzeit: ', ''),
                'camera': self.right_panel.camera_label.text().replace('Kamera: ', '')
            }
            self.load_pair(left_path, right_path, left_meta, right_meta)
