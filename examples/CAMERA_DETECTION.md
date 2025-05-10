# Camera Detection Guide

This guide explains how the improved camera detection system works in PiCamera2 Web Streamer.

## Overview

PiCamera2 Web Streamer now includes intelligent camera detection that ensures it always finds the correct camera device, even if Linux changes the /dev numbering between reboots or when devices are reconnected.

## How It Works

The camera detection system uses multiple methods to find the right camera:

1. **Config file settings**: First checks for explicit configuration in config.ini
2. **USB ID Detection**: Matches cameras by vendor ID and product ID (Hardware identifiers)
3. **Name Pattern Matching**: Falls back to identifying cameras by name
4. **Default fallback**: Uses camera index 0 if no specific camera is found

## Usage

### Testing Camera Detection

Run the detection tool to see what cameras are detected:

```bash
python examples/find_camera.py
```

This will:
- List all available cameras
- Show USB information including vendor/product IDs
- Identify which camera will be used
- Show the correct camera index

### Configuration

In `config.ini`, you can configure camera detection:

```ini
[camera]
# Explicitly set the camera index, bypassing auto-detection
# camera_index = 0

# Force detection by USB vendor:product ID (format: "vendor_id:product_id")
usb_camera_id = 0c45:636d
```

## Adding Support for New Cameras

To add detection for a specific USB camera:

1. Use `lsusb -v` to identify your camera's vendor:product ID
2. Add the ID to your config.ini file
3. For common cameras, you can add direct support in the code:

```python
def find_specific_camera() -> Optional[str]:
    # First try by USB ID
    device = find_camera_by_usb_id('vendor_id', 'product_id')
    if device:
        return device
    
    # Try by name pattern
    device = find_camera_by_name('Camera_Name')
    if device:
        return device
    
    return None
```

## Troubleshooting

If the camera detection isn't working:

1. **Check USB information**:
   ```bash
   lsusb -v | grep -A 5 "Camera"
   ```

2. **List video devices**:
   ```bash
   v4l2-ctl --list-devices
   ```

3. **Verify hardware detection**:
   ```bash
   ls -l /dev/video*
   ```

4. **Test a specific camera index**:
   Edit config.ini and set `camera_index = X` (where X is 0, 1, 2, etc.)

## USB Camera Reference

Common USB camera identifiers:

| Camera | Vendor ID | Product ID | Name Pattern |
|--------|-----------|------------|--------------|
| Arducam 12MP | 0c45 | 636d | Arducam_12MP |
| Raspberry Pi Camera Module 3 | 2bd9 | 0011 | Raspberry_Pi |
| Logitech C920 | 046d | 082d | HD_Pro_Webcam |

To add more cameras to this list, submit a pull request with the camera information.