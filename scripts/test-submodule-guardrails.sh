#!/bin/bash
# test-submodule-guardrails.sh - Test all submodule guardrails

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ERRORS=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[TEST]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1" >&2
    ((ERRORS++))
}

test_homebrew_guardrails() {
    log_info "Testing Homebrew submodule guardrails..."

    cd "${REPO_ROOT}/submodules/homebrew-rxiv-maker"

    # Test baseline validation
    if ./scripts/validate-homebrew-integrity.sh >/dev/null 2>&1; then
        log_success "Homebrew baseline validation passed"
    else
        log_error "Homebrew baseline validation failed"
        return 1
    fi

    # Test contamination detection
    log_info "Testing Homebrew contamination detection..."

    # Create temporary contamination
    touch pyproject.toml

    if ./scripts/validate-homebrew-integrity.sh >/dev/null 2>&1; then
        log_error "Homebrew validation failed to detect contamination"
        rm -f pyproject.toml
        return 1
    else
        log_success "Homebrew validation correctly detected contamination"
    fi

    # Clean up
    rm -f pyproject.toml

    # Verify cleanup worked
    if ./scripts/validate-homebrew-integrity.sh >/dev/null 2>&1; then
        log_success "Homebrew validation passed after cleanup"
    else
        log_error "Homebrew validation failed after cleanup"
        return 1
    fi

    return 0
}

test_vscode_guardrails() {
    log_info "Testing VSCode submodule guardrails..."

    cd "${REPO_ROOT}/submodules/vscode-rxiv-maker"

    # Test baseline validation
    if node scripts/validate-vscode-integrity.js >/dev/null 2>&1; then
        log_success "VSCode baseline validation passed"
    else
        log_error "VSCode baseline validation failed"
        return 1
    fi

    # Test contamination detection
    log_info "Testing VSCode contamination detection..."

    # Create temporary contamination
    touch pyproject.toml

    if node scripts/validate-vscode-integrity.js >/dev/null 2>&1; then
        log_error "VSCode validation failed to detect contamination"
        rm -f pyproject.toml
        return 1
    else
        log_success "VSCode validation correctly detected contamination"
    fi

    # Clean up
    rm -f pyproject.toml

    # Verify cleanup worked
    if node scripts/validate-vscode-integrity.js >/dev/null 2>&1; then
        log_success "VSCode validation passed after cleanup"
    else
        log_error "VSCode validation failed after cleanup"
        return 1
    fi

    return 0
}

test_scoop_structure() {
    log_info "Testing Scoop submodule structure..."

    cd "${REPO_ROOT}/submodules/scoop-rxiv-maker"

    # Test JSON validity
    if python3 -m json.tool bucket/rxiv-maker.json >/dev/null 2>&1; then
        log_success "Scoop manifest JSON is valid"
    else
        log_error "Scoop manifest JSON is invalid"
        return 1
    fi

    # Check required files exist
    required_files=("bucket/rxiv-maker.json" "README.md")
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Found required Scoop file: $file"
        else
            log_error "Missing required Scoop file: $file"
            return 1
        fi
    done

    # Test contamination prevention via .gitignore
    forbidden_patterns=("*.py" "pyproject.toml" "Makefile" "Formula/")
    for pattern in "${forbidden_patterns[@]}"; do
        if grep -q "$pattern" .gitignore; then
            log_success "Scoop .gitignore prevents contamination: $pattern"
        else
            log_error "Scoop .gitignore missing contamination prevention: $pattern"
        fi
    done

    return 0
}

main() {
    log_info "Starting submodule guardrails testing..."
    log_info "Repository root: ${REPO_ROOT}"
    echo

    # Test each submodule
    test_homebrew_guardrails
    echo
    test_vscode_guardrails
    echo
    test_scoop_structure
    echo

    if [[ $ERRORS -eq 0 ]]; then
        log_success "🎉 All submodule guardrails tests passed!"
        log_info "All submodules are protected against contamination."
    else
        log_error "❌ Found ${ERRORS} test failure(s)."
        log_error "Some submodule guardrails may not be working correctly."
        exit 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
