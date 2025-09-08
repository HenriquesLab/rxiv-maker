#!/bin/bash

# coordinate-release-workflows.sh
# Centralized workflow coordination and status checking for rxiv-maker release process
# Part of Phase 1.3: Sequential release workflow improvements

set -euo pipefail

# Script configuration
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="coordinate-release-workflows.sh"

# Default configuration
DEFAULT_TIMEOUT=600  # 10 minutes
DEFAULT_RETRY_ATTEMPTS=3
DEFAULT_RETRY_DELAY=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

show_usage() {
    cat << EOF
${SCRIPT_NAME} v${SCRIPT_VERSION}
Centralized workflow coordination and status checking for rxiv-maker releases

Usage: $0 <command> [options]

Commands:
  validate-pypi       Validate PyPI package availability
  validate-github     Validate GitHub release readiness
  validate-all        Validate all release sources
  coordinate-homebrew Coordinate Homebrew workflow trigger
  coordinate-apt      Coordinate APT repository workflow trigger
  monitor-workflows   Monitor cross-repository workflow health

Options:
  --version VERSION   Package version to validate/coordinate
  --tag TAG          Release tag (defaults to v\${VERSION})
  --timeout SECONDS  Maximum wait time (default: ${DEFAULT_TIMEOUT})
  --retries COUNT    Maximum retry attempts (default: ${DEFAULT_RETRY_ATTEMPTS})
  --delay SECONDS    Delay between retries (default: ${DEFAULT_RETRY_DELAY})
  --verbose          Enable verbose output
  --dry-run          Show what would be done without executing
  --help            Show this help message

Examples:
  $0 validate-all --version 1.4.23
  $0 coordinate-homebrew --version 1.4.23 --verbose
  $0 monitor-workflows --tag v1.4.23 --timeout 900

Environment Variables:
  GH_TOKEN          GitHub token for API access (required)
  PACKAGE_NAME      Package name (default: rxiv-maker)
EOF
}

# Parse command line arguments
parse_arguments() {
    COMMAND=""
    VERSION=""
    TAG=""
    TIMEOUT="${DEFAULT_TIMEOUT}"
    RETRIES="${DEFAULT_RETRY_ATTEMPTS}"
    RETRY_DELAY="${DEFAULT_RETRY_DELAY}"
    VERBOSE=false
    DRY_RUN=false
    PACKAGE_NAME="${PACKAGE_NAME:-rxiv-maker}"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                VERSION="$2"
                shift 2
                ;;
            --tag)
                TAG="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --retries)
                RETRIES="$2"
                shift 2
                ;;
            --delay)
                RETRY_DELAY="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            validate-pypi|validate-github|validate-all|coordinate-homebrew|coordinate-apt|monitor-workflows)
                COMMAND="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Set default tag if not provided
    if [[ -z "${TAG}" && -n "${VERSION}" ]]; then
        TAG="v${VERSION}"
    fi

    # Validate required parameters
    if [[ -z "${COMMAND}" ]]; then
        log_error "Command is required"
        show_usage
        exit 1
    fi

    if [[ -z "${GH_TOKEN}" ]]; then
        log_error "GH_TOKEN environment variable is required"
        exit 1
    fi
}

# Verbose logging
verbose_log() {
    if [[ "${VERBOSE}" == "true" ]]; then
        log_info "$1"
    fi
}

# Retry wrapper with exponential backoff
retry_with_backoff() {
    local max_attempts="$1"
    local delay="$2"
    local command_desc="$3"
    shift 3

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        verbose_log "Attempt ${attempt}/${max_attempts}: ${command_desc}"

        if "$@"; then
            return 0
        fi

        if [[ $attempt -lt $max_attempts ]]; then
            local backoff_delay=$((delay * attempt))
            verbose_log "Command failed, waiting ${backoff_delay} seconds before retry..."
            sleep "$backoff_delay"
        fi

        ((attempt++))
    done

    log_error "Command '${command_desc}' failed after ${max_attempts} attempts"
    return 1
}

