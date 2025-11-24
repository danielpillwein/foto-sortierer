import logging
from pathlib import Path
from PyQt6.QtGui import QPixmap, QImage, QImageReader
from PyQt6.QtCore import QObject, pyqtSignal, QThread, Qt
from concurrent.futures import ThreadPoolExecutor
import functools

class MediaLoader(QObject):
    """
    Handles loading of images and videos with caching and threading.
    """
    image_loaded = pyqtSignal(str, QPixmap) # path, pixmap
    error_occurred = pyqtSignal(str, str) # path, error message

    image_ready_internal = pyqtSignal(str, QImage) # Internal signal to transfer QImage to main thread

    def __init__(self, cache_size=20):
        super().__init__()
        self.logger = logging.getLogger("FotoSortierer.MediaLoader")
        self.cache = {} # Simple LRU-like dict: path -> QPixmap
        self.cache_size = cache_size
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.loading_tasks = {} # path -> future
        
        # Connect internal signal to main thread slot
        self.image_ready_internal.connect(self._handle_loaded_image)

    def load_media(self, path, target_size=None):
        """
        Requests to load a media file. Emits image_loaded when done.
        For videos, it might just verify existence or load a thumbnail (future).
        """
        path_str = str(path)
        
        # Check cache first
        if path_str in self.cache:
            self.image_loaded.emit(path_str, self.cache[path_str])
            return

        # Submit to thread pool
        if path_str not in self.loading_tasks:
            future = self.executor.submit(self._load_image_sync, path_str, target_size)
            self.loading_tasks[path_str] = future
            future.add_done_callback(functools.partial(self._on_load_complete, path_str))

    def _load_image_sync(self, path, target_size):
        """
        Actual loading logic running in a separate thread.
        Returns QImage to be converted to QPixmap in the main thread (for safety).
        """
        try:
            reader = QImageReader(path)
            reader.setAutoTransform(True)
            
            if target_size:
                # Scale while loading for performance if needed
                # reader.setScaledSize(target_size) 
                pass

            image = reader.read()
            if image.isNull():
                raise ValueError(f"Failed to load image: {reader.errorString()}")
            
            return image
        except Exception as e:
            self.logger.error(f"Error loading {path}: {e}")
            raise e

    def _on_load_complete(self, path, future):
        """
        Callback when loading is done.
        """
        try:
            image = future.result()
            self.image_ready_internal.emit(path, image)
        except Exception as e:
            self.error_occurred.emit(path, str(e))
        finally:
            # Cleanup task tracking is done in main thread slot or here? 
            # Safe to do here if dict is thread safe? Dicts are atomic in CPython but let's be safe.
            # Better to clean up in main thread.
            pass

    def _handle_loaded_image(self, path, image):
        """
        Slot running on main thread. Converts QImage to QPixmap and caches it.
        """
        if path in self.loading_tasks:
            del self.loading_tasks[path]
            
        pixmap = QPixmap.fromImage(image)
        
        # Cache management (Simple LRU)
        if len(self.cache) >= self.cache_size:
            # Remove first item (oldest)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
            
        self.cache[path] = pixmap
        self.image_loaded.emit(path, pixmap)

    # To properly handle QPixmap creation on main thread, we need a slot on the main thread.
    # Since MediaLoader lives on main thread (created there), its slots run on main thread 
    # if connected with AutoConnection/QueuedConnection.
    
    def preload(self, paths):
        """
        Preloads a list of paths into cache.
        """
        for path in paths:
            self.load_media(path)

    def clear_cache(self):
        self.cache.clear()
