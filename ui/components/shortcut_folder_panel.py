from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor
from pathlib import Path
from typing import List


class ShortcutFolderPanel(QWidget):
    """
    Folder grid panel component with shortcut support.
    Displays folders in a 2-column grid with shortcuts 1-9 for the first 9 folders.
    """
    folder_clicked = pyqtSignal(Path)  # Emits path of clicked folder
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folders = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the folder panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { 
                background: transparent; 
                border: none; 
            }
            QScrollBar:vertical { 
                background: #1A1A1C; 
                width: 8px; 
            }
            QScrollBar::handle:vertical { 
                background: #333; 
                border-radius: 4px; 
            }
        """)
        
        # Create content widget for grid
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        
        # Create grid layout (2 columns)
        self.grid_layout = QGridLayout(self.content_widget)
        self.grid_layout.setSpacing(12)  # Gap between cards
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)
    
    def set_folders(self, folders: List[Path]):
        """
        Populate the panel with folder cards.
        
        Args:
            folders: List of Path objects representing folders to display
        """
        self.folders = folders
        self._rebuild_grid()
    
    def clear(self):
        """Remove all folder cards."""
        self.folders = []
        self._rebuild_grid()
    
    def _rebuild_grid(self):
        """Rebuild the folder grid from current folders list."""
        # Clear existing widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.folders:
            # Show placeholder when empty
            placeholder = QLabel("Keine Unterordner")
            placeholder.setStyleSheet("""
                color: #666;
                font-size: 13px;
                padding: 20px;
            """)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(placeholder, 0, 0, 1, 2)
            return
        
        # Create folder cards
        for i, folder in enumerate(self.folders):
            card = self._create_folder_card(folder, i)
            
            # Add to grid (2 columns)
            row = i // 2
            col = i % 2
            self.grid_layout.addWidget(card, row, col)
    
    def _create_folder_card(self, folder: Path, index: int) -> QPushButton:
        """
        Create a single folder card button.
        
        Args:
            folder: Path object for the folder
            index: Index in the list (for shortcut badge)
            
        Returns:
            QPushButton configured as a folder card
        """
        from PyQt6.QtWidgets import QHBoxLayout
        
        btn = QPushButton()
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Connect click handler
        btn.clicked.connect(lambda: self.folder_clicked.emit(folder))
        
        # Create card layout
        content_layout = QHBoxLayout(btn)
        content_layout.setContentsMargins(12, 0, 12, 0)
        content_layout.setSpacing(10)
        
        # Folder icon (yellow)
        icon_lbl = QLabel()
        icon_path = Path(__file__).parent.parent / "assets" / "icons" / "folder.svg"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            # Colorize to yellow
            colored_pixmap = self._colorize_pixmap(pixmap, "#EAB308")
            icon_lbl.setPixmap(colored_pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_lbl.setText("📁")
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        content_layout.addWidget(icon_lbl)
        
        # Folder name
        name_lbl = QLabel(folder.name)
        name_lbl.setStyleSheet("color: #E0E0E0; font-size: 13px; border: none; background: transparent;")
        content_layout.addWidget(name_lbl)
        
        content_layout.addStretch()
        
        # Shortcut badge (only for first 9)
        if index < 9:
            shortcut_lbl = QLabel(str(index + 1))
            shortcut_lbl.setFixedSize(24, 24)
            shortcut_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            shortcut_lbl.setStyleSheet("""
                background-color: #374151; 
                color: #E0E0E0; 
                border-radius: 4px; 
                font-size: 11px; 
                border: none;
            """)
            content_layout.addWidget(shortcut_lbl)
        
        # Card styling
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0F0F0F;
                border: 1px solid #333;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #444;
            }
        """)
        
        return btn
    
    def _colorize_pixmap(self, pixmap: QPixmap, color_hex: str) -> QPixmap:
        """
        Colorize a pixmap with the given color.
        
        Args:
            pixmap: Source pixmap
            color_hex: Hex color string (e.g., "#EAB308")
            
        Returns:
            Colorized pixmap
        """
        if pixmap.isNull():
            return pixmap
        
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(colored_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Draw the original pixmap
        painter.drawPixmap(0, 0, pixmap)
        
        # Fill with color using SourceIn composition mode (keeps alpha of original)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), QColor(color_hex))
        painter.end()
        
        return colored_pixmap
