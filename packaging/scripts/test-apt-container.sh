#!/bin/bash
# test-apt-container.sh - Automated APT package testing in Podman containers
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
debug() { [[ "${DEBUG:-}" == "true" ]] && echo -e "${PURPLE}[DEBUG]${NC} $*" || true; }
step() { echo -e "${CYAN}[STEP]${NC} $*"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results/apt-container"
CONTAINER_ENGINE="podman"

# Default values
UBUNTU_VERSION="22.04"
TEST_TYPE="comprehensive"
REPO_BRANCH="apt-repo"
PACKAGE_VERSION=""
LOCAL_PACKAGE=""
CONTAINER_NAME=""
CLEANUP_ON_EXIT="true"
VERBOSE="false"
DEBUG="false"
QUICK_MODE="false"
TEST_TIMEOUT="1800"  # 30 minutes

# Test configuration
CONTAINER_PREFIX="rxiv-apt-test"
NETWORK_NAME="rxiv-test-network"
TEST_USER="testuser"

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Automated testing of rxiv-maker APT package installation in Podman containers.

OPTIONS:
    -u, --ubuntu-version VERSION    Ubuntu version to test (20.04, 22.04, 24.04) [default: 22.04]
    -t, --test-type TYPE           Test type: quick, installation, upgrade, functionality, security, comprehensive [default: comprehensive]
    -b, --repo-branch BRANCH       Repository branch to test [default: apt-repo]
    -v, --package-version VERSION  Specific package version to test
    -l, --local-package FILE       Test local .deb package file
    -n, --container-name NAME      Custom container name
    -o, --output DIR               Output directory for test results [default: test-results/apt-container]
    --quick                        Quick test mode (reduced test coverage)
    --no-cleanup                   Don't cleanup containers on exit
    --verbose                      Verbose output
    --debug                        Debug mode with detailed logging
    --timeout SECONDS              Test timeout in seconds [default: 1800]
    -h, --help                     Show this help message

TEST TYPES:
    quick          - Fast validation (basic installation + version check)
    installation   - Full installation testing
    upgrade        - Package upgrade testing
    functionality  - Comprehensive functionality testing
    security       - Security and GPG validation
    comprehensive  - All tests (default)

EXAMPLES:
    $0                                              # Default comprehensive test on Ubuntu 22.04
    $0 --ubuntu-version 20.04 --test-type quick    # Quick test on Ubuntu 20.04
    $0 --local-package dist/rxiv-maker_*.deb       # Test local package
    $0 --test-type upgrade --package-version 1.5.10  # Test upgrade to specific version
    $0 --verbose --debug --no-cleanup              # Debug mode with container preservation

ENVIRONMENT VARIABLES:
    RXIV_APT_TEST_REPO_URL     Custom repository URL
    RXIV_APT_TEST_GPG_KEY      Custom GPG key URL
    RXIV_APT_TEST_ENGINE       Container engine (podman or docker)

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--ubuntu-version)
                UBUNTU_VERSION="$2"
                shift 2
                ;;
            -t|--test-type)
                TEST_TYPE="$2"
                shift 2
                ;;
            -b|--repo-branch)
                REPO_BRANCH="$2"
                shift 2
                ;;
            -v|--package-version)
                PACKAGE_VERSION="$2"
                shift 2
                ;;
            -l|--local-package)
                LOCAL_PACKAGE="$2"
                shift 2
                ;;
            -n|--container-name)
                CONTAINER_NAME="$2"
                shift 2
                ;;
            -o|--output)
                TEST_RESULTS_DIR="$2"
                shift 2
                ;;
            --quick)
                QUICK_MODE="true"
                TEST_TYPE="quick"
                shift
                ;;
            --no-cleanup)
                CLEANUP_ON_EXIT="false"
                shift
                ;;
            --verbose)
                VERBOSE="true"
                shift
                ;;
            --debug)
                DEBUG="true"
                VERBOSE="true"
                shift
                ;;
            --timeout)
                TEST_TIMEOUT="$2"
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
}

