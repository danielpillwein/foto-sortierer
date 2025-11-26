from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QTime
from PyQt6.QtGui import QIcon
from pathlib import Path
import time

class DuplicateScanScreen(QWidget):
    scan_completed = pyqtSignal(list)
    scan_cancelled = pyqtSignal()
    continue_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_complete = False
        self.total_files = 0
        self.current_progress = 0
        self.start_time = None
        self.elapsed_seconds = 0
        
        # Timer for updating elapsed time
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        self.load_stylesheet()
        self.init_ui()
        
    def load_stylesheet(self):
        style_path = Path("assets/style.qss")
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
    
    def init_ui(self):
        # Main layout - pure black background (#000000)
        self.setStyleSheet("background-color: #000000;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Center container (unchanged styling)
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
        center_layout.setContentsMargins(50, 40, 50, 40)
        center_layout.setSpacing(15)
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
        scan_title = QLabel("Duplikate werden gesucht")
        scan_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; border: none; background: transparent;")
        scan_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(scan_title)
        
        # Subtitle
        scan_subtitle = QLabel("Bitte warten Sie, während Ihre Dateien analysiert werden")
        scan_subtitle.setStyleSheet("font-size: 13px; color: #888888; border: none; background: transparent;")
        scan_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(scan_subtitle)
        
        center_layout.addSpacing(10)
        
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
        
        center_layout.addSpacing(10)
        
        # Time display (Laufzeit | Verbleibend) - above stats
        self.time_display = QLabel("Laufzeit: 00:00:00   |   Verbleibend: ~0:00")
        self.time_display.setStyleSheet("font-size: 14px; font-weight: bold; color: #CCCCCC; border: none; background: transparent;")
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.time_display)
        
        center_layout.addSpacing(5)
        
        # Stats row - transparent background, no borders
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        
        # Total files stat
        self.total_card = self.create_stat_item("0", "Dateien gesamt")
        stats_row.addWidget(self.total_card)
        
        # Deleted duplicates stat
        self.deleted_card = self.create_stat_item("0", "Gelöschte Duplikate", highlight=True)
        stats_row.addWidget(self.deleted_card)
        
        # Review duplicates stat
        self.review_card = self.create_stat_item("0", "Zu prüfen", highlight=True)
        stats_row.addWidget(self.review_card)
        
        center_layout.addLayout(stats_row)
        
        center_layout.addSpacing(10)
        
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
    
    def create_stat_item(self, value, label, highlight=False):
        """Create a stat item widget (no border, no background)."""
        item = QWidget()
        item.setStyleSheet("background: transparent; border: none;")
        
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(4)
        item_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_color = "#2D7DFF" if highlight else "#FFFFFF"
        value_label.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {value_color}; border: none; background: transparent;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #999999; border: none; background: transparent;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        item_layout.addWidget(value_label)
        item_layout.addWidget(text_label)
        
        # Store references for updates
        item.value_label = value_label
        item.text_label = text_label
        
        return item
    
    def update_progress(self, current: int, total: int, deleted: int = 0, to_review: int = 0, status: str = ""):
        """Update progress display."""
        self.current_progress = current
        self.total_files = total
        
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_percent.setText(f"{progress}%")
            
            # Update stats
            self.deleted_card.value_label.setText(f"{deleted:,}")
            self.review_card.value_label.setText(f"{to_review:,}")
            
            # Update time display
            self.update_time_display()
            
            # Check if complete
            if progress >= 100:
                self.set_complete()
    
    def set_total_files(self, total: int):
        """Set total number of files."""
        self.total_files = total
        self.total_card.value_label.setText(f"{total:,}")
    
    def start_timer(self):
        """Start the elapsed time timer."""
        self.start_time = time.time()
        self.elapsed_seconds = 0
        self.timer.start(1000)  # Update every second
    
    def update_timer(self):
        """Update elapsed time every second."""
        if self.start_time and not self.is_complete:
            self.elapsed_seconds = int(time.time() - self.start_time)
            self.update_time_display()
    
    def update_time_display(self):
        """Update the time display with elapsed and remaining time."""
        # Format elapsed time as HH:MM:SS
        hours = self.elapsed_seconds // 3600
        minutes = (self.elapsed_seconds % 3600) // 60
        seconds = self.elapsed_seconds % 60
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Calculate remaining time
        if self.current_progress > 0 and self.current_progress < self.total_files and self.elapsed_seconds > 0:
            avg_time_per_file = self.elapsed_seconds / self.current_progress
            remaining = self.total_files - self.current_progress
            remaining_seconds = int(remaining * avg_time_per_file)
            remaining_minutes = remaining_seconds // 60
            remaining_secs = remaining_seconds % 60
            remaining_str = f"~{remaining_minutes}:{remaining_secs:02d}"
            
            self.time_display.setText(f"Laufzeit: {elapsed_str}   |   Verbleibend: {remaining_str}")
        else:
            # When complete or just started
            if self.is_complete:
                self.time_display.setText(f"Laufzeit: {elapsed_str}")
            else:
                self.time_display.setText(f"Laufzeit: {elapsed_str}   |   Verbleibend: ~0:00")
    
    def set_complete(self):
        """Mark scan as complete and show continue button."""
        if not self.is_complete:  # Only execute once
            self.is_complete = True
            
            # Update elapsed time one last time
            if self.start_time:
                self.elapsed_seconds = int(time.time() - self.start_time)
            
            self.timer.stop()  # Stop the timer
            self.progress_bar.setValue(100)
            self.progress_percent.setText("100%")
            
            # Update time display to show only elapsed time
            hours = self.elapsed_seconds // 3600
            minutes = (self.elapsed_seconds % 3600) // 60
            seconds = self.elapsed_seconds % 60
            elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_display.setText(f"Laufzeit: {elapsed_str}")
            
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
