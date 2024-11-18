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

# Setup virtual environment for publishing
setup_venv() {
    log_info "Setting up virtual environment for publishing..."
    
    # Remove existing publish-venv if it exists
    if [ -d "publish-venv" ]; then
        log_warn "Removing existing publish virtual environment..."
        rm -rf publish-venv
    fi
    
    # Create fresh virtual environment
    python3 -m venv publish-venv
    
    # Activate virtual environment
    source publish-venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required publishing tools
    pip install twine build
    
    log_info "Virtual environment setup complete"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
    rm -rf publish-venv
}

# Set trap to clean up on exit
trap cleanup EXIT

# Clean previous builds
log_info "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Setup and activate virtual environment
setup_venv

# Build the package
log_info "Building package..."
python -m build

# Check the distribution files
log_info "Checking distribution files with twine..."
twine check dist/*

# Final confirmation before publishing
log_info "Ready to upload to PyPI"
log_warn "Please ensure you have:"
echo "1. Updated the version number in pyproject.toml"
echo "2. Committed all changes to git"
echo "3. Created a git tag for this version"
echo "4. Have your PyPI credentials ready (~/.pypirc)"
echo
read -p "Continue with PyPI upload? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Aborting PyPI upload."
    exit 0
fi

# Upload to PyPI
log_info "Uploading to PyPI..."
twine upload dist/*

log_info "Publishing complete!"
log_info "Package can now be installed with: pip install picamera2-webstream"
log_info "Please push the git tag: git push origin <tag-name>"