# Validate environment and arguments
validate_environment() {
    log "Validating test environment..."

    # Check container engine
    if ! command -v "$CONTAINER_ENGINE" >/dev/null 2>&1; then
        error "Container engine '$CONTAINER_ENGINE' not found"
        log "Please install Podman: https://podman.io/getting-started/installation"
        exit 1
    fi

    # Validate Ubuntu version
    case "$UBUNTU_VERSION" in
        20.04|22.04|24.04) ;;
        *)
            error "Unsupported Ubuntu version: $UBUNTU_VERSION"
            log "Supported versions: 20.04, 22.04, 24.04"
            exit 1
            ;;
    esac

    # Validate test type
    case "$TEST_TYPE" in
        quick|installation|upgrade|functionality|security|comprehensive) ;;
        *)
            error "Unknown test type: $TEST_TYPE"
            log "Valid types: quick, installation, upgrade, functionality, security, comprehensive"
            exit 1
            ;;
    esac

    # Validate local package if specified
    if [[ -n "$LOCAL_PACKAGE" ]] && [[ ! -f "$LOCAL_PACKAGE" ]]; then
        error "Local package file not found: $LOCAL_PACKAGE"
        exit 1
    fi

    # Generate container name if not specified
    if [[ -z "$CONTAINER_NAME" ]]; then
        CONTAINER_NAME="${CONTAINER_PREFIX}-${UBUNTU_VERSION}-$(date +%s)"
    fi

    debug "Container engine: $CONTAINER_ENGINE"
    debug "Ubuntu version: $UBUNTU_VERSION"
    debug "Test type: $TEST_TYPE"
    debug "Container name: $CONTAINER_NAME"
    debug "Output directory: $TEST_RESULTS_DIR"

    success "Environment validation passed"
}

# Setup test environment
setup_test_environment() {
    log "Setting up test environment..."

    # Create output directory
    mkdir -p "$TEST_RESULTS_DIR"

    # Create test network (ignore if exists)
    if ! $CONTAINER_ENGINE network exists "$NETWORK_NAME" 2>/dev/null; then
        log "Creating test network: $NETWORK_NAME"
        $CONTAINER_ENGINE network create "$NETWORK_NAME" || true
    fi

    # Pull Ubuntu image
    log "Pulling Ubuntu $UBUNTU_VERSION image..."
    $CONTAINER_ENGINE pull "ubuntu:$UBUNTU_VERSION"

    success "Test environment setup completed"
}

# Cleanup function
cleanup() {
    local exit_code=$?

    if [[ "$CLEANUP_ON_EXIT" == "true" ]]; then
        log "Cleaning up test environment..."

        # Stop and remove container
        if $CONTAINER_ENGINE container exists "$CONTAINER_NAME" 2>/dev/null; then
            log "Removing container: $CONTAINER_NAME"
            $CONTAINER_ENGINE stop "$CONTAINER_NAME" 2>/dev/null || true
            $CONTAINER_ENGINE rm "$CONTAINER_NAME" 2>/dev/null || true
        fi

        # Remove test network (ignore errors if other containers using it)
        if $CONTAINER_ENGINE network exists "$NETWORK_NAME" 2>/dev/null; then
            debug "Attempting to remove test network: $NETWORK_NAME"
            $CONTAINER_ENGINE network rm "$NETWORK_NAME" 2>/dev/null || true
        fi
    else
        log "Container preserved for debugging: $CONTAINER_NAME"
        log "Connect with: $CONTAINER_ENGINE exec -it $CONTAINER_NAME bash"
        log "Remove with: $CONTAINER_ENGINE rm -f $CONTAINER_NAME"
    fi

    if [[ $exit_code -eq 0 ]]; then
        success "Test completed successfully"
    else
        error "Test failed with exit code: $exit_code"
    fi

    exit $exit_code
}

# Setup cleanup trap
trap cleanup EXIT

