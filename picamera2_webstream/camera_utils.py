#!/usr/bin/env python3
import subprocess
import re
import os
import logging
from typing import Dict, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

def get_v4l2_devices() -> List[Dict]:
    """
    Get a list of all video devices with their detailed information.
    
    Returns:
        List of dictionaries containing device information
    """
    try:
        # Get list of all video devices
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True, check=True)
        devices = result.stdout.strip().split('\n\n')
        
        device_info = []
        for device_block in devices:
            if not device_block.strip():
                continue
            
            lines = device_block.strip().split('\n')
            device_name = lines[0].strip().rstrip(':')
            
            # Extract device paths that contain 'video'
            device_paths = [l.strip() for l in lines[1:] if '/dev/video' in l]
            
            if not device_paths:
                continue
                
            # Get first video device for capabilities
            main_device = device_paths[0]
            
            try:
                # Get device capabilities
                caps = subprocess.run(['v4l2-ctl', '--device', main_device, '--info'],
                                    capture_output=True, text=True, check=True)
                
                # Get USB info if it's a USB device
                usb_info = {}
                if 'usb' in device_name.lower() or 'usb' in device_block.lower():
                    for path in device_paths:
                        # Extract the device number
                        vid_match = re.search(r'/dev/video(\d+)', path)
                        if vid_match:
                            vid_num = vid_match.group(1)
                            sys_path = f"/sys/class/video4linux/video{vid_num}/device"
                            
                            if os.path.exists(sys_path):
                                # Try to find USB vendor and product ID
                                try:
                                    # Navigate up to find the USB device info
                                    vendor_paths = list(subprocess.run(
                                        ['find', sys_path, '-name', 'idVendor'],
                                        capture_output=True, text=True, check=True
                                    ).stdout.strip().split('\n'))
                                    
                                    if vendor_paths and vendor_paths[0]:
                                        vendor_path = vendor_paths[0]
                                        product_path = os.path.join(os.path.dirname(vendor_path), 'idProduct')
                                        
                                        if os.path.exists(vendor_path) and os.path.exists(product_path):
                                            with open(vendor_path, 'r') as f:
                                                vendor_id = f.read().strip()
                                            with open(product_path, 'r') as f:
                                                product_id = f.read().strip()
                                                
                                            usb_info['vendor_id'] = vendor_id
                                            usb_info['product_id'] = product_id
                                            
                                            # Also try to get manufacturer and product strings
                                            mfg_path = os.path.join(os.path.dirname(vendor_path), 'manufacturer')
                                            prod_path = os.path.join(os.path.dirname(vendor_path), 'product')
                                            
                                            if os.path.exists(mfg_path):
                                                with open(mfg_path, 'r') as f:
                                                    usb_info['manufacturer'] = f.read().strip()
                                            
                                            if os.path.exists(prod_path):
                                                with open(prod_path, 'r') as f:
                                                    usb_info['product'] = f.read().strip()
                                except Exception as e:
                                    logger.debug(f"Could not get USB details: {e}")
                
                device_info.append({
                    'name': device_name,
                    'paths': device_paths,
                    'main_path': main_device,
                    'capabilities': caps.stdout,
                    'usb_info': usb_info
                })
            except subprocess.CalledProcessError:
                logger.warning(f"Could not get capabilities for {main_device}")
                
        return device_info
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running v4l2-ctl: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def find_camera_by_usb_id(vendor_id: str, product_id: str) -> Optional[str]:
    """
    Find a camera device by its USB vendor and product ID.
    
    Args:
        vendor_id: USB vendor ID (e.g., '0c45')
        product_id: USB product ID (e.g., '636d')
        
    Returns:
        Path to the camera device or None if not found
    """
    devices = get_v4l2_devices()
    
    for device in devices:
        usb_info = device.get('usb_info', {})
        if (usb_info.get('vendor_id', '').lower() == vendor_id.lower() and 
            usb_info.get('product_id', '').lower() == product_id.lower()):
            # Return the first video device path
            return device['main_path']
    
    return None

