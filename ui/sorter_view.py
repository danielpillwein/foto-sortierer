from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QSplitter, QProgressBar, QLineEdit, QGridLayout,
    QMessageBox, QInputDialog, QGraphicsScene, QGraphicsView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPainter
from pathlib import Path
import os

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
        header_widget.setStyleSheet("background-color: #1A1A1C; border-bottom: 1px solid #2A2A2C;")
        
        main_layout = QVBoxLayout(header_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top row with controls
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(20)
        
        # Close button
        close_btn = QPushButton("× Session schließen")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #AAA;
                border: 1px solid #333;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #252527; color: #E0E0E0; border-color: #555; }
        """)
        close_btn.clicked.connect(self.close_session_clicked.emit)
        top_layout.addWidget(close_btn)
        
        # Session name
        self.session_name_label = QLabel("Session: -")
        self.session_name_label.setStyleSheet("color: #888; font-size: 13px;")
        top_layout.addWidget(self.session_name_label)
        
        top_layout.addStretch()
        
        # Progress label
        self.progress_label = QLabel("0 / 0 Medien")
        self.progress_label.setStyleSheet("color: #888; font-size: 13px;")
        top_layout.addWidget(self.progress_label)
        
        # Stats button
        stats_btn = QPushButton("📊 Details / Stats")
        stats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stats_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #AAA;
                border: 1px solid #333;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #252527; color: #E0E0E0; border-color: #555; }
        """)
        top_layout.addWidget(stats_btn)
        
        main_layout.addLayout(top_layout)
        
        # Progress bar (at the bottom of header)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: transparent; border: none; }
            QProgressBar::chunk { background-color: #2D7DFF; }
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
        # Section Title
        title = QLabel("DATEI-INFOS")
        title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        parent_layout.addWidget(title)
        
        # Content Layout
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Camera row
        cam_row = QHBoxLayout()
        cam_lbl = QLabel("Kamera:")
        cam_lbl.setStyleSheet("color: #888; font-size: 13px;")
        cam_val = QLabel("iPhone 13 Pro")
        cam_val.setStyleSheet("color: #E0E0E0; font-size: 13px;")
        cam_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        cam_row.addWidget(cam_lbl)
        cam_row.addStretch()
        cam_row.addWidget(cam_val)
        layout.addLayout(cam_row)
        
        # Date row
        date_row = QHBoxLayout()
        date_lbl = QLabel("Datum:")
        date_lbl.setStyleSheet("color: #888; font-size: 13px;")
        self.date_value = QLabel("15.08.2024")
        self.date_value.setStyleSheet("color: #E0E0E0; font-size: 13px;")
        self.date_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        self.date_input.setStyleSheet("""
            QLineEdit { background-color: #252527; color: #E0E0E0; border: 1px solid #444; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        """)
        self.date_input.hide()
        date_row.addWidget(date_lbl)
        date_row.addStretch()
        date_row.addWidget(self.date_value)
        date_row.addWidget(self.date_input)
        layout.addLayout(date_row)
        
        # Time row
        time_row = QHBoxLayout()
        time_lbl = QLabel("Uhrzeit:")
        time_lbl.setStyleSheet("color: #888; font-size: 13px;")
        self.time_value = QLabel("14:23:17")
        self.time_value.setStyleSheet("color: #E0E0E0; font-size: 13px;")
        self.time_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("HH:MM")
        self.time_input.setStyleSheet(self.date_input.styleSheet())
        self.time_input.hide()
        time_row.addWidget(time_lbl)
        time_row.addStretch()
        time_row.addWidget(self.time_value)
        time_row.addWidget(self.time_input)
        layout.addLayout(time_row)
        
        # Edit/Save button
        self.edit_btn = QPushButton("✏️ Infos bearbeiten")
        self.edit_btn.setStyleSheet("""
            QPushButton { background-color: #2D7DFF; color: white; border: none; padding: 8px; border-radius: 6px; font-weight: 500; font-size: 12px; }
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
        self.folder_list_layout = QVBoxLayout(self.folder_list_content)
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
        
        # Helper to create action buttons
        def create_action_btn(text, icon_name, color, shortcut, callback):
            btn = QPushButton()
            btn.setFixedHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(callback)
            
            # Layout for button content
            content_layout = QHBoxLayout(btn)
            content_layout.setContentsMargins(16, 0, 16, 0)
            content_layout.setSpacing(12)
            
            # Icon
            icon_lbl = QLabel()
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / icon_name
            if icon_path.exists():
                pixmap = QPixmap(str(icon_path))
                icon_lbl.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                icon_lbl.setText("•")
                icon_lbl.setStyleSheet("color: white; font-size: 16px;")
            content_layout.addWidget(icon_lbl)
            
            # Text
            text_lbl = QLabel(text)
            text_lbl.setStyleSheet("color: white; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            content_layout.addWidget(text_lbl)
            
            content_layout.addStretch()
            
            # Shortcut Badge
            badge = QLabel(shortcut)
            badge.setFixedSize(32, 24)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet("background-color: rgba(0,0,0,0.3); color: #EEE; border-radius: 4px; font-size: 11px; border: none;")
            content_layout.addWidget(badge)
            
            # Button Style
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 8px;
                    border: none;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {color}DD;
                }}
                QPushButton:pressed {{
                    background-color: {color}AA;
                }}
            """)
            return btn

        # Delete button
        self.delete_btn = create_action_btn("Löschen", "trash.svg", "#D64242", "Del", self.delete_current_file)
        layout.addWidget(self.delete_btn)
        
        # New folder button
        self.new_folder_btn = create_action_btn("Neuer Ordner", "folder-plus.svg", "#2D7DFF", "N", self.create_new_folder_dialog)
        layout.addWidget(self.new_folder_btn)
        
        parent_layout.addLayout(layout)

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
                 icon_lbl.setPixmap(pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
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
            shortcut_lbl.setStyleSheet("background-color: #333; color: #AAA; border-radius: 4px; font-size: 11px; border: none;")
            layout.addWidget(shortcut_lbl)
            
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2A2A2C;
                    border: 1px solid #333;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #333;
                    border-color: #444;
                }
            """)
            
            self.folder_list_layout.addWidget(btn)

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
        # Placeholder: toggle edit mode for EXIF fields
        self.is_editing = not self.is_editing
        # Show/hide input fields based on edit mode
        self.date_input.setVisible(self.is_editing)
        self.time_input.setVisible(self.is_editing)
        self.edit_btn.setText("💾 Save" if self.is_editing else "✏️ Infos bearbeiten")
        if not self.is_editing:
            self.save_exif_changes()

    def save_exif_changes(self):
        # Placeholder for saving EXIF changes
        pass

    # ---------------------------------------------------------------------
    # Media loading and file operations (basic implementations)
    # ---------------------------------------------------------------------
    def on_media_loaded(self, file_path: str):
        """Handle the signal when a new media file is loaded.
        Loads the image and updates the file info label.
        """
        pixmap = QPixmap(file_path)
        self.display_image(pixmap)
        
        file_name = Path(file_path).name
        size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        
        dimensions = f"{pixmap.width()}x{pixmap.height()}" if not pixmap.isNull() else "Unknown"
        
        self.file_info_label.setText(f"{file_name} • {size_mb:.1f} MB • {dimensions}")

    def delete_current_file(self):
        """Placeholder for deleting the current file.
        Actual implementation should remove the file and update UI.
        """
        # TODO: Implement deletion logic
        pass

    def create_new_folder_dialog(self):
        """Placeholder for creating a new folder via dialog.
        Actual implementation should prompt user and refresh folder list.
        """
        # TODO: Implement folder creation dialog
        pass

    def move_current_file(self, target_folder: str):
        """Placeholder for moving the current file to a target folder.
        Actual implementation should move the file on disk and update UI.
        """
        # TODO: Implement file moving logic
        pass

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
            self.progress_label.setText(f"{processed} / {total} Medien")
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
        else:
             # Fallback if index is out of bounds (e.g. after deletion)
            if self.files:
                self.current_file_index = 0
                self.load_current_file()
            else:
                self.display_image(None)
