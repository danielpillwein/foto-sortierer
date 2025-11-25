from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QSplitter, QProgressBar, QLineEdit, QGridLayout,
    QMessageBox, QInputDialog, QGraphicsScene, QGraphicsView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPainter, QColor
from pathlib import Path
import os
import shutil

class SorterView(QWidget):
    """Main Sorter View Interface - 1:1 Mockup Implementation"""
    close_session_clicked = pyqtSignal()

    def __init__(self, session_manager, media_loader, exif_manager):
        super().__init__()
        self.session_manager = session_manager
        self.media_loader = media_loader
        self.exif_manager = exif_manager
        self.current_session_id = None
        self.current_file_index = 0
        self.files = []
        self.zoom_level = 1.0
        # Connect media loaded signal
        self.media_loader.image_loaded.connect(self.on_media_loaded)
        self.init_ui()

    # ---------------------------------------------------------------------
    # Keyboard handling
    # ---------------------------------------------------------------------
    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            self.move_to_folder_by_index(key - Qt.Key.Key_1)
        elif key == Qt.Key.Key_Delete:
            self.delete_current_file()
        elif key == Qt.Key.Key_Escape:
            self.close_session_clicked.emit()
        elif key == Qt.Key.Key_N:
            self.create_new_folder_dialog()
        elif key == Qt.Key.Key_Left:
            self.navigate_file(-1)
        elif key == Qt.Key.Key_Right:
            self.navigate_file(1)
        else:
            super().keyPressEvent(event)

    def move_to_folder_by_index(self, index):
        if not self.files or not self.current_session_id:
            return
        session = self.session_manager.sessions.get(self.current_session_id)
        if not session:
            return
        target_base = Path(session["target_path"])
        if not target_base.exists():
            return
        existing_folders = sorted([p for p in target_base.iterdir() if p.is_dir()])
        if index < len(existing_folders):
            self.move_current_file(str(existing_folders[index]))

    def navigate_file(self, delta):
        if not self.files:
            return
        new_index = self.current_file_index + delta
        if 0 <= new_index < len(self.files):
            self.current_file_index = new_index
            self.load_current_file()

    # ---------------------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------------------
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.init_header()
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setStyleSheet("QSplitter::handle { background-color: #2A2A2C; width: 1px; }")
        self.init_media_display()
        self.init_sidebar()
        self.main_layout.addWidget(self.content_splitter)

    def init_header(self):
        # Main container for header
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet("background-color: #131314;") # Dark background matching mockup
        
        main_layout = QVBoxLayout(header_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top row with controls
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(15)
        
        # Close button
        close_btn = QPushButton("X  Session schließen")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B2D31;
                color: #C0C0C0;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #35373C; color: #E0E0E0; }
        """)
        close_btn.clicked.connect(self.close_session_clicked.emit)
        top_layout.addWidget(close_btn)
        
        # Vertical Separator (Simple Pipe)
        separator = QLabel("|")
        separator.setStyleSheet("color: #444; font-size: 16px; font-weight: 300;")
        top_layout.addWidget(separator)
        
        # Session name
        self.session_name_label = QLabel("Session: -")
        self.session_name_label.setStyleSheet("color: #777; font-size: 13px;")
        top_layout.addWidget(self.session_name_label)
        
        top_layout.addStretch()
        
        # Progress label
        self.progress_label = QLabel("0 / 0 Medien")
        self.progress_label.setStyleSheet("color: #777; font-size: 13px;")
        top_layout.addWidget(self.progress_label)
        
        
        # Stats button
        stats_btn = QPushButton("  Details / Stats")
        stats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Load and set icon
        icon_path = Path(__file__).parent.parent / "assets" / "icons" / "stats.svg"
        if icon_path.exists():
            stats_btn.setIcon(QIcon(str(icon_path)))
            stats_btn.setIconSize(QPixmap(16, 16).size())
        
        stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B2D31;
                color: #C0C0C0;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover { 
                background-color: #35373C; 
                color: #E0E0E0;
                border-color: #444; 
            }
        """)
        top_layout.addWidget(stats_btn)
        
        main_layout.addLayout(top_layout)
        
        # Progress bar (at the bottom of header)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #1A1A1C; border: none; }
            QProgressBar::chunk { background-color: #2D7DFF; border-radius: 0px; }
        """)
        main_layout.addWidget(self.progress_bar)
        
        self.main_layout.addWidget(header_widget)

    def init_media_display(self):
        self.media_container = QWidget()
        self.media_container.setStyleSheet("background-color: #0E0E0F;")
        
        layout = QVBoxLayout(self.media_container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        # Top bar with info and controls
        top_bar = QHBoxLayout()
        
        # File Info
        self.file_info_label = QLabel("Keine Datei ausgewählt")
        self.file_info_label.setStyleSheet("color: #AAA; font-size: 13px;")
        top_bar.addWidget(self.file_info_label)
        
        top_bar.addStretch()
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(4)
        
        def create_icon_btn(icon_name, tooltip, callback):
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / icon_name
            if icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
                btn.setIconSize(QPixmap(16, 16).size())
            else:
                # Fallback text if icon missing
                text_map = {"zoom-in.svg": "+", "zoom-out.svg": "-", "maximize.svg": "⛶"}
                btn.setText(text_map.get(icon_name, "?"))
            
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: rgba(255,255,255,0.05); 
                    color: #AAA; 
                    border: none; 
                    border-radius: 4px; 
                }
                QPushButton:hover { 
                    background-color: rgba(255,255,255,0.1); 
                    color: #E0E0E0; 
                }
            """)
            btn.clicked.connect(callback)
            return btn

        self.zoom_in_btn = create_icon_btn("zoom-in.svg", "Vergrößern", self.zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = create_icon_btn("zoom-out.svg", "Verkleinern", self.zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        top_bar.addLayout(zoom_layout)
        layout.addLayout(top_bar)
        
        layout.addSpacing(15)
        
        # Graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        layout.addWidget(self.view)
        
        self.content_splitter.addWidget(self.media_container)

    def init_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("background-color: #1A1A1C; border-left: 1px solid #2A2A2C;")
        
        # Main layout for the sidebar
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(20)
        
        # 1. Info Panel (Fixed height)
        self.init_info_panel(sidebar_layout)
        
        # 2. Folder Panel (Expands)
        self.init_folder_panel(sidebar_layout)
        
        # 3. Action Panel (Fixed height)
        self.init_action_panel(sidebar_layout)
        
        self.content_splitter.addWidget(self.sidebar)

    def init_info_panel(self, parent_layout):
        # Section Title - keep this one QLabel for the header
        title = QLabel("DATEI-INFOS")
        title.setStyleSheet("color: #666; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        parent_layout.addWidget(title)
        
        # Content Layout
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Camera row
        cam_row = QHBoxLayout()
        cam_lbl_text = QLineEdit("Kamera:")
        cam_lbl_text.setReadOnly(True)
        cam_lbl_text.setFrame(False)
        cam_lbl_text.setStyleSheet("color: #666; font-size: 13px; border: none; background: transparent;")
        self.camera_value = QLineEdit("—")
        self.camera_value.setReadOnly(True)
        self.camera_value.setFrame(False)
        self.camera_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.camera_value.setStyleSheet("color: #E0E0E0; font-size: 13px; border: none; background: transparent;")
        self.camera_input = QLineEdit()
        self.camera_input.setPlaceholderText("z.B. iPhone 13 Pro")
        self.camera_input.setStyleSheet("""
            QLineEdit { background-color: #252527; color: #E0E0E0; border: 1px solid #444; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        """)
        self.camera_input.hide()
        cam_row.addWidget(cam_lbl_text)
        cam_row.addStretch()
        cam_row.addWidget(self.camera_value)
        cam_row.addWidget(self.camera_input)
        layout.addLayout(cam_row)
        
        # Date row
        date_row = QHBoxLayout()
        date_lbl_text = QLineEdit("Datum:")
        date_lbl_text.setReadOnly(True)
        date_lbl_text.setFrame(False)
        date_lbl_text.setStyleSheet("color: #666; font-size: 13px; border: none; background: transparent;")
        self.date_value = QLineEdit("—")
        self.date_value.setReadOnly(True)
        self.date_value.setFrame(False)
        self.date_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.date_value.setStyleSheet("color: #E0E0E0; font-size: 13px; border: none; background: transparent;")
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("DD.MM.YYYY")
        self.date_input.setStyleSheet("""
            QLineEdit { background-color: #252527; color: #E0E0E0; border: 1px solid #444; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        """)
        self.date_input.hide()
        date_row.addWidget(date_lbl_text)
        date_row.addStretch()
        date_row.addWidget(self.date_value)
        date_row.addWidget(self.date_input)
        layout.addLayout(date_row)
        
        # Time row
        time_row = QHBoxLayout()
        time_lbl_text = QLineEdit("Uhrzeit:")
        time_lbl_text.setReadOnly(True)
        time_lbl_text.setFrame(False)
        time_lbl_text.setStyleSheet("color: #666; font-size: 13px; border: none; background: transparent;")
        self.time_value = QLineEdit("—")
        self.time_value.setReadOnly(True)
        self.time_value.setFrame(False)
        self.time_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.time_value.setStyleSheet("color: #E0E0E0; font-size: 13px; border: none; background: transparent;")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("HH:MM:SS")
        self.time_input.setStyleSheet(self.date_input.styleSheet())
        self.time_input.hide()
        time_row.addWidget(time_lbl_text)
        time_row.addStretch()
        time_row.addWidget(self.time_value)
        time_row.addWidget(self.time_input)
        layout.addLayout(time_row)
        
        
        # Edit/Save button
        self.edit_btn = QPushButton("  Infos bearbeiten")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Load and set icon
        edit_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "edit.svg"
        if edit_icon_path.exists():
            self.edit_btn.setIcon(QIcon(str(edit_icon_path)))
            self.edit_btn.setIconSize(QPixmap(16, 16).size())
        
        self.edit_btn.setStyleSheet("""
            QPushButton { 
                background-color: #2D7DFF; 
                color: white; 
                border: none; 
                padding: 10px; 
                border-radius: 6px; 
                font-weight: 500; 
                font-size: 13px; 
            }
            QPushButton:hover { background-color: #3B82F6; }
        """)
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.is_editing = False
        layout.addWidget(self.edit_btn)
        
        parent_layout.addLayout(layout)
        parent_layout.addSpacing(10)

    def init_folder_panel(self, parent_layout):
        title = QLabel("ZIELORDNER")
        title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        parent_layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #1A1A1C; width: 8px; }
            QScrollBar::handle:vertical { background: #333; border-radius: 4px; }
        """)
        
        self.folder_list_content = QWidget()
        self.folder_list_content.setStyleSheet("background: transparent;")
        self.folder_list_layout = QGridLayout(self.folder_list_content)
        self.folder_list_layout.setSpacing(8)
        self.folder_list_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.folder_list_content)
        parent_layout.addWidget(scroll, 1) # Stretch factor 1 to take remaining space
        parent_layout.addSpacing(10)

    def init_action_panel(self, parent_layout):
        title = QLabel("AKTIONEN")
        title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        parent_layout.addWidget(title)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Delete button
        self.delete_btn = QPushButton()
        self.delete_btn.setFixedHeight(44)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_current_file)
        
        delete_layout = QHBoxLayout(self.delete_btn)
        delete_layout.setContentsMargins(16, 0, 16, 0)
        delete_layout.setSpacing(12)
        
        # Delete Icon
        del_icon_lbl = QLabel()
        del_icon_lbl.setStyleSheet("background: transparent; border: none;")
        del_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "trash.svg"
        if del_icon_path.exists():
            pixmap = QPixmap(str(del_icon_path))
            del_icon_lbl.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            del_icon_lbl.setText("🗑️")
        delete_layout.addWidget(del_icon_lbl)
        
        # Delete Text
        del_text_lbl = QLabel("Löschen")
        del_text_lbl.setStyleSheet("color: white; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        delete_layout.addWidget(del_text_lbl)
        
        delete_layout.addStretch()
        
        # Delete Shortcut Badge
        del_badge = QLabel("Del")
        del_badge.setFixedSize(32, 24)
        del_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        del_badge.setStyleSheet("background-color: #7F1D1D; color: #EEE; border-radius: 4px; font-size: 11px; border: none;")
        delete_layout.addWidget(del_badge)
        
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                border-radius: 8px;
                border: none;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:pressed {
                background-color: #B91C1C;
            }
        """)
        layout.addWidget(self.delete_btn)
        
        # New folder button
        self.new_folder_btn = QPushButton()
        self.new_folder_btn.setFixedHeight(44)
        self.new_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_folder_btn.clicked.connect(self.create_new_folder_dialog)
        
        nf_layout = QHBoxLayout(self.new_folder_btn)
        nf_layout.setContentsMargins(16, 0, 16, 0)
        nf_layout.setSpacing(12)
        # Removed AlignCenter to match Delete button (Left aligned content)
        
        # New Folder Icon
        nf_icon_lbl = QLabel()
        nf_icon_lbl.setStyleSheet("background: transparent; border: none;")
        nf_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "folder-plus.svg"
        if nf_icon_path.exists():
            pixmap = QPixmap(str(nf_icon_path))
            nf_icon_lbl.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            nf_icon_lbl.setText("➕")
        nf_layout.addWidget(nf_icon_lbl)
        
        # New Folder Text
        nf_text_lbl = QLabel("Neuer Ordner")
        nf_text_lbl.setStyleSheet("color: white; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        nf_layout.addWidget(nf_text_lbl)
        
        nf_layout.addStretch()
        
        # New Folder Shortcut Badge
        nf_badge = QLabel("N")
        nf_badge.setFixedSize(32, 24)
        nf_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nf_badge.setStyleSheet("background-color: rgba(0,0,0,0.2); color: #EEE; border-radius: 4px; font-size: 11px; border: none;")
        nf_layout.addWidget(nf_badge)
        
        self.new_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                border-radius: 8px;
                border: none;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        layout.addWidget(self.new_folder_btn)
        
        parent_layout.addLayout(layout)

    def colorize_pixmap(self, pixmap, color_hex):
        """Colorize a pixmap with the given color."""
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

    def populate_folder_list(self, target_path):
        # Clear existing items
        while self.folder_list_layout.count():
            item = self.folder_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        target_base = Path(target_path)
        if not target_base.exists():
            return

        # Get subdirectories
        folders = sorted([p for p in target_base.iterdir() if p.is_dir()])
        
        for i, folder in enumerate(folders):
            if i >= 9: break # Limit to 9 shortcuts
            
            btn = QPushButton()
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Use a lambda that captures the current folder path
            btn.clicked.connect(lambda checked, p=str(folder): self.move_current_file(p))
            
            layout = QHBoxLayout(btn)
            layout.setContentsMargins(12, 0, 12, 0)
            layout.setSpacing(10)
            
            # Icon
            icon_lbl = QLabel()
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "folder.svg"
            if icon_path.exists():
                 pixmap = QPixmap(str(icon_path))
                 # Colorize the icon to #EAB308 (Yellow)
                 colored_pixmap = self.colorize_pixmap(pixmap, "#EAB308")
                 icon_lbl.setPixmap(colored_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                 icon_lbl.setText("📁")
            layout.addWidget(icon_lbl)
            
            # Name
            name_lbl = QLabel(folder.name)
            name_lbl.setStyleSheet("color: #E0E0E0; font-size: 13px; border: none; background: transparent;")
            layout.addWidget(name_lbl)
            
            layout.addStretch()
            
            # Shortcut
            shortcut_lbl = QLabel(str(i + 1))
            shortcut_lbl.setFixedSize(24, 24)
            shortcut_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Updated background color to #374151 as requested
            shortcut_lbl.setStyleSheet("background-color: #374151; color: #E0E0E0; border-radius: 4px; font-size: 11px; border: none;")
            layout.addWidget(shortcut_lbl)
            
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
            
            # Add to grid layout (2 columns)
            row = i // 2
            col = i % 2
            self.folder_list_layout.addWidget(btn, row, col)

    # ---------------------------------------------------------------------
    # Image handling and zoom
    # ---------------------------------------------------------------------
    def display_image(self, pixmap):
        self.scene.clear()
        if pixmap and not pixmap.isNull():
            self.scene.addPixmap(pixmap)
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.scene.addText("No Image", QFont("Arial", 20)).setDefaultTextColor(Qt.GlobalColor.gray)

    def zoom_in(self):
        self.view.scale(1.2, 1.2)
        self.zoom_level *= 1.2

    def zoom_out(self):
        if self.zoom_level > 1.0:
            self.view.scale(1/1.2, 1/1.2)
            self.zoom_level /= 1.2

    # ---------------------------------------------------------------------
    # EXIF edit handling (placeholders)
    # ---------------------------------------------------------------------
    def toggle_edit_mode(self):
        # Toggle edit mode for EXIF fields
        self.is_editing = not self.is_editing
        
        if self.is_editing:
            # Entering edit mode: prefill inputs with current values
            # Camera: use as-is
            current_camera = self.camera_value.text()
            if current_camera != "—":
                self.camera_input.setText(current_camera)
            else:
                self.camera_input.clear()
            
            # Date: convert from DD.MM.YYYY to input format
            current_date = self.date_value.text()
            if current_date != "—":
                self.date_input.setText(current_date)
            else:
                self.date_input.clear()
            
            # Time: use as-is
            current_time = self.time_value.text()
            if current_time != "—":
                self.time_input.setText(current_time)
            else:
                self.time_input.clear()
            
            # Update button to show save icon and text
            save_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "save.svg"
            if save_icon_path.exists():
                self.edit_btn.setIcon(QIcon(str(save_icon_path)))
            self.edit_btn.setText("  Speichern")
        else:
            # Exiting edit mode: save changes
            self.save_exif_changes()
            
            # Update button to show edit icon and text
            edit_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "edit.svg"
            if edit_icon_path.exists():
                self.edit_btn.setIcon(QIcon(str(edit_icon_path)))
            self.edit_btn.setText("  Infos bearbeiten")
        
        # Toggle visibility of value labels and input fields
        self.camera_value.setVisible(not self.is_editing)
        self.date_value.setVisible(not self.is_editing)
        self.time_value.setVisible(not self.is_editing)
        self.camera_input.setVisible(self.is_editing)
        self.date_input.setVisible(self.is_editing)
        self.time_input.setVisible(self.is_editing)

    def save_exif_changes(self):
        """Save EXIF changes from input fields to the current file."""
        if not self.files or self.current_file_index >= len(self.files):
            return
        
        current_file = self.files[self.current_file_index]
        
        # Prepare new data dictionary
        new_data = {}
        
        # Parse camera model
        camera_text = self.camera_input.text().strip()
        if camera_text:
            new_data["camera_model"] = camera_text
        
        # Parse date and time
        date_text = self.date_input.text().strip()
        time_text = self.time_input.text().strip()
        
        if date_text and time_text:
            try:
                # Parse DD.MM.YYYY and HH:MM:SS
                date_parts = date_text.split('.')
                time_parts = time_text.split(':')
                
                if len(date_parts) == 3 and len(time_parts) == 3:
                    day, month, year = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                    hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
                    
                    from datetime import datetime
                    new_data["date_taken"] = datetime(year, month, day, hour, minute, second)
            except (ValueError, IndexError) as e:
                # Invalid date/time format - skip updating
                pass
        
        # Save to EXIF if we have any data to update
        if new_data:
            success = self.exif_manager.update_metadata(current_file, new_data)
            if success:
                # Update the displayed values with the saved data
                if "camera_model" in new_data:
                    self.camera_value.setText(new_data["camera_model"])
                if "date_taken" in new_data:
                    self.date_value.setText(new_data["date_taken"].strftime("%d.%m.%Y"))
                    self.time_value.setText(new_data["date_taken"].strftime("%H:%M:%S"))

    # ---------------------------------------------------------------------
    # Media loading and file operations (basic implementations)
    # ---------------------------------------------------------------------
    def on_media_loaded(self, file_path: str):
        """Handle the signal when a new media file is loaded.
        Loads the image and updates the file info label and EXIF data.
        """
        pixmap = QPixmap(file_path)
        self.display_image(pixmap)
        
        file_name = Path(file_path).name
        size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        
        dimensions = f"{pixmap.width()}x{pixmap.height()}" if not pixmap.isNull() else "Unknown"
        
        self.file_info_label.setText(f"{file_name} • {size_mb:.1f} MB • {dimensions}")
        
        # Read and display EXIF data
        try:
            metadata = self.exif_manager.get_metadata(file_path)
            
            # Update camera
            camera = metadata.get("camera_model", "—")
            self.camera_value.setText(camera if camera != "Unknown" else "—")
            
            # Update date and time
            date_taken = metadata.get("date_taken")
            if date_taken:
                # Format: DD.MM.YYYY
                date_str = date_taken.strftime("%d.%m.%Y")
                time_str = date_taken.strftime("%H:%M:%S")
                self.date_value.setText(date_str)
                self.time_value.setText(time_str)
            else:
                self.date_value.setText("—")
                self.time_value.setText("—")
        except Exception as e:
            # If EXIF reading fails, show placeholder
            self.camera_value.setText("—")
            self.date_value.setText("—")
            self.time_value.setText("—")

    def delete_current_file(self):
        """Moves the current file to a 'gelöscht_{session_id}' folder in the user's home directory."""
        if not self.files or self.current_file_index >= len(self.files):
            return
            
        if not self.current_session_id:
            return
            
        # Use the same logic as DuplicateDetector for the trash folder
        # ~/Foto-Sortierer/gelöscht_{session_id}
        deleted_dir = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{self.current_session_id}"))
        
        # Ensure deleted directory exists
        try:
            deleted_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Papierkorb-Ordner nicht erstellen:\n{str(e)}")
            return
            
        # Reuse move logic by moving to the deleted folder
        self.move_current_file(str(deleted_dir))

    def create_new_folder_dialog(self):
        """Opens a dialog to create a new folder in the target directory."""
        if not self.current_session_id:
            return
            
        session = self.session_manager.sessions.get(self.current_session_id)
        if not session:
            return
            
        target_base = Path(session["target_path"])
        if not target_base.exists():
            QMessageBox.warning(self, "Fehler", "Zielverzeichnis existiert nicht.")
            return
            
        folder_name, ok = QInputDialog.getText(self, "Neuer Ordner", "Name des neuen Ordners:")
        
        if ok and folder_name:
            # Sanitize folder name (basic)
            safe_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_name:
                QMessageBox.warning(self, "Ungültiger Name", "Bitte geben Sie einen gültigen Ordnernamen ein.")
                return
                
            new_folder_path = target_base / safe_name
            
            try:
                if new_folder_path.exists():
                     QMessageBox.warning(self, "Fehler", "Ein Ordner mit diesem Namen existiert bereits.")
                     return
                     
                new_folder_path.mkdir(parents=True)
                # Refresh folder list
                self.populate_folder_list(str(target_base))
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Ordners:\n{str(e)}")

    def move_current_file(self, target_folder: str):
        """Moves the current file to the target folder."""
        if not self.files or self.current_file_index >= len(self.files):
            return
            
        current_file_path = Path(self.files[self.current_file_index])
        if not current_file_path.exists():
            QMessageBox.warning(self, "Fehler", "Die Datei existiert nicht mehr.")
            # Remove from list and refresh
            self.files.pop(self.current_file_index)
            self.load_current_file()
            return

        target_dir = Path(target_folder)
        if not target_dir.exists():
            QMessageBox.warning(self, "Fehler", f"Der Zielordner existiert nicht:\n{target_folder}")
            return

        target_path = target_dir / current_file_path.name
        
        # Handle filename collision
        if target_path.exists():
            base = target_path.stem
            suffix = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{base}_{counter}{suffix}"
                counter += 1

        try:
            shutil.move(str(current_file_path), str(target_path))
            
            # Update internal state
            self.files.pop(self.current_file_index)
            
            # Update session stats
            if self.current_session_id:
                session = self.session_manager.sessions.get(self.current_session_id)
                if session:
                    session["processed_files"] = session.get("processed_files", 0) + 1
                    self.session_manager.save_sessions()
                    
                    # Update progress bar
                    total = session.get("total_files", len(self.files) + session["processed_files"])
                    self.update_progress(session["processed_files"], total)
            
            # Load next file (index stays same because we popped the current one)
            # But if we were at the last item, we need to adjust
            if self.current_file_index >= len(self.files):
                self.current_file_index = max(0, len(self.files) - 1)
                
            self.load_current_file()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Verschieben der Datei:\n{str(e)}")

    def load_session(self, session_id):
        """Loads a session and initializes the view with files."""
        self.current_session_id = session_id
        session = self.session_manager.sessions.get(session_id)
        if not session:
            return

        self.session_name_label.setText(f"Session: {session.get('name', 'Unbenannt')}")
        
        # Load files
        from core.file_manager import FileManager
        file_manager = FileManager()
        media_files = file_manager.scan_directory(session["source_path"])
        self.files = [f["path"] for f in media_files]
        
        # Update session with total files if not set
        if session.get("total_files", 0) == 0:
            session["total_files"] = len(self.files)
            self.session_manager.save_sessions()
        
        # Populate folder list
        self.populate_folder_list(session["target_path"])
        
        # Update progress
        total = session.get("total_files", len(self.files))
        processed = session.get("processed_files", 0)
        self.update_progress(processed, total)
        
        # Reset index and load first file
        self.current_file_index = 0
        self.load_current_file()

    def update_progress(self, processed, total):
        """Updates the progress bar and label."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(processed)
            self.progress_label.setText(f"{processed:,} / {total:,} Medien")
        else:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_label.setText("0 / 0 Medien")

    def load_current_file(self):
        """Load and display the current file based on self.current_file_index."""
        if not self.files:
            self.display_image(None)
            self.file_info_label.setText("Keine Dateien vorhanden")
            return
            
        if 0 <= self.current_file_index < len(self.files):
            file_path = self.files[self.current_file_index]
            self.on_media_loaded(file_path)
            
            # Update progress display from session data
            if self.current_session_id:
                session = self.session_manager.sessions.get(self.current_session_id)
                if session:
                    total = session.get("total_files", len(self.files))
                    processed = session.get("processed_files", 0)
                    self.update_progress(processed, total)
        else:
             # Fallback if index is out of bounds (e.g. after deletion)
            if self.files:
                self.current_file_index = 0
                self.load_current_file()
            else:
                self.display_image(None)
