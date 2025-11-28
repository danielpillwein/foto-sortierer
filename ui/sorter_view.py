from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSplitter, QGraphicsView, QGraphicsScene, QLineEdit, 
    QProgressBar, QSlider, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QSize, QUrl
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from pathlib import Path
import os
import shutil

# Import breadcrumb navigation components
from ui.components.breadcrumb_bar import BreadcrumbBar
from ui.components.shortcut_folder_panel import ShortcutFolderPanel
from ui.components.stats_popup import StatsPopup
from ui.components.completion_popup import CompletionPopup
from ui.components.clickable_slider import ClickableSlider

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
        self.current_file_supports_exif = False  # Track if current file supports EXIF
        
        # Navigation state for breadcrumb system
        self.target_root = None  # Root of target directory
        self.current_navigation_path = []  # List of Path objects representing breadcrumb path
        self.current_subfolders = []  # Subfolders at current level
        
        # Video player components (initialized in init_ui)
        # Video player components (initialized in init_ui)
        self.media_player = None
        self.audio_output = None
        self.video_widget = None
        self.current_media_type = 'image'  # 'image' or 'video'
        self.video_initialized = False
        
        # Connect media loaded signal
        self.media_loader.image_loaded.connect(self.on_media_loaded)
        self.current_stats_popup = None
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.init_ui()

    # ---------------------------------------------------------------------
    # Keyboard handling
    # ---------------------------------------------------------------------
    def keyPressEvent(self, event):
        key = event.key()
        
        # Spacebar for Video Play/Pause - Exclusive handling
        if key == Qt.Key.Key_Space:
            if self.current_media_type == 'video':
                self.toggle_play_pause()
            event.accept()  # Consume event to prevent button activation
            return

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
        elif key == Qt.Key.Key_Plus:
            self.keep_current_file()
        else:
            super().keyPressEvent(event)

    def move_to_folder_by_index(self, index):
        """Handle numeric shortcut (1-9) to navigate or move to folder."""
        if index < len(self.current_subfolders):
            folder = self.current_subfolders[index]
            self.handle_folder_action(folder)

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
        stats_btn = QPushButton("  Statistiken")
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
        stats_btn.clicked.connect(lambda: self.show_stats_popup(stats_btn))
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
        top_bar.setSpacing(8) # Spacing between elements
        
        # File Info Container
        file_info_widget = QWidget()
        file_info_layout = QHBoxLayout(file_info_widget)
        file_info_layout.setContentsMargins(0, 0, 0, 0)
        file_info_layout.setSpacing(8)

        # Icon
        self.file_icon_label = QLabel()
        self.file_icon_label.setFixedSize(20, 20)
        self.file_icon_label.setStyleSheet("background: transparent; border: none;")
        file_info_layout.addWidget(self.file_icon_label)

        # Filename (White)
        self.file_name_label = QLabel("Keine Datei")
        self.file_name_label.setStyleSheet("color: #E0E0E0; font-size: 13px; font-weight: 600; border: none;")
        file_info_layout.addWidget(self.file_name_label)

        # Metadata (Gray)
        self.file_meta_label = QLabel("")
        self.file_meta_label.setStyleSheet("color: #666; font-size: 13px; border: none;")
        file_info_layout.addWidget(self.file_meta_label)

        top_bar.addWidget(file_info_widget)
        
        top_bar.addStretch()
        
        # Zoom controls (only for images)
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
        
        # Media display area - stack image and video widgets
        media_stack = QWidget()
        media_stack_layout = QVBoxLayout(media_stack)
        media_stack_layout.setContentsMargins(0, 0, 0, 0)
        media_stack_layout.setSpacing(0)
        
        # Graphics view for images
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        media_stack_layout.addWidget(self.view)
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background: transparent;")
        self.video_widget.hide()  # Hidden by default
        media_stack_layout.addWidget(self.video_widget)
        
        layout.addWidget(media_stack, 1)  # Stretch factor 1
        
        # Video controls panel
        self.video_controls_panel = QWidget()
        self.video_controls_panel.setFixedHeight(60)
        self.video_controls_panel.setStyleSheet("background-color: #0E0E0F;")
        self.video_controls_panel.hide()  # Hidden by default
        
        # Single row layout for all controls
        controls_layout = QHBoxLayout(self.video_controls_panel)
        controls_layout.setContentsMargins(20, 0, 20, 0)
        controls_layout.setSpacing(12)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Play/Pause button (Left)
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set initial icon
        icon_path = Path(__file__).parent.parent / "assets" / "icons" / "play.svg"
        if icon_path.exists():
            self.play_pause_btn.setIcon(QIcon(str(icon_path)))
            self.play_pause_btn.setIconSize(QSize(16, 16))
            
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                border: none;
                border-radius: 20px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_pause_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Current time label
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setStyleSheet("color: #666; font-size: 13px; min-width: 45px;")
        controls_layout.addWidget(self.current_time_label, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Timeline slider (Clickable)
        self.timeline_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2A2A2C;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #2D7DFF;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #E0E0E0;
            }
        """)
        # Connect both clicked (jump) and sliderMoved (drag)
        self.timeline_slider.clicked.connect(self.on_slider_moved)
        self.timeline_slider.sliderMoved.connect(self.on_slider_moved)
        controls_layout.addWidget(self.timeline_slider, 1, Qt.AlignmentFlag.AlignVCenter)
        
        # Duration label
        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet("color: #666; font-size: 13px; min-width: 45px;")
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls_layout.addWidget(self.duration_label, 0, Qt.AlignmentFlag.AlignVCenter)
        
        layout.addWidget(self.video_controls_panel)
        
        # Initialize media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect media player signals
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        
        self.content_splitter.addWidget(self.media_container)

    def init_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("background-color: #1A1A1C; border: none;")
        
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
        """Initialize the breadcrumb-based folder navigation panel."""
        title = QLabel("ZIELORDNER")
        title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        parent_layout.addWidget(title)
        
        # Add breadcrumb bar
        self.breadcrumb_bar = BreadcrumbBar()
        self.breadcrumb_bar.breadcrumb_clicked.connect(self.navigate_to_breadcrumb)
        parent_layout.addWidget(self.breadcrumb_bar)
                
        # Add shortcut folder panel
        self.shortcut_panel = ShortcutFolderPanel()
        self.shortcut_panel.folder_clicked.connect(self.handle_folder_action)
        parent_layout.addWidget(self.shortcut_panel, 1)  # Stretch factor 1 to take remaining space
        
        parent_layout.addSpacing(10)

    def init_action_panel(self, parent_layout):
        title = QLabel("AKTIONEN")
        title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none;")
        parent_layout.addWidget(title)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 1. Keep in Source Button
        self.keep_btn = QPushButton()
        self.keep_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.keep_btn.setFixedHeight(45)
        self.keep_btn.clicked.connect(self.keep_current_file)
        
        keep_layout = QHBoxLayout(self.keep_btn)
        keep_layout.setContentsMargins(15, 0, 15, 0)
        
        keep_icon_label = QLabel()
        keep_icon_label.setStyleSheet("background: transparent; border: none;")
        keep_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "keep.svg"
        if keep_icon_path.exists():
            keep_icon_label.setPixmap(QPixmap(str(keep_icon_path)).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        keep_layout.addWidget(keep_icon_label)
        
        keep_text_label = QLabel("Im Quellordner lassen")
        keep_text_label.setStyleSheet("color: white; font-weight: 600; font-size: 13px; border: none; background: transparent;")
        keep_layout.addWidget(keep_text_label)
        
        keep_layout.addStretch()
        
        keep_shortcut = QLabel("+")
        keep_shortcut.setAlignment(Qt.AlignmentFlag.AlignCenter)
        keep_shortcut.setFixedSize(24, 24)
        keep_shortcut.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); color: white; border-radius: 4px; font-size: 12px; font-weight: bold;")
        keep_layout.addWidget(keep_shortcut)
        
        self.keep_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                border: none;
                border-radius: 8px;
                text-align: left;
            }
            QPushButton:hover { background-color: #4B5563; }
        """)
        layout.addWidget(self.keep_btn)
        
        # 2. Delete Button
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
        
        # 3. New Folder Button
        self.new_folder_btn = QPushButton()
        self.new_folder_btn.setFixedHeight(44)
        self.new_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_folder_btn.clicked.connect(self.create_new_folder_dialog)
        
        nf_layout = QHBoxLayout(self.new_folder_btn)
        nf_layout.setContentsMargins(16, 0, 16, 0)
        nf_layout.setSpacing(12)
        
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
        nf_text_lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600; border: none; background: transparent;")
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

    # ---------------------------------------------------------------------
    # Breadcrumb Navigation Methods
    # ---------------------------------------------------------------------
    def handle_folder_action(self, folder: Path):
        """
        Decide whether to navigate into folder or move file.
        If folder has subfolders, navigate. Otherwise, move file.
        """
        from core.file_manager import FileManager
        file_manager = FileManager()
        subfolders = file_manager.list_subfolders(folder)
        
        if subfolders:
            # Folder has subfolders - navigate deeper
            self.navigate_to_folder(folder)
        else:
            # Leaf folder - move file here
            self.move_current_file(str(folder))
    
    def navigate_to_folder(self, folder: Path):
        """Navigate into a subfolder - updates breadcrumb and panel."""
        self.current_navigation_path.append(folder)
        self.update_navigation_ui()
    
    def navigate_to_breadcrumb(self, index: int):
        """Navigate back to a breadcrumb level."""
        # Index 0 is the target root
        if index == 0:
            # Navigate back to root
            self.current_navigation_path = []
        else:
            # Navigate to specific level (index-1 because root is index 0)
            self.current_navigation_path = self.current_navigation_path[:index]
        self.update_navigation_ui()
    
    def update_navigation_ui(self):
        """Refresh breadcrumb and folder panel based on current navigation state."""
        if not self.target_root:
            return
        
        # Determine current folder
        if self.current_navigation_path:
            current_folder = self.current_navigation_path[-1]
        else:
            current_folder = self.target_root
        
        # Build breadcrumb segments - ALWAYS start with target root
        segments = [self.target_root.name]
        
        # Add navigation path segments (if any)
        if self.current_navigation_path:
            segments.extend([p.name for p in self.current_navigation_path])
        
        self.breadcrumb_bar.set_path(segments)
        
        # Update subfolders list
        from core.file_manager import FileManager
        file_manager = FileManager()
        self.current_subfolders = file_manager.list_subfolders(current_folder)
        
        # Update shortcut panel
        self.shortcut_panel.set_folders(self.current_subfolders)

    # ---------------------------------------------------------------------
    # Image handling and zoom
    # ---------------------------------------------------------------------
    def display_image(self, pixmap):
        self.current_media_type = 'image'
        
        # Stop video playback if active
        if self.media_player and self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.stop()
            
        # Ensure video widgets are hidden
        if self.video_widget:
            self.video_widget.hide()
        if self.video_controls_panel:
            self.video_controls_panel.hide()
            
        # Show image view and controls
        self.view.show()
        self.zoom_in_btn.show()
        self.zoom_out_btn.show()
        
        self.scene.clear()
        if pixmap and not pixmap.isNull():
            self.scene.addPixmap(pixmap)
            self.scene.setSceneRect(QRectF(pixmap.rect())) # Explicitly set scene rect
            
            # Reset zoom and scrollbars for new image
            self.zoom_level = 1.0
            self.view.resetTransform()
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.view.centerOn(self.scene.sceneRect().center())
        else:
            self.scene.addText("No Image", QFont("Arial", 20)).setDefaultTextColor(Qt.GlobalColor.gray)

    def zoom_in(self):
        self.view.scale(1.2, 1.2)
        self.zoom_level *= 1.2
        
        # Enable scrollbars and drag if zoomed in
        if self.zoom_level > 1.0:
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def zoom_out(self):
        if self.zoom_level > 1.0:
            self.view.scale(1/1.2, 1/1.2)
            self.zoom_level /= 1.2
            
            # Disable scrollbars, drag and fit if back to original or smaller
            if self.zoom_level <= 1.01: # Use small epsilon for float comparison
                self.zoom_level = 1.0
                self.view.resetTransform()
                self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
                self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        """Handle resize events to maintain Best Fit."""
        super().resizeEvent(event)
        if self.zoom_level == 1.0 and hasattr(self, 'view') and hasattr(self, 'scene') and self.scene.items():
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.view.centerOn(self.scene.sceneRect().center())

    # ---------------------------------------------------------------------
    # Video playback methods
    # ---------------------------------------------------------------------
    def is_video_file(self, file_path):
        """Check if file is a video format."""
        video_extensions = {'.mp4', '.mov', '.avi', '.3gp', '.mkv', '.webm', '.flv', '.wmv'}
        return Path(file_path).suffix.lower() in video_extensions
    
    def is_gif_file(self, file_path):
        """Check if file is a GIF."""
        return Path(file_path).suffix.lower() == '.gif'
    
    def display_video(self, file_path):
        """Load and display a video file."""
        self.current_media_type = 'video'
        
        # Hide image view, show video view
        self.view.hide()
        self.video_widget.show()
        self.video_controls_panel.show()
        
        # Hide zoom controls for videos
        self.zoom_in_btn.hide()
        self.zoom_out_btn.hide()
        
        # Stop any current playback
        self.media_player.stop()
        
        # Reset initialization flag
        self.video_initialized = False
        
        # Load video
        self.media_player.setSource(QUrl.fromLocalFile(str(file_path)))
        
        # Auto-play video
        self.media_player.play()
        
        # Reset controls - set pause icon (since we are auto-playing)
        pause_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "pause.svg"
        if pause_icon_path.exists():
            self.play_pause_btn.setIcon(QIcon(str(pause_icon_path)))
            
        self.current_time_label.setText("0:00")
        self.duration_label.setText("0:00")
        self.timeline_slider.setValue(0)
    
    def display_gif(self, file_path):
        """Load and display a GIF file with auto-loop and no controls."""
        self.current_media_type = 'gif'
        
        # Hide image view, show video view
        self.view.hide()
        self.video_widget.show()
        self.video_controls_panel.hide()  # Hide controls for GIFs
        
        # Hide zoom controls for GIFs
        self.zoom_in_btn.hide()
        self.zoom_out_btn.hide()
        
        # Stop any current playback
        self.media_player.stop()
        
        # Reset initialization flag
        self.video_initialized = False
        
        # Load GIF
        self.media_player.setSource(QUrl.fromLocalFile(str(file_path)))
        
        # Set to loop indefinitely
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        
        # Auto-play GIF
        self.media_player.play()
        
    def on_media_status_changed(self, status):
        """Handle media status changes."""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            if not self.video_initialized:
                # Video loaded - ready to play
                self.video_initialized = True
                # If we are in video mode (not GIF), ensure it plays
                if self.current_media_type == 'video':
                    self.media_player.play()
                    
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Video ended - reset to play icon
            if self.current_media_type == 'video':  # Don't update for GIFs (they loop)
                play_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "play.svg"
                if play_icon_path.exists():
                    self.play_pause_btn.setIcon(QIcon(str(play_icon_path)))
    
    def toggle_play_pause(self):
        """Toggle between play and pause states."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            # Set play icon
            play_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "play.svg"
            if play_icon_path.exists():
                self.play_pause_btn.setIcon(QIcon(str(play_icon_path)))
        else:
            self.media_player.play()
            # Set pause icon
            pause_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "pause.svg"
            if pause_icon_path.exists():
                self.play_pause_btn.setIcon(QIcon(str(pause_icon_path)))
    
    def on_position_changed(self, position):
        """Update timeline and current time when video position changes."""
        # Prevent slider update loop
        if not self.timeline_slider.isSliderDown():
            self.timeline_slider.setValue(position)
        
        # Update current time label
        self.current_time_label.setText(self.format_time(position))
    
    def on_duration_changed(self, duration):
        """Update duration label and slider range when video duration is known."""
        self.timeline_slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))
    
    def on_slider_moved(self, position):
        """Seek to position when user drags the timeline slider."""
        self.media_player.setPosition(position)
    
    def format_time(self, milliseconds):
        """Convert milliseconds to MM:SS format."""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def switch_to_image_view(self):
        """Switch display to image view."""
        self.current_media_type = 'image'
        
        # Stop video playback
        if self.media_player:
            self.media_player.stop()
        
        # Show image view, hide video view
        self.video_widget.hide()
        self.video_controls_panel.hide()
        self.view.show()
        
        # Show zoom controls for images
        self.zoom_in_btn.show()
        self.zoom_out_btn.show()


    # ---------------------------------------------------------------------
    # EXIF edit handling (placeholders)
    # ---------------------------------------------------------------------
    def toggle_edit_mode(self):
        # Don't allow editing if file doesn't support EXIF
        if not self.current_file_supports_exif:
            return
        
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

    def update_edit_button_state(self):
        """Update the edit button text and style based on EXIF support."""
        if not self.current_file_supports_exif:
            # File doesn't support EXIF - disable button
            self.edit_btn.setText("  Nicht editierbar")
            self.edit_btn.setEnabled(False)
            self.edit_btn.setCursor(Qt.CursorShape.ArrowCursor)
            self.edit_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3A3A3C; 
                    color: #666; 
                    border: none; 
                    padding: 10px; 
                    border-radius: 6px; 
                    font-weight: 500; 
                    font-size: 13px; 
                }
            """)
        else:
            # File supports EXIF - enable button
            self.edit_btn.setText("  Infos bearbeiten")
            self.edit_btn.setEnabled(True)
            self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Load and set icon
            edit_icon_path = Path(__file__).parent.parent / "assets" / "icons" / "edit.svg"
            if edit_icon_path.exists():
                self.edit_btn.setIcon(QIcon(str(edit_icon_path)))
            
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
    def on_media_loaded(self, file_path: str, pixmap: QPixmap = None):
        """Handle the signal when a new media file is loaded.
        Loads the image/video and updates the file info label and EXIF data.
        """
        # Check if it's a GIF file first
        if self.is_gif_file(file_path):
            self.display_gif(file_path)
            
            # Update Icon for GIF
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "video.svg"
            if icon_path.exists():
                self.file_icon_label.setPixmap(QPixmap(str(icon_path)).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            # For GIF, show file size
            size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            self.file_meta_label.setText(f"• {size_mb:.1f} MB • GIF")
            
        # Check if it's a video file
        elif self.is_video_file(file_path):
            self.display_video(file_path)
            
            # Update Icon for video
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "video.svg"
            if icon_path.exists():
                self.file_icon_label.setPixmap(QPixmap(str(icon_path)).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            # For video, we don't have dimensions from pixmap
            size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            self.file_meta_label.setText(f"• {size_mb:.1f} MB • Video")
            
        else:
            # It's an image
            if pixmap is None:
                pixmap = QPixmap(file_path)
            
            self.display_image(pixmap)
            
            # Update Icon for image
            icon_path = Path(__file__).parent.parent / "assets" / "icons" / "image_blue.svg"
            if icon_path.exists():
                self.file_icon_label.setPixmap(QPixmap(str(icon_path)).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            size_mb = Path(file_path).stat().st_size / (1024 * 1024)
            dimensions = f"{pixmap.width()}x{pixmap.height()}" if not pixmap.isNull() else "Unknown"
            self.file_meta_label.setText(f"• {size_mb:.1f} MB • {dimensions}")
        
        file_name = Path(file_path).name
        
        # Truncate filename if > 30 chars
        display_name = file_name
        if len(file_name) > 30:
            display_name = file_name[:27] + "..."
            
        self.file_name_label.setText(display_name)
        
        # Check if file supports EXIF
        self.current_file_supports_exif = self.exif_manager.supports_exif(file_path)
        
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
        
        # Update edit button state based on EXIF support
        self.update_edit_button_state()

    def delete_current_file(self):
        """Moves the current file to a 'gelöscht_{session_id}' folder in the user's home directory."""
        if not self.files or self.current_file_index >= len(self.files):
            return
            
        if not self.current_session_id:
            return
        
        current_file_path = Path(self.files[self.current_file_index])
        
        # Get file size before moving
        try:
            file_size = current_file_path.stat().st_size
        except Exception as e:
            file_size = 0
            
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
        # Store the file count before move
        files_before = len(self.files)
        self.move_current_file(str(deleted_dir))
        
        # If file was successfully moved (file list decreased), update deleted stats
        if len(self.files) < files_before:
            self.session_manager.update_deleted_stats(self.current_session_id, file_size)
            
            # Update progress after deletion
            if self.current_session_id:
                session = self.session_manager.sessions.get(self.current_session_id)
                if session:
                    initial_count = session.get("initial_filecount", 0)
                    sorted_count = session.get("sorted_files", 0)
                    deleted_count = session.get("deleted_count", 0)
                    
                    processed = sorted_count + deleted_count
                    self.update_progress(processed, initial_count)
            
            # Check for completion
            if not self.files:
                self.show_completion_popup()
                return

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
                self.update_navigation_ui()
                
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen des Ordners:\n{str(e)}")

    def keep_current_file(self):
        """Keeps the file in source folder, counts as sorted, moves to next."""
        if not self.files or self.current_file_index >= len(self.files):
            return

        # Release file lock if it's a video or gif being played
        if self.media_player and self.current_media_type in ['video', 'gif']:
            self.media_player.stop()
            self.media_player.setSource(QUrl())

        # Update internal state (remove from list as it's processed)
        self.files.pop(self.current_file_index)
        
        # Update session stats
        if self.current_session_id:
            session = self.session_manager.sessions.get(self.current_session_id)
            if session:
                session["sorted_files"] = session.get("sorted_files", 0) + 1
                self.session_manager.save_sessions()
                
                # Update progress bar
                initial_count = session.get("initial_filecount", 0)
                sorted_count = session.get("sorted_files", 0)
                deleted_count = session.get("deleted_count", 0)
                
                processed = sorted_count + deleted_count
                self.update_progress(processed, initial_count)
                
                # Check for completion
                if not self.files:
                    self.show_completion_popup()
                    return
        
        # Load next file
        if self.current_file_index >= len(self.files):
            self.current_file_index = max(0, len(self.files) - 1)
            
        self.load_current_file()

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

        # Release file lock if it's a video or gif being played
        if self.media_player and self.current_media_type in ['video', 'gif']:
            self.media_player.stop()
            self.media_player.setSource(QUrl())

        try:
            shutil.move(str(current_file_path), str(target_path))
            
            # Update internal state
            self.files.pop(self.current_file_index)
            
            # Check if this is a sorting operation (not deletion)
            # Deletion goes to ~/Foto-Sortierer/gelöscht_{session_id}
            is_deletion = "gelöscht_" in str(target_dir)
            
            # Update session stats - only increment sorted_files if sorting (not deleting)
            if self.current_session_id and not is_deletion:
                session = self.session_manager.sessions.get(self.current_session_id)
                if session:
                    session["sorted_files"] = session.get("sorted_files", 0) + 1
                    self.session_manager.save_sessions()
                    
                    # Update progress bar
                    initial_count = session.get("initial_filecount", 0)
                    sorted_count = session.get("sorted_files", 0)
                    deleted_count = session.get("deleted_count", 0)
                    
                    processed = sorted_count + deleted_count
                    self.update_progress(processed, initial_count)
                    
                    # Check for completion
                    if not self.files:
                        self.show_completion_popup()
                        return
            
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
        
        # Update session with file counts if not set (for sessions without duplicate detection)
        if session.get("initial_filecount", 0) == 0:
            file_count = len(self.files)
            session["initial_filecount"] = file_count
            self.session_manager.save_sessions()
        
        # Initialize navigation state
        self.target_root = Path(session["target_path"])
        self.current_navigation_path = []  # Start at root
        self.update_navigation_ui()
        
        # Update progress
        initial_count = session.get("initial_filecount", len(self.files))
        sorted_count = session.get("sorted_files", 0)
        deleted_count = session.get("deleted_count", 0)
        processed = sorted_count + deleted_count
        self.update_progress(processed, initial_count)
        
        # Reset index and load first file
        self.current_file_index = 0
        self.load_current_file()
        
        # Set focus to view to capture keyboard events
        self.setFocus()

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
            self.file_name_label.setText("Keine Dateien vorhanden")
            return
            
        if 0 <= self.current_file_index < len(self.files):
            file_path = self.files[self.current_file_index]
            self.on_media_loaded(file_path)
            
            # Update progress display from session data
            if self.current_session_id:
                session = self.session_manager.sessions.get(self.current_session_id)
                if session:
                    initial_count = session.get("initial_filecount", len(self.files))
                    sorted_count = session.get("sorted_files", 0)
                    deleted_count = session.get("deleted_count", 0)
                    processed = sorted_count + deleted_count
                    self.update_progress(processed, initial_count)
        else:
             # Fallback if index is out of bounds (e.g. after deletion)
            if self.files:
                self.current_file_index = 0
                self.load_current_file()
            else:
                self.display_image(None)
                self.file_name_label.setText("Keine Dateien vorhanden")

    def show_stats_popup(self, button):
        """Show statistics popup for the current session."""
        if not self.current_session_id:
            return
            
        session = self.session_manager.sessions.get(self.current_session_id)
        if not session:
            return

        # Close previous popup if open
        if self.current_stats_popup:
            self.current_stats_popup.close()
            self.current_stats_popup = None
        
        # Create new popup
        popup = StatsPopup(session, self)
        self.current_stats_popup = popup
        
        # Position popup: Top-right corner of popup under bottom-right corner of button
        # Get button's bottom-right coordinate in global space
        btn_bottom_right = button.mapToGlobal(button.rect().bottomRight())
        
        # Calculate popup position
        # x = button_right - popup_width
        # y = button_bottom + margin
        popup_x = btn_bottom_right.x() - popup.width()
        popup_y = btn_bottom_right.y() + 5
        
        popup.move(popup_x, popup_y)
        
        # Show popup
        popup.show()

    def show_completion_popup(self):
        """Show a completion message when all files have been processed."""
        if not self.current_session_id:
            return
            
        session = self.session_manager.sessions.get(self.current_session_id)
        if not session:
            return
        
        # Create dark overlay
        overlay = QWidget(self)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.6);")
        overlay.setGeometry(self.rect())
        overlay.show()
        
        # Create and show custom completion popup
        popup = CompletionPopup(session, self)
        
        # Connect signals
        popup.close_requested.connect(self.close_session_clicked.emit)
        popup.open_source_requested.connect(lambda: self.open_folder('source'))
        popup.open_target_requested.connect(lambda: self.open_folder('target'))
        popup.show_deleted_requested.connect(self.show_deleted_files)
        popup.perm_delete_requested.connect(self.permanently_delete_files)
        
        # Show popup first to get its actual size
        popup.show()
        
        # Center popup on main window using actual dimensions
        parent_geometry = self.window().geometry()
        popup_x = parent_geometry.x() + (parent_geometry.width() - popup.width()) // 2
        popup_y = parent_geometry.y() + (parent_geometry.height() - popup.height()) // 2
        popup.move(popup_x, popup_y)
        
        # Hide and exec as modal dialog
        popup.hide()
        popup.exec()
        
        # Remove overlay after popup closes
        overlay.deleteLater()
    
    def open_folder(self, folder_type):
        """Open source or target folder in file explorer."""
        if not self.current_session_id:
            return
            
        session = self.session_manager.sessions.get(self.current_session_id)
        if not session:
            return
        
        # Determine which folder to open
        if folder_type == 'source':
            folder_path = Path(session.get('source_path', ''))
            folder_name = "Quellordner"
        else:  # target
            folder_path = Path(session.get('target_path', ''))
            folder_name = "Zielordner"
        
        if not folder_path.exists():
            QMessageBox.warning(
                self,
                "Ordner nicht gefunden",
                f"Der {folder_name} existiert nicht mehr."
            )
            return
        
        # Open folder in file explorer
        import subprocess
        try:
            subprocess.run(['explorer', str(folder_path)])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Öffnen",
                f"Der {folder_name} konnte nicht geöffnet werden:\n{str(e)}"
            )
    
    def show_deleted_files(self):
        """Open the deleted files folder in file explorer."""
        if not self.current_session_id:
            return
        
        # Deleted files are stored in ~/Foto-Sortierer/gelöscht_{session_id}
        deleted_folder = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{self.current_session_id}"))
        
        if not deleted_folder.exists():
            QMessageBox.information(
                self,
                "Keine gelöschten Dateien",
                "Es wurden noch keine Dateien gelöscht."
            )
            return
        
        # Open folder in file explorer
        import subprocess
        try:
            subprocess.run(['explorer', str(deleted_folder)])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler beim Öffnen",
                f"Der Ordner konnte nicht geöffnet werden:\n{str(e)}"
            )
    
    def permanently_delete_files(self):
        """Permanently delete all deleted files after confirmation."""
        if not self.current_session_id:
            return
        
        # Deleted files are stored in ~/Foto-Sortierer/gelöscht_{session_id}
        deleted_folder = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{self.current_session_id}"))
        
        if not deleted_folder.exists():
            QMessageBox.information(
                self,
                "Keine gelöschten Dateien",
                "Es wurden noch keine Dateien gelöscht."
            )
            return
        
        # Count files
        file_count = sum(1 for _ in deleted_folder.rglob("*") if _.is_file())
        
        # Confirmation dialog with German buttons
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Gelöschte Dateien endgültig löschen?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(f"Möchtest du wirklich alle {file_count} gelöschten Dateien unwiderruflich löschen?")
        msg_box.setInformativeText("Diese Aktion kann nicht rückgängig gemacht werden!")
        
        # Create custom German buttons
        ja_button = msg_box.addButton('Ja', QMessageBox.ButtonRole.YesRole)
        nein_button = msg_box.addButton('Nein', QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(nein_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ja_button:
            try:
                shutil.rmtree(deleted_folder)
                
                # Do NOT update session stats - keep them as they are
                
                QMessageBox.information(
                    self,
                    "Erfolgreich gelöscht",
                    f"Alle {file_count} gelöschten Dateien wurden endgültig gelöscht."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler beim Löschen",
                    f"Die Dateien konnten nicht gelöscht werden:\n{str(e)}"
                )


