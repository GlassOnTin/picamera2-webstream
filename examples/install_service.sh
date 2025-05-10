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

# Check if script is run as root
if [ "$EUID" -eq 0 ]; then
    log_error "Please do not run this script as root or with sudo"
    exit 1
fi

# Get the absolute path of the virtual environment
if [ ! -d "venv" ]; then
    log_error "Virtual environment not found. Please run install.sh first"
    exit 1
fi
VENV_PATH=$(readlink -f "venv")

# Get the absolute path of the installation directory
INSTALL_DIR=$(pwd)

# Create systemd service file
create_service_file() {
    cat > picamera2-webstream.service << EOL
[Unit]
Description=PiCamera2 Web Stream Service
After=network.target

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${VENV_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Reduce libcamera log level to prevent excessive logging
Environment=LIBCAMERA_LOG_LEVELS=*:WARNING
ExecStartPre=${VENV_PATH}/bin/python ${INSTALL_DIR}/examples/find_camera.py
ExecStart=${VENV_PATH}/bin/python ${INSTALL_DIR}/examples/picamera2-webstream.py
Restart=always
RestartSec=3
StandardOutput=append:/var/log/picamera2-webstream.log
StandardError=append:/var/log/picamera2-webstream.log

[Install]
WantedBy=multi-user.target
EOL

    log_info "Created systemd service file"
}

# Create the stream service script with improved camera detection
create_stream_script() {
    # Copy over the latest version of picamera2-webstream.py
    cp ${INSTALL_DIR}/examples/picamera2-webstream.py ${INSTALL_DIR}/examples/stream_service.py
    chmod +x ${INSTALL_DIR}/examples/stream_service.py

    log_info "Created service script using latest camera detection improvements"
}

# Create log file
sudo touch /var/log/picamera2-webstream.log
sudo chown $USER:$USER /var/log/picamera2-webstream.log
log_info "Created log file"

# Create log rotation configuration
create_logrotate_config() {
    log_info "Creating log rotation configuration..."
    cat > picamera2-webstream.logrotate << EOL
/var/log/picamera2-webstream.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 0644 root root
    postrotate
        systemctl restart picamera2-webstream.service
    endscript
}
EOL

    # Install logrotate configuration
    sudo cp picamera2-webstream.logrotate /etc/logrotate.d/picamera2-webstream
    log_info "Log rotation configuration installed"
}

# Create the service files
create_service_file
create_stream_script
create_logrotate_config

# Install the service
log_info "Installing systemd service..."
sudo cp picamera2-webstream.service /etc/systemd/system/
sudo systemctl daemon-reload

# Success message and next steps
echo
log_info "Service installation complete!"
echo
echo "To control the service:"
echo "  Start:   sudo systemctl start picamera2-webstream"
echo "  Stop:    sudo systemctl stop picamera2-webstream"
echo "  Status:  sudo systemctl status picamera2-webstream"
echo "  Enable:  sudo systemctl enable picamera2-webstream"
echo "  Logs:    tail -f /var/log/picamera2-webstream.log"
echo
read -p "Would you like to start and enable the service now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable picamera2-webstream
    sudo systemctl restart picamera2-webstream
    log_info "Service started and enabled"
    echo "Check the status with: sudo systemctl status picamera2-webstream"
else
    log_info "Service installed but not started"
    log_info "Start manually with: sudo systemctl start picamera2-webstream"
fi
