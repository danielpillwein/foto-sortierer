# 📸 FotoSortierer

**FotoSortierer** is a powerful, user-friendly desktop application designed to streamline the organization of large photo and video collections.  
It helps you **sort**, **clean up**, **detect duplicates**, and **edit EXIF metadata** — all in a fast, modern dark-mode interface.

---

## ⭐ Key Features

| Feature | Description |
|---------|-------------|
| 🗂️ **Session Management** | Create and resume sorting sessions at any time. Your progress is always saved. |
| 🔍 **Duplicate Detection** | Intelligent perceptual hashing finds exact and near-duplicate images. |
| 🚚 **Media Sorting** | Move files into subfolders using **direct hotkeys** for each folder — fast and efficient. |
| 🗑️ **Delete Unwanted Files** | Remove files instantly via hotkey or on-screen controls. |
| 🏷️ **EXIF Metadata Editing** | View and edit date/time, camera model, and more directly inside the app. |
| 🎞️ **Video Playback** | Built-in video player with seek bar and playback controls. |
| ⚡ **High Performance** | Multi-threaded scanning, lazy loading, and caching for smooth handling of large libraries. |
| 🌙 **Dark Mode** | Modern, distraction-free dark UI optimized for long sorting sessions. |

**Tech Stack:** Python · PyQt6 · Pillow · ImageHash

---

## 📥 Installation & Usage

### 🪟 Windows Release
1. Visit the **[Releases](../../releases)** page.  
2. Download the latest `FotoSortierer.exe`.  
3. Run the executable — **no Python installation required**.

---

## 🚀 How to Use

### 1. **Start Screen**
View existing sessions or create a new one.

### 2. **Create a New Session**
Select:
- **Source Folder** → unsorted photos/videos  
- **Target Folder** → where sorted media will be organized  

Optional: enable **Duplicate Scan** before sorting.

### 3. **Duplicate Scan (Optional)**
Automatically detects visually similar images using perceptual hashing.

### 4. **Sorting Workflow**
- **Move into subfolders** using **dedicated hotkeys** (each folder displays its number/letter shortcut).  
- **Delete a file** using the `Delete` key.  
- **Keep the file unchanged** using `+`.  


### 5. **EXIF Editing**
Use *"Infos bearbeiten"* to adjust incorrect or missing metadata.

### 6. **Finish**
Close the session and continue anytime from the Start Screen.

---


## 🛠️ Development

### 📁 Project Structure
- **core/** – logic for sessions, duplicates, file operations, EXIF handling, caching, etc.  
- **ui/** – PyQt6 interface (main window, sorting view, dialogs)  
- **utils/** – helper utilities  
- **assets/** – icons, images, stylesheets (`.qss`)  
- **data/** – generated session & configuration data  
- **main.py** – application entry point  

### ▶️ Run from Source

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
python main.py
```
### 🏗️ Building the Executable

To build a standalone Windows executable using PyInstaller:
```bash
pyinstaller FotoSortierer.spec
```

**Or a basic one-directory build:**

```bash
pyinstaller --noconfirm --onedir --windowed --icon "assets/icons/app-icon.ico" --add-data "assets;assets" --name "FotoSortierer" main.py
```

The final build will be located in:
`dist/FotoSortierer`