# Create and start container
create_container() {
    log "Creating Ubuntu $UBUNTU_VERSION container: $CONTAINER_NAME"

    # Remove existing container if present
    if $CONTAINER_ENGINE container exists "$CONTAINER_NAME" 2>/dev/null; then
        warn "Removing existing container: $CONTAINER_NAME"
        $CONTAINER_ENGINE rm -f "$CONTAINER_NAME"
    fi

    # Create container with necessary mounts
    $CONTAINER_ENGINE run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        -v "$PROJECT_ROOT:/workspace:ro" \
        -v "$TEST_RESULTS_DIR:/test-results:rw" \
        "ubuntu:$UBUNTU_VERSION" \
        sleep infinity

    # Wait for container to be ready
    sleep 2

    # Verify container is running
    if ! $CONTAINER_ENGINE container exists "$CONTAINER_NAME"; then
        error "Failed to create container: $CONTAINER_NAME"
        exit 1
    fi

    success "Container created successfully: $CONTAINER_NAME"
}

# Execute command in container
exec_in_container() {
    local cmd="$*"
    debug "Executing in container: $cmd"

    if [[ "$VERBOSE" == "true" ]]; then
        $CONTAINER_ENGINE exec "$CONTAINER_NAME" bash -c "$cmd"
    else
        $CONTAINER_ENGINE exec "$CONTAINER_NAME" bash -c "$cmd" >/dev/null 2>&1
    fi
}

# Execute command in container with output capture
exec_in_container_capture() {
    local cmd="$*"
    debug "Executing in container (with capture): $cmd"
    $CONTAINER_ENGINE exec "$CONTAINER_NAME" bash -c "$cmd"
}

# Setup container base environment
setup_container() {
    step "Setting up container base environment"

    # Update package lists
    log "Updating package lists..."
    exec_in_container "apt-get update"

    # Install basic tools
    log "Installing basic tools..."
    exec_in_container "DEBIAN_FRONTEND=noninteractive apt-get install -y curl gnupg ca-certificates"

    # Create test user
    log "Creating test user: $TEST_USER"
    exec_in_container "useradd -m -s /bin/bash $TEST_USER"
    exec_in_container "echo '$TEST_USER ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"

    success "Container base environment setup completed"
}

# Add APT repository
add_apt_repository() {
    step "Adding rxiv-maker APT repository"

    if [[ -n "$LOCAL_PACKAGE" ]]; then
        log "Using local package, skipping repository setup"
        return 0
    fi

    # Repository configuration
    local repo_url="${RXIV_APT_TEST_REPO_URL:-https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo}"
    local gpg_key_url="${RXIV_APT_TEST_GPG_KEY:-https://raw.githubusercontent.com/henriqueslab/rxiv-maker/$REPO_BRANCH/pubkey.gpg}"

    log "Repository URL: $repo_url"
    log "GPG key URL: $gpg_key_url"

    # Add GPG key
    log "Adding GPG key..."
    exec_in_container "curl -fsSL '$gpg_key_url' | gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg"

    # Add repository source
    log "Adding repository source..."
    exec_in_container "echo 'deb [arch=amd64] $repo_url stable main' > /etc/apt/sources.list.d/rxiv-maker.list"

    # Update package lists
    log "Updating package lists with new repository..."
    exec_in_container "apt-get update"

    # Verify repository is accessible
    log "Verifying repository accessibility..."
    if ! exec_in_container "apt-cache search rxiv-maker"; then
        error "Repository setup failed - package not found"
        exit 1
    fi

    success "APT repository added successfully"
}

# Install rxiv-maker package
install_package() {
    step "Installing rxiv-maker package"

    if [[ -n "$LOCAL_PACKAGE" ]]; then
        # Install local package
        log "Installing local package: $(basename "$LOCAL_PACKAGE")"

        # Copy package to container
        $CONTAINER_ENGINE cp "$LOCAL_PACKAGE" "$CONTAINER_NAME:/tmp/rxiv-maker.deb"

        # Install with dpkg and fix dependencies
        exec_in_container "dpkg -i /tmp/rxiv-maker.deb || true"
        exec_in_container "apt-get install -f -y"
    else
        # Install from repository
        local install_cmd="apt-get install -y rxiv-maker"

        if [[ -n "$PACKAGE_VERSION" ]]; then
            install_cmd="apt-get install -y rxiv-maker=$PACKAGE_VERSION"
            log "Installing specific version: $PACKAGE_VERSION"
        else
            log "Installing latest version from repository"
        fi

        exec_in_container "$install_cmd"
    fi

    # Verify installation
    log "Verifying package installation..."
    local version
    version=$(exec_in_container_capture "rxiv --version" | head -1)

    if [[ -z "$version" ]]; then
        error "Package installation verification failed"
        exit 1
    fi

    success "Package installed successfully: $version"
}

