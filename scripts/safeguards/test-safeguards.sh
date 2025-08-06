#!/bin/bash
# test-safeguards.sh - Test safeguards by simulating corruption scenarios
# WARNING: Only run this in a test branch - it will create temporary corruption!

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

log_info() {
    echo -e "${BLUE}[TEST]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1" >&2
}

# Test function that expects validation to FAIL
test_corruption_detection() {
    local test_name="$1"
    local setup_corruption="$2"
    local cleanup_corruption="$3"

    log_info "Testing: $test_name"

    # Set up corruption
    eval "$setup_corruption"

    # Run validation (should fail)
    if ./scripts/safeguards/validate-submodules.sh >/dev/null 2>&1; then
        log_error "$test_name - Validation passed when it should have failed!"
        eval "$cleanup_corruption"
        return 1
    else
        log_success "$test_name - Validation correctly detected corruption"
    fi

    # Clean up corruption
    eval "$cleanup_corruption"

    # Verify cleanup worked
    if ! ./scripts/safeguards/validate-submodules.sh >/dev/null 2>&1; then
        log_error "$test_name - Failed to clean up corruption!"
        return 1
    else
        log_success "$test_name - Cleanup successful"
    fi

    return 0
}

main() {
    cd "$REPO_ROOT"

    log_info "Starting safeguard corruption tests..."
    log_info "Repository: $REPO_ROOT"
    echo

    # Verify baseline state is clean
    if ! ./scripts/safeguards/validate-submodules.sh >/dev/null 2>&1; then
        log_error "Repository is not in a clean state before testing!"
        log_error "Please fix existing issues before running corruption tests."
        exit 1
    fi

    log_success "Baseline validation passed - starting corruption tests"
    echo

    # Test 1: URL Corruption
    test_corruption_detection \
        "URL Corruption Test" \
        "sed -i.bak 's/henriqueslab/CORRUPTED/' .gitmodules" \
        "mv .gitmodules.bak .gitmodules"

    # Test 2: File Contamination
    test_corruption_detection \
        "File Contamination Test" \
        "touch submodules/homebrew-rxiv-maker/contamination.py" \
        "rm -f submodules/homebrew-rxiv-maker/contamination.py"

    # Test 3: Missing Required Files (simulate by temporarily moving)
    test_corruption_detection \
        "Missing Required Files Test" \
        "mv submodules/vscode-rxiv-maker/package.json submodules/vscode-rxiv-maker/package.json.hidden" \
        "mv submodules/vscode-rxiv-maker/package.json.hidden submodules/vscode-rxiv-maker/package.json"

    # Test 4: VSCode Extension Contamination
    test_corruption_detection \
        "VSCode Contamination Test" \
        "mkdir -p submodules/vscode-rxiv-maker/src/rxiv_maker && touch submodules/vscode-rxiv-maker/pyproject.toml" \
        "rm -rf submodules/vscode-rxiv-maker/src/rxiv_maker submodules/vscode-rxiv-maker/pyproject.toml"

    echo
    log_success "🎉 All corruption detection tests passed!"
    log_info "The safeguards are working correctly and will catch repository corruption."

    # Final validation to ensure we're back to clean state
    if ./scripts/safeguards/validate-submodules.sh >/dev/null 2>&1; then
        log_success "Final validation: Repository is clean"
    else
        log_error "Final validation failed - cleanup may be incomplete"
        exit 1
    fi
}

# Only run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
