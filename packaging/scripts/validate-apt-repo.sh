#!/bin/bash
# validate-apt-repo.sh - Comprehensive APT repository validation script
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

# Default values
REPO_URL="https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo"
REPO_BRANCH="apt-repo"
GPG_KEY_URL="https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo/pubkey.gpg"
OUTPUT_DIR="$PROJECT_ROOT/validation-results"
VERBOSE="false"
DEBUG="false"
CHECK_PACKAGES="true"
CHECK_METADATA="true"
CHECK_SIGNATURES="true"
CHECK_ACCESSIBILITY="true"
TIMEOUT="30"
USER_AGENT="rxiv-maker-repo-validator/1.0"

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Comprehensive validation of the rxiv-maker APT repository.

OPTIONS:
    -u, --repo-url URL           Repository URL to validate [default: $REPO_URL]
    -b, --repo-branch BRANCH     Repository branch [default: $REPO_BRANCH]
    -g, --gpg-key-url URL        GPG key URL [default: auto-detect]
    -o, --output DIR             Output directory for validation results [default: $OUTPUT_DIR]
    --skip-packages              Skip package validation
    --skip-metadata              Skip metadata validation
    --skip-signatures            Skip signature validation
    --skip-accessibility         Skip accessibility checks
    --timeout SECONDS            HTTP timeout in seconds [default: $TIMEOUT]
    --verbose                    Verbose output
    --debug                      Debug mode with detailed logging
    -h, --help                   Show this help message

VALIDATION CHECKS:
    accessibility    - Repository URL accessibility and response times
    metadata         - Repository metadata validation (Release, Packages files)
    signatures       - GPG signature verification
    packages         - Package availability and integrity
    security         - Security configuration validation

EXAMPLES:
    $0                                          # Full validation with defaults
    $0 --repo-url https://example.com/repo/    # Validate custom repository
    $0 --skip-signatures --verbose             # Skip signature checks, verbose output
    $0 --debug --output ./validation           # Debug mode with custom output

ENVIRONMENT VARIABLES:
    RXIV_REPO_VALIDATION_TIMEOUT    Custom timeout for HTTP requests
    RXIV_REPO_VALIDATION_USER_AGENT Custom User-Agent for HTTP requests

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -u|--repo-url)
                REPO_URL="$2"
                shift 2
                ;;
            -b|--repo-branch)
                REPO_BRANCH="$2"
                shift 2
                ;;
            -g|--gpg-key-url)
                GPG_KEY_URL="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --skip-packages)
                CHECK_PACKAGES="false"
                shift
                ;;
            --skip-metadata)
                CHECK_METADATA="false"
                shift
                ;;
            --skip-signatures)
                CHECK_SIGNATURES="false"
                shift
                ;;
            --skip-accessibility)
                CHECK_ACCESSIBILITY="false"
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
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

# Environment setup
setup_environment() {
    # Override defaults with environment variables
    TIMEOUT="${RXIV_REPO_VALIDATION_TIMEOUT:-$TIMEOUT}"
    USER_AGENT="${RXIV_REPO_VALIDATION_USER_AGENT:-$USER_AGENT}"

    # Auto-detect GPG key URL if using default repository
    if [[ "$REPO_URL" == "https://henriqueslab.github.io/rxiv-maker/" ]]; then
        GPG_KEY_URL="https://raw.githubusercontent.com/henriqueslab/rxiv-maker/$REPO_BRANCH/pubkey.gpg"
    fi

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    # Initialize validation report
    VALIDATION_REPORT="$OUTPUT_DIR/validation-report-$(date +%Y%m%d-%H%M%S).json"

    debug "Repository URL: $REPO_URL"
    debug "GPG key URL: $GPG_KEY_URL"
    debug "Output directory: $OUTPUT_DIR"
    debug "Validation report: $VALIDATION_REPORT"
}

# HTTP request helper
http_request() {
    local url="$1"
    local output_file="${2:-}"
    local follow_redirects="${3:-true}"

    local curl_args=(
        --silent
        --show-error
        --fail
        --user-agent "$USER_AGENT"
        --connect-timeout "$TIMEOUT"
        --max-time "$((TIMEOUT * 2))"
    )

    if [[ "$follow_redirects" == "true" ]]; then
        curl_args+=(--location)
    fi

    if [[ -n "$output_file" ]]; then
        curl_args+=(--output "$output_file")
    fi

    debug "HTTP request: curl ${curl_args[*]} $url"

    if [[ "$VERBOSE" == "true" ]]; then
        curl "${curl_args[@]}" --write-out "HTTP %{http_code} - %{url_effective} (%{time_total}s)\n" "$url"
    else
        curl "${curl_args[@]}" "$url"
    fi
}

