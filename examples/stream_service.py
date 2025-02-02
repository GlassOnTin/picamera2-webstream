#!/usr/bin/env python3
import logging
import signal
from picamera2_webstream import VideoStream, create_picamera_app
from picamera2_webstream import FFmpegStream, create_ffmpeg_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def signal_handler(signum, frame):
    """Handle shutdown gracefully"""
    logging.info("Shutdown signal received")
    stream.stop()
    exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    stream = None
    try:
        # Create and start the video stream
        stream = FFmpegStream(
            width=1280,
            height=720,
            framerate=30,
            device='/dev/video0'
        ).start()
        
        # Create Flask app with our stream
        app = create_ffmpeg_app(stream)
        
        # Run the server
        context = ('/home/ian/picamera2-webstream/cert.pem', '/home/ian/picamera2-webstream/key.pem')
        app.run(
            host='0.0.0.0',
            port=443,
            ssl_context=context,
            threaded=True
        )
    except Exception as e:
        logging.error(f"Server error: {str(e)}")
    finally:
        if stream: stream.stop()
