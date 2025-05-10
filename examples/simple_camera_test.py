#!/usr/bin/env python3
import os
import sys
import logging
from picamera2 import Picamera2
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    Simple camera test without any complex controls
    """
    logging.info("Starting simple camera test")
    
    try:
        # Initialize camera with index 0
        picam2 = Picamera2(0)
        logging.info("Camera initialized")
        
        # Create a simple configuration
        config = picam2.create_preview_configuration()
        logging.info("Configuration created")
        
        # Configure camera
        picam2.configure(config)
        logging.info("Camera configured")
        
        # Start camera
        picam2.start()
        logging.info("Camera started")
        
        # Wait a bit
        time.sleep(2)
        
        # Capture an image to test
        picam2.capture_file("test_image.jpg")
        logging.info("Captured test image to test_image.jpg")
        
        # Stop camera
        picam2.stop()
        logging.info("Camera stopped")
        
        logging.info("Test completed successfully")
        return True
    except Exception as e:
        logging.error(f"Error during test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)