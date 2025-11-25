import logging
from pathlib import Path
from datetime import datetime
import piexif
from PIL import Image
from .metadata_extractor import MetadataExtractor

class ExifManager(MetadataExtractor):
    """
    Manages reading and writing of EXIF metadata.
    Extends MetadataExtractor for reading capabilities.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("FotoSortierer.ExifManager")

    def get_metadata(self, file_path):
        """
        Returns a dictionary of relevant metadata.
        """
        date_taken = self.get_date_taken(file_path)
        camera_model = self._get_camera_model(file_path)
        
        return {
            "date_taken": date_taken,
            "camera_model": camera_model,
            "filename": Path(file_path).name,
            "filesize": Path(file_path).stat().st_size,
            # Add resolution if needed, can be read from Image.open()
        }

    def _get_camera_model(self, file_path):
        try:
            img = Image.open(file_path)
            if "exif" in img.info:
                exif_dict = piexif.load(img.info["exif"])
                model = exif_dict.get("0th", {}).get(piexif.ImageIFD.Model)
                if model:
                    return model.decode("utf-8").strip()
        except Exception:
            pass
        return "Unknown"

    def supports_exif(self, file_path):
        """
        Check if the file format supports EXIF metadata.
        Returns True for JPEG, WEBP, and TIFF files.
        """
        path = Path(file_path)
        return path.suffix.lower() in ['.jpg', '.jpeg', '.webp', '.tiff']

    def update_metadata(self, file_path, new_data):
        """
        Updates EXIF metadata for the given file.
        new_data: dict with keys 'date_taken' (datetime), 'camera_model' (str)
        """
        path = Path(file_path)
        if not self.supports_exif(file_path):
            self.logger.warning(f"Cannot update EXIF for {file_path} - format does not support EXIF")
            return False
        
        if not path.exists():
            self.logger.warning(f"Cannot update EXIF for {file_path} - file does not exist")
            return False

        try:
            img = Image.open(path)
            exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "thumbnail": None, "GPS": {}}
            
            if "exif" in img.info:
                try:
                    exif_dict = piexif.load(img.info["exif"])
                except Exception:
                    pass # Start fresh if corrupt

            # Update Date Taken
            if "date_taken" in new_data and isinstance(new_data["date_taken"], datetime):
                dt_str = new_data["date_taken"].strftime("%Y:%m:%d %H:%M:%S")
                exif_dict["0th"][piexif.ImageIFD.DateTime] = dt_str
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_str
                exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = dt_str

            # Update Camera Model
            if "camera_model" in new_data and new_data["camera_model"]:
                exif_dict["0th"][piexif.ImageIFD.Model] = new_data["camera_model"].encode("utf-8")

            exif_bytes = piexif.dump(exif_dict)
            img.save(path, exif=exif_bytes)
            return True

        except Exception as e:
            self.logger.error(f"Failed to update EXIF for {path}: {e}")
            return False