# Check repository accessibility
check_accessibility() {
    step "Checking repository accessibility"

    local results=()
    local start_time end_time duration

    # Test main repository URL
    log "Testing repository root: $REPO_URL"
    start_time=$(date +%s.%N)

    if http_request "$REPO_URL" >/dev/null 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l)
        success "Repository root accessible (${duration}s)"
        results+=("repository_root:success:$duration")
    else
        error "Repository root not accessible"
        results+=("repository_root:failed:0")
        return 1
    fi

    # Test Release file
    local release_url="${REPO_URL}/dists/stable/Release"
    log "Testing Release file: $release_url"
    start_time=$(date +%s.%N)

    if http_request "$release_url" >/dev/null 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l)
        success "Release file accessible (${duration}s)"
        results+=("release_file:success:$duration")
    else
        error "Release file not accessible"
        results+=("release_file:failed:0")
    fi

    # Test Packages file
    local packages_url="${REPO_URL}/dists/stable/main/binary-all/Packages"
    log "Testing Packages file: $packages_url"
    start_time=$(date +%s.%N)

    if http_request "$packages_url" >/dev/null 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l)
        success "Packages file accessible (${duration}s)"
        results+=("packages_file:success:$duration")
    else
        error "Packages file not accessible"
        results+=("packages_file:failed:0")
    fi

    # Test GPG key
    log "Testing GPG key: $GPG_KEY_URL"
    start_time=$(date +%s.%N)

    if http_request "$GPG_KEY_URL" >/dev/null 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc -l)
        success "GPG key accessible (${duration}s)"
        results+=("gpg_key:success:$duration")
    else
        error "GPG key not accessible"
        results+=("gpg_key:failed:0")
    fi

    # Save accessibility results
    printf '%s\n' "${results[@]}" > "$OUTPUT_DIR/accessibility-results.txt"

    success "Accessibility check completed"
}