# Validate PyPI package availability
validate_pypi() {
    local version="$1"
    local package_name="${PACKAGE_NAME}"

    log_info "Validating PyPI package: ${package_name} v${version}"

    local download_url="https://pypi.org/pypi/${package_name}/${version}/json"

    # Check PyPI JSON API
    if ! curl -f -s "${download_url}" >/dev/null; then
        log_error "PyPI API not responding for ${package_name} v${version}"
        return 1
    fi

    # Verify package metadata
    local package_info
    package_info=$(curl -s "${download_url}" | jq -r '.info.version // empty' 2>/dev/null || echo "")

    if [[ "${package_info}" != "${version}" ]]; then
        log_error "Version mismatch: expected ${version}, got ${package_info}"
        return 1
    fi

    # Check distribution files
    local wheel_count tarball_count
    wheel_count=$(curl -s "${download_url}" | jq '[.urls[] | select(.filename | endswith(".whl"))] | length' 2>/dev/null || echo "0")
    tarball_count=$(curl -s "${download_url}" | jq '[.urls[] | select(.filename | endswith(".tar.gz"))] | length' 2>/dev/null || echo "0")

    if [[ $wheel_count -eq 0 && $tarball_count -eq 0 ]]; then
        log_error "No distribution files found for ${package_name} v${version}"
        return 1
    fi

    # Test pip index availability
    if ! pip index versions "${package_name}" 2>/dev/null | grep -q "$version"; then
        log_warning "Package not yet available in pip index (may still be propagating)"
    fi

    log_success "PyPI package ${package_name} v${version} is available"
    verbose_log "Distribution files: ${wheel_count} wheels, ${tarball_count} source distributions"
    return 0
}

# Validate GitHub release readiness
validate_github() {
    local tag="$1"

    log_info "Validating GitHub release: ${tag}"

    # Check GitHub release exists
    if ! gh release view "${tag}" --json name,tagName >/dev/null 2>&1; then
        log_error "GitHub release ${tag} not found or not accessible"
        return 1
    fi

    # Get tarball URL and verify accessibility
    local tarball_url
    tarball_url=$(gh release view "${tag}" --json tarballUrl --jq '.tarballUrl' 2>/dev/null || echo "")

    if [[ -z "${tarball_url}" ]]; then
        log_error "Tarball URL not available for release ${tag}"
        return 1
    fi

    # Test tarball downloadability
    if ! curl -I -f -s "${tarball_url}" >/dev/null 2>&1; then
        log_error "Tarball not downloadable: ${tarball_url}"
        return 1
    fi

    # Check release assets
    local asset_count
    asset_count=$(gh release view "${tag}" --json assets --jq '.assets | length' 2>/dev/null || echo "0")

    log_success "GitHub release ${tag} is ready"
    verbose_log "Tarball URL: ${tarball_url}"
    verbose_log "Release assets: ${asset_count}"
    return 0
}

# Validate all release sources
validate_all() {
    local version="$1"
    local tag="$2"

    log_info "Comprehensive release validation for version ${version}"

    local validation_results=()

    # Validate PyPI
    if retry_with_backoff "$RETRIES" "$RETRY_DELAY" "PyPI validation" validate_pypi "$version"; then
        validation_results+=("PyPI:✅")
    else
        validation_results+=("PyPI:❌")
    fi

    # Validate GitHub
    if retry_with_backoff "$RETRIES" "$RETRY_DELAY" "GitHub validation" validate_github "$tag"; then
        validation_results+=("GitHub:✅")
    else
        validation_results+=("GitHub:❌")
    fi

    # Report results
    log_info "Validation Results:"
    for result in "${validation_results[@]}"; do
        echo "  ${result}"
    done

    # Check if any validations failed
    for result in "${validation_results[@]}"; do
        if [[ "$result" == *"❌"* ]]; then
            log_error "Some validations failed"
            return 1
        fi
    done

    log_success "All release sources validated successfully"
    return 0
}