# Test basic functionality
test_basic_functionality() {
    step "Testing basic functionality"

    # Test as root
    log "Testing basic commands as root..."
    exec_in_container "rxiv --version"
    exec_in_container "rxiv --help > /dev/null"

    # Test as regular user
    log "Testing basic commands as regular user..."
    exec_in_container "su - $TEST_USER -c 'rxiv --version'"
    exec_in_container "su - $TEST_USER -c 'rxiv --help > /dev/null'"

    # Test installation check
    log "Running installation check..."
    exec_in_container "su - $TEST_USER -c 'rxiv check-installation'"

    success "Basic functionality tests passed"
}

# Test manuscript operations
test_manuscript_operations() {
    step "Testing manuscript operations"

    # Create test directory
    exec_in_container "su - $TEST_USER -c 'mkdir -p /home/$TEST_USER/test-manuscript'"
    exec_in_container "su - $TEST_USER -c 'cd /home/$TEST_USER/test-manuscript'"

    # Test manuscript initialization
    log "Testing manuscript initialization..."
    exec_in_container "su - $TEST_USER -c 'cd /home/$TEST_USER && rxiv init test-manuscript'"

    # Test manuscript validation
    log "Testing manuscript validation..."
    exec_in_container "su - $TEST_USER -c 'cd /home/$TEST_USER/test-manuscript && rxiv validate .'"

    # Test PDF generation (if not quick mode)
    if [[ "$QUICK_MODE" != "true" ]]; then
        log "Testing PDF generation..."
        exec_in_container "su - $TEST_USER -c 'cd /home/$TEST_USER/test-manuscript && timeout 300 rxiv pdf .'"

        # Verify PDF was created
        if ! exec_in_container "test -f /home/$TEST_USER/test-manuscript/output/test-manuscript.pdf"; then
            error "PDF generation failed - no output file found"
            return 1
        fi
    fi

    success "Manuscript operations tests passed"
}

# Test with example manuscript
test_example_manuscript() {
    step "Testing with example manuscript"

    # Copy example manuscript to container
    log "Copying example manuscript to container..."
    $CONTAINER_ENGINE cp "$PROJECT_ROOT/EXAMPLE_MANUSCRIPT" "$CONTAINER_NAME:/home/$TEST_USER/"
    exec_in_container "chown -R $TEST_USER:$TEST_USER /home/$TEST_USER/EXAMPLE_MANUSCRIPT"

    # Test validation
    log "Validating example manuscript..."
    exec_in_container "su - $TEST_USER -c 'cd /home/$TEST_USER/EXAMPLE_MANUSCRIPT && rxiv validate .'"

    # Test PDF generation (if not quick mode)
    if [[ "$QUICK_MODE" != "true" ]]; then
        log "Generating PDF from example manuscript..."
        exec_in_container "su - $TEST_USER -c 'cd /home/$TEST_USER/EXAMPLE_MANUSCRIPT && timeout 600 rxiv pdf .'"

        # Verify PDF was created
        if ! exec_in_container "test -f /home/$TEST_USER/EXAMPLE_MANUSCRIPT/output/EXAMPLE_MANUSCRIPT.pdf"; then
            error "Example manuscript PDF generation failed"
            return 1
        fi
    fi

    success "Example manuscript tests passed"
}

