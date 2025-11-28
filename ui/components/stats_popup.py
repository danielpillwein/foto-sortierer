from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from pathlib import Path
import os


class StatsPopup(QFrame):
    """Custom popup widget for displaying session statistics."""
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the popup UI."""
        self.setFixedWidth(280)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Styling with drop shadow
        self.setStyleSheet("""
            QFrame {
                background-color: #2A2A2C;
                border: 1px solid #3A3A3C;
                border-radius: 8px;
            }
        """)
        

        
        # Add stat rows with left-aligned labels and right-aligned values
        stat_data = self.calculate_stats()
        for item in stat_data:
            # Check if this is a separator
            if item == "separator":
                # Add horizontal ruler
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("""
                    QFrame {
                        background-color: rgba(58, 58, 60, 0.4);
                        border: none;
                        max-height: 1px;
                        min-height: 1px;
                        margin: 4px 0px;
                    }
                """)
                layout.addWidget(separator)
            else:
                # Regular stat row
                label_text, value_text = item
                row = QHBoxLayout()
                row.setSpacing(12)
                
                # Label (left-aligned)
                label = QLabel(label_text)
                label.setStyleSheet("""
                    QLabel {
                        color: #AAAAAA;
                        font-size: 13px;
                        background: transparent;
                        border: none;
                    }
                """)
                
                # Value (right-aligned)
                value = QLabel(value_text)
                value.setStyleSheet("""
                    QLabel {
                        color: #E0E0E0;
                        font-size: 13px;
                        font-weight: bold;
                        background: transparent;
                        border: none;
                    }
                """)
                value.setAlignment(Qt.AlignmentFlag.AlignRight)
                
                row.addWidget(label)
                row.addStretch()
                row.addWidget(value)
                
                layout.addLayout(row)
    
    def calculate_stats(self):
        """Calculate all statistics for the session."""
        session_id = self.session.get("id")
        
        # Get file counts
        initial_count = self.session.get("initial_filecount", 0)
        
        # 1. Ursprünglich (show initial count)
        urspruenglich = ("Ursprünglich:", f"{initial_count:,}")
        
        # 2. Gelöscht (read from session data)
        deleted_count = self.session.get("deleted_count", 0)
        geloescht = ("Gelöscht:", f"{deleted_count:,}")
        
        # 3. Freier Speicher (read from session data)
        freed_size = self.session.get("deleted_size_bytes", 0)
        freed_formatted = self.format_size(freed_size)
        freier_speicher = ("Freier Speicher:", freed_formatted)
        
        # 4. Sortiert (read from session data)
        sorted_count = self.session.get("sorted_files", 0)
        # Percentages based on initial_filecount
        sorted_percent = round((sorted_count / initial_count * 100)) if initial_count > 0 else 0
        sortiert = ("Sortiert:", f"{sorted_count:,} ({sorted_percent}%)")
        
        # 5. Noch zu sortieren (initial - sorted - deleted)
        remaining = initial_count - sorted_count - deleted_count
        remaining = max(0, remaining)  # Ensure non-negative
        remaining_percent = round((remaining / initial_count * 100)) if initial_count > 0 else 0
        noch_zu_sortieren = ("Noch zu sortieren:", f"{remaining:,} ({remaining_percent}%)")
        
        # 6. Geschätzte Restdauer (dummy)
        geschaetzt = ("Geschätzte Restdauer:", "bald verfügbar")
        
        # Return as list of tuples (label, value) with separators
        return [
            urspruenglich,
            sortiert,
            noch_zu_sortieren,
            "separator",
            geloescht,
            freier_speicher,
            "separator",
            geschaetzt
        ]
    
    def count_files_in_folder(self, folder_path):
        """Count all files recursively in a folder."""
        if not folder_path.exists():
            return 0
        
        count = 0
        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    count += 1
        except (PermissionError, OSError):
            pass
        
        return count
    
    def get_folder_size(self, folder_path):
        """Calculate total size of all files in folder (in bytes)."""
        if not folder_path.exists():
            return 0
        
        total_size = 0
        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass
        
        return total_size
    
    def format_size(self, bytes_size):
        """Format size with smart unit selection (no decimals, whole numbers only)."""
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            kb = round(bytes_size / 1024)
            return f"{kb} KB"
        elif bytes_size < 1024 * 1024 * 1024:
            mb = round(bytes_size / (1024 * 1024))
            return f"{mb} MB"
        else:
            gb = round(bytes_size / (1024 * 1024 * 1024))
            return f"{gb} GB"
