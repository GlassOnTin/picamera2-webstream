#!/usr/bin/env python3
import sys
import json
import subprocess
from picamera2 import Picamera2
import logging
from time import sleep

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def get_v4l2_devices():
    """Get list of video devices and their capabilities"""
    try:
        # Get list of all video devices
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True)
        devices = result.stdout.split('\n\n')
        
        device_info = []
        for device in devices:
            if not device.strip():
                continue
            
            lines = device.strip().split('\n')
            device_name = lines[0].strip(':')
            device_paths = [l.strip() for l in lines[1:] if 'video' in l]
            
            for path in device_paths:
                try:
                    # Get device capabilities
                    caps = subprocess.run(['v4l2-ctl', '--device', path, '--all'],
                                        capture_output=True, text=True)
                    device_info.append({
                        'name': device_name,
                        'path': path,
                        'capabilities': caps.stdout
                    })
                except subprocess.CalledProcessError:
                    logging.warning(f"Could not get capabilities for {path}")
                    
        return device_info
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running v4l2-ctl: {e}")
        return []

def test_camera_settings(device_path=None):
    """Test different camera settings and report results"""
    picam2 = Picamera2()
    
    # Get all camera configurations
    configs = picam2.sensor_modes
    
    logging.info("Available camera configurations:")
    for i, config in enumerate(configs):
        logging.info(f"Mode {i}: {json.dumps(config, indent=2)}")
    
    # Test different formats and resolutions
    test_configs = [
        {"size": (1920, 1080), "format": "MJPEG"},
        {"size": (1280, 720), "format": "MJPEG"},
        {"size": (640, 480), "format": "MJPEG"},
    ]
    
    logging.info("\nTesting different configurations:")
    results = []
    for config in test_configs:
        try:
            camera_config = picam2.create_video_configuration(
                main={"size": config["size"], 
                      "format": config["format"]},
                buffer_count=4
            )
            picam2.configure(camera_config)
            picam2.start()
            
            # Test framerate
            frames = 0
            start_time = time.time()
            for _ in range(30):  # Test for 30 frames
                picam2.capture_array()
                frames += 1
            
            duration = time.time() - start_time
            fps = frames / duration
            
            results.append({
                "config": config,
                "success": True,
                "fps": fps,
                "error": None
            })
            
            picam2.stop()
            sleep(0.5)  # Give camera time to reset
            
        except Exception as e:
            results.append({
                "config": config,
                "success": False,
                "fps": 0,
                "error": str(e)
            })
            picam2.stop()
            sleep(0.5)
    
    return results

def main():
    logging.info("Camera Diagnostics Tool")
    logging.info("======================")
    
    # Check for v4l2-utils
    try:
        subprocess.run(['v4l2-ctl', '--version'], capture_output=True)
    except FileNotFoundError:
        logging.error("v4l2-utils not found. Please install with:")
        logging.error("sudo apt install v4l2-utils")
        sys.exit(1)
    
    # Get device information
    logging.info("\nDetecting video devices...")
    devices = get_v4l2_devices()
    
    if not devices:
        logging.error("No video devices found!")
        sys.exit(1)
    
    # Print device information
    for device in devices:
        logging.info(f"\nDevice: {device['name']}")
        logging.info(f"Path: {device['path']}")
        logging.info("Capabilities:")
        print(device['capabilities'])
    
    # Test camera settings
    logging.info("\nTesting camera configurations...")
    results = test_camera_settings()
    
    logging.info("\nTest Results:")
    for result in results:
        config = result["config"]
        if result["success"]:
            logging.info(
                f"Resolution: {config['size']}, Format: {config['format']}"
                f" - {result['fps']:.1f} FPS"
            )
        else:
            logging.warning(
                f"Resolution: {config['size']}, Format: {config['format']}"
                f" - Failed: {result['error']}"
            )
    
    logging.info("\nRecommended Configuration:")
    # Find best performing configuration
    successful_results = [r for r in results if r["success"]]
    if successful_results:
        best = max(successful_results, key=lambda x: x["fps"])
        print(f"""
stream = VideoStream(
    resolution={best['config']['size']},
    framerate={int(best['fps'])},
    format="{best['config']['format']}",
    brightness=0.0,
    contrast=1.0,
    saturation=1.0
)
""")
    else:
        logging.error("No working configurations found!")

if __name__ == "__main__":
    main()