#!/bin/bash

# Test Homebrew Workflow Locally
# This script simulates the homebrew workflow validation steps for local testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Test Homebrew Workflow Locally

Usage: $0 [OPTIONS] [VERSION]

OPTIONS:
    -h, --help          Show this help message
    -v, --verbose       Enable verbose output
    --skip-install      Skip actual homebrew installation (just test version extraction)
    --test-extraction   Only test version extraction logic
    --cleanup           Clean up any existing installations

ARGUMENTS:
    VERSION             Version to test (e.g., 1.5.16). If not provided, uses current codebase version.

EXAMPLES:
    $0                          # Test with current codebase version
    $0 1.5.16                   # Test with specific version
    $0 --test-extraction        # Only test version extraction
    $0 --cleanup                # Clean up installations

This script helps validate homebrew workflow changes locally before deployment.
EOF
}

# Parse command line arguments
VERBOSE=false
SKIP_INSTALL=false
TEST_EXTRACTION_ONLY=false
CLEANUP_ONLY=false
TEST_VERSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --test-extraction)
            TEST_EXTRACTION_ONLY=true
            shift
            ;;
        --cleanup)
            CLEANUP_ONLY=true
            shift
            ;;
        [0-9]*)
            TEST_VERSION="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Cleanup function
cleanup_installations() {
    log_info "Cleaning up existing installations..."

    # Clean up homebrew installation
    if command -v brew >/dev/null 2>&1; then
        brew uninstall rxiv-maker 2>/dev/null || true
        brew untap HenriquesLab/rxiv-maker 2>/dev/null || true
        log_success "Homebrew cleanup completed"
    else
        log_warning "Homebrew not found, skipping brew cleanup"
    fi

    # Clean up pipx installation if present
    if command -v pipx >/dev/null 2>&1; then
        pipx uninstall rxiv-maker 2>/dev/null || true
        log_success "Pipx cleanup completed"
    fi
}

