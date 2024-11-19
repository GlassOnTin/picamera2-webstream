#!/usr/bin/env python3
import logging
import signal
from stream_ffmpeg import FFmpegStream, create_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def signal_handler(signum, frame):
    logging.info("Shutdown signal received")
    stream.stop()
    exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        stream = FFmpegStream(
            width=1280,
            height=720,
            framerate=30,
            device='/dev/video0'
        ).start()
        
        app = create_app(stream)
        
        context = ('cert.pem', 'key.pem')
        app.run(
            host='0.0.0.0', 
            port=443, 
            ssl_context=context,
            threaded=True
        )
    except Exception as e:
        logging.error(f"Server error: {str(e)}")
    finally:
        if 'stream' in globals():
            stream.stop()