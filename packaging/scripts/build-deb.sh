#!/bin/bash
# build-deb.sh - Build Debian package for rxiv-maker
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BUILD_DIR="$PROJECT_ROOT/build/debian"
DEB_DIR="$BUILD_DIR/deb"

# Parse command line arguments
CLEAN=false
SIGN=false
GPG_KEY=""
OUTPUT_DIR="$PROJECT_ROOT/dist"

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Build Debian package for rxiv-maker

OPTIONS:
    -c, --clean        Clean build directory before building
    -s, --sign         Sign the package with GPG
    -k, --key KEY      GPG key ID to use for signing
    -o, --output DIR   Output directory for built packages (default: dist/)
    -h, --help         Show this help message

EXAMPLES:
    $0                              # Basic build
    $0 --clean                      # Clean build
    $0 --sign --key ABCD1234        # Build and sign with specific key
    $0 --clean --output /tmp/debs   # Clean build with custom output

ENVIRONMENT VARIABLES:
    RXIV_DEB_SIGN_KEY    Default GPG key for signing
    RXIV_DEB_OUTPUT      Default output directory

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -s|--sign)
            SIGN=true
            shift
            ;;
        -k|--key)
            GPG_KEY="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Use environment variables as fallbacks
GPG_KEY="${GPG_KEY:-${RXIV_DEB_SIGN_KEY:-}}"
OUTPUT_DIR="${OUTPUT_DIR:-${RXIV_DEB_OUTPUT:-$PROJECT_ROOT/dist}}"

# Validate environment
validate_environment() {
    log "Validating build environment..."

    # Check for required tools
    local required_tools=("dpkg-buildpackage" "debhelper" "python3" "pip")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            error "Required tool not found: $tool"
            warn "Install with: sudo apt-get install dpkg-dev debhelper python3 python3-pip"
            exit 1
        fi
    done

    # Check for optional tools
    if ! command -v "dh" >/dev/null 2>&1; then
        warn "debhelper 'dh' command not found, some features may not work"
    fi

    # Validate GPG setup if signing is requested
    if [[ "$SIGN" == "true" ]]; then
        if [[ -z "$GPG_KEY" ]]; then
            error "GPG signing requested but no key specified"
            warn "Use --key <KEY_ID> or set RXIV_DEB_SIGN_KEY environment variable"
            exit 1
        fi

        if ! command -v "gpg" >/dev/null 2>&1; then
            error "GPG not found but signing requested"
            exit 1
        fi

        # Test GPG key
        if ! gpg --list-secret-keys "$GPG_KEY" >/dev/null 2>&1; then
            error "GPG key not found or not accessible: $GPG_KEY"
            exit 1
        fi

        log "Using GPG key: $GPG_KEY"
    fi

    success "Environment validation passed"
}

# Get package version
get_version() {
    cd "$PROJECT_ROOT"
    python3 -c "exec(open('src/rxiv_maker/__version__.py').read()); print(__version__)"
}

# Update debian/changelog with current version
update_changelog() {
    local version="$1"
    local changelog_file="$PROJECT_ROOT/packaging/debian/changelog"
    local temp_file=$(mktemp)

    log "Updating debian/changelog for version $version"

    # Create new changelog entry
    cat > "$temp_file" << EOF
rxiv-maker ($version-1) stable; urgency=medium

  * Release version $version
  * See CHANGELOG.md for detailed changes
  * Automated build from release workflow

 -- Rxiv-Maker Contributors <rxiv.maker@gmail.com>  $(date -R)

EOF

    # Append existing changelog if it exists
    if [[ -f "$changelog_file" ]]; then
        cat "$changelog_file" >> "$temp_file"
    fi

    mv "$temp_file" "$changelog_file"
    success "Updated debian/changelog"
}

# Prepare build environment
prepare_build() {
    log "Preparing build environment..."

    if [[ "$CLEAN" == "true" ]]; then
        log "Cleaning build directory..."
        rm -rf "$BUILD_DIR"
    fi

    mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

    # Create source directory
    local src_dir="$BUILD_DIR/rxiv-maker-$(get_version)"
    rm -rf "$src_dir"

    # Copy source files
    log "Copying source files..."
    cp -r "$PROJECT_ROOT" "$src_dir"

    # Copy debian packaging files to source root
    log "Setting up debian packaging..."
    rm -rf "$src_dir/debian"
    cp -r "$PROJECT_ROOT/packaging/debian" "$src_dir/debian"

    # Clean up source directory
    cd "$src_dir"
    rm -rf .git .github __pycache__ .pytest_cache .coverage htmlcov
    rm -rf build dist *.egg-info packaging
    rm -rf test-results test_cache test_manuscript_cli
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # Update changelog
    update_changelog "$(get_version)"

    success "Build environment prepared"
}

