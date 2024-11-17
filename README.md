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

### Manual Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/picamera2-webstream.git
cd picamera2-webstream
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Generate SSL certificates:
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the picamera2 team for their excellent camera interface
- The Flask team for their lightweight web framework

