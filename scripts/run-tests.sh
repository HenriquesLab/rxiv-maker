#!/bin/bash
# Test execution script for rxiv-maker optimized test suite
# Supports different test categories and execution modes

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_CATEGORY="all"
PARALLEL=false
COVERAGE=false
VERBOSE=false
FAIL_FAST=false
OUTPUT_DIR="test-reports"

# Function to print colored output
print_colored() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test Categories:
    smoke       - Quick smoke tests (2-5 minutes)
    unit        - Unit tests for components (5-15 minutes)
    integration - Integration tests (10-30 minutes)
    e2e         - End-to-end tests (20-60 minutes)
    regression  - Regression tests (15-45 minutes)
    slow        - All slow tests (60+ minutes)
    all         - All tests (variable time)

Test Suites:
    validation  - Validation system tests
    processor   - Content processor tests
    infrastructure - Infrastructure tests (Docker, network, filesystem)

Options:
    -c, --category CATEGORY    Test category to run (default: all)
    -p, --parallel            Run tests in parallel
    -v, --verbose             Verbose output
    -f, --fail-fast           Stop on first failure
    --coverage                Generate coverage report
    --output-dir DIR          Output directory for reports (default: test-reports)
    -h, --help                Show this help message

Examples:
    $0 --category smoke
    $0 --category unit --parallel --coverage
    $0 --category integration --verbose
    $0 --category all --parallel --output-dir ci-reports
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--category)
            TEST_CATEGORY="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_colored $RED "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add verbosity
if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add fail fast
if [[ "$FAIL_FAST" == "true" ]]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add parallel execution
if [[ "$PARALLEL" == "true" ]]; then
    # Check if pytest-xdist is available
    if python -c "import xdist" 2>/dev/null; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
        print_colored $BLUE "Running tests in parallel mode"
    else
        print_colored $YELLOW "Warning: pytest-xdist not available, running sequentially"
    fi
fi

# Add coverage
if [[ "$COVERAGE" == "true" ]]; then
    # Check if pytest-cov is available
    if python -c "import pytest_cov" 2>/dev/null; then
        PYTEST_CMD="$PYTEST_CMD --cov=src/rxiv_maker --cov-report=html:$OUTPUT_DIR/coverage --cov-report=term"
        print_colored $BLUE "Coverage reporting enabled"
    else
        print_colored $YELLOW "Warning: pytest-cov not available, skipping coverage"
    fi
fi

# Add HTML report if available
if python -c "import pytest_html" 2>/dev/null; then
    PYTEST_CMD="$PYTEST_CMD --html=$OUTPUT_DIR/report.html --self-contained-html"
fi

# Add JUnit XML for CI
PYTEST_CMD="$PYTEST_CMD --junit-xml=$OUTPUT_DIR/junit.xml"

# Set test category
case $TEST_CATEGORY in
    smoke)
        PYTEST_CMD="$PYTEST_CMD -m smoke"
        print_colored $GREEN "Running smoke tests..."
        ;;
    unit)
        PYTEST_CMD="$PYTEST_CMD -m unit"
        print_colored $GREEN "Running unit tests..."
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD -m integration"
        print_colored $GREEN "Running integration tests..."
        ;;
    e2e)
        PYTEST_CMD="$PYTEST_CMD -m e2e"
        print_colored $GREEN "Running end-to-end tests..."
        ;;
    regression)
        PYTEST_CMD="$PYTEST_CMD -m regression"
        print_colored $GREEN "Running regression tests..."
        ;;
    slow)
        PYTEST_CMD="$PYTEST_CMD -m slow"
        print_colored $GREEN "Running slow tests..."
        ;;
    validation)
        PYTEST_CMD="$PYTEST_CMD -m validation"
        print_colored $GREEN "Running validation tests..."
        ;;
    processor)
        PYTEST_CMD="$PYTEST_CMD -m processor"
        print_colored $GREEN "Running processor tests..."
        ;;
    infrastructure)
        PYTEST_CMD="$PYTEST_CMD -m infrastructure"
        print_colored $GREEN "Running infrastructure tests..."
        ;;
    all)
        print_colored $GREEN "Running all tests..."
        ;;
    *)
        print_colored $RED "Unknown test category: $TEST_CATEGORY"
        show_usage
        exit 1
        ;;
esac

# Display configuration
print_colored $BLUE "Test Configuration:"
echo "  Category: $TEST_CATEGORY"
echo "  Parallel: $PARALLEL"
echo "  Coverage: $COVERAGE"
echo "  Verbose: $VERBOSE"
echo "  Output Directory: $OUTPUT_DIR"
echo ""

# Check test environment
print_colored $BLUE "Checking test environment..."

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "  Python: $PYTHON_VERSION"

# Check pytest availability
if python -c "import pytest" 2>/dev/null; then
    PYTEST_VERSION=$(python -c "import pytest; print(pytest.__version__)")
    echo "  Pytest: $PYTEST_VERSION"
else
    print_colored $RED "Error: pytest not available"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "pytest.ini" ]]; then
    print_colored $RED "Error: pytest.ini not found. Run from repository root."
    exit 1
fi

# Run tests
print_colored $BLUE "Starting test execution..."
echo "Command: $PYTEST_CMD"
echo ""

START_TIME=$(date +%s)

# Execute tests
if eval $PYTEST_CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    print_colored $GREEN "✅ Tests completed successfully in ${DURATION}s"

    # Show report locations
    echo ""
    print_colored $BLUE "Reports generated:"
    echo "  JUnit XML: $OUTPUT_DIR/junit.xml"

    if [[ "$COVERAGE" == "true" ]] && python -c "import pytest_cov" 2>/dev/null; then
        echo "  Coverage HTML: $OUTPUT_DIR/coverage/index.html"
    fi

    if python -c "import pytest_html" 2>/dev/null; then
        echo "  HTML Report: $OUTPUT_DIR/report.html"
    fi

    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    print_colored $RED "❌ Tests failed after ${DURATION}s"
    exit 1
fi