def find_camera_by_name(name_pattern: str) -> Optional[str]:
    """
    Find a camera device by its name using a pattern match.
    
    Args:
        name_pattern: String pattern to match in device name
        
    Returns:
        Path to the camera device or None if not found
    """
    devices = get_v4l2_devices()
    
    for device in devices:
        if name_pattern.lower() in device['name'].lower():
            return device['main_path']
    
    return None

def find_arducam() -> Optional[str]:
    """
    Find the Arducam device specifically.
    
    Returns:
        Path to the Arducam device or None if not found
    """
    # First try by USB ID (Arducam 12MP is 0c45:636d)
    device = find_camera_by_usb_id('0c45', '636d')
    if device:
        return device
    
    # Try by name
    device = find_camera_by_name('Arducam')
    if device:
        return device
    
    return None

def get_camera_index() -> int:
    """
    Get the camera index to use with Picamera2.

    This function tries to find the correct camera based on:
    1. Config file settings (if present)
    2. USB camera ID or name pattern matching

    Returns:
        Camera index (0, 1, 2, etc.) or 0 if not found
    """
    # Try to read from config file
    try:
        import configparser
        import os

        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')

        if os.path.exists(config_path):
            config.read(config_path)

            # Check if camera_index is explicitly set
            if 'camera' in config and 'camera_index' in config['camera']:
                try:
                    index = int(config['camera']['camera_index'])
                    logger.info(f"Using camera index {index} from config file")
                    return index
                except ValueError:
                    logger.warning("Invalid camera_index in config file")

            # Check if USB camera ID is specified
            if 'camera' in config and 'usb_camera_id' in config['camera']:
                usb_id = config['camera']['usb_camera_id']
                if ':' in usb_id:
                    vendor_id, product_id = usb_id.split(':')
                    logger.info(f"Looking for USB camera with ID {vendor_id}:{product_id}")
                    camera_path = find_camera_by_usb_id(vendor_id, product_id)
                    if camera_path:
                        match = re.search(r'/dev/video(\d+)', camera_path)
                        if match:
                            index = int(match.group(1))
                            logger.info(f"Found USB camera at {camera_path} with index {index}")
                            return index
    except Exception as e:
        logger.warning(f"Error reading config file: {e}")

    # Fall back to finding Arducam
    camera_path = find_arducam()

    if not camera_path:
        logger.warning("Could not find specific camera. Using default camera index 0.")
        return 0

    # Extract index from device path (e.g., /dev/video0 -> 0)
    match = re.search(r'/dev/video(\d+)', camera_path)
    if match:
        index = int(match.group(1))
        logger.info(f"Found Arducam at {camera_path} with index {index}")
        return index

    logger.warning(f"Could not determine index from path {camera_path}. Using default index 0.")
    return 0

def list_available_cameras() -> None:
    """
    List all available camera devices with their information.
    Useful for diagnostics.
    """
    devices = get_v4l2_devices()
    
    logger.info(f"Found {len(devices)} camera devices:")
    for i, device in enumerate(devices):
        logger.info(f"\nCamera {i+1}: {device['name']}")
        logger.info(f"Paths: {', '.join(device['paths'])}")
        
        if device['usb_info']:
            usb = device['usb_info']
            logger.info("USB Information:")
            if 'vendor_id' in usb and 'product_id' in usb:
                logger.info(f"  ID: {usb.get('vendor_id', 'Unknown')}:{usb.get('product_id', 'Unknown')}")
            if 'manufacturer' in usb:
                logger.info(f"  Manufacturer: {usb.get('manufacturer', 'Unknown')}")
            if 'product' in usb:
                logger.info(f"  Product: {usb.get('product', 'Unknown')}")

if __name__ == '__main__':
    # Set up logging if run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # List all cameras
    list_available_cameras()
    
    # Try to find Arducam
    arducam_path = find_arducam()
    if arducam_path:
        logger.info(f"\nFound Arducam at {arducam_path}")
        logger.info(f"Use camera index: {get_camera_index()}")
    else:
        logger.info("\nCould not find Arducam")