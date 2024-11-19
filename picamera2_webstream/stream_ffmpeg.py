#!/usr/bin/env python3
import subprocess
import threading
import logging
from flask import Flask, Response
import io
import signal
from time import sleep

class FFmpegStream:
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
            '-f', 'video4linux2',
            '-input_format', 'mjpeg',
            '-i', self.device,
            '-c:v', 'mjpeg',
            '-f', 'mpjpeg',
            '-q:v', '5',  # Quality factor (2-31, lower is better)
            '-r', str(self.framerate),
            '-s', f'{self.width}x{self.height}',
            '-'  # Output to pipe
        ]
        
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return self

    def stop(self):
        self.stop_event.set()
        if self.process:
            self.process.terminate()
            self.process.wait()

    def _read_frame(self):
        marker = b'--ffmpeg\r\nContent-Type: image/jpeg\r\n'
        while not self.stop_event.is_set():
            if self.process.poll() is not None:
                break
                
            frame = io.BytesIO()
            while True:
                chunk = self.process.stdout.read(1024)
                if not chunk:
                    break
                frame.write(chunk)
                if chunk.endswith(b'\xff\xd9'):  # JPEG end marker
                    frame_data = frame.getvalue()
                    yield marker + b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n\r\n' + frame_data + b'\r\n'
                    break

def create_app(stream_instance):
    app = Flask(__name__)
    
    def generate_frames():
        with stream_instance.clients_lock:
            stream_instance.clients += 1
            logging.info(f"Client connected. Total clients: {stream_instance.clients}")
        
        try:
            yield from stream_instance._read_frame()
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
            mimetype='multipart/x-mixed-replace; boundary=ffmpeg'
        )

    return app