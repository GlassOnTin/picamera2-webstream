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

# Function to print usage
print_usage() {
    echo "Usage: $0 [-v <version>] [commit message]"
    echo
    echo "Options:"
    echo "  -v <version>  Specify version (e.g., 1.2.3)"
    echo "                If not specified, patch version will be incremented"
    echo
    echo "Examples:"
    echo "  $0 \"Fix bug in camera detection\""
    echo "  $0 -v 1.2.0 \"Add new feature X\""
    exit 1
}

# Function to validate version number
validate_version() {
    if ! [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format. Must be in format X.Y.Z (e.g., 1.2.3)"
        exit 1
    fi
}

# Function to get current version from pyproject.toml
get_current_version() {
    if [ ! -f "pyproject.toml" ]; then
        log_error "pyproject.toml not found"
        exit 1
    fi
    version=$(grep "^version = " pyproject.toml | cut -d'"' -f2)
    if [ -z "$version" ]; then
        log_error "Version not found in pyproject.toml"
        exit 1
    fi
    echo "$version"
}

# Function to increment patch version
increment_patch_version() {
    local version=$1
    local major=$(echo $version | cut -d. -f1)
    local minor=$(echo $version | cut -d. -f2)
    local patch=$(echo $version | cut -d. -f3)
    echo "$major.$minor.$((patch + 1))"
}

# Function to update version in files
update_version() {
    local new_version=$1
    
    # Update pyproject.toml
    sed -i "s/^version = .*/version = \"$new_version\"/" pyproject.toml
    
    # Update __init__.py if it exists
    if [ -f "picamera2_webstream/__init__.py" ]; then
        sed -i "s/__version__ = .*/__version__ = '$new_version'/" picamera2_webstream/__init__.py
    fi
}

# Parse arguments
while getopts ":v:h" opt; do
    case ${opt} in
        v )
            NEW_VERSION=$OPTARG
            validate_version $NEW_VERSION
            ;;
        h )
            print_usage
            ;;
        \? )
            log_error "Invalid option: $OPTARG"
            print_usage
            ;;
        : )
            log_error "Invalid option: $OPTARG requires an argument"
            print_usage
            ;;
    esac
done
shift $((OPTIND -1))

# Get commit message
COMMIT_MSG="$*"
if [ -z "$COMMIT_MSG" ]; then
    log_error "Commit message is required"
    print_usage
fi

# Get current version
CURRENT_VERSION=$(get_current_version)
log_info "Current version: $CURRENT_VERSION"

# Determine new version
if [ -z "$NEW_VERSION" ]; then
    NEW_VERSION=$(increment_patch_version $CURRENT_VERSION)
    log_info "Incrementing patch version to $NEW_VERSION"
fi

# Check if working directory is clean
if ! git diff-index --quiet HEAD --; then
    log_warn "You have uncommitted changes. These will be included in the version bump commit."
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in files
log_info "Updating version to $NEW_VERSION"
update_version $NEW_VERSION

# Git operations
log_info "Committing changes..."
git add pyproject.toml picamera2_webstream/__init__.py 2>/dev/null || true
git commit -m "Bump version to $NEW_VERSION: $COMMIT_MSG"

# Create git tag
log_info "Creating git tag v$NEW_VERSION..."
git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION: $COMMIT_MSG"

# Success message and next steps
echo
log_info "Version bump complete!"
echo "Next steps:"
echo "1. Push changes and tag:"
echo "   git push origin main"
echo "   git push origin v$NEW_VERSION"
echo
echo "2. Publish to PyPI:"
echo "   ./publish.sh"
echo
echo "3. Create GitHub release (optional):"
echo "   gh release create v$NEW_VERSION -t \"Version $NEW_VERSION\" -n \"$COMMIT_MSG\""