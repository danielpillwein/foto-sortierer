from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget
from ui.start_screen import StartScreen
from ui.new_session_screen import NewSessionScreen
from core.session_manager import SessionManager
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FotoSortierer")
        self.resize(1280, 800) # Adjusted height for better view
        
        # Managers
        self.session_manager = SessionManager()
        
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

    def show_start_screen(self):
        self.start_screen.refresh_sessions()
        self.stack.setCurrentWidget(self.start_screen)

    def show_new_session_screen(self):
        self.stack.setCurrentWidget(self.new_session_screen)

    def create_session(self, data):
        try:
            session_id = self.session_manager.create_session(
                name=data["name"],
                source_path=data["source"],
                target_path=data["target"],
                detect_duplicates=data["detect_duplicates"]
            )
            QMessageBox.information(self, "Erfolg", f"Session '{data['name']}' erstellt!")
            self.show_start_screen()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Konnte Session nicht erstellen: {e}")

    def resume_session(self, session_id):
        QMessageBox.information(self, "Info", f"Session {session_id} wird fortgesetzt (TODO: Phase 3)")
