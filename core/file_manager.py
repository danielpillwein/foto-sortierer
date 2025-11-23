import os
import logging
from pathlib import Path

class FileManager:
    VALID_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
        '.mp4', '.mov', '.avi', '.3gp'             # Videos
    }

    def __init__(self):
        self.logger = logging.getLogger("FotoSortierer.FileManager")

    def scan_directory(self, source_path):
        """
        Recursively scans the directory for valid media files.
        Returns a list of Path objects.
        """
        path = Path(source_path)
        media_files = []

        if not path.exists() or not path.is_dir():
            self.logger.error(f"Invalid source path: {source_path}")
            return []

        try:
            # Using os.walk for robust recursive scanning
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in self.VALID_EXTENSIONS:
                        media_files.append(file_path)
        except PermissionError:
            self.logger.error(f"Permission denied accessing {source_path}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {source_path}: {e}")

        self.logger.info(f"Found {len(media_files)} media files in {source_path}")
        return media_files

    def check_permissions(self, path):
        """Checks if read/write permissions exist for a path."""
        path = Path(path)
        try:
            if not path.exists():
                # Check parent if file doesn't exist
                return os.access(path.parent, os.R_OK | os.W_OK)
            return os.access(path, os.R_OK | os.W_OK)
        except Exception:
            return False
