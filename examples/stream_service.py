#!/usr/bin/env python3
import logging
import signal
from picamera2_webstream import VideoStream, create_app

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
    
    try:
        # Create and start the video stream
        stream = VideoStream(
            resolution=(1280, 720),
            framerate=30,
            brightness=0.0,
            contrast=1.0,
            saturation=1.0
        ).start()
        
        # Create Flask app with our stream
        app = create_app(stream)
        
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
        stream.stop()