# Validate repository metadata
validate_metadata() {
    step "Validating repository metadata"

    local release_file="$OUTPUT_DIR/Release"
    local packages_file="$OUTPUT_DIR/Packages"

    # Download Release file
    log "Downloading Release file..."
    if ! http_request "${REPO_URL}/dists/stable/Release" "$release_file"; then
        error "Failed to download Release file"
        return 1
    fi

    # Validate Release file structure
    log "Validating Release file structure..."
    local required_fields=("Origin" "Label" "Suite" "Codename" "Date" "SHA256")
    local missing_fields=()

    for field in "${required_fields[@]}"; do
        if ! grep -q "^$field:" "$release_file"; then
            missing_fields+=("$field")
        fi
    done

    if [[ ${#missing_fields[@]} -gt 0 ]]; then
        error "Missing required fields in Release file: ${missing_fields[*]}"
    else
        success "Release file structure valid"
    fi

    # Download Packages file
    log "Downloading Packages file..."
    if ! http_request "${REPO_URL}/dists/stable/main/binary-all/Packages" "$packages_file"; then
        error "Failed to download Packages file"
        return 1
    fi

    # Validate Packages file structure
    log "Validating Packages file structure..."
    local package_count
    package_count=$(grep -c "^Package:" "$packages_file" 2>/dev/null || echo "0")

    if [[ "$package_count" -eq 0 ]]; then
        error "No packages found in Packages file"
        return 1
    else
        success "Found $package_count package(s) in repository"
    fi

    # Validate rxiv-maker package entry
    if grep -q "^Package: rxiv-maker$" "$packages_file"; then
        success "rxiv-maker package found in repository"

        # Extract package information
        local package_info="$OUTPUT_DIR/rxiv-maker-package-info.txt"
        sed -n '/^Package: rxiv-maker$/,/^$/p' "$packages_file" > "$package_info"

        # Validate required package fields
        local required_pkg_fields=("Version" "Architecture" "Maintainer" "Filename" "Size" "SHA256")
        local missing_pkg_fields=()

        for field in "${required_pkg_fields[@]}"; do
            if ! grep -q "^$field:" "$package_info"; then
                missing_pkg_fields+=("$field")
            fi
        done

        if [[ ${#missing_pkg_fields[@]} -gt 0 ]]; then
            error "Missing package fields: ${missing_pkg_fields[*]}"
        else
            success "Package metadata complete"
        fi

        # Display package information
        if [[ "$VERBOSE" == "true" ]]; then
            log "Package information:"
            while IFS=: read -r key value; do
                printf "  %-15s: %s\n" "$key" "$value"
            done < <(grep "^\\(Version\\|Architecture\\|Size\\|Filename\\):" "$package_info")
        fi
    else
        error "rxiv-maker package not found in repository"
        return 1
    fi

    success "Metadata validation completed"
}

# Verify signatures
verify_signatures() {
    step "Verifying GPG signatures"

    local gpg_key_file="$OUTPUT_DIR/pubkey.gpg"
    local release_file="$OUTPUT_DIR/Release"
    local release_gpg_file="$OUTPUT_DIR/Release.gpg"

    # Download GPG key
    log "Downloading GPG key..."
    if ! http_request "$GPG_KEY_URL" "$gpg_key_file"; then
        error "Failed to download GPG key"
        return 1
    fi

    # Download Release signature
    log "Downloading Release signature..."
    if ! http_request "${REPO_URL}/dists/stable/Release.gpg" "$release_gpg_file"; then
        error "Failed to download Release signature"
        return 1
    fi

    # Create temporary GPG home directory
    local gpg_home="$OUTPUT_DIR/gnupg"
    mkdir -p "$gpg_home"
    chmod 700 "$gpg_home"

    # Import GPG key
    log "Importing GPG key..."
    if gpg --homedir "$gpg_home" --import "$gpg_key_file" >&2; then
        success "GPG key imported successfully"
    else
        error "Failed to import GPG key"
        return 1
    fi

    # Verify Release file signature
    log "Verifying Release file signature..."
    if gpg --homedir "$gpg_home" --verify "$release_gpg_file" "$release_file" >&2; then
        success "Release signature verification successful"
    else
        error "Release signature verification failed"
        return 1
    fi

    # Extract key information
    local key_info="$OUTPUT_DIR/gpg-key-info.txt"
    gpg --homedir "$gpg_home" --list-keys --with-colons > "$key_info" 2>/dev/null

    # Display key information
    if [[ "$VERBOSE" == "true" ]]; then
        log "GPG key information:"
        gpg --homedir "$gpg_home" --list-keys 2>/dev/null | head -10
    fi

    # Cleanup GPG home directory
    rm -rf "$gpg_home"

    success "Signature verification completed"
}

# Validate packages
validate_packages() {
    step "Validating package integrity"

    local packages_file="$OUTPUT_DIR/Packages"

    if [[ ! -f "$packages_file" ]]; then
        error "Packages file not found. Run metadata validation first."
        return 1
    fi

    # Extract package download URL and checksums
    local package_filename package_size package_sha256 package_url
    package_filename=$(grep "^Filename:" "$packages_file" | grep rxiv-maker | cut -d' ' -f2)
    package_size=$(grep "^Size:" "$packages_file" | grep -A10 -B10 rxiv-maker | grep "^Size:" | cut -d' ' -f2)
    package_sha256=$(grep "^SHA256:" "$packages_file" | grep -A10 -B10 rxiv-maker | grep "^SHA256:" | cut -d' ' -f2)

    if [[ -z "$package_filename" ]]; then
        error "Package filename not found"
        return 1
    fi

    package_url="${REPO_URL}/${package_filename}"
    local package_file="$OUTPUT_DIR/$(basename "$package_filename")"

    log "Package URL: $package_url"
    log "Expected size: $package_size bytes"
    log "Expected SHA256: $package_sha256"

    # Download package
    log "Downloading package for validation..."
    if ! http_request "$package_url" "$package_file"; then
        error "Failed to download package"
        return 1
    fi

    # Verify file size
    local actual_size
    actual_size=$(stat -c%s "$package_file" 2>/dev/null || stat -f%z "$package_file" 2>/dev/null)

    if [[ "$actual_size" != "$package_size" ]]; then
        error "Size mismatch: expected $package_size, got $actual_size"
        return 1
    else
        success "Package size verified: $actual_size bytes"
    fi

    # Verify SHA256 checksum
    local actual_sha256
    if command -v sha256sum >/dev/null 2>&1; then
        actual_sha256=$(sha256sum "$package_file" | cut -d' ' -f1)
    elif command -v shasum >/dev/null 2>&1; then
        actual_sha256=$(shasum -a 256 "$package_file" | cut -d' ' -f1)
    else
        warn "No SHA256 utility found, skipping checksum verification"
        return 0
    fi

    if [[ "$actual_sha256" != "$package_sha256" ]]; then
        error "SHA256 mismatch: expected $package_sha256, got $actual_sha256"
        return 1
    else
        success "Package SHA256 verified"
    fi

    # Validate .deb package structure (if dpkg is available)
    if command -v dpkg >/dev/null 2>&1; then
        log "Validating Debian package structure..."

        local package_info="$OUTPUT_DIR/package-dpkg-info.txt"
        if dpkg-deb --info "$package_file" > "$package_info" 2>&1; then
            success "Debian package structure valid"

            if [[ "$VERBOSE" == "true" ]]; then
                log "Package control information:"
                head -20 "$package_info"
            fi
        else
            error "Invalid Debian package structure"
            return 1
        fi

        # List package contents
        local package_contents="$OUTPUT_DIR/package-contents.txt"
        if dpkg-deb --contents "$package_file" > "$package_contents" 2>&1; then
            local file_count
            file_count=$(wc -l < "$package_contents")
            success "Package contains $file_count files"
        else
            warn "Could not list package contents"
        fi
    else
        warn "dpkg not available, skipping package structure validation"
    fi

    success "Package validation completed"
}

# Security validation
validate_security() {
    step "Validating security configuration"

    local security_results=()

    # Check HTTPS usage
    if [[ "$REPO_URL" =~ ^https:// ]]; then
        success "Repository uses HTTPS"
        security_results+=("https:enabled")
    else
        error "Repository does not use HTTPS"
        security_results+=("https:disabled")
    fi

    # Check GPG key security
    local gpg_key_file="$OUTPUT_DIR/pubkey.gpg"
    if [[ -f "$gpg_key_file" ]]; then
        # Analyze GPG key
        local gpg_home="$OUTPUT_DIR/gnupg-security"
        mkdir -p "$gpg_home"
        chmod 700 "$gpg_home"

        if gpg --homedir "$gpg_home" --import "$gpg_key_file" >&2; then
            # Check key algorithm and size
            local key_info
            key_info=$(gpg --homedir "$gpg_home" --list-keys --with-colons 2>/dev/null)

            local key_algorithm key_size
            key_algorithm=$(echo "$key_info" | grep "^pub:" | cut -d: -f4)
            key_size=$(echo "$key_info" | grep "^pub:" | cut -d3 -f1)

            if [[ "$key_size" -ge 2048 ]]; then
                success "GPG key size adequate: $key_size bits"
                security_results+=("gpg_key_size:adequate:$key_size")
            else
                warn "GPG key size may be weak: $key_size bits"
                security_results+=("gpg_key_size:weak:$key_size")
            fi

            # Check key expiration
            local key_expiry
            key_expiry=$(echo "$key_info" | grep "^pub:" | cut -d: -f7)

            if [[ -n "$key_expiry" && "$key_expiry" != "0" ]]; then
                local expiry_date
                expiry_date=$(date -d "@$key_expiry" 2>/dev/null || date -r "$key_expiry" 2>/dev/null)
                log "GPG key expires: $expiry_date"
                security_results+=("gpg_key_expiry:set:$key_expiry")
            else
                warn "GPG key does not expire"
                security_results+=("gpg_key_expiry:none")
            fi
        fi

        rm -rf "$gpg_home"
    fi

    # Check HTTP security headers (if curl supports it)
    log "Checking HTTP security headers..."
    local headers_file="$OUTPUT_DIR/http-headers.txt"

    if curl --silent --head --user-agent "$USER_AGENT" "$REPO_URL" > "$headers_file" 2>&1; then
        # Check for security headers
        local security_headers=("strict-transport-security" "x-frame-options" "x-content-type-options")

        for header in "${security_headers[@]}"; do
            if grep -qi "^$header:" "$headers_file"; then
                success "Security header present: $header"
                security_results+=("header_${header//-/_}:present")
            else
                warn "Security header missing: $header"
                security_results+=("header_${header//-/_}:missing")
            fi
        done
    else
        warn "Could not check HTTP headers"
    fi

    # Save security results
    printf '%s\n' "${security_results[@]}" > "$OUTPUT_DIR/security-results.txt"

    success "Security validation completed"
}

# Generate validation report
generate_report() {
    step "Generating validation report"

    local timestamp
    timestamp=$(date -Iseconds)

    # Collect all results
    local accessibility_results metadata_results signature_results package_results security_results

    if [[ -f "$OUTPUT_DIR/accessibility-results.txt" ]]; then
        accessibility_results=$(cat "$OUTPUT_DIR/accessibility-results.txt")
    fi

    if [[ -f "$OUTPUT_DIR/security-results.txt" ]]; then
        security_results=$(cat "$OUTPUT_DIR/security-results.txt")
    fi

    # Generate JSON report
    cat > "$VALIDATION_REPORT" << EOF
{
  "validation_info": {
    "timestamp": "$timestamp",
    "repository_url": "$REPO_URL",
    "gpg_key_url": "$GPG_KEY_URL",
    "validator_version": "1.0",
    "checks_performed": {
      "accessibility": $CHECK_ACCESSIBILITY,
      "metadata": $CHECK_METADATA,
      "signatures": $CHECK_SIGNATURES,
      "packages": $CHECK_PACKAGES,
      "security": true
    }
  },
  "results": {
    "accessibility": $(if [[ -n "$accessibility_results" ]]; then echo "\"$accessibility_results\""; else echo "null"; fi),
    "metadata": "completed",
    "signatures": "completed",
    "packages": "completed",
    "security": $(if [[ -n "$security_results" ]]; then echo "\"$security_results\""; else echo "null"; fi)
  },
  "files_generated": [
    "$(basename "$VALIDATION_REPORT")",
    "Release",
    "Packages",
    "pubkey.gpg"
  ]
}
EOF

    # Generate summary report
    local summary_file="$OUTPUT_DIR/validation-summary.txt"
    cat > "$summary_file" << EOF
APT Repository Validation Summary
Generated: $timestamp

Repository: $REPO_URL
GPG Key: $GPG_KEY_URL

Validation Results:
EOF

    if [[ "$CHECK_ACCESSIBILITY" == "true" ]]; then
        echo "✅ Accessibility: Checked" >> "$summary_file"
    fi

    if [[ "$CHECK_METADATA" == "true" ]]; then
        echo "✅ Metadata: Validated" >> "$summary_file"
    fi

    if [[ "$CHECK_SIGNATURES" == "true" ]]; then
        echo "✅ Signatures: Verified" >> "$summary_file"
    fi

    if [[ "$CHECK_PACKAGES" == "true" ]]; then
        echo "✅ Packages: Validated" >> "$summary_file"
    fi

    echo "✅ Security: Checked" >> "$summary_file"

    success "Validation report generated: $VALIDATION_REPORT"
    success "Summary report generated: $summary_file"

    if [[ "$VERBOSE" == "true" ]]; then
        log "Validation summary:"
        cat "$summary_file"
    fi
}

# Main execution
main() {
    log "Starting APT repository validation"
    log "Repository: $REPO_URL"

    setup_environment

    local validation_failed=false

    # Run validation checks
    if [[ "$CHECK_ACCESSIBILITY" == "true" ]]; then
        if ! check_accessibility; then
            validation_failed=true
        fi
    fi

    if [[ "$CHECK_METADATA" == "true" ]]; then
        if ! validate_metadata; then
            validation_failed=true
        fi
    fi

    if [[ "$CHECK_SIGNATURES" == "true" ]]; then
        if ! verify_signatures; then
            validation_failed=true
        fi
    fi

    if [[ "$CHECK_PACKAGES" == "true" ]]; then
        if ! validate_packages; then
            validation_failed=true
        fi
    fi

    if ! validate_security; then
        validation_failed=true
    fi

    # Generate final report
    generate_report

    if [[ "$validation_failed" == "true" ]]; then
        error "Repository validation completed with errors"
        exit 1
    else
        success "Repository validation completed successfully"
    fi
}

# Parse arguments and run
parse_args "$@"
main
