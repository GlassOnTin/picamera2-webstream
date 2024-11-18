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

# Stop and disable the service
log_info "Stopping and disabling service..."
sudo systemctl stop picamera2-webstream || true
sudo systemctl disable picamera2-webstream || true

# Remove service files
log_info "Removing service files..."
sudo rm -f /etc/systemd/system/picamera2-webstream.service
sudo systemctl daemon-reload

# Clean up log file
read -p "Remove log file? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo rm -f /var/log/picamera2-webstream.log
    log_info "Removed log file"
fi

log_info "Service uninstallation complete"