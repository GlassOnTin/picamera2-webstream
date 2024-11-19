#!/bin/bash
set -e

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on a Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        log_error "This script must be run on a Raspberry Pi"
        exit 1
    fi
}

# Check if script is run as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root or with sudo"
        exit 1
    fi
}

# Install system dependencies
install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required packages
    sudo apt install -y \
        python3-full \
        python3-venv \
        ffmpeg \
        openssl \
        v4l-utils
        
    log_info "System dependencies installed successfully"
}

# Enable camera interface
enable_camera() {
    log_info "Checking camera setup..."
    
    # First check if raspi-config is available
    if ! command -v raspi-config >/dev/null 2>&1; then    
        log_error "raspi-config not found. Please ensure you are running on a Raspberry Pi"
        exit 1
    fi
    
    # Ask user if they want to enable the Raspberry Pi camera interface
    read -p "Are you using a Raspberry Pi Camera Module (CSI camera)? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping Raspberry Pi camera interface setup"
        return 0
    fi
    
    log_info "Enabling Raspberry Pi camera interface..."
    
    # Check if camera interface is already enabled
    if vcgencmd get_camera | grep -q "supported=1 detected=1"; then
        log_info "Camera interface is already enabled and camera is detected"
        return 0
    fi
    
    # Try to enable the camera interface
    if ! sudo raspi-config nonint do_camera 0; then
        log_error "Failed to enable camera interface"
        exit 1
    fi
    
    log_info "Camera interface enabled. A reboot may be required."
    
    # Ask user if they want to reboot now
    read -p "A reboot is recommended. Would you like to reboot now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rebooting system..."
        sudo reboot
    else
        log_warn "Please reboot your system manually to apply changes"
    fi
}

# Verify camera detection
verify_camera() {
    log_info "Verifying camera setup..."
    
    if ! libcamera-hello --version &>/dev/null; then
        log_error "libcamera-hello verification failed. Please check your installation"
        exit 1
    fi
    
    # Function to check for USB cameras
    check_usb_cameras() {
        local usb_found=0
        
        # Read the output into an array for proper processing
        while IFS= read -r line; do
            if [[ $line == *"usb"* ]]; then
                camera_name=${line%%:*}  # Get the camera name before the colon
                log_info "Found USB camera: $camera_name"
                usb_found=1
            fi
        done < <(v4l2-ctl --list-devices 2>/dev/null)
        
        # Return based on whether we found any USB cameras
        if [ $usb_found -eq 0 ]; then
            return 1
        else
            return 0
        fi
    }
    
    # Only check for CSI camera if user confirmed they're using one
    if [[ $ENABLE_CSI_CAMERA =~ ^[Yy]$ ]]; then
        if ! vcgencmd get_camera | grep -q "supported=1 detected=1"; then
            log_warn "Raspberry Pi Camera Module not detected. Please check your camera connection"
            log_warn "You may need to reboot after enabling the camera interface"
        else
            log_info "Raspberry Pi Camera Module detected successfully"
        fi
    else
        # Check for USB cameras
        if ! check_usb_cameras; then
            log_warn "No USB cameras were detected. Please check your camera connection"
            log_warn "Available video devices:"
            v4l2-ctl --list-devices
        else 
            log_info "USB camera(s) detected and ready"
        fi
    fi
    
    # Final verification of video devices
    if ! ls /dev/video* >/dev/null 2>&1; then
        log_error "No video devices found in /dev/"
        exit 1
    fi
}

# Setup virtual environment
setup_venv() {
    log_info "Setting up virtual environment..."
    
    # Check python3-venv is installed
    if ! dpkg -l | grep -q python3-venv; then
        log_error "python3-venv not installed. Installing now..."
        sudo apt install -y python3-venv
    fi
    
    # Remove existing venv if it exists
    if [ -d "venv" ]; then
        log_warn "Removing existing virtual environment..."
        rm -rf venv
    fi
    
    # Create fresh virtual environment with verbose output
    log_info "Creating virtual environment..."
    if ! python3 -m venv venv --system-site-packages; then
        log_error "Failed to create virtual environment"
        log_error "Please try: sudo apt install python3-venv python3-full"
        exit 1
    fi
    
    if [ ! -f "venv/bin/activate" ]; then
        log_error "Virtual environment created but activate script not found"
        exit 1
    fi
    
    # Try to activate virtual environment
    log_info "Activating virtual environment..."
    if ! source venv/bin/activate; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Verify we're in the virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        log_error "Virtual environment not properly activated"
        exit 1
    fi
    
    log_info "Virtual environment location: $VIRTUAL_ENV"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Flask and any other pure Python dependencies
    pip install flask
    
    log_info "Virtual environment setup complete"
}

# Generate SSL certificates
generate_ssl_certs() {
    log_info "Checking SSL certificates..."
    
    if [ -f "cert.pem" ] || [ -f "key.pem" ]; then
        log_warn "SSL certificates already exist."
        read -p "Would you like to generate new certificates? Existing ones will be backed up. (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing SSL certificates"
            return 0
        fi
        
        # Backup existing certificates
        local timestamp=$(date +%Y%m%d_%H%M%S)
        log_info "Backing up existing certificates..."
        if [ -f "cert.pem" ]; then
            mv cert.pem "cert.pem.backup_${timestamp}"
        fi
        if [ -f "key.pem" ]; then
            mv key.pem "key.pem.backup_${timestamp}"
        fi
        log_info "Existing certificates backed up with timestamp ${timestamp}"
    fi
    
    log_info "Generating new SSL certificates..."
    # Generate self-signed certificates
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out cert.pem -keyout key.pem -days 365 \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
    
    log_info "SSL certificates generated successfully"
}

# Add user to video group
add_to_video_group() {
    log_info "Adding user to video group..."
    
    if groups | grep -q "\bvideo\b"; then
        log_warn "User already in video group"
    else
        sudo usermod -a -G video $USER
        log_warn "User added to video group. Please log out and back in for changes to take effect."
    fi
}

# Install the package
install_package() {
    log_info "Installing picamera2-webstream..."
    pip install --use-pep517 -e .
    log_info "Package installed successfully"
}

# Create example configuration
create_config() {
    log_info "Creating example configuration..."
    cat > config.ini << EOL
[camera]
resolution_width = 1280
resolution_height = 720
framerate = 30
format = MJPEG
brightness = 0.0
contrast = 1.0
saturation = 1.0

[server]
port = 443
host = 0.0.0.0
EOL
}


# Main installation process
main() {
    echo -e "${GREEN}PiCamera2 Web Streamer Installation${NC}"
    echo "==============================="
    
    # Perform checks
    check_raspberry_pi
    check_root
    
    # Install everything
    install_system_dependencies
    
    # Store the camera type response for later use in verify_camera
    read -p "Are you using a Raspberry Pi Camera Module (CSI camera)? (y/N) " -n 1 -r ENABLE_CSI_CAMERA
    echo
    
    if [[ $ENABLE_CSI_CAMERA =~ ^[Yy]$ ]]; then
        enable_camera
    else
        log_info "Skipping Raspberry Pi camera interface setup"
    fi
    
    add_to_video_group
    setup_venv
    generate_ssl_certs
    verify_camera
    install_package
    create_config
    
    echo "==============================="
    log_info "Installation complete!"
    log_warn "Please log out and back in for group changes to take effect"
    log_info "To start using picamera2-webstream:"
    echo "1. Activate the virtual environment: source venv/bin/activate"
    echo "2. Run the example: python examples/basic_stream.py"
    echo "3. Open https://your-pi-ip in your browser"
}

# Run main installation
main