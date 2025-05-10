#!/usr/bin/env python3
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picamera2_webstream.camera_utils import (
    list_available_cameras,
    find_arducam,
    get_camera_index
)

def main():
    """
    Utility to find and diagnose camera devices.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Camera Detection Utility")
    logging.info("=======================")
    
    # List all available cameras
    list_available_cameras()
    
    # Specifically try to find the Arducam
    camera_path = find_arducam()
    if camera_path:
        logging.info(f"\nArducam found at: {camera_path}")
        camera_index = get_camera_index()
        logging.info(f"Camera index for Picamera2: {camera_index}")
        logging.info("\nTo use this camera in your script:")
        logging.info(f"from picamera2 import Picamera2")
        logging.info(f"picam2 = Picamera2({camera_index})")
    else:
        logging.warning("\nArducam not found!")
        logging.info("Check that the camera is properly connected.")
        logging.info("You may need to manually specify the camera index.")

if __name__ == "__main__":
    main()