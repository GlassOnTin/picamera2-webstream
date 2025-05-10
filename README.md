# PiCamera2 Web Streamer

A Flask-based web streaming solution for Raspberry Pi cameras using PiCamera2. Stream your Raspberry Pi camera feed securely over HTTPS with minimal latency.

## Features

- Real-time MJPEG streaming over HTTPS
- Adaptive frame rate based on client connections
- Clean shutdown handling
- Mobile-responsive web interface
- Thread-safe implementation
- Configurable camera parameters
- Resource-efficient with multiple client support

## Dependencies

A split installation approach ensures compatibility with Raspberry Pi OS while keeping application-specific dependencies isolated.

### System Packages (installed via apt)
- python3-libcamera
- python3-picamera2
- python3-opencv
- python3-numpy

### Virtual Environment Packages (installed via pip)
- flask
- Additional Python-only dependencies

## Installation

### Via pip
```bash
pip install picamera2-webstream
```

## Quick Installation

For a quick automated installation:

```bash
git clone https://github.com/glassontin/picamera2-webstream.git
cd picamera2-webstream
```

For an ffmpeg based webstream:
```
./install_ffmpeg.sh
```

For a picamera2 OpenCV based webstream use:
```
./install_picamera.sh
```

The installation script will:
1. Install all required system dependencies
2. Enable the camera interface
3. Set up a Python virtual environment
4. Install Python package dependencies
5. Generate SSL certificates
6. Add your user to the video group
7. Verify camera detection

After installation completes:
1. Log out and log back in (required for video group access)
2. Activate the virtual environment: `source venv/bin/activate`
3. Run the example: `python examples/ffmpeg_stream.py`
4. Open `https://your-pi-ip` in your browser

To uninstall:
```bash
./uninstall.sh
```

## Usage

Two streaming implementations are available:

### 1. FFmpeg-based (Recommended)
```python
from picamera2_webstream import FFmpegStream, create_ffmpeg_app

stream = FFmpegStream(
    width=1280,
    height=720,
    framerate=30,
    device='/dev/video0'
).start()

app = create_ffmpeg_app(stream)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'))
```

Advantages:
- Lighter weight (fewer dependencies)
- Hardware acceleration where available
- Better performance for basic streaming
- Works with both USB and CSI cameras
- Lower CPU usage

### 2. PiCamera2-based
```python
from picamera2_webstream import VideoStream, create_picamera_app

stream = VideoStream(
    resolution=(1280, 720),
    framerate=30,
    brightness=0.0,
    contrast=1.0
).start()

app = create_picamera_app(stream)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'))
```

Advantages:
- Full PiCamera2 feature set
- More camera controls
- Better for image processing
- Native Raspberry Pi camera support
- Access to raw camera data

### Choosing the Right Implementation

Use FFmpeg-based streaming when:
- You need basic video streaming
- You want minimal dependencies
- CPU resources are limited
- You're using a USB webcam

Use PiCamera2-based streaming when:
- You need advanced camera controls
- You want to do image processing
- You need raw camera data
- You're using the Raspberry Pi camera module

### Accessing the Stream

For either implementation:
1. Open your browser and navigate to `https://your-pi-ip`
2. Accept the self-signed certificate warning
3. View your camera stream!

## Camera Configuration

### Automatic Configuration
To find the optimal settings for your camera, run the diagnostic tool:

```bash
python examples/camera_diagnostics.py
```

This will:
1. Detect all available cameras
2. Show detailed camera capabilities
3. Test different resolutions and formats
4. Measure actual achievable framerates
5. Suggest optimal configuration settings

### Manual Configuration
You can customize various parameters when initializing the VideoStream:

```python
stream = VideoStream(
    resolution=(1280, 720),  # Width x Height
    framerate=30,           # Target framerate
    format="MJPEG",        # Video format
    brightness=0.0,        # -1.0 to 1.0
    contrast=1.0,          # 0.0 to 2.0
    saturation=1.0         # 0.0 to 2.0
)
```

Common camera settings:
1. Resolution: Common values include (1920, 1080), (1280, 720), (640, 480)
2. Format: Usually "MJPEG" for web streaming
3. Framerate: Higher values (30+) for smooth video, lower values (15-) for reduced bandwidth

To see all available settings for your camera:
```bash
# List all video devices
v4l2-ctl --list-devices

# Show device capabilities (replace X with your device number)
v4l2-ctl -d /dev/videoX --all

# List supported formats
v4l2-ctl -d /dev/videoX --list-formats-ext
```

For USB cameras, you might also want to check:
```bash
# Show detailed USB device information
lsusb -v | grep -A 10 "Video"
```

### Performance Considerations
- Higher resolutions and framerates require more CPU and bandwidth
- MJPEG format provides good quality with reasonable bandwidth usage
- If streaming over the internet, consider lower resolutions and framerates
- Monitor CPU usage and network bandwidth to find optimal settings

## Development

If you want to modify the code:

1. Create a development environment:
```bash
# Clone and enter the repository
git clone https://github.com/glassontin/picamera2-webstream.git
cd picamera2-webstream

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .
```

2. Run tests (once implemented):
```bash
pip install pytest
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the picamera2 team for their excellent camera interface
- The Flask team for their lightweight web framework

## Intelligent Camera Detection

PiCamera2 Web Streamer now includes intelligent camera detection that ensures it always finds the correct camera device, even if Linux changes the /dev numbering:

1. **USB ID Detection**: Identifies cameras by vendor and product ID (e.g., Arducam 12MP = 0c45:636d)
2. **Name Pattern Matching**: Falls back to identifying cameras by name
3. **Configuration Options**: Fine-tune detection through config.ini
4. **Diagnostic Tool**: Use `examples/find_camera.py` to troubleshoot camera detection

### Configuration Options

In `config.ini`, you can configure camera detection:

```ini
[camera]
# Override auto-detection with a specific camera index
# camera_index = 0

# Force detection by USB vendor:product ID
usb_camera_id = 0c45:636d
```

## Improved Logging System

The new version includes a robust logging system:

1. **Configurable Log Levels**: Set log verbosity in config.ini with DEBUG, INFO, WARNING, ERROR, or CRITICAL
2. **Automatic Log Rotation**: Prevents log files from growing too large
3. **Log Compression**: Old logs are automatically compressed to save space

Logs are stored in `/var/log/picamera2-webstream.log` and rotated weekly.

## Troubleshooting

Common issues and solutions:

1. Camera not detected:
   - Ensure the camera is properly connected
   - Check if the camera interface is enabled in `raspi-config`
   - Verify with `libcamera-hello` command
   - Run the diagnostic tool: `python examples/find_camera.py`

2. Camera found but with incorrect device:
   - The system automatically detects the correct USB camera
   - Specify a USB ID in config.ini: `usb_camera_id = vendor:product`
   - Run the diagnostic tool to verify: `python examples/find_camera.py`

3. Excessive logging:
   - Reduce log level in config.ini: `level = WARNING`
   - Check service configuration: `Environment=LIBCAMERA_LOG_LEVELS=*:WARNING`
   - Rotate logs manually: `sudo logrotate /etc/logrotate.d/picamera2-webstream`

4. ImportError for picamera2:
   - Make sure system packages are installed: `sudo apt install python3-libcamera python3-picamera2`
   - Ensure you're using the virtual environment

5. Permission denied errors:
   - Ensure your user is in the video group: `sudo usermod -a -G video $USER`
   - Logout and login again for group changes to take effect
