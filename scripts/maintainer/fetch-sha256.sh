#!/bin/bash
# SHA256 Fetcher Script for Package Managers
#
# This script provides a reliable way to fetch SHA256 hashes for rxiv-maker
# packages from PyPI, fixing the shell interpolation issues that caused
# package manager update failures.
#
# Usage:
#   ./fetch-sha256.sh <version> [package_type]
#
# Examples:
#   ./fetch-sha256.sh 1.4.8           # Gets sdist SHA256
#   ./fetch-sha256.sh 1.4.8 sdist     # Gets sdist SHA256 explicitly
#   ./fetch-sha256.sh 1.4.8 wheel     # Gets wheel SHA256
#
# Environment Variables:
#   PACKAGE_NAME - Override package name (default: rxiv-maker)
#   DEBUG - Set to 1 for verbose output

set -euo pipefail

# Configuration
PACKAGE_NAME="${PACKAGE_NAME:-rxiv-maker}"
DEBUG="${DEBUG:-0}"

# Colors for output (if terminal supports it)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Logging functions
log_info() {
    if [[ "$DEBUG" == "1" ]]; then
        echo -e "${BLUE}INFO:${NC} $1" >&2
    fi
}

log_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1" >&2
}

log_error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

log_success() {
    if [[ "$DEBUG" == "1" ]]; then
        echo -e "${GREEN}SUCCESS:${NC} $1" >&2
    fi
}

# Usage function
usage() {
    cat << EOF
Usage: $0 <version> [package_type]

Fetch SHA256 hash for rxiv-maker package from PyPI.

Arguments:
  version       Package version (e.g., 1.4.8)
  package_type  Package type: sdist (default) or wheel

Environment Variables:
  PACKAGE_NAME  Override package name (default: rxiv-maker)
  DEBUG         Set to 1 for verbose output

Examples:
  $0 1.4.8           # Gets sdist SHA256
  $0 1.4.8 sdist     # Gets sdist SHA256 explicitly
  $0 1.4.8 wheel     # Gets wheel SHA256

Exit Codes:
  0  Success - SHA256 printed to stdout
  1  Error - Details printed to stderr
EOF
}

# Validate Python availability
check_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    else
        log_error "Python is required but not found in PATH"
        exit 1
    fi

    log_info "Using Python: $PYTHON_CMD"
}

# Fetch SHA256 using Python (more reliable than complex shell parsing)
fetch_sha256_python() {
    local version="$1"
    local package_type="${2:-sdist}"

    log_info "Fetching SHA256 for $PACKAGE_NAME version $version (type: $package_type)"

    # Use a here-document to avoid shell escaping issues
    local python_script
    python_script=$(cat << 'EOF'
import json
import sys
import urllib.request
import urllib.error

def main():
    package_name = sys.argv[1]
    version = sys.argv[2]
    package_type = sys.argv[3] if len(sys.argv) > 3 else 'sdist'

    url = f"https://pypi.org/pypi/{package_name}/json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))

        releases = data.get('releases', {})
        version_files = releases.get(version, [])

        if not version_files:
            print(f"No files found for version {version}", file=sys.stderr)
            sys.exit(1)

        # Look for the specified package type (handle wheel -> bdist_wheel mapping)
        search_type = 'bdist_wheel' if package_type == 'wheel' else package_type
        target_file = None
        for file_info in version_files:
            if file_info.get('packagetype') == search_type:
                target_file = file_info
                break

        # Fall back to sdist if requested type not found and we're looking for wheel
        if not target_file and package_type == 'wheel':
            for file_info in version_files:
                if file_info.get('packagetype') == 'sdist':
                    target_file = file_info
                    break

        # Fall back to any file if still not found
        if not target_file:
            target_file = version_files[0]

        sha256 = target_file.get('digests', {}).get('sha256')
        if not sha256:
            print("No SHA256 hash found", file=sys.stderr)
            sys.exit(1)

        print(sha256)

    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Invalid JSON response from PyPI", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
)

    # Execute Python script
    local sha256
    if sha256=$($PYTHON_CMD -c "$python_script" "$PACKAGE_NAME" "$version" "$package_type" 2>/dev/null); then
        log_success "SHA256 retrieved successfully"
        echo "$sha256"
        return 0
    else
        log_error "Failed to fetch SHA256 hash"
        return 1
    fi
}

# Validate SHA256 format
validate_sha256() {
    local sha256="$1"

    if [[ ! "$sha256" =~ ^[a-f0-9]{64}$ ]]; then
        log_error "Invalid SHA256 format: $sha256"
        return 1
    fi

    log_info "SHA256 format validation passed"
    return 0
}

# Main function
main() {
    # Parse arguments
    if [[ $# -lt 1 ]] || [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
        usage
        exit 0
    fi

    local version="$1"
    local package_type="${2:-sdist}"

    log_info "Starting SHA256 fetch for $PACKAGE_NAME $version"

    # Validate inputs
    if [[ -z "$version" ]]; then
        log_error "Version is required"
        usage
        exit 1
    fi

    if [[ "$package_type" != "sdist" ]] && [[ "$package_type" != "wheel" ]]; then
        log_error "Package type must be 'sdist' or 'wheel'"
        exit 1
    fi

    # Check Python availability
    check_python

    # Fetch SHA256
    local sha256
    if sha256=$(fetch_sha256_python "$version" "$package_type"); then
        # Validate SHA256 format
        if validate_sha256 "$sha256"; then
            # Output only the SHA256 (for script consumption)
            echo "$sha256"
            log_success "SHA256 fetch completed successfully"
            exit 0
        else
            exit 1
        fi
    else
        log_error "Failed to fetch SHA256 for $PACKAGE_NAME version $version"
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"
