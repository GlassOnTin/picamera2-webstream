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

## Prerequisites

- Raspberry Pi (tested on Raspberry Pi 4)
- Raspberry Pi Camera Module
- Python 3.7+
- picamera2
- OpenCV
- Flask

## Installation

### Via pip
```bash
pip install picamera2-webstream
```

## Quick Installation

For a quick automated installation:

```bash
git clone https://github.com/yourusername/picamera2-webstream.git
cd picamera2-webstream
./install.sh
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
3. Run the example: `python examples/basic_stream.py`
4. Open `https://your-pi-ip` in your browser

To uninstall:
```bash
./uninstall.sh
```

## Usage

1. Basic usage:
```python
from picamera2_webstream import VideoStream
from flask import Flask

app = Flask(__name__)
stream = VideoStream()
stream.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context=('cert.pem', 'key.pem'))
```

2. Access the stream:
- Open your browser and navigate to `https://your-pi-ip`
- Accept the self-signed certificate warning
- View your camera stream!

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
git clone https://github.com/yourusername/picamera2-webstream.git
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

## Troubleshooting

Common issues and solutions:

1. Camera not detected:
   - Ensure the camera is properly connected
   - Check if the camera interface is enabled in `raspi-config`
   - Verify with `libcamera-hello` command

2. ImportError for picamera2:
   - Make sure system packages are installed: `sudo apt install python3-libcamera python3-picamera2`
   - Ensure you're using the virtual environment

3. SSL Certificate issues:
   - Regenerate certificates if they've expired
   - Ensure certificates are in the same directory as the script

4. Permission denied errors:
   - Ensure your user is in the video group: `sudo usermod -a -G video $USER`
   - Logout and login again for group changes to take effect
   
### Camera Access Issues

If you get errors about the camera being in use:

1. Check camera status:
```bash
python examples/check_camera.py
```

2. Stop any running camera services:
```bash
# Stop the web stream service if running
sudo systemctl stop picamera2-webstream

# Check what's using the camera
sudo fuser -v /dev/video0
```

3. Common issues:
- Service is running while trying to run example script
- Multiple instances trying to access the camera
- Camera is being used by another application
- Previous instance didn't clean up properly

### Running Multiple Instances

PiCamera2 only allows one process to access the camera at a time. To switch between:

1. Service to Interactive:
```bash
# Stop service first
sudo systemctl stop picamera2-webstream

# Then run your script
python examples/basic_stream.py
```

2. Interactive to Service:
```bash
# Stop your script (Ctrl+C)
# Then start service
sudo systemctl start picamera2-webstream
```