# Version extraction test function (simulates the workflow logic)
test_version_extraction() {
    local expected_version="$1"

    log_info "Testing version extraction logic..."

    # Check if rxiv command exists
    if ! command -v rxiv >/dev/null 2>&1; then
        log_error "rxiv command not found. Install rxiv-maker first or use --skip-install."
        return 1
    fi

    # Test version extraction with timeout (simulates workflow logic)
    log_info "Running version command with timeout..."

    if command -v timeout >/dev/null 2>&1; then
        VERSION_OUTPUT=$(timeout 30 rxiv --version 2>&1)
        VERSION_CMD_EXIT_CODE=$?
        if [ $VERSION_CMD_EXIT_CODE -eq 124 ]; then
            log_error "Version command timed out after 30 seconds"
            return 1
        elif [ $VERSION_CMD_EXIT_CODE -ne 0 ]; then
            log_error "Version command failed with exit code $VERSION_CMD_EXIT_CODE"
            echo "Output: '$VERSION_OUTPUT'"
            return 1
        fi
    else
        VERSION_OUTPUT=$(rxiv --version 2>&1)
        if [ $? -ne 0 ]; then
            log_error "Version command failed"
            echo "Output: '$VERSION_OUTPUT'"
            return 1
        fi
    fi

    if [ "$VERBOSE" = true ]; then
        echo "Raw version output: '$VERSION_OUTPUT'"
    fi

    # Extract version using multiple methods (simulates workflow logic)
    log_info "Testing version extraction methods..."

    # Method 1: sed extraction
    EXTRACTED_VERSION=$(echo "$VERSION_OUTPUT" | sed -n 's/.*version \([0-9][0-9.]*\).*/\1/p')

    if [ -z "$EXTRACTED_VERSION" ]; then
        log_warning "Primary version extraction failed, trying fallback methods..."
        # Method 2: specific regex fallback
        EXTRACTED_VERSION=$(echo "$VERSION_OUTPUT" | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
    fi

    if [ -z "$EXTRACTED_VERSION" ]; then
        log_warning "Fallback extraction failed, trying alternative regex..."
        # Method 3: general regex fallback
        EXTRACTED_VERSION=$(echo "$VERSION_OUTPUT" | grep -o '[0-9][0-9.]*' | head -1)
    fi

    # Validate extracted version format
    if [ -z "$EXTRACTED_VERSION" ]; then
        log_error "Failed to extract version from output: '$VERSION_OUTPUT'"
        return 1
    fi

    if ! echo "$EXTRACTED_VERSION" | grep -q '^[0-9][0-9.]*$'; then
        log_error "Invalid version format extracted: '$EXTRACTED_VERSION'"
        return 1
    fi

    log_success "Extracted version: '$EXTRACTED_VERSION'"

    # Compare with expected version if provided
    if [ -n "$expected_version" ]; then
        if [ "$EXTRACTED_VERSION" = "$expected_version" ]; then
            log_success "Version match: expected '$expected_version', got '$EXTRACTED_VERSION'"
        else
            log_error "Version mismatch: expected '$expected_version', got '$EXTRACTED_VERSION'"
            return 1
        fi
    fi

    return 0
}

# Get codebase version
get_codebase_version() {
    local codebase_version
    codebase_version=$(python -c "
import sys
import os
sys.path.insert(0, 'src')
try:
    from rxiv_maker import __version__
    print(__version__)
except ImportError as e:
    print(f'Error importing version: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$codebase_version" ]; then
        log_error "Failed to get codebase version"
        return 1
    fi

    echo "$codebase_version"
}

# Test homebrew installation
test_homebrew_installation() {
    local version="$1"

    log_info "Testing homebrew installation for version $version..."

    # Check if homebrew is available
    if ! command -v brew >/dev/null 2>&1; then
        log_error "Homebrew not found. Please install homebrew first."
        return 1
    fi

    # Clean up first
    cleanup_installations

    # Add tap
    log_info "Adding homebrew tap..."
    if ! brew tap HenriquesLab/rxiv-maker; then
        log_error "Failed to add homebrew tap"
        return 1
    fi

    # Install with retry logic (simulates workflow)
    log_info "Installing rxiv-maker with retry logic..."
    INSTALL_SUCCESS=false
    for attempt in {1..3}; do
        log_info "Installation attempt $attempt/3..."

        if brew install rxiv-maker; then
            log_success "Installation successful on attempt $attempt"
            INSTALL_SUCCESS=true
            break
        else
            log_warning "Installation failed on attempt $attempt"

            if [ $attempt -lt 3 ]; then
                log_info "Waiting 5 seconds before retry..."
                sleep 5

                # Clean up any partial installation
                log_info "Cleaning up before retry..."
                brew uninstall rxiv-maker 2>/dev/null || true
                brew cleanup || true
            fi
        fi
    done

    if [ "$INSTALL_SUCCESS" != "true" ]; then
        log_error "Installation failed after 3 attempts"
        return 1
    fi

    # Test version extraction
    if ! test_version_extraction "$version"; then
        log_error "Version extraction test failed"
        return 1
    fi

    log_success "Homebrew installation test completed successfully"
    return 0
}

# Main execution
main() {
    echo "Homebrew Workflow Local Testing"
    echo "==============================="

    # Handle cleanup-only mode
    if [ "$CLEANUP_ONLY" = true ]; then
        cleanup_installations
        log_success "Cleanup completed"
        exit 0
    fi

    # Get target version
    if [ -z "$TEST_VERSION" ]; then
        log_info "Getting codebase version..."
        TEST_VERSION=$(get_codebase_version)
        if [ $? -ne 0 ]; then
            exit 1
        fi
        log_info "Using codebase version: $TEST_VERSION"
    else
        log_info "Using specified version: $TEST_VERSION"
    fi

    # Test extraction only mode
    if [ "$TEST_EXTRACTION_ONLY" = true ]; then
        log_info "Testing version extraction only..."
        if test_version_extraction "$TEST_VERSION"; then
            log_success "Version extraction test passed"
            exit 0
        else
            log_error "Version extraction test failed"
            exit 1
        fi
    fi

    # Full test mode
    if [ "$SKIP_INSTALL" = true ]; then
        log_info "Skipping installation, testing extraction only..."
        if test_version_extraction "$TEST_VERSION"; then
            log_success "Version extraction test passed"
        else
            log_error "Version extraction test failed"
            exit 1
        fi
    else
        log_info "Running full homebrew installation test..."
        if test_homebrew_installation "$TEST_VERSION"; then
            log_success "All tests passed!"
        else
            log_error "Tests failed"
            exit 1
        fi
    fi
}

# Run main function
main "$@"
