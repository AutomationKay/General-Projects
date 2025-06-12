
# File Sorting Automation

This script monitors a specified directory and automatically sorts files into subfolders by type (images, videos, music, documents, archives, executables).

### Features
- Real-time monitoring via `watchdog`
- Extension-based sorting into configurable folders
- Automatic renaming of duplicates
- Configurable via top-of-script variables or a separate config file
- Clean logging with timestamps; can be redirected to file

### Prerequisites
- Python 3.6+
- `watchdog` package (`pip install watchdog`)
- Read/write permissions for source and destination directories


### (Recommended) Create a virtual environment:

bash
Copy
Edit
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

### Install dependencies:

bash
Copy
Edit
pip install watchdog
Edit the script’s top variables to point to your desired source_dir and destination folders. Ensure directories exist or add code to create them.

### Configuration
Paths: Modify source_dir, dest_image, dest_music, etc.

Extensions: Edit extension lists at the top (image_extensions, video_extensions, etc.) to include or exclude file types.

Logging: By default logs to console. To log to a file, adjust logging.basicConfig in __main__.

### Usage
Run the script:

bash
Copy
Edit
python file_sorter.py
Watch the console for move confirmations. To stop:

Press Ctrl+C.

### How It Works
FileMover: A subclass of FileSystemEventHandler that, on each modification in source_dir, scans entries and routes them to type-specific handlers.

Type Handlers: Check extensions and call move_file(...) when a match is found.

Duplicate Handling: unique_name() appends a numeric suffix if a file with the same name exists in the target.

Moving Files: Uses shutil.move(...) to relocate files.