# Build the package
build_package() {
    log "Building Debian package..."

    local src_dir="$BUILD_DIR/rxiv-maker-$(get_version)"
    cd "$src_dir"

    # Install build dependencies
    log "Installing build dependencies..."
    python3 -m pip install --user --upgrade build hatchling

    # Build the package
    local build_opts=()

    if [[ "$SIGN" == "true" ]]; then
        log "Building signed package with key: $GPG_KEY"
        build_opts+=("-k$GPG_KEY")
    else
        log "Building unsigned package"
        build_opts+=("-us" "-uc")  # unsigned source and changes
    fi

    # Add additional build options
    build_opts+=("-b")  # binary-only build
    build_opts+=("--build-profiles=nocheck")  # skip tests during build

    # Run dpkg-buildpackage
    log "Running dpkg-buildpackage with options: ${build_opts[*]}"
    if ! dpkg-buildpackage "${build_opts[@]}"; then
        error "Package build failed"
        exit 1
    fi

    success "Package built successfully"
}

# Post-build processing
post_build() {
    log "Processing built packages..."

    local version="$(get_version)"
    local build_parent="$(dirname "$BUILD_DIR/rxiv-maker-$version")"

    # Find built packages
    local deb_files=()
    while IFS= read -r -d '' file; do
        deb_files+=("$file")
    done < <(find "$build_parent" -name "*.deb" -print0)

    if [[ ${#deb_files[@]} -eq 0 ]]; then
        error "No .deb files found after build"
        exit 1
    fi

    # Copy packages to output directory
    log "Copying packages to output directory: $OUTPUT_DIR"
    for deb_file in "${deb_files[@]}"; do
        local filename=$(basename "$deb_file")
        cp "$deb_file" "$OUTPUT_DIR/"
        success "Package: $OUTPUT_DIR/$filename"
    done

    # Copy additional files if they exist
    for ext in "changes" "buildinfo" "dsc"; do
        find "$build_parent" -name "*.$ext" -exec cp {} "$OUTPUT_DIR/" \; 2>/dev/null || true
    done

    # Package information
    log "Package information:"
    for deb_file in "${deb_files[@]}"; do
        local filename=$(basename "$deb_file")
        local size=$(stat -f%z "$deb_file" 2>/dev/null || stat -c%s "$deb_file")
        log "  - $filename: $size bytes"

        # Show package info
        if command -v dpkg-deb >/dev/null 2>&1; then
            log "  Package details:"
            dpkg-deb --info "$deb_file" | sed 's/^/    /'
        fi
    done
}

# Validate built package
validate_package() {
    log "Validating built package..."

    local version="$(get_version)"
    local deb_file="$OUTPUT_DIR/rxiv-maker_${version}-1_all.deb"

    if [[ ! -f "$deb_file" ]]; then
        warn "Primary package file not found: $deb_file"
        return 0
    fi

    # Check package with lintian if available
    if command -v lintian >/dev/null 2>&1; then
        log "Running lintian checks..."
        if lintian "$deb_file"; then
            success "Lintian checks passed"
        else
            warn "Lintian found issues (non-fatal)"
        fi
    else
        warn "lintian not found, skipping package validation"
    fi

    # Test installation in chroot if available
    if command -v pbuilder >/dev/null 2>&1 && [[ -f /etc/pbuilderrc ]]; then
        log "Testing package installation..."
        # This would require pbuilder setup, skip for now
        warn "pbuilder test skipped (requires configuration)"
    fi
}

# Main execution
main() {
    log "Starting Debian package build for rxiv-maker"
    log "Project root: $PROJECT_ROOT"
    log "Build directory: $BUILD_DIR"
    log "Output directory: $OUTPUT_DIR"

    validate_environment
    prepare_build
    build_package
    post_build
    validate_package

    success "Debian package build completed successfully!"
    log "Built packages are available in: $OUTPUT_DIR"

    # Final instructions
    cat << EOF

📦 Installation Instructions:
   sudo dpkg -i $OUTPUT_DIR/rxiv-maker_*.deb
   sudo apt-get install -f  # Fix any dependency issues

🔍 Package Contents:
   dpkg-deb --contents $OUTPUT_DIR/rxiv-maker_*.deb

📋 Package Info:
   dpkg-deb --info $OUTPUT_DIR/rxiv-maker_*.deb

EOF
}

# Run main function
main "$@"
