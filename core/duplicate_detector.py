import logging
import imagehash
import cv2
import numpy as np
import json
import os
import shutil
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
from .config_manager import ConfigManager

class DuplicateDetector:
    def __init__(self, config_manager: ConfigManager):
        self.logger = logging.getLogger("FotoSortierer.DuplicateDetector")
        self.config = config_manager
        self.hash_size = self.config.get("hash_size", 8)
        self.threshold_hard = self.config.get("threshold_hard", 4)
        self.threshold_soft = self.config.get("threshold_soft", 10)
        self.cancelled = False
        self.cache_path = Path("cache/hash_cache.json")
        self.hash_cache = self._load_cache()
        self._lock = threading.Lock()

    def _load_cache(self) -> Dict[str, str]:
        """Load hash cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
        return {}

    def _save_cache(self):
        """Save hash cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.hash_cache, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def calculate_phash_image(self, image_path: str) -> Optional[str]:
        """Calculate perceptual hash for an image."""
        try:
            with Image.open(image_path) as img:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                hash_value = imagehash.phash(img, hash_size=self.hash_size)
                return str(hash_value)
        except Exception as e:
            self.logger.warning(f"Error hashing image {image_path}: {e}")
            return None

    def calculate_phash_video(self, video_path: str) -> Optional[str]:
        """Calculate perceptual hash for a video (middle frame)."""
        try:
            # Suppress OpenCV/FFmpeg logging
            try:
                cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
            except AttributeError:
                pass
            
            # Note: 'moov atom not found' is a C-level FFmpeg error printed to stderr.
            # It's hard to suppress fully in Python without redirecting stderr file descriptors,
            # which can be risky in a GUI app. 
            # We accept that corrupt files might print this, but we ensure the app doesn't crash.
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                hash_value = imagehash.phash(img, hash_size=self.hash_size)
                return str(hash_value)
            return None
        except Exception as e:
            self.logger.warning(f"Error hashing video {video_path}: {e}")
            return None

    def _get_file_hash(self, file_info: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Worker to get hash for a single file (check cache first)."""
        if self.cancelled:
            return file_info["path"], None

        path = file_info["path"]
        mtime = file_info["mtime"]
        size = file_info["size"]
        cache_key = f"{path}_{size}_{mtime}"

        with self._lock:
            if cache_key in self.hash_cache:
                return path, self.hash_cache[cache_key]

        # Calculate new hash
        if file_info["type"] == "video":
            hash_val = self.calculate_phash_video(path)
        else:
            hash_val = self.calculate_phash_image(path)

        if hash_val:
            with self._lock:
                self.hash_cache[cache_key] = hash_val
        
        return path, hash_val

    def scan_and_process(self, file_list: List[Dict[str, Any]], session_id: str, progress_callback=None) -> List[Tuple[str, str]]:
        """
        Main entry point.
        1. Calculate hashes.
        2. Detect duplicates.
        3. Auto-delete hard duplicates.
        4. Return soft duplicates for review.
        """
        self.cancelled = False
        self.logger.info(f"Processing {len(file_list)} files...")

        # 1. Calculate Hashes
        file_hashes = {}
        total = len(file_list)
        processed = 0

        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            futures = {executor.submit(self._get_file_hash, f): f for f in file_list}
            
            for future in as_completed(futures):
                if self.cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return []
                
                path, hash_val = future.result()
                if hash_val:
                    file_hashes[path] = hash_val
                
                processed += 1
                if progress_callback:
                    # During hashing, deleted and review are 0
                    progress_callback(processed, total, 0, 0, "Analysiere Dateien...")

        self._save_cache()
        
        if self.cancelled:
            return []

        # 2. Detect & Resolve
        return self._resolve_duplicates(file_hashes, file_list, session_id, progress_callback)

    def _resolve_duplicates(self, file_hashes: Dict[str, str], file_list: List[Dict[str, Any]], session_id: str, progress_callback=None) -> List[Tuple[str, str]]:
        """
        Compare hashes, delete hard duplicates, return soft pairs.
        """
        # Map path -> file_info for quick lookup
        file_map = {f["path"]: f for f in file_list}
        total_files = len(file_list)
        
        
        # Group by Hash (Exact Duplicates)
        exact_groups = {}
        for path, h in file_hashes.items():
            if h not in exact_groups:
                exact_groups[h] = []
            exact_groups[h].append(path)

        # Process groups with same hash
        deleted_files = set()
        soft_duplicate_pairs = []
        
        for h, paths in exact_groups.items():
            if len(paths) > 1:
                # Group files by size
                size_groups = {}
                for p in paths:
                    size = file_map[p]["size"]
                    if size not in size_groups:
                        size_groups[size] = []
                    size_groups[size].append(p)
                
                # Check if we have mixed sizes (soft duplicates) or all same size (exact duplicates)
                if len(size_groups) == 1:
                    # All files have same size -> True exact duplicates -> Auto-delete all but one
                    self._auto_delete_group(paths, file_map, session_id, deleted_files)
                    if progress_callback:
                        progress_callback(total_files, total_files, len(deleted_files), len(soft_duplicate_pairs), "Lösche exakte Duplikate...")
                else:
                    # Mixed sizes -> We have both exact duplicates AND soft duplicates
                    self.logger.info(f"Found mixed size group with hash {h}: {len(size_groups)} different sizes")
                    for size, size_paths in size_groups.items():
                        self.logger.info(f"  Size {size}: {len(size_paths)} files - {size_paths}")
                    
                    # 1. Auto-delete exact duplicates within each size group (keep one per size)
                    for size, size_paths in size_groups.items():
                        if len(size_paths) > 1:
                            self._auto_delete_group(size_paths, file_map, session_id, deleted_files)
                    
                    # 2. Create soft duplicate pairs between different size groups
                    size_group_list = list(size_groups.values())
                    for i in range(len(size_group_list)):
                        for j in range(i + 1, len(size_group_list)):
                            # Get one representative from each size group (the one that wasn't deleted)
                            group_i_remaining = [p for p in size_group_list[i] if p not in deleted_files]
                            group_j_remaining = [p for p in size_group_list[j] if p not in deleted_files]
                            
                            if group_i_remaining and group_j_remaining:
                                # Add pair between representatives
                                pair = (group_i_remaining[0], group_j_remaining[0])
                                soft_duplicate_pairs.append(pair)
                                self.logger.info(f"Created soft duplicate pair: {pair}")
                    
                    if progress_callback:
                        progress_callback(total_files, total_files, len(deleted_files), len(soft_duplicate_pairs), "Gefundene Soft-Duplikate...")

        # Update progress with deleted count
        if progress_callback:
            progress_callback(total_files, total_files, len(deleted_files), len(soft_duplicate_pairs), "Suche nach ähnlichen Bildern...")

        # Prepare for Soft Duplicate Search
        remaining_paths = [p for p in file_hashes.keys() if p not in deleted_files]
        remaining_hashes = {p: file_hashes[p] for p in remaining_paths}
        
        uncertain_pairs = []
        checked_pairs = set()

        paths = list(remaining_hashes.keys())
        n = len(paths)
        
        self.logger.info(f"Checking {n} files for soft duplicates...")

        hash_objects = {p: imagehash.hex_to_hash(h) for p, h in remaining_hashes.items()}
        path_list = list(hash_objects.keys())
        
        for i in range(n):
            if self.cancelled: break
            
            p1 = path_list[i]
            h1 = hash_objects[p1]
            
            for j in range(i + 1, n):
                p2 = path_list[j]
                h2 = hash_objects[p2]
                
                dist = h1 - h2
                
                if dist <= self.threshold_hard:
                    # Hard duplicate missed by exact match
                    pass 
                
                if dist <= self.threshold_soft:
                    pair = tuple(sorted((p1, p2)))
                    if pair not in checked_pairs:
                        checked_pairs.add(pair)
                        uncertain_pairs.append((p1, p2, dist))

        # Now process the found pairs
        final_soft_pairs = []
        
        # Union-Find for hard duplicates
        parent = {p: p for p in remaining_paths}
        def find(p):
            if parent[p] != p:
                parent[p] = find(parent[p])
            return parent[p]
        def union(p1, p2):
            root1 = find(p1)
            root2 = find(p2)
            if root1 != root2:
                parent[root1] = root2

        hard_pairs = []
        for p1, p2, dist in uncertain_pairs:
            if dist <= self.threshold_hard:
                union(p1, p2)
                hard_pairs.append((p1, p2))
            else:
                final_soft_pairs.append((p1, p2))

        # Group hard duplicates
        hard_groups = {}
        for p in remaining_paths:
            root = find(p)
            if root not in hard_groups:
                hard_groups[root] = []
            hard_groups[root].append(p)

        # Delete Hard Duplicates
        for root, group in hard_groups.items():
            if len(group) > 1:
                group = [f for f in group if f not in deleted_files]
                if len(group) > 1:
                    self._auto_delete_group(group, file_map, session_id, deleted_files)
                    # Update progress after each hard duplicate group deletion
                    if progress_callback:
                        progress_callback(total_files, total_files, len(deleted_files), len(soft_duplicate_pairs), "Lösche ähnliche Duplikate...")

        # Filter soft pairs (from hamming distance)
        real_soft_pairs = []
        for p1, p2 in final_soft_pairs:
            if p1 not in deleted_files and p2 not in deleted_files:
                real_soft_pairs.append((p1, p2))
        
        # Filter soft duplicates from exact hash groups (remove pairs with deleted files)
        filtered_soft_pairs = []
        for p1, p2 in soft_duplicate_pairs:
            if p1 not in deleted_files and p2 not in deleted_files:
                filtered_soft_pairs.append((p1, p2))
        
        # Merge with soft duplicates from exact hash groups (same pHash, different size/EXIF)
        all_soft_pairs = filtered_soft_pairs + real_soft_pairs

        # Final Update
        if progress_callback:
            progress_callback(total_files, total_files, len(deleted_files), len(all_soft_pairs), "Fertig!")

        self.logger.info(f"Auto-deleted hard duplicates. Found {len(all_soft_pairs)} soft pairs for review.")
        return all_soft_pairs

    def _auto_delete_group(self, paths: List[str], file_map: Dict[str, Any], session_id: str, deleted_set: Set[str]):
        """
        Keep the best file, delete others.
        Criteria: Largest size -> Oldest mtime.
        """
        # Sort: Primary = Size (Desc), Secondary = Time (Asc)
        # We want the largest file. If sizes equal, we want the oldest (original).
        sorted_files = sorted(paths, key=lambda p: (-file_map[p]["size"], file_map[p]["mtime"]))
        
        keeper = sorted_files[0]
        to_delete = sorted_files[1:]
        
        delete_dir = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{session_id}"))
        delete_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in to_delete:
            if file_path in deleted_set:
                continue
                
            try:
                src = Path(file_path)
                if src.exists():
                    dst = delete_dir / src.name
                    # Handle name collision in delete folder
                    counter = 1
                    while dst.exists():
                        dst = delete_dir / f"{src.stem}_{counter}{src.suffix}"
                        counter += 1
                    
                    shutil.move(str(src), str(dst))
                    deleted_set.add(file_path)
                    self.logger.info(f"Auto-deleted hard duplicate: {file_path} -> {dst}")
            except Exception as e:
                self.logger.error(f"Error moving file {file_path}: {e}")

    def cancel(self):
        self.cancelled = True

    def get_image_metadata(self, image_path: str) -> Dict[str, str]:
        """Extract basic metadata from an image for UI display."""
        path = Path(image_path)
        try:
            if not path.exists():
                return {"filename": path.name, "date": "N/A", "time": "N/A", "camera": "N/A"}
            
            stat = path.stat()
            mtime = time.localtime(stat.st_mtime)
            
            # Try to get EXIF data
            camera = "Unbekannt"
            try:
                with Image.open(path) as img:
                    exif = img.getexif()
                    if exif:
                        # 271: Make, 272: Model
                        make = exif.get(271, "")
                        model = exif.get(272, "")
                        if make or model:
                            camera = f"{make} {model}".strip()
            except:
                pass
            
            return {
                "filename": path.name,
                "date": time.strftime("%d.%m.%Y", mtime),
                "time": time.strftime("%H:%M", mtime),
                "camera": camera
            }
        except Exception as e:
            self.logger.error(f"Error getting metadata for {path}: {e}")
            return {
                "filename": path.name,
                "date": "Error",
                "time": "Error",
                "camera": "Error"
            }

    def move_to_trash(self, file_path: str, session_id: str) -> bool:
        """Move a file to the session's trash folder."""
        try:
            src = Path(file_path)
            if not src.exists():
                return False
                
            delete_dir = Path(os.path.expanduser(f"~/Foto-Sortierer/gelöscht_{session_id}"))
            delete_dir.mkdir(parents=True, exist_ok=True)
            
            dst = delete_dir / src.name
            # Handle name collision
            counter = 1
            while dst.exists():
                dst = delete_dir / f"{src.stem}_{counter}{src.suffix}"
                counter += 1
            
            shutil.move(str(src), str(dst))
            self.logger.info(f"Moved to trash: {src} -> {dst}")
            return True
        except Exception as e:
            self.logger.error(f"Error moving to trash {file_path}: {e}")
            return False

