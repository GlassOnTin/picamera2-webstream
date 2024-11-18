#!/usr/bin/env python3
import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_camera_status():
    """Comprehensive camera status check"""
    logger.info("Checking camera status...")
    
    # Check for video devices
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True)
        logger.info("\nAvailable video devices:")
        print(result.stdout)
    except subprocess.CalledProcessError:
        logger.error("Failed to list video devices")
    
    # Check processes using video devices
    logger.info("\nChecking for processes using the camera:")
    for i in range(5):  # Check video0 through video4
        try:
            result = subprocess.run(
                ['sudo', 'fuser', '-v', f'/dev/video{i}'],
                capture_output=True,
                text=True
            )
            if result.stderr:
                print(f"\nProcesses using /dev/video{i}:")
                print(result.stderr)
        except subprocess.CalledProcessError:
            continue
    
    # Check systemd service status
    try:
        result = subprocess.run(
            ['systemctl', 'status', 'picamera2-webstream'],
            capture_output=True,
            text=True
        )
        logger.info("\nPiCamera2 Web Stream service status:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        if e.returncode == 4:
            logger.info("PiCamera2 Web Stream service is not running")
        else:
            logger.error("Failed to check service status")

if __name__ == "__main__":
    check_camera_status()