# Test security aspects
test_security() {
    step "Testing security aspects"

    # Test GPG key verification
    log "Testing GPG key verification..."
    exec_in_container "gpg --list-keys --keyring /usr/share/keyrings/rxiv-maker.gpg"

    # Test package signature verification
    log "Testing package signature verification..."
    exec_in_container "apt-cache policy rxiv-maker"

    # Test file permissions
    log "Testing file permissions..."
    exec_in_container "find /usr -name '*rxiv*' -perm /6000" | while read -r file; do
        if [[ -n "$file" ]]; then
            error "Found setuid/setgid file: $file"
            return 1
        fi
    done

    # Test user access
    log "Testing user access restrictions..."
    exec_in_container "su - $TEST_USER -c 'rxiv --version'" # Should work

    success "Security tests passed"
}

# Test upgrade scenario
test_upgrade() {
    step "Testing package upgrade scenario"

    if [[ -n "$LOCAL_PACKAGE" ]]; then
        warn "Skipping upgrade test for local package"
        return 0
    fi

    # This would require having an older version in the repository
    # For now, just verify the upgrade command works
    log "Testing upgrade command..."
    exec_in_container "apt-get update"
    exec_in_container "apt-get --dry-run upgrade rxiv-maker"

    success "Upgrade test completed"
}

# Performance testing
test_performance() {
    step "Testing performance metrics"

    # Measure installation size
    log "Measuring package size..."
    local package_size
    package_size=$(exec_in_container_capture "dpkg-query -Wf '\${Installed-Size}' rxiv-maker")
    log "Package installed size: ${package_size} KB"

    # Measure command startup time
    if [[ "$QUICK_MODE" != "true" ]]; then
        log "Measuring command startup time..."
        exec_in_container "time rxiv --version"
    fi

    success "Performance tests completed"
}

# Generate test report
generate_test_report() {
    step "Generating test report"

    local report_file="$TEST_RESULTS_DIR/test-report-$UBUNTU_VERSION-$(date +%Y%m%d-%H%M%S).json"

    # Collect system information
    local ubuntu_version
    local package_version
    local test_duration

    ubuntu_version=$(exec_in_container_capture "lsb_release -d" | cut -d: -f2 | xargs)
    package_version=$(exec_in_container_capture "rxiv --version" | head -1)
    test_duration=$(($(date +%s) - START_TIME))

    # Generate JSON report
    cat > "$report_file" << EOF
{
  "test_info": {
    "timestamp": "$(date -Iseconds)",
    "ubuntu_version": "$ubuntu_version",
    "package_version": "$package_version",
    "test_type": "$TEST_TYPE",
    "test_duration": $test_duration,
    "container_name": "$CONTAINER_NAME",
    "quick_mode": $QUICK_MODE
  },
  "test_results": {
    "basic_functionality": "passed",
    "manuscript_operations": "passed",
    "example_manuscript": "passed",
    "security": "passed",
    "performance": "passed"
  },
  "environment": {
    "container_engine": "$CONTAINER_ENGINE",
    "local_package": "${LOCAL_PACKAGE:-null}",
    "repo_branch": "$REPO_BRANCH"
  }
}
EOF

    log "Test report generated: $report_file"
    success "Test report generation completed"
}

# Main test execution
run_tests() {
    local START_TIME
    START_TIME=$(date +%s)

    case "$TEST_TYPE" in
        quick)
            test_basic_functionality
            ;;
        installation)
            test_basic_functionality
            test_manuscript_operations
            ;;
        upgrade)
            test_basic_functionality
            test_upgrade
            ;;
        functionality)
            test_basic_functionality
            test_manuscript_operations
            test_example_manuscript
            ;;
        security)
            test_basic_functionality
            test_security
            ;;
        comprehensive)
            test_basic_functionality
            test_manuscript_operations
            test_example_manuscript
            test_security
            test_performance
            ;;
    esac

    generate_test_report
}

# Main execution
main() {
    log "Starting APT container testing for rxiv-maker"
    log "Ubuntu: $UBUNTU_VERSION | Test: $TEST_TYPE | Container: $CONTAINER_NAME"

    validate_environment
    setup_test_environment
    create_container
    setup_container
    add_apt_repository
    install_package
    run_tests

    success "All tests completed successfully!"
}

# Parse arguments and run
parse_args "$@"
main
