import json
import logging
import time
import os
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
            "detect_duplicates": detect_duplicates,
            "progress": 0,
            "initial_filecount": 0,
            "sorted_files": 0,
            "deleted_count": 0,
            "deleted_size_bytes": 0
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
            detector = DuplicateDetector(config_manager, session_manager=self)

            # 1. Scan Directory and store initial count
            files = file_manager.scan_directory(session["source_path"])
            session["initial_filecount"] = len(files)
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

    def move_file(self, session_id, file_path, target_folder):
        """
        Moves a file to the target folder.
        Note: Does NOT update sorted_files - caller is responsible for that.
        """
        import shutil
        
        session = self.sessions.get(session_id)
        if not session:
            return False

        source = Path(file_path)
        destination = Path(target_folder) / source.name
        
        try:
            # Ensure target directory exists
            Path(target_folder).mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source), str(destination))
            return True
        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {e}")
            return False

    def update_deleted_stats(self, session_id, file_size):
        """
        Updates the deleted file count and size for a session.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session["deleted_count"] = session.get("deleted_count", 0) + 1
        session["deleted_size_bytes"] = session.get("deleted_size_bytes", 0) + file_size
        self.save_sessions()
        return True
    
    def delete_file(self, session_id, file_path):
        """
        Moves a file to the 'gelöscht_<session_id>' folder and updates deleted stats.
        """
        # Get file size before moving
        try:
            file_size = Path(file_path).stat().st_size
        except Exception as e:
            self.logger.error(f"Error getting file size for {file_path}: {e}")
            file_size = 0
        
        trash_folder = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{session_id}"))
        success = self.move_file(session_id, file_path, str(trash_folder))
        
        if success:
            self.update_deleted_stats(session_id, file_size)
        
        return success

    def get_session_progress(self, session_id):
        """
        Returns a dict with progress stats.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "progress": session.get("progress", 0),
            "processed": session.get("sorted_files", 0),
            "total": session.get("initial_filecount", 0)
        }
