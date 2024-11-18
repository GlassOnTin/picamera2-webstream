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

# Check if twine is installed
if ! command -v twine &>/dev/null; then
    log_info "Installing twine..."
    pip install twine
fi

# Clean previous builds
log_info "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Install build dependencies
log_info "Installing build tools..."
pip install --upgrade build

# Build the package
log_info "Building package..."
python -m build

# Check the distribution files
log_info "Checking distribution files..."
twine check dist/*

# Ask if we should upload to TestPyPI first
read -p "Would you like to upload to TestPyPI first? (Recommended) (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    log_info "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
    
    log_info "Testing installation from TestPyPI..."
    pip install --index-url https://test.pypi.org/simple/ picamera2-webstream
    
    read -p "Did the TestPyPI installation work correctly? Ready to publish to PyPI? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Aborting PyPI upload. Please fix any issues and try again."
        exit 0
    fi
fi

# Upload to PyPI
log_info "Uploading to PyPI..."
twine upload dist/*

log_info "Publishing complete!"
log_info "Package can now be installed with: pip install picamera2-webstream"