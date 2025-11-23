import os
import random
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from collections import Counter

def generate_random_image(path, width=640, height=480):
    """Generates a random colored image."""
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    d.text((10, 10), f"Test Image\n{path.name}", fill=(255, 255, 255))
    img.save(path)

def generate_dummy_file(path, size_kb=10):
    """Generates a dummy file of approximate size."""
    with open(path, 'wb') as f:
        f.write(os.urandom(size_kb * 1024))

def set_file_times(path):
    """Sets random access and modification times for a file."""
    # Random date within last 10 years
    days_delta = random.randint(0, 365 * 10)
    date = datetime.now() - timedelta(days=days_delta)
    timestamp = date.timestamp()
    os.utime(path, (timestamp, timestamp))

def print_tree(startpath, max_files_per_folder=3):
    """Prints a simplified directory tree."""
    print("\n--- Folder Structure (Preview) ---")
    startpath = Path(startpath)
    for root, dirs, files in os.walk(startpath):
        root_path = Path(root)
        level = len(root_path.relative_to(startpath).parts)
        indent = '    ' * level
        print(f"{indent}📂 {root_path.name}/")
        
        subindent = '    ' * (level + 1)
        for f in files[:max_files_per_folder]:
            print(f"{subindent}📄 {f}")
        if len(files) > max_files_per_folder:
            print(f"{subindent}... ({len(files) - max_files_per_folder} more files)")

def create_test_data(target_dir, num_files=50, max_depth=3):
    """Creates a test directory structure with dummy media files."""
    target_path = Path(target_dir)
    
    if target_path.exists():
        print(f"Cleaning up existing directory: {target_path}")
        shutil.rmtree(target_path)
    
    target_path.mkdir(parents=True, exist_ok=True)
    print(f"Generating test data in: {target_path}")

    extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
        '.mp4', '.mov', '.avi', '.3gp'             # Videos
    ]
    
    stats = Counter()

    for i in range(num_files):
        # Determine depth
        depth = random.randint(0, max_depth)
        current_dir = target_path
        
        # Create subdirectories
        for _ in range(depth):
            sub_dir_name = f"Folder_{random.randint(1, 10)}"
            current_dir = current_dir / sub_dir_name
            current_dir.mkdir(exist_ok=True)
        
        # Create file
        ext = random.choice(extensions)
        stats[ext] += 1
        
        filename = f"media_{i:04d}{ext}"
        file_path = current_dir / filename
        
        # Verbose output removed in favor of progress
        # print(f"Creating {file_path}")
        
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            try:
                generate_random_image(file_path)
            except Exception as e:
                print(f"Error creating image {file_path}: {e}")
                generate_dummy_file(file_path) # Fallback
        else:
            generate_dummy_file(file_path, size_kb=100) # Dummy video
            
        set_file_times(file_path)

        if (i + 1) % 10 == 0 or (i + 1) == num_files:
            print(f"Progress: {i + 1}/{num_files} files generated...")

    print("\nTest data generation complete.")
    
    # Print Statistics
    print("\n--- Statistics ---")
    print(f"Total files: {num_files}")
    for ext, count in stats.most_common():
        print(f"{ext}: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test data for FotoSortierer")
    parser.add_argument("--target", type=str, default="test_data", help="Target directory for test data")
    parser.add_argument("--count", type=int, default=50, help="Number of files to generate")
    
    args = parser.parse_args()
    create_test_data(args.target, num_files=args.count)
