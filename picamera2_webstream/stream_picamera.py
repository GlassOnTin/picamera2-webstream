#!/usr/bin/env python3
import cv2
import numpy as np
from flask import Flask, Response
import threading
from picamera2 import Picamera2
import logging
import io
from time import sleep, time
import signal

class VideoStream:
    def __init__(self, resolution=(1280, 720), framerate=30, format="MJPEG",
                 brightness=0.0, contrast=1.0, saturation=1.0):
        self.lock = threading.Lock()
        self.frame_buffer = None
        self.stop_event = threading.Event()
        self.frame_count = 0
        self.clients = 0
        self.clients_lock = threading.Lock()
        
        self.picam2 = Picamera2(0)
        
        config = self.picam2.create_video_configuration(
            main={"size": resolution, "format": format},
            controls={
                "Brightness": brightness,
                "Contrast": contrast,
                "Saturation": saturation,
                "AnalogueGain": 1.0,
                "AeEnable": True,
                "ExposureTime": int(1000000/framerate)
            },
            buffer_count=4
        )
        
        self.picam2.configure(config)
        self.buffer = io.BytesIO()
        self.framerate = framerate
        
    def start(self):
        """Start the video streaming thread"""
        self.picam2.start()
        self._capture_single_frame()
        self.capture_thread = threading.Thread(target=self._capture_frames, 
                                            daemon=True, 
                                            name="CaptureThread")
        self.capture_thread.start()
        return self
        
    def _capture_single_frame(self):
        """Capture a single frame"""
        try:
            self.buffer.seek(0)
            self.buffer.truncate()
            self.picam2.capture_file(self.buffer, format='jpeg')
            self.frame_buffer = self.buffer.getvalue()
            return True
        except Exception as e:
            logging.error(f"Error capturing initial frame: {str(e)}")
            return False
        
    def stop(self):
        """Stop the video streaming"""
        self.stop_event.set()
        if hasattr(self, 'picam2'):
            self.picam2.stop()
        
    def _capture_frames(self):
        """Continuously capture frames from the camera"""
        frame_interval = 1/self.framerate
        
        while not self.stop_event.is_set():
            try:
                start_time = time()
                
                # Only capture if we have clients or no frame
                if self.clients > 0 or self.frame_buffer is None:
                    self.buffer.seek(0)
                    self.buffer.truncate()
                    self.picam2.capture_file(self.buffer, format='jpeg')
                    jpeg_data = self.buffer.getvalue()
                    
                    with self.lock:
                        self.frame_buffer = jpeg_data
                        
                    if self.frame_count % 300 == 0:
                        logging.info(f"Stream stats - Frame: {self.frame_count}, "
                                   f"Size: {len(jpeg_data)} bytes, "
                                   f"Clients: {self.clients}")
                    self.frame_count += 1
                
                # Maintain frame rate
                elapsed = time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    sleep(sleep_time)
                    
            except Exception as e:
                logging.error(f"Error capturing frame: {str(e)}")
                sleep(0.1)

def create_app(stream_instance):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    def generate_frames():
        """Generator function to yield video frames"""
        with stream_instance.clients_lock:
            stream_instance.clients += 1
            logging.info(f"Client connected. Total clients: {stream_instance.clients}")
        
        try:
            while True:
                frame_data = None
                with stream_instance.lock:
                    if stream_instance.frame_buffer is not None:
                        frame_data = stream_instance.frame_buffer
                
                if frame_data is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_data)).encode() + b'\r\n'
                           b'\r\n' + frame_data + b'\r\n')
                
                sleep(1/stream_instance.framerate)
                
        finally:
            with stream_instance.clients_lock:
                stream_instance.clients -= 1
                logging.info(f"Client disconnected. Remaining clients: {stream_instance.clients}")

    @app.route('/video_feed')
    def video_feed():
        """Route to access the video stream"""
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    @app.route('/')
    def index():
        """Route for the main page"""
        return """
        <html>
            <head>
                <title>Pi Camera Stream</title>
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
    
    return app