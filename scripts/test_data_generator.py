import os
import random
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from collections import Counter
import piexif

def generate_random_image(path, width=640, height=480, seed=None):
    """Generates a random colored image with optional seed for reproducibility."""
    if seed is not None:
        random.seed(seed)
    
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    
    # Add some random shapes for variety
    for _ in range(random.randint(3, 8)):
        x1 = random.randint(0, width - 1)
        y1 = random.randint(0, height - 1)
        x2 = random.randint(x1, width)  # Ensure x2 >= x1
        y2 = random.randint(y1, height)  # Ensure y2 >= y1
        shape_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        d.rectangle([x1, y1, x2, y2], fill=shape_color)
    
    d.text((10, 10), f"Test Image\n{path.name}", fill=(255, 255, 255))
    return img

def add_exif_data(img, camera_model="TestCam", date_time=None):
    """Adds EXIF data to an image."""
    if date_time is None:
        date_time = datetime.now()
    
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: camera_model.encode(),
            piexif.ImageIFD.Model: f"{camera_model} Model".encode(),
            piexif.ImageIFD.Software: b"Test Generator",
            piexif.ImageIFD.DateTime: date_time.strftime("%Y:%m:%d %H:%M:%S").encode(),
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: date_time.strftime("%Y:%m:%d %H:%M:%S").encode(),
            piexif.ExifIFD.DateTimeDigitized: date_time.strftime("%Y:%m:%d %H:%M:%S").encode(),
        }
    }
    
    return piexif.dump(exif_dict)

def generate_dummy_file(path, size_kb=10):
    """Generates a dummy file of approximate size."""
    with open(path, 'wb') as f:
        f.write(os.urandom(size_kb * 1024))

def set_file_times(path, date=None):
    """Sets access and modification times for a file."""
    if date is None:
        days_delta = random.randint(0, 365 * 10)
        date = datetime.now() - timedelta(days=days_delta)
    
    timestamp = date.timestamp()
    os.utime(path, (timestamp, timestamp))

def create_test_data(target_dir, num_files=100, max_depth=3, duplicate_ratio=0.3, soft_duplicate_ratio=0.1):
    """
    Creates realistic test data with duplicates.
    
    Args:
        target_dir: Target directory
        num_files: Total number of files to generate
        max_depth: Maximum folder depth
        duplicate_ratio: Ratio of files that are exact duplicates (0.0-1.0)
        soft_duplicate_ratio: Ratio of files that are soft duplicates (0.0-1.0)
    """
    target_path = Path(target_dir)
    
    if target_path.exists():
        print(f"Cleaning up existing directory: {target_path}")
        shutil.rmtree(target_path)
    
    target_path.mkdir(parents=True, exist_ok=True)
    print(f"Generating realistic test data in: {target_path}")
    print(f"  - Unique files: ~{int(num_files * (1 - duplicate_ratio - soft_duplicate_ratio))}")
    print(f"  - Exact duplicates: ~{int(num_files * duplicate_ratio)}")
    print(f"  - Soft duplicates (same image, different EXIF): ~{int(num_files * soft_duplicate_ratio)}\n")

    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    stats = Counter()
    
    # Track which images we've created for duplicates
    created_images = []
    unique_count = 0
    exact_dup_count = 0
    soft_dup_count = 0

    for i in range(num_files):
        # Determine depth
        depth = random.randint(0, max_depth)
        current_dir = target_path
        
        # Create subdirectories
        for _ in range(depth):
            sub_dir_name = f"Folder_{random.randint(1, 10)}"
            current_dir = current_dir / sub_dir_name
            current_dir.mkdir(exist_ok=True)
        
        # Determine file type
        ext = random.choice(extensions)
        stats[ext] += 1
        filename = f"media_{i:04d}{ext}"
        file_path = current_dir / filename
        
        # Decide: unique, exact duplicate, or soft duplicate
        rand = random.random()
        
        if rand < duplicate_ratio and len(created_images) > 0:
            # Create exact duplicate
            original = random.choice(created_images)
            shutil.copy2(original, file_path)
            exact_dup_count += 1
            print(f"[EXACT DUP] {file_path.name} <- copy of {original.name}")
            
        elif rand < (duplicate_ratio + soft_duplicate_ratio) and len(created_images) > 0:
            # Create soft duplicate (same image, different EXIF)
            original = random.choice([img for img in created_images if img.suffix in ['.jpg', '.jpeg']])
            
            # Copy image
            img = Image.open(original)
            
            # Add different EXIF data
            different_date = datetime.now() - timedelta(days=random.randint(1, 365))
            different_camera = random.choice(["Canon", "Nikon", "Sony", "iPhone"])
            
            try:
                exif_bytes = add_exif_data(img, camera_model=different_camera, date_time=different_date)
                img.save(file_path, exif=exif_bytes)
            except:
                # Fallback if EXIF fails
                img.save(file_path)
            
            set_file_times(file_path, different_date)
            soft_dup_count += 1
            print(f"[SOFT DUP] {file_path.name} <- same as {original.name}, different EXIF")
            
        else:
            # Create unique image
            try:
                img = generate_random_image(file_path, seed=i)
                
                # Add EXIF for JPEGs
                if ext in ['.jpg', '.jpeg']:
                    random_date = datetime.now() - timedelta(days=random.randint(0, 365 * 5))
                    random_camera = random.choice(["Canon EOS", "Nikon D", "Sony Alpha", "iPhone 12", "Samsung Galaxy"])
                    exif_bytes = add_exif_data(img, camera_model=random_camera, date_time=random_date)
                    img.save(file_path, exif=exif_bytes)
                    set_file_times(file_path, random_date)
                else:
                    img.save(file_path)
                    set_file_times(file_path)
                
                created_images.append(file_path)
                unique_count += 1
                
            except Exception as e:
                print(f"Error creating image {file_path}: {e}")
                generate_dummy_file(file_path)
                set_file_times(file_path)

        if (i + 1) % 10 == 0 or (i + 1) == num_files:
            print(f"Progress: {i + 1}/{num_files} files generated...")

    print("\n" + "="*100)
    print("Test data generation complete!")
    print("="*100)
    
    # Print Statistics
    print("\n--- File Type Statistics ---")
    print(f"Total files: {num_files}")
    for ext, count in stats.most_common():
        print(f"  {ext}: {count}")
    
    print("\n--- Duplicate Statistics ---")
    print(f"  Unique images: {unique_count}")
    print(f"  Exact duplicates: {exact_dup_count}")
    print(f"  Soft duplicates: {soft_dup_count}")
    print(f"\nExpected behavior:")
    print(f"  - {exact_dup_count} files should be auto-deleted")
    print(f"  - {soft_dup_count} pairs should appear for manual review")
    print(f"  - {unique_count} files should remain unique")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic test data for FotoSortierer")
    parser.add_argument("--target", type=str, default="test_data", help="Target directory for test data")
    parser.add_argument("--count", type=int, default=100, help="Number of files to generate")
    parser.add_argument("--duplicates", type=float, default=0.3, help="Ratio of exact duplicates (0.0-1.0)")
    parser.add_argument("--soft-duplicates", type=float, default=0.1, help="Ratio of soft duplicates (0.0-1.0)")
    
    args = parser.parse_args()
    create_test_data(args.target, num_files=args.count, duplicate_ratio=args.duplicates, soft_duplicate_ratio=args.soft_duplicates)
