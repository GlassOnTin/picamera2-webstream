#!/usr/bin/env python3
import subprocess
import threading
import logging
from flask import Flask, Response
import io
import signal
from time import sleep

class VideoStream:
    def __init__(self, width=1280, height=720, framerate=30, device='/dev/video0'):
        self.width = width
        self.height = height
        self.framerate = framerate
        self.device = device
        self.process = None
        self.lock = threading.Lock()
        self.clients = 0
        self.clients_lock = threading.Lock()
        self.stop_event = threading.Event()

    def start(self):
        command = [
            'ffmpeg',
            '-f', 'v4l2',
            '-input_format', 'mjpeg',
            '-video_size', f'{self.width}x{self.height}',
            '-i', self.device,
            '-vf', f'scale={self.width}:{self.height}',
            '-c:v', 'mjpeg',
            '-q:v', '5',
            '-f', 'image2pipe',
            '-update', '1',
            '-'
        ]
        
        logging.info(f"Starting FFmpeg with command: {' '.join(command)}")
        
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**9
        )
        
        threading.Thread(target=self._log_stderr, daemon=True).start()
        return self

    def _read_frame(self):
        header = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
        footer = b'\r\n'
        buffer = bytearray()
        
        while not self.stop_event.is_set():
            try:
                # Read in chunks
                chunk = self.process.stdout.read(4096)
                if not chunk:
                    break
                    
                buffer.extend(chunk)
                
                # Look for JPEG end marker
                while len(buffer) > 2:
                    try:
                        # Find start marker
                        start = buffer.index(b'\xff\xd8')
                        # Find end marker
                        end = buffer.index(b'\xff\xd9', start) + 2
                        
                        # Extract the frame
                        frame = buffer[start:end]
                        # Remove the frame from buffer
                        buffer = buffer[end:]
                        
                        # Yield the frame
                        yield header + frame + footer
                        
                    except ValueError:
                        # Start or end marker not found
                        break
                        
                # Keep buffer size reasonable
                if len(buffer) > 1000000:
                    buffer = buffer[-50000:]
                    
            except Exception as e:
                logging.error(f"Error reading frame: {str(e)}")
                break

    def _log_stderr(self):
        """Log FFmpeg error output"""
        for line in iter(self.process.stderr.readline, b''):
            line_text = line.decode().strip()
            # Only log non-progress lines
            if not line_text.startswith('frame='):
                logging.info(f"FFmpeg: {line_text}")
    def stop(self):
        self.stop_event.set()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

def create_app(stream_instance):
    app = Flask(__name__)
    
    def generate_frames():
        with stream_instance.clients_lock:
            stream_instance.clients += 1
            logging.info(f"Client connected. Total clients: {stream_instance.clients}")
        
        try:
            for frame in stream_instance._read_frame():
                yield frame
        finally:
            with stream_instance.clients_lock:
                stream_instance.clients -= 1
                logging.info(f"Client disconnected. Remaining clients: {stream_instance.clients}")

    @app.route('/')
    def index():
        return """
        <html>
            <head>
                <title>FFmpeg Camera Stream</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { margin: 0; padding: 0; background: #000; }
                    .container { 
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                    }
                    img { max-width: 100%; height: auto; }
                </style>
            </head>
            <body>
                <div class="container">
                    <img src="/video_feed" alt="Camera Stream" />
                </div>
            </body>
        </html>
        """

    @app.route('/video_feed')
    def video_feed():
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    return app
