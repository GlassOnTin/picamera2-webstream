#!/bin/bash
set -e

# Text colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Main uninstallation process
main() {
    echo -e "${GREEN}PiCamera2 Web Streamer Uninstallation${NC}"
    echo "================================="
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        log_info "Deactivating virtual environment..."
        deactivate || true
    fi
    
    # Remove virtual environment
    if [ -d "venv" ]; then
        log_info "Removing virtual environment..."
        rm -rf venv
    fi
    
    # Remove SSL certificates
    if [ -f "cert.pem" ] || [ -f "key.pem" ]; then
        log_info "Removing SSL certificates..."
        rm -f cert.pem key.pem
    fi
    
    # Remove all package metadata (both old and new formats)
    log_info "Removing package metadata..."
    rm -rf *.egg-info
    rm -rf build/
    rm -rf dist/
    rm -rf .eggs/
    rm -rf __pycache__
    rm -rf picamera2_webstream/__pycache__
    rm -rf .pytest_cache
    
    # Remove config file if it exists
    if [ -f "config.ini" ]; then
        log_info "Removing configuration file..."
        rm -f config.ini
    fi
    
    log_info "Uninstallation complete!"
    log_info "System packages (python3-picamera2, etc.) were not removed."
    log_warn "If you want to remove system packages, you can use:"
    echo "sudo apt remove python3-picamera2 python3-libcamera python3-opencv python3-numpy python3-prctl"
    log_warn "You may need to reboot after removing system packages."
}

# Run main uninstallation
main