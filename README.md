# simple-camera

A Python simple camera application with photo capture, video recording, and customizable settings.

## Features

- 📷 **Photo Capture** - Take single photos or burst mode
- 🎥 **Video Recording** - Record timed or manual video clips
- ⚙️ **Settings** - Configure resolution, FPS, formats, and more
- 👁️ **Preview** - Live camera preview window
- 🖼️ **GUI Interface** - User-friendly graphical interface
- 📁 **Auto-organization** - Captures saved to `./captures/` directory

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### GUI Interface (Recommended)

```bash
# Launch the graphical interface
python gui.py
```

The GUI provides:
- Live camera preview
- One-click photo capture
- Video recording with timer
- Settings management
- Easy camera selection

### Command Line Interface

```bash
# List available cameras
python main.py list

# Capture a photo
python main.py photo

# Capture a photo with custom name
python main.py photo -n my_photo

# Capture 5 photos with 2 second intervals
python main.py photo -N 5 -i 2

# Record a 10-second video
python main.py video -d 10

# Record video with custom resolution
python main.py video -d 30 -r 1920x1080

# Preview camera feed (5 seconds)
python main.py preview

# Preview for 30 seconds
python main.py preview -d 30

# Show current settings
python main.py settings --show

# Save settings to file
python main.py settings --save my_settings.json

# Load settings from file
python main.py settings --load my_settings.json

# Reset settings to defaults
python main.py settings --reset
```

### CLI Options

**Photo:**
| Option | Description |
|--------|-------------|
| `-n, --name` | Output filename |
| `-N, --count` | Number of photos (default: 1) |
| `-i, --interval` | Interval between photos in seconds (default: 1.0) |
| `-r, --resolution` | Resolution like `1280x720` |
| `-f, --format` | Photo format: png, jpg, bmp |

**Video:**
| Option | Description |
|--------|-------------|
| `-n, --name` | Output filename |
| `-d, --duration` | Recording duration in seconds |
| `-r, --resolution` | Resolution like `1920x1080` |
| `-f, --format` | Video format: mp4, avi, mkv |
| `--fps` | Frames per second |

**General:**
| Option | Description |
|--------|-------------|
| `-c, --camera-id` | Camera device ID (default: 0) |

### Python API

```python
from camera import Camera

# Using context manager (recommended)
with Camera() as cam:
    cam.open()
    
    # Capture a photo
    cam.capture_photo("my_photo.png")
    
    # Record a 10-second video
    cam.record_video(duration=10, filename="my_video.mp4")
    
    # Preview camera
    cam.preview(duration=5)

# Manual usage
cam = Camera(camera_id=0)
cam.open()

# Update settings
cam.update_settings(
    resolution=(1920, 1080),
    fps=30,
    photo_format="jpg"
)

# Capture photo
filepath = cam.capture_photo()
print(f"Saved: {filepath}")

# Start/stop recording
cam.start_recording()
# ... recording ...
cam.stop_recording()

cam.close()
```

## Settings

Default settings:
- **Resolution:** 1280x720
- **FPS:** 30
- **Photo Format:** PNG
- **Video Format:** MP4
- **Video Codec:** mp4v

Settings can be customized via:
- CLI: `--resolution`, `--fps`, `--format`
- API: `update_settings()`
- Config file: `save_settings()` / `load_settings()`

## Project Structure

```
simple-camera/
├── camera.py      # Core camera module
├── main.py        # CLI interface
├── gui.py         # GUI interface
├── requirements.txt
├── README.md
└── captures/      # Output directory for photos/videos
```

## License

MIT License - see [LICENSE](LICENSE) for details.
