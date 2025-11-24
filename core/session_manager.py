import json
import logging
import time
from pathlib import Path

class SessionManager:
    def __init__(self, sessions_file="data/sessions.json"):
        self.sessions_file = Path(sessions_file)
        self.logger = logging.getLogger("FotoSortierer.SessionManager")
        self.sessions = self.load_sessions()

    def load_sessions(self):
        """Loads sessions from JSON file."""
        if not self.sessions_file.exists():
            return {}
        
        try:
            with open(self.sessions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading sessions: {e}")
            return {}

    def save_sessions(self):
        """Saves sessions to JSON file."""
        self.sessions_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.sessions_file, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, indent=4)
        except IOError as e:
            self.logger.error(f"Error saving sessions: {e}")

    def create_session(self, name, source_path, target_path, detect_duplicates=False):
        """Creates a new session and saves it."""
        session_id = str(int(time.time()))
        session_data = {
            "id": session_id,
            "name": name,
            "source_path": str(source_path),
            "target_path": str(target_path),
            "created_at": time.time(),
            "last_accessed": time.time(),
            "status": "new", # new, scanning, sorting, completed
            "detect_duplicates": detect_duplicates,
            "progress": 0,
            "total_files": 0,
            "processed_files": 0
        }
        self.sessions[session_id] = session_data
        self.save_sessions()
        self.logger.info(f"Created session '{name}' ({session_id})")
        return session_id

    def get_all_sessions(self):
        """Returns a list of all sessions sorted by last accessed."""
        return sorted(self.sessions.values(), key=lambda x: x.get("last_accessed", 0), reverse=True)

    def delete_session(self, session_id):
        """Deletes a session by its ID."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.save_sessions()
            self.logger.info(f"Deleted session {session_id}")
            return True
        return False

    def run_duplicate_check(self, session_id, config_manager):
        """Runs the duplicate check for a specific session."""
        from .file_manager import FileManager
        from .duplicate_detector import DuplicateDetector

        session = self.sessions.get(session_id)
        if not session:
            self.logger.error(f"Session {session_id} not found.")
            return None

        if not session.get("detect_duplicates"):
            self.logger.info(f"Duplicate detection disabled for session {session_id}.")
            return []

        self.logger.info(f"Starting duplicate check for session {session_id}...")
        session["status"] = "scanning"
        self.save_sessions()

        try:
            file_manager = FileManager()
            detector = DuplicateDetector(config_manager)

            # 1. Scan Directory
            files = file_manager.scan_directory(session["source_path"])
            session["total_files"] = len(files)
            self.save_sessions()

            # 2. Detect Duplicates
            duplicates = detector.scan_and_process(files, session_id)
            
            # 3. Save Results
            dupe_file = self.sessions_file.parent / f"session_{session_id}_duplicates.json"
            with open(dupe_file, "w", encoding="utf-8") as f:
                json.dump(duplicates, f, indent=4)
            
            session["duplicate_file"] = str(dupe_file)
            session["status"] = "review_duplicates" if duplicates else "ready_to_sort"
            self.save_sessions()
            
            return duplicates

        except Exception as e:
            self.logger.error(f"Error during duplicate check: {e}")
            session["status"] = "error"
            self.save_sessions()
            raise e
