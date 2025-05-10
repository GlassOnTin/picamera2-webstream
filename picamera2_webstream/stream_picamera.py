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
from .camera_utils import get_camera_index

class VideoStream:
    def __init__(self, width=1280, height=720, framerate=30, format="MJPEG",
                 brightness=0.0, contrast=1.0, saturation=1.0):
        self.resolution = (width, height)
        self.lock = threading.Lock()
        self.frame_buffer = None
        self.stop_event = threading.Event()
        self.frame_count = 0
        self.clients = 0
        self.clients_lock = threading.Lock()
        self.framerate = framerate
        
        # Get the camera index using our utility function
        camera_index = get_camera_index()
        logging.info(f"Using camera at index {camera_index}")
        self.picam2 = Picamera2(camera_index)
        
        try:
            # Simple configuration without problematic controls
            config = self.picam2.create_video_configuration(
                main={"size": self.resolution, "format": format},
                buffer_count=4
            )
            
            # Configure the camera
            self.picam2.configure(config)
            
            # Apply camera controls after configuration
            self.set_camera_properties(brightness, contrast, saturation)
            
            self.buffer = io.BytesIO()
            logging.info("Camera configuration complete")
        except Exception as e:
            logging.error(f"Error configuring camera: {e}")
            raise
            
    def set_camera_properties(self, brightness, contrast, saturation):
        """
        Set camera properties safely using v4l2 controls if available
        """
        try:
            # Scale the normalized values to the camera's range
            # These are set through libcamera metadata
            controls = {}
            
            # Most v4l2 cameras support these controls but with different ranges
            # We use a try/except block for each control to handle unsupported ones
            try:
                # Brightness: Map 0.0 to midpoint of range (-1.0 to 1.0 -> -64 to 64)
                brightness_value = int(brightness * 64)
                logging.info(f"Setting brightness to {brightness_value}")
                controls["Brightness"] = brightness_value
            except Exception as e:
                logging.warning(f"Could not set brightness: {e}")
                
            try:
                # Contrast: Map normalized to camera range (0.0 to 2.0 -> 0 to 64)
                contrast_value = int(contrast * 32)
                logging.info(f"Setting contrast to {contrast_value}")
                controls["Contrast"] = contrast_value
            except Exception as e:
                logging.warning(f"Could not set contrast: {e}")
                
            try:
                # Saturation: Map normalized to camera range (0.0 to 2.0 -> 0 to 128)
                saturation_value = int(saturation * 64)
                logging.info(f"Setting saturation to {saturation_value}")
                controls["Saturation"] = saturation_value
            except Exception as e:
                logging.warning(f"Could not set saturation: {e}")
                
            # Apply controls if any were set
            if controls:
                logging.info(f"Applying camera controls: {controls}")
                self.picam2.set_controls(controls)
                
        except Exception as e:
            logging.warning(f"Error setting camera properties: {e}")
        
    def start(self):
        """Start the video streaming thread"""
        try:
            self.picam2.start()
            success = self._capture_single_frame()
            
            if not success:
                logging.error("Failed to capture initial frame")
                return None
                
            self.capture_thread = threading.Thread(target=self._capture_frames, 
                                               daemon=True, 
                                               name="CaptureThread")
            self.capture_thread.start()
            logging.info("Video stream started successfully")
            return self
        except Exception as e:
            logging.error(f"Error starting camera: {e}")
            return None
        
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
            try:
                self.picam2.stop()
            except Exception as e:
                logging.error(f"Error stopping camera: {e}")
        
    def _capture_frames(self):
        """Continuously capture frames from the camera"""
        frame_interval = 1/self.framerate
        retries = 0
        max_retries = 3

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
                    retries = 0  # Reset retries on success

                # Maintain frame rate
                elapsed = time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    sleep(sleep_time)

            except RuntimeError as e:
                logging.error(f"Runtime error during capture: {e}")
                retries += 1
                if retries >= max_retries:
                    logging.error("Max retries exceeded. Restarting camera...")
                    try:
                        self.picam2.stop()
                        sleep(1)  # Wait before restarting
                        self.picam2.start()
                        retries = 0
                    except Exception as restart_error:
                        logging.error(f"Error restarting camera: {restart_error}")
                        sleep(5)  # Give more time before next attempt
            except Exception as e:
                logging.error(f"Unexpected error during capture: {e}")
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