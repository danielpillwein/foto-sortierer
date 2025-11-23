import logging
from pathlib import Path
from datetime import datetime
from PIL import Image, UnidentifiedImageError
import piexif

class MetadataExtractor:
    def __init__(self):
        self.logger = logging.getLogger("FotoSortierer.MetadataExtractor")

    def get_date_taken(self, file_path):
        """
        Extracts the date taken from EXIF or file modification time.
        Returns a datetime object.
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return None

        # Try EXIF for images
        if path.suffix.lower() in ['.jpg', '.jpeg', '.webp', '.tiff']:
            try:
                img = Image.open(path)
                if "exif" in img.info:
                    exif_dict = piexif.load(img.info["exif"])
                    # 36867 is DateTimeOriginal, 36868 is DateTimeDigitized
                    date_str = exif_dict.get("Exif", {}).get(36867)
                    if date_str:
                        return self._parse_exif_date(date_str)
            except (UnidentifiedImageError, ValueError, Exception) as e:
                self.logger.warning(f"Could not read EXIF from {path}: {e}")

        # Fallback: File modification time
        try:
            timestamp = path.stat().st_mtime
            return datetime.fromtimestamp(timestamp)
        except OSError as e:
            self.logger.error(f"Error reading file stats for {path}: {e}")
            return datetime.now() # Absolute fallback

    def _parse_exif_date(self, date_bytes):
        """Parses EXIF date string (b'YYYY:MM:DD HH:MM:SS') to datetime."""
        try:
            date_str = date_bytes.decode("utf-8")
            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except (ValueError, AttributeError):
            return None
