import os
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

class FileManager:
    VALID_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
        '.mp4', '.mov', '.avi', '.3gp'             # Videos
    }

    def __init__(self):
        self.logger = logging.getLogger("FotoSortierer.FileManager")

    def scan_directory(self, source_path: str) -> List[Dict[str, Any]]:
        """
        Recursively scans the directory for valid media files.
        Returns a list of dictionaries containing file metadata.
        """
        path = Path(source_path)
        media_files = []

        if not path.exists() or not path.is_dir():
            self.logger.error(f"Invalid source path: {source_path}")
            return []

        self.logger.info(f"Starting recursive scan of {source_path}")

        try:
            # Using os.walk for robust recursive scanning
            for root, _, files in os.walk(path):
                for file in files:
                    try:
                        file_path = Path(root) / file
                        
                        # Check extension (case-insensitive)
                        if file_path.suffix.lower() in self.VALID_EXTENSIONS:
                            # Get basic metadata
                            stat = file_path.stat()
                            
                            file_info = {
                                "path": str(file_path),
                                "size": stat.st_size,
                                "mtime": stat.st_mtime,
                                "extension": file_path.suffix.lower(),
                                "type": "video" if file_path.suffix.lower() in {'.mp4', '.mov', '.avi', '.3gp'} else "image"
                            }
                            media_files.append(file_info)
                            
                    except (PermissionError, OSError) as e:
                        self.logger.warning(f"Skipping file {file}: {e}")
                        continue
                        
        except PermissionError:
            self.logger.error(f"Permission denied accessing {source_path}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {source_path}: {e}")

        self.logger.info(f"Found {len(media_files)} media files in {source_path}")
        return media_files

    def list_subfolders(self, path: Path) -> List[Path]:
        """
        Returns a sorted list of subdirectories in the given path.
        Only returns direct children, not recursive.
        
        Args:
            path: Path object to scan for subdirectories
            
        Returns:
            List of Path objects representing subdirectories, sorted alphabetically
        """
        if not path.exists() or not path.is_dir():
            self.logger.warning(f"Invalid path for listing subfolders: {path}")
            return []
        
        try:
            subfolders = [p for p in path.iterdir() if p.is_dir()]
            return sorted(subfolders, key=lambda p: p.name.lower())
        except PermissionError:
            self.logger.error(f"Permission denied accessing {path}")
            return []
        except Exception as e:
            self.logger.error(f"Error listing subfolders in {path}: {e}")
            return []

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
