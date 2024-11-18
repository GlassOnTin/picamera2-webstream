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

### Via pip (Coming Soon)
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

## Configuration

You can customize various parameters when initializing the VideoStream:

```python
stream = VideoStream(
    resolution=(1280, 720),
    framerate=30,
    format="MJPEG",
    brightness=0.0,
    contrast=1.0,
    saturation=1.0
)
```

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