# Coordinate Homebrew workflow trigger
coordinate_homebrew() {
    local version="$1"
    local tag="$2"

    log_info "Coordinating Homebrew workflow trigger for ${tag}"

    # Pre-flight validation
    if ! validate_all "$version" "$tag"; then
        log_error "Release sources not ready for Homebrew workflow"
        return 1
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "[DRY RUN] Would trigger: gh workflow run homebrew-auto-update.yml --field tag_name=${tag}"
        return 0
    fi

    # Trigger workflow with retry
    if retry_with_backoff "$RETRIES" "$RETRY_DELAY" "Homebrew workflow trigger" \
        gh workflow run homebrew-auto-update.yml --field tag_name="${tag}"; then
        log_success "Homebrew workflow triggered successfully for ${tag}"
        return 0
    else
        log_error "Failed to trigger Homebrew workflow"
        return 1
    fi
}

# Note: APT repository workflow coordination removed
# The rxiv-maker package is now distributed exclusively via pip/pipx

# Monitor cross-repository workflow health
monitor_workflows() {
    local tag="$1"

    log_info "Monitoring cross-repository workflow health for ${tag}"

    # This could be enhanced to check workflow run statuses, but for now
    # it validates that all the necessary workflows are accessible

    local workflows=(
        # Note: Homebrew and APT workflows removed - using pip/pipx distribution only
    )

    local all_accessible=true

    for workflow in "${workflows[@]}"; do
        local repo="${workflow%:*}"
        local workflow_file="${workflow#*:}"

        if [[ "$repo" == "main" ]]; then
            repo_arg=""
        else
            repo_arg="--repo $repo"
        fi

        verbose_log "Checking accessibility of $workflow_file in $repo"

        if ! gh workflow list $repo_arg | grep -q "$workflow_file"; then
            log_error "Workflow $workflow_file not accessible in $repo"
            all_accessible=false
        else
            verbose_log "✅ $workflow_file accessible in $repo"
        fi
    done

    if [[ "$all_accessible" == "true" ]]; then
        log_success "All cross-repository workflows are accessible"
        return 0
    else
        log_error "Some workflows are not accessible"
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting ${SCRIPT_NAME} v${SCRIPT_VERSION}"

    parse_arguments "$@"

    # Validate required parameters based on command
    case "$COMMAND" in
        validate-pypi|validate-all|coordinate-homebrew|coordinate-apt)
            if [[ -z "${VERSION}" ]]; then
                log_error "Version is required for command: ${COMMAND}"
                exit 1
            fi
            ;;
        validate-github|monitor-workflows)
            if [[ -z "${TAG}" ]]; then
                log_error "Tag is required for command: ${COMMAND}"
                exit 1
            fi
            ;;
    esac

    # Set timeout for operations
    local start_time
    start_time=$(date +%s)

    # Execute command
    case "$COMMAND" in
        validate-pypi)
            validate_pypi "$VERSION"
            ;;
        validate-github)
            validate_github "$TAG"
            ;;
        validate-all)
            validate_all "$VERSION" "$TAG"
            ;;
        coordinate-homebrew)
            coordinate_homebrew "$VERSION" "$TAG"
            ;;
        coordinate-apt)
            coordinate_apt "$VERSION" "$TAG"
            ;;
        monitor-workflows)
            monitor_workflows "$TAG"
            ;;
        *)
            log_error "Unknown command: ${COMMAND}"
            exit 1
            ;;
    esac

    local exit_code=$?
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [[ $exit_code -eq 0 ]]; then
        log_success "Command '${COMMAND}' completed successfully in ${duration}s"
    else
        log_error "Command '${COMMAND}' failed after ${duration}s"
    fi

    exit $exit_code
}

# Run main function with all arguments
main "$@"
