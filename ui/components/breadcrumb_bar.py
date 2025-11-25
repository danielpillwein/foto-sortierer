from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List


class BreadcrumbBar(QWidget):
    """
    Breadcrumb navigation bar component.
    Displays a clickable path with segments separated by arrows.
    Implements ellipsis rule for long paths.
    """
    breadcrumb_clicked = pyqtSignal(int)  # Emits index of clicked segment
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path_segments = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the breadcrumb bar UI."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Set fixed height as per spec
        self.setFixedHeight(32)
        
        # Background styling
        self.setStyleSheet("""
            BreadcrumbBar {
                background-color: transparent;
            }
        """)
    
    def set_path(self, path_segments: List[str]):
        """
        Update the breadcrumb display with new path segments.
        
        Args:
            path_segments: List of folder names representing the path
        """
        self.path_segments = path_segments
        self._rebuild_breadcrumbs()
    
    def clear(self):
        """Clear all breadcrumb segments."""
        self.path_segments = []
        self._rebuild_breadcrumbs()
    
    def _rebuild_breadcrumbs(self):
        """Rebuild the breadcrumb UI from current path segments with ellipsis rule."""
        # Clear existing widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.path_segments:
            # Show placeholder when empty
            placeholder = QLabel("Zielordner")
            placeholder.setStyleSheet("""
                color: #666;
                font-size: 13px;
                font-weight: 500;
            """)
            self.layout.addWidget(placeholder)
            return
        
        # Apply ellipsis rule if path is too long (>4 segments)
        # Always show: first, second-to-last, last
        # Replace middle segments with ellipsis
        display_segments = []
        segment_indices = []  # Track original indices for click handling
        
        if len(self.path_segments) > 4:
            # Show first segment (target root)
            display_segments.append(self.path_segments[0])
            segment_indices.append(0)
            
            # Add ellipsis placeholder
            display_segments.append("…")
            segment_indices.append(-1)  # -1 indicates ellipsis (not clickable)
            
            # Show second-to-last segment
            display_segments.append(self.path_segments[-2])
            segment_indices.append(len(self.path_segments) - 2)
            
            # Show last segment
            display_segments.append(self.path_segments[-1])
            segment_indices.append(len(self.path_segments) - 1)
        else:
            # Show all segments
            display_segments = self.path_segments.copy()
            segment_indices = list(range(len(self.path_segments)))
        
        # Create breadcrumb segments
        for i, (segment, original_idx) in enumerate(zip(display_segments, segment_indices)):
            if original_idx == -1:
                # Ellipsis - non-clickable gray tag
                ellipsis_label = QLabel(segment)
                ellipsis_label.setStyleSheet("""
                    QLabel {
                        background-color: #3A3A3D;
                        color: #888;
                        border: none;
                        padding: 4px 12px;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: 500;
                    }
                """)
                self.layout.addWidget(ellipsis_label)
            else:
                # Regular clickable segment button
                segment_btn = QPushButton(segment)
                segment_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                segment_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3A3A3D;
                        color: #E0E0E0;
                        border: none;
                        padding: 4px 12px;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #4A4A4D;
                        color: #FFFFFF;
                    }
                """)
                
                # Connect click handler with ORIGINAL index
                segment_btn.clicked.connect(lambda checked, idx=original_idx: self.breadcrumb_clicked.emit(idx))
                self.layout.addWidget(segment_btn)
            
            # Add arrow separator (except after last segment)
            if i < len(display_segments) - 1:
                arrow = QLabel(">")
                arrow.setStyleSheet("""
                    color: #666;
                    font-size: 13px;
                    font-weight: 300;
                """)
                self.layout.addWidget(arrow)
        
        # Add stretch to push breadcrumbs to the left
        self.layout.addStretch()
