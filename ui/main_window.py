from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget
from PyQt6.QtCore import QThread, pyqtSignal
from ui.start_screen import StartScreen
from ui.new_session_screen import NewSessionScreen
from ui.duplicate_scan_screen import DuplicateScanScreen
from ui.duplicate_review_screen import DuplicateReviewScreen
from core.session_manager import SessionManager
from core.duplicate_detector import DuplicateDetector
from pathlib import Path
import glob

class DuplicateScanThread(QThread):
    progress_update = pyqtSignal(int, int, int, int, str) # current, total, deleted, review, status
    scan_complete = pyqtSignal(list)
    
    def __init__(self, source_path, detector, session_id):
        super().__init__()
        self.source_path = source_path
        self.detector = detector
        self.session_id = session_id
        self.is_cancelled = False
    
    def run(self):
        if self.is_cancelled:
            return
        
        # Use FileManager to get initial list for progress
        from core.file_manager import FileManager
        file_manager = FileManager()
        files = file_manager.scan_directory(self.source_path)
        
        # Run duplicate detection
        def progress_callback(current, total, deleted, review, status):
            if not self.is_cancelled:
                self.progress_update.emit(current, total, deleted, review, status)
        
        # New API returns list of soft duplicate pairs
        soft_duplicates = self.detector.scan_and_process(files, self.session_id, progress_callback)
        
        if not self.is_cancelled:
            self.scan_complete.emit(soft_duplicates)
    
    def cancel(self):
        self.is_cancelled = True
        self.detector.cancel()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FotoSortierer")
        self.resize(1280, 800)
        
        # Managers
        from core.config_manager import ConfigManager
        self.config_manager = ConfigManager()
        self.session_manager = SessionManager()
        self.duplicate_detector = DuplicateDetector(self.config_manager)
        
        # Logger
        import logging
        self.logger = logging.getLogger("FotoSortierer.MainWindow")
        
        # State
        self.current_session_id = None
        self.duplicate_pairs = []
        self.current_pair_index = 0
        self.scan_thread = None
        
        # Load global style
        self.load_stylesheet()
        
        # Stacked Widget for Navigation
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Initialize Screens
        self.init_screens()

    def load_stylesheet(self):
        style_path = Path("assets/style.qss")
        if style_path.exists():
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print("Warning: Style sheet not found!")

    def init_screens(self):
        # 1. Start Screen
        self.start_screen = StartScreen(self.session_manager)
        self.start_screen.create_session_clicked.connect(self.show_new_session_screen)
        self.start_screen.resume_session_clicked.connect(self.resume_session)
        self.stack.addWidget(self.start_screen)

        # 2. New Session Screen
        self.new_session_screen = NewSessionScreen()
        self.new_session_screen.back_clicked.connect(self.show_start_screen)
        self.new_session_screen.session_created.connect(self.create_session)
        self.stack.addWidget(self.new_session_screen)
        
        # 3. Duplicate Scan Screen
        self.duplicate_scan_screen = DuplicateScanScreen()
        self.duplicate_scan_screen.scan_cancelled.connect(self.cancel_duplicate_scan)
        self.duplicate_scan_screen.continue_clicked.connect(self.on_scan_continue)
        self.stack.addWidget(self.duplicate_scan_screen)
        
        # 4. Duplicate Review Screen
        self.duplicate_review_screen = DuplicateReviewScreen()
        self.duplicate_review_screen.keep_left.connect(self.keep_left_image)
        self.duplicate_review_screen.keep_right.connect(self.keep_right_image)
        self.duplicate_review_screen.keep_both.connect(self.keep_both_images)
        self.duplicate_review_screen.review_completed.connect(self.complete_duplicate_review)
        self.stack.addWidget(self.duplicate_review_screen)

    def show_start_screen(self):
        self.start_screen.refresh_sessions()
        self.stack.setCurrentWidget(self.start_screen)

    def show_new_session_screen(self):
        self.new_session_screen.reset_form()
        self.stack.setCurrentWidget(self.new_session_screen)

    def create_session(self, data):
        try:
            session_id = self.session_manager.create_session(
                name=data["name"],
                source_path=data["source"],
                target_path=data["target"],
                detect_duplicates=data["detect_duplicates"]
            )
            self.current_session_id = session_id
            
            # If duplicate detection is enabled, start scan
            if data["detect_duplicates"]:
                self.start_duplicate_scan(data["source"])
            else:
                QMessageBox.information(self, "Erfolg", f"Session '{data['name']}' erstellt!")
                self.show_start_screen()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Session nicht erstellen: {e}")
    
    def start_duplicate_scan(self, source_path):
        """Start duplicate detection scan."""
        self.stack.setCurrentWidget(self.duplicate_scan_screen)
        
        # Use FileManager to get accurate count (recursively)
        from core.file_manager import FileManager
        file_manager = FileManager()
        files = file_manager.scan_directory(source_path)
        total_files = len(files)
        
        self.duplicate_scan_screen.set_total_files(total_files)
        
        # Reset UI
        self.duplicate_scan_screen.progress_bar.setValue(0)
        self.duplicate_scan_screen.progress_percent.setText("0%")
        self.duplicate_scan_screen.action_btn.setText("Scan abbrechen")
        
        # Create and start scan thread
        self.scan_thread = DuplicateScanThread(source_path, self.duplicate_detector, self.current_session_id)
        self.scan_thread.progress_update.connect(self.duplicate_scan_screen.update_progress)
        self.scan_thread.scan_complete.connect(self.on_scan_complete)
        
        self.scan_thread.start()
    
    def cancel_duplicate_scan(self):
        """Cancel ongoing duplicate scan."""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.cancel()
            self.scan_thread.wait()
        self.show_start_screen()
    
    def on_scan_complete(self, soft_duplicates):
        """Handle completion of duplicate scan."""
        self.duplicate_pairs = soft_duplicates
        self.current_pair_index = 0
        
        # Mark scan as complete
        self.duplicate_scan_screen.set_complete()
    
    def on_scan_continue(self):
        """Handle continue button click after scan completion."""
        if len(self.duplicate_pairs) > 0:
            # Show first pair for manual review
            self.show_next_duplicate_pair()
        else:
            QMessageBox.information(self, "Scan abgeschlossen", "Keine weiteren Dubletten gefunden!")
            self.show_start_screen()
    
    def show_next_duplicate_pair(self):
        """Show next duplicate pair for manual review."""
        if self.current_pair_index < len(self.duplicate_pairs):
            self.stack.setCurrentWidget(self.duplicate_review_screen)
            
            # Pair is (path1, path2)
            left_path_str, right_path_str = self.duplicate_pairs[self.current_pair_index]
            left_path = Path(left_path_str)
            right_path = Path(right_path_str)
            
            # Get metadata
            left_metadata = self.duplicate_detector.get_image_metadata(left_path_str)
            right_metadata = self.duplicate_detector.get_image_metadata(right_path_str)
            
            # Load pair
            self.duplicate_review_screen.load_pair(left_path, right_path, left_metadata, right_metadata)
            self.duplicate_review_screen.update_progress(
                self.current_pair_index + 1,
                len(self.duplicate_pairs)
            )
        else:
            # All pairs reviewed
            self.complete_duplicate_review()
    
    def keep_left_image(self):
        """User chose to keep left image, delete right."""
        if self.current_pair_index < len(self.duplicate_pairs):
            left_path, right_path = self.duplicate_pairs[self.current_pair_index]
            
            # Move right to trash
            if self.duplicate_detector.move_to_trash(right_path, self.current_session_id):
                # Remove all remaining pairs that contain the deleted file
                self.duplicate_pairs = [
                    (l, r) for l, r in self.duplicate_pairs[self.current_pair_index + 1:]
                    if l != right_path and r != right_path
                ]
                self.current_pair_index = 0  # Reset index since we rebuilt the list
            else:
                QMessageBox.warning(self, "Fehler", f"Konnte Datei nicht löschen: {right_path}")
                self.current_pair_index += 1
            
            self.show_next_duplicate_pair()
    
    def keep_right_image(self):
        """User chose to keep right image, delete left."""
        if self.current_pair_index < len(self.duplicate_pairs):
            left_path, right_path = self.duplicate_pairs[self.current_pair_index]
            
            # Move left to trash
            if self.duplicate_detector.move_to_trash(left_path, self.current_session_id):
                # Remove all remaining pairs that contain the deleted file
                self.duplicate_pairs = [
                    (l, r) for l, r in self.duplicate_pairs[self.current_pair_index + 1:]
                    if l != left_path and r != left_path
                ]
                self.current_pair_index = 0  # Reset index since we rebuilt the list
            else:
                QMessageBox.warning(self, "Fehler", f"Konnte Datei nicht löschen: {left_path}")
                self.current_pair_index += 1
            
            self.show_next_duplicate_pair()
    
    def keep_both_images(self):
        """User chose to keep both images."""
        if self.current_pair_index < len(self.duplicate_pairs):
            # Just skip to next pair without deleting anything
            self.current_pair_index += 1
            self.show_next_duplicate_pair()
    
    def complete_duplicate_review(self):
        """Complete duplicate review process."""
        QMessageBox.information(self, "Abgeschlossen", "Dublettenprüfung abgeschlossen!")
        self.show_start_screen()

    def resume_session(self, session_id):
        QMessageBox.information(self, "Info", f"Session {session_id} wird fortgesetzt (TODO: Sortier-Ansicht)")
