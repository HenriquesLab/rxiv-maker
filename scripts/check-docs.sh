#!/bin/bash
# 📋 Local Documentation Validation Script
# Part of Phase 3.4c: Create living documentation with automated validation

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VALIDATION_SCRIPT="$SCRIPT_DIR/validate_documentation.py"
REPORT_FILE="$PROJECT_ROOT/docs_validation_report.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo "📋 DOCUMENTATION VALIDATION"
    echo "============================"
    echo "Validating code examples in documentation..."
    echo
}

print_separator() {
    echo
    echo "────────────────────────────────────────"
    echo
}

check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not installed"
        return 1
    fi

    # Check validation script exists
    if [ ! -f "$VALIDATION_SCRIPT" ]; then
        log_error "Validation script not found at: $VALIDATION_SCRIPT"
        return 1
    fi

    # Install Python dependencies if needed
    if ! python3 -c "import yaml" 2>/dev/null; then
        log_warning "PyYAML not found, installing..."
        pip3 install --user PyYAML
    fi

    log_success "Dependencies OK"
    return 0
}

run_validation() {
    local verbose_flag=""
    local files_to_check=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                verbose_flag="--verbose"
                shift
                ;;
            -f|--files)
                shift
                files_to_check="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                return 1
                ;;
        esac
    done

    log_info "Running validation..."

    # Build command
    local cmd="python3 \"$VALIDATION_SCRIPT\" --docs-dir \"$PROJECT_ROOT\" --output \"$REPORT_FILE\""

    if [ -n "$verbose_flag" ]; then
        cmd="$cmd $verbose_flag"
    fi

    if [ -n "$files_to_check" ]; then
        cmd="$cmd --files $files_to_check"
    fi

    # Run validation
    if eval "$cmd"; then
        log_success "Validation completed successfully"
        return 0
    else
        log_error "Validation failed"
        return 1
    fi
}

show_results() {
    if [ -f "$REPORT_FILE" ]; then
        print_separator
        log_info "Validation Results Summary:"
        echo

        # Extract key metrics
        local total_files=$(grep -o "Files processed.*: [0-9]*" "$REPORT_FILE" | grep -o "[0-9]*" | head -1)
        local total_blocks=$(grep -o "Code blocks found.*: [0-9]*" "$REPORT_FILE" | grep -o "[0-9]*" | head -1)
        local valid_blocks=$(grep -o "Valid blocks.*: [0-9]*" "$REPORT_FILE" | grep -o "[0-9]*" | head -1)
        local invalid_blocks=$(grep -o "Invalid blocks.*: [0-9]*" "$REPORT_FILE" | grep -o "[0-9]*" | head -1)
        local success_rate=$(grep -o "Success rate.*: [0-9]*\.[0-9]*" "$REPORT_FILE" | grep -o "[0-9]*\.[0-9]*" | head -1)

        echo "  📁 Files processed:    ${total_files:-0}"
        echo "  📝 Code blocks found:  ${total_blocks:-0}"
        echo "  ✅ Valid blocks:       ${valid_blocks:-0}"
        echo "  ❌ Invalid blocks:     ${invalid_blocks:-0}"
        echo "  📊 Success rate:       ${success_rate:-0}%"

        # Status indicator
        if [ -n "$success_rate" ]; then
            local rate_int=$(echo "$success_rate" | cut -d. -f1)
            if [ "$rate_int" -ge 95 ]; then
                echo -e "  🎯 Status:             ${GREEN}EXCELLENT${NC}"
            elif [ "$rate_int" -ge 90 ]; then
                echo -e "  🎯 Status:             ${YELLOW}GOOD${NC}"
            elif [ "$rate_int" -ge 75 ]; then
                echo -e "  🎯 Status:             ${YELLOW}NEEDS ATTENTION${NC}"
            else
                echo -e "  🎯 Status:             ${RED}CRITICAL${NC}"
            fi
        fi

        print_separator
        log_info "Full report saved to: $REPORT_FILE"

        # Show issues if any
        if grep -q "## ❌ Issues Found" "$REPORT_FILE"; then
            echo
            log_warning "Issues found in documentation:"
            echo
            # Extract and display first few issues
            sed -n '/## ❌ Issues Found/,/## ✅ Validation Results by File/p' "$REPORT_FILE" | head -20
        fi
    else
        log_error "Validation report not found"
        return 1
    fi
}

run_quick_check() {
    log_info "Running quick documentation check..."

    # Check for common issues in markdown files
    local issues_found=0

    log_info "Checking for common markdown issues..."

    # Check for broken internal links
    for md_file in "$PROJECT_ROOT"/*.md; do
        if [ -f "$md_file" ]; then
            # Check for broken markdown links
            if grep -n '\]\([^)]*\)' "$md_file" | grep -v 'http' | grep -v '#' >/dev/null; then
                log_warning "Potential broken links in $(basename "$md_file")"
                ((issues_found++))
            fi
        fi
    done

    # Check for outdated version references
    if grep -r "v1\.[0-4]\." "$PROJECT_ROOT"/*.md 2>/dev/null >/dev/null; then
        log_warning "Found potentially outdated version references"
        ((issues_found++))
    fi

    if [ $issues_found -eq 0 ]; then
        log_success "Quick check passed"
        return 0
    else
        log_warning "Quick check found $issues_found potential issues"
        return 1
    fi
}

show_help() {
    echo "📋 Documentation Validation Script"
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -v, --verbose         Enable verbose output"
    echo "  -f, --files FILES     Validate only specific files"
    echo "  -q, --quick          Run quick check only"
    echo "  -h, --help           Show this help message"
    echo
    echo "Examples:"
    echo "  $0                    # Validate all documentation"
    echo "  $0 --verbose          # Verbose validation"
    echo "  $0 -f \"README.md\"     # Validate only README.md"
    echo "  $0 --quick            # Quick check for common issues"
    echo
}

# Main execution
main() {
    print_header

    # Parse global options
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -q|--quick)
            run_quick_check
            exit $?
            ;;
    esac

    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi

    print_separator

    # Run validation
    if run_validation "$@"; then
        show_results
        log_success "Documentation validation completed successfully! 🎉"
        exit 0
    else
        show_results
        log_error "Documentation validation failed! Please fix the issues above."
        echo
        echo "💡 Tips:"
        echo "  • Check the full report at: $REPORT_FILE"
        echo "  • Run with --verbose for detailed output"
        echo "  • Test individual files with -f filename.md"
        echo
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
