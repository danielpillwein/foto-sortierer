from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from pathlib import Path

class DuplicateScanScreen(QWidget):
    scan_completed = pyqtSignal(list)
    scan_cancelled = pyqtSignal()
    continue_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_complete = False
        self.total_files = 0
        self.load_stylesheet()
        self.init_ui()
        
    def load_stylesheet(self):
        style_path = Path("assets/style.qss")
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
    
    def init_ui(self):
        # Main layout - full screen dark background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Center container
        center_container = QWidget()
        center_container.setFixedSize(800, 520)
        center_container.setStyleSheet("""
            QWidget {
                background-color: #1A1A1C;
                border-radius: 12px;
                border: 1px solid #2A2A2C;
            }
        """)
        
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(60, 60, 60, 60)
        center_layout.setSpacing(25)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Search icon
        icon_container = QLabel()
        icon_container.setFixedSize(80, 80)
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setStyleSheet("""
            QLabel {
                background-color: #2D7DFF;
                border-radius: 40px;
                border: none;
            }
        """)
        
        # Load SVG icon
        icon_label = QLabel(icon_container)
        icon_pixmap = QIcon("assets/icons/search.svg").pixmap(48, 48)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")
        icon_label.setGeometry(16, 16, 48, 48)
        
        center_layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Title
        scan_title = QLabel("Dubletten werden gesucht")
        scan_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; border: none; background: transparent;")
        scan_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(scan_title)
        
        # Subtitle
        scan_subtitle = QLabel("Bitte warten Sie, während Ihre Dateien analysiert werden")
        scan_subtitle.setStyleSheet("font-size: 13px; color: #888888; border: none; background: transparent;")
        scan_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(scan_subtitle)
        
        center_layout.addSpacing(15)
        
        # Progress section
        progress_container = QVBoxLayout()
        progress_container.setSpacing(10)
        
        # Progress header
        progress_header = QHBoxLayout()
        progress_label = QLabel("Fortschritt")
        progress_label.setStyleSheet("font-size: 13px; color: #AAAAAA; border: none; background: transparent;")
        
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("font-size: 13px; font-weight: bold; color: #2D7DFF; border: none; background: transparent;")
        
        progress_header.addWidget(progress_label)
        progress_header.addStretch()
        progress_header.addWidget(self.progress_percent)
        
        progress_container.addLayout(progress_header)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2A2A2C;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #2D7DFF;
                border-radius: 4px;
            }
        """)
        progress_container.addWidget(self.progress_bar)
        
        center_layout.addLayout(progress_container)
        
        center_layout.addSpacing(15)
        
        # Stats cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        # Total files card
        self.total_card = self.create_stat_card("0", "Dateien gesamt")
        stats_row.addWidget(self.total_card)
        
        # Deleted duplicates card
        self.deleted_card = self.create_stat_card("0", "Gelöschte Dubletten", highlight=True)
        stats_row.addWidget(self.deleted_card)
        
        # Review duplicates card
        self.review_card = self.create_stat_card("0", "Zu prüfen", highlight=True)
        stats_row.addWidget(self.review_card)
        
        # Time remaining card
        self.time_card = self.create_stat_card("~0:00", "Verbleibende Zeit")
        stats_row.addWidget(self.time_card)
        
        center_layout.addLayout(stats_row)
        
        center_layout.addSpacing(15)
        
        # Action button
        self.action_btn = QPushButton("Scan abbrechen")
        self.action_btn.setFixedHeight(45)
        self.action_btn.setFixedWidth(180)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A2A2C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        self.action_btn.clicked.connect(self.on_action_clicked)
        center_layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        main_layout.addWidget(center_container)
    
    def create_stat_card(self, value, label, highlight=False):
        """Create a stat card widget."""
        card = QFrame()
        card.setFixedSize(180, 85) # Slightly smaller to fit 4 cards
        card.setStyleSheet("""
            QFrame {
                background-color: #0E0E0F;
                border-radius: 8px;
                border: 1px solid #2A2A2C;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(4)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_color = "#2D7DFF" if highlight else "#FFFFFF"
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {value_color}; border: none; background: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 11px; color: #888888; border: none; background: transparent;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(text_label)
        
        # Store references for updates
        card.value_label = value_label
        card.text_label = text_label
        
        return card
    
    def update_progress(self, current: int, total: int, deleted: int = 0, to_review: int = 0, status: str = ""):
        """Update progress display."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_percent.setText(f"{progress}%")
            
            # Update stats
            self.deleted_card.value_label.setText(f"{deleted:,}")
            self.review_card.value_label.setText(f"{to_review:,}")
            
            # Estimate remaining time
            if current > 0 and current < total:
                avg_time_per_file = 0.1
                remaining = total - current
                remaining_seconds = int(remaining * avg_time_per_file)
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                self.time_card.value_label.setText(f"~{minutes}:{seconds:02d}")
    
    def set_total_files(self, total: int):
        """Set total number of files."""
        self.total_files = total
        self.total_card.value_label.setText(f"{total:,}")
    
    def set_complete(self):
        """Mark scan as complete and show continue button."""
        self.is_complete = True
        self.progress_bar.setValue(100)
        self.progress_percent.setText("100%")
        self.action_btn.setText("Weiter")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
    
    def on_action_clicked(self):
        """Handle action button click."""
        if self.is_complete:
            self.continue_clicked.emit()
        else:
            self.scan_cancelled.emit()
