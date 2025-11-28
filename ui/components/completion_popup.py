from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from pathlib import Path
import os


class CompletionPopup(QDialog):
    """Custom popup widget for displaying session completion with statistics and folder deletion options."""
    
    close_requested = pyqtSignal()
    open_source_requested = pyqtSignal()
    open_target_requested = pyqtSignal()
    show_deleted_requested = pyqtSignal()
    perm_delete_requested = pyqtSignal()
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the popup UI."""
        self.setFixedWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Content container (for styling)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)
        
        # Styling with drop shadow
        content.setStyleSheet("""
            QWidget {
                background-color: #2A2A2C;
                border: 1px solid #3A3A3C;
                border-radius: 12px;
            }
        """)
        
        # Add subtle drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        content.setGraphicsEffect(shadow)
        
        # Title
        title = QLabel("Alle Dateien wurden verarbeitet!")
        title.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)
        
        # Session name
        session_name = self.session.get('name', 'Unbenannt')
        session_label = QLabel(f"Session: {session_name}")
        session_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)
        session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(session_label)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("""
            QFrame {
                background-color: rgba(58, 58, 60, 0.4);
                border: none;
                max-height: 1px;
                min-height: 1px;
                margin: 8px 0px;
            }
        """)
        content_layout.addWidget(separator1)
        
        # Statistics section
        stat_data = self.calculate_stats()
        for item in stat_data:
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
                content_layout.addWidget(separator)
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
                
                content_layout.addLayout(row)
        
        # Separator before buttons
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("""
            QFrame {
                background-color: rgba(58, 58, 60, 0.4);
                border: none;
                max-height: 1px;
                min-height: 1px;
                margin: 8px 0px;
            }
        """)
        content_layout.addWidget(separator2)
        
        # Folder action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Open source folder button
        open_source_btn = QPushButton("Quellordner öffnen")
        open_source_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_source_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #252527;
                border: 1px solid #444;
            }
        """)
        open_source_btn.clicked.connect(self.open_source_requested.emit)
        buttons_layout.addWidget(open_source_btn)
        
        # Open target folder button
        open_target_btn = QPushButton("Zielordner öffnen")
        open_target_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_target_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #252527;
                border: 1px solid #444;
            }
        """)
        open_target_btn.clicked.connect(self.open_target_requested.emit)
        buttons_layout.addWidget(open_target_btn)
        
        # Deleted files row (two buttons side by side)
        deleted_row = QHBoxLayout()
        deleted_row.setSpacing(8)
        
        # Show deleted files button
        show_deleted_btn = QPushButton("Gelöschte anzeigen")
        show_deleted_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        show_deleted_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #252527;
                border: 1px solid #444;
            }
        """)
        show_deleted_btn.clicked.connect(self.show_deleted_requested.emit)
        deleted_row.addWidget(show_deleted_btn)
        
        # Permanently delete button
        perm_delete_btn = QPushButton("Endgültig löschen")
        perm_delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        perm_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 4px;
                font-weight: 500;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #252527;
                border: 1px solid #444;
            }
        """)
        perm_delete_btn.clicked.connect(self.perm_delete_requested.emit)
        deleted_row.addWidget(perm_delete_btn)
        
        buttons_layout.addLayout(deleted_row)
        
        # Close button
        close_btn = QPushButton("Schließen")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
        close_btn.clicked.connect(self.close_and_emit)
        buttons_layout.addWidget(close_btn)
        
        content_layout.addLayout(buttons_layout)
        
        layout.addWidget(content)
    
    def close_and_emit(self):
        """Close the popup and emit signal."""
        self.close_requested.emit()
        self.close()
    
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
