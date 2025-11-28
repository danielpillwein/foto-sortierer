from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QFrame, QGridLayout, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from datetime import datetime
import subprocess
import os
from pathlib import Path

from ui.components.stats_popup import StatsPopup

class StartScreen(QWidget):
    create_session_clicked = pyqtSignal()
    resume_session_clicked = pyqtSignal(str) # session_id

    def __init__(self, session_manager):
        super().__init__()
        self.session_manager = session_manager
        self.current_stats_popup = None  # Track open popup
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # --- Header ---
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        app_title = QLabel("FotoSortierer")
        app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #E0E0E0;")
        section_title = QLabel("Sessions")
        section_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #AAAAAA;")
        title_layout.addWidget(app_title)
        title_layout.addWidget(section_title)
        
        new_session_btn = QPushButton("+ Neue Session erstellen")
        new_session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_session_btn.setFixedSize(200, 40)
        new_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover { background-color: #3B82F6; }
        """)
        new_session_btn.clicked.connect(self.create_session_clicked.emit)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(new_session_btn)
        
        layout.addLayout(header_layout)

        # --- Session Grid (Scrollable) ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

        self.refresh_sessions()

    def refresh_sessions(self):
        # Clear existing items
        for i in reversed(range(self.scroll_layout.count())): 
            item = self.scroll_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        sessions = self.session_manager.get_all_sessions()
        
        if not sessions:
            # Center the layout for empty state
            self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Show empty state message
            empty_label = QLabel("Noch keine Session vorhanden.\nErstelle eine neue Session oben rechts.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    font-weight: 500;
                    padding: 40px;
                }
            """)
            # Add to grid, spanning 3 columns
            self.scroll_layout.addWidget(empty_label, 0, 0, 1, 3)
            return

        # Reset alignment for grid view
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        row = 0
        col = 0
        max_cols = 3

        for session in sessions:
            card = self.create_session_card(session)
            self.scroll_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def delete_session_clicked(self, session_id, session_name):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Session löschen')
        msg_box.setText(f"Möchtest du die Session '{session_name}' wirklich löschen?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # Create custom buttons with German text
        ja_button = msg_box.addButton('Ja', QMessageBox.ButtonRole.YesRole)
        nein_button = msg_box.addButton('Nein', QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(nein_button)
        
        # Style the buttons
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #1A1A1C;
            }
            QMessageBox QLabel {
                color: #E0E0E0;
            }
            QPushButton {
                min-width: 80px;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        
        ja_button.setStyleSheet("""
            QPushButton {
                background-color: #2D7DFF;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #3B82F6;
            }
        """)
        
        nein_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ja_button:
            if self.session_manager.delete_session(session_id):
                self.refresh_sessions()

    def open_target_folder(self, session):
        """Open the target folder for a session in file explorer."""
        target_path = session.get("target_path")
        if target_path and str(target_path).strip():
            path_obj = Path(target_path).resolve()
            if path_obj.exists():
                subprocess.run(['explorer', str(path_obj)])
                return
        
        QMessageBox.information(self, "Info", "Zielordner nicht gefunden.")
    
    def open_trash_folder(self, session_id):
        """Open the trash folder for a session in file explorer."""
        trash_folder = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{session_id}"))
        
        if trash_folder.exists():
            # Open folder in Windows Explorer
            subprocess.run(['explorer', str(trash_folder)])
        else:
            QMessageBox.information(self, "Info", "Noch keine Dateien gelöscht.")

    def create_session_card(self, session):
        card = QFrame()
        card.setFixedSize(380, 200)
        card.setStyleSheet("""
            QFrame {
                background-color: #1A1A1C;
                border: 1px solid #2A2A2C;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 1px solid #3D3D3F;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header (Title + Delete Button)
        header_row = QHBoxLayout()
        
        name_label = QLabel(session.get("name", "Unbenannt"))
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF; border: none; background: transparent;")
        
        delete_btn = QPushButton()
        delete_btn.setIcon(QIcon("assets/icons/trash.svg"))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setFixedSize(24, 24)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_session_clicked(session["id"], session.get("name", "Unbenannt")))
        
        header_row.addWidget(name_label)
        header_row.addStretch()
        header_row.addWidget(delete_btn)
        
        layout.addLayout(header_row)
        
        # Stats Container
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(6)
        
        # Media Count
        media_row = QHBoxLayout()
        media_row.setSpacing(8)
        media_icon = QLabel()
        media_icon.setPixmap(QIcon("assets/icons/image.svg").pixmap(16, 16))
        media_icon.setStyleSheet("border: none; background: transparent;")
        
        media_text = QLabel(f"{session.get('initial_filecount', 0)} Medien")
        media_text.setStyleSheet("color: #AAAAAA; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        
        media_row.addWidget(media_icon)
        media_row.addWidget(media_text)
        media_row.addStretch()
        stats_layout.addLayout(media_row)

        # Progress Text
        prog_row = QHBoxLayout()
        prog_row.setSpacing(8)
        prog_icon = QLabel()
        prog_icon.setPixmap(QIcon("assets/icons/chart.svg").pixmap(16, 16))
        prog_icon.setStyleSheet("border: none; background: transparent;")
        
        # Calculate progress: (sorted + deleted) / initial
        initial_count = session.get('initial_filecount', 0)
        sorted_files = session.get('sorted_files', 0)
        deleted_count = session.get('deleted_count', 0)
        
        if initial_count > 0:
            progress_val = int(((sorted_files + deleted_count) / initial_count) * 100)
        else:
            progress_val = 0
            
        prog_text = QLabel(f"{progress_val}% sortiert")
        prog_text.setStyleSheet("color: #AAAAAA; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        
        prog_row.addWidget(prog_icon)
        prog_row.addWidget(prog_text)
        prog_row.addStretch()
        stats_layout.addLayout(prog_row)
        
        layout.addLayout(stats_layout)
        
        # Spacer
        layout.addSpacing(5)
        
        # Progress Bar
        progress_bar = QFrame()
        progress_bar.setFixedHeight(6)
        progress_bar.setStyleSheet("background-color: #2A2A2C; border-radius: 3px; border: none;")
        
        # Calculate width based on percentage (max width approx 340px)
        fill_width = int(340 * (progress_val / 100))
        if fill_width < 6 and progress_val > 0: fill_width = 6 # Min width if started
        
        fill = QFrame(progress_bar)
        fill.setGeometry(0, 0, fill_width, 6)
        color = "#22C55E" if progress_val == 100 else "#2D7DFF"
        fill.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
        
        layout.addWidget(progress_bar)
        
        layout.addStretch()

        # Actions
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        if progress_val == 100:
            # Static text "Fertig sortiert"
            action_btn = QLabel("Fertig sortiert")
            action_btn.setFixedHeight(36)
            action_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            action_btn.setStyleSheet("""
                QLabel {
                    color: #22C55E;
                    font-weight: bold;
                    font-size: 13px;
                    border: none;
                    background: transparent;
                    padding: 0 8px;
                }
            """)
        else:
            # Resume button
            action_btn = QPushButton("Fortsetzen")
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            action_btn.setFixedHeight(36)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1A1A1C;
                    color: #E0E0E0;
                    border: 1px solid #333;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover { 
                    background-color: #252527; 
                    border: 1px solid #444;
                }
            """)
            action_btn.clicked.connect(lambda: self.resume_session_clicked.emit(session["id"]))
        
        stats_btn = QPushButton()
        stats_btn.setIcon(QIcon("assets/icons/bar_chart.svg"))
        stats_btn.setIconSize(QSize(18, 18))
        stats_btn.setFixedSize(36, 36)
        stats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #252527; 
                border: 1px solid #444;
            }
        """)
        stats_btn.clicked.connect(lambda: self.show_stats_popup(session, stats_btn))
        
        # Target folder button
        target_btn = QPushButton("Ziel")
        target_btn.setIcon(QIcon("assets/icons/folder_outline.svg"))
        target_btn.setIconSize(QSize(16, 16))
        target_btn.setFixedHeight(36)
        target_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        target_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover { 
                background-color: #252527; 
                border: 1px solid #444;
            }
        """)
        target_btn.setToolTip("Zielordner öffnen")
        target_btn.clicked.connect(lambda: self.open_target_folder(session))
        
        # Deleted files button
        deleted_btn = QPushButton("Gelöscht")
        deleted_btn.setIcon(QIcon("assets/icons/archive.svg"))
        deleted_btn.setIconSize(QSize(16, 16))
        deleted_btn.setFixedHeight(36)
        deleted_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        deleted_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A1A1C;
                color: #E0E0E0;
                border: 1px solid #333;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover { 
                background-color: #252527; 
                border: 1px solid #444;
            }
        """)
        deleted_btn.setToolTip("Gelöschte Dateien anzeigen")
        deleted_btn.clicked.connect(lambda: self.open_trash_folder(session["id"]))
        
        # Add stretch to push buttons to bottom if needed, but layout has stretch above
        action_layout.addWidget(action_btn, 1) # Stretch factor 1 for main button
        action_layout.addWidget(stats_btn)
        action_layout.addWidget(target_btn)
        action_layout.addWidget(deleted_btn)
        
        layout.addLayout(action_layout)
        
        return card
    
    def show_stats_popup(self, session, button):
        """Show statistics popup for a session."""
        # Close previous popup if open
        if self.current_stats_popup:
            self.current_stats_popup.close()
            self.current_stats_popup = None
        
        # Create new popup
        popup = StatsPopup(session, self)
        self.current_stats_popup = popup
        
        # Position popup relative to button (bottom-right)
        button_pos = button.mapToGlobal(button.rect().bottomLeft())
        popup.move(button_pos.x(), button_pos.y() + 5)
        
        # Show popup
        popup.show()
