#!/bin/bash
# run-container-tests.sh - Multi-container APT package testing orchestrator
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
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results/multi-container"

# Default values
UBUNTU_VERSIONS="20.04,22.04,24.04"
TEST_TYPES="installation,functionality"
PARALLEL_JOBS="3"
CONTAINER_ENGINE="podman"
REPO_BRANCH="apt-repo"
LOCAL_PACKAGE=""
CLEANUP_ON_EXIT="true"
VERBOSE="false"
DEBUG="false"
QUICK_MODE="false"
TEST_TIMEOUT="1800"  # 30 minutes per test
FAIL_FAST="false"
GENERATE_REPORT="true"
OUTPUT_FORMAT="json"

# Test orchestration
JOBS_RUNNING=()
JOBS_COMPLETED=()
JOBS_FAILED=()
TOTAL_TESTS=0
TESTS_PASSED=0
TESTS_FAILED=0

show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Multi-container orchestrator for comprehensive APT package testing across multiple Ubuntu versions and test scenarios.

OPTIONS:
    -v, --ubuntu-versions VERSIONS  Comma-separated Ubuntu versions [default: $UBUNTU_VERSIONS]
    -t, --test-types TYPES          Comma-separated test types [default: $TEST_TYPES]
    -j, --parallel JOBS             Number of parallel jobs [default: $PARALLEL_JOBS]
    -e, --container-engine ENGINE   Container engine (podman or docker) [default: $CONTAINER_ENGINE]
    -b, --repo-branch BRANCH        Repository branch to test [default: $REPO_BRANCH]
    -l, --local-package FILE        Test local .deb package file
    -o, --output DIR                Output directory for test results [default: $TEST_RESULTS_DIR]
    --quick                         Quick test mode (reduced coverage)
    --fail-fast                     Stop on first test failure
    --no-cleanup                    Don't cleanup containers on exit
    --no-report                     Skip final report generation
    --format FORMAT                 Report format: json, html, junit [default: $OUTPUT_FORMAT]
    --timeout SECONDS               Test timeout per container [default: $TEST_TIMEOUT]
    --verbose                       Verbose output
    --debug                         Debug mode with detailed logging
    -h, --help                      Show this help message

TEST TYPES:
    quick           - Fast validation (basic installation + version check)
    installation    - Full installation testing
    upgrade         - Package upgrade testing
    functionality   - Comprehensive functionality testing
    security        - Security and GPG validation
    performance     - Performance benchmarking
    comprehensive   - All tests combined

UBUNTU VERSIONS:
    20.04, 22.04, 24.04            - Supported Ubuntu LTS versions

EXAMPLES:
    $0                                              # Default: all versions, installation+functionality
    $0 -v "22.04,24.04" -t "quick"                 # Quick test on Ubuntu 22.04 and 24.04
    $0 -j 1 -t "comprehensive" --verbose           # Sequential comprehensive testing
    $0 --local-package dist/rxiv-maker_*.deb       # Test local package across all versions
    $0 --fail-fast --timeout 900                   # Stop on first failure, 15min timeout
    $0 --format html --output ./reports            # Generate HTML report

ENVIRONMENT VARIABLES:
    RXIV_APT_TEST_REPO_URL      Custom repository URL
    RXIV_APT_TEST_GPG_KEY       Custom GPG key URL
    RXIV_APT_TEST_ENGINE        Container engine override

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--ubuntu-versions)
                UBUNTU_VERSIONS="$2"
                shift 2
                ;;
            -t|--test-types)
                TEST_TYPES="$2"
                shift 2
                ;;
            -j|--parallel)
                PARALLEL_JOBS="$2"
                shift 2
                ;;
            -e|--container-engine)
                CONTAINER_ENGINE="$2"
                shift 2
                ;;
            -b|--repo-branch)
                REPO_BRANCH="$2"
                shift 2
                ;;
            -l|--local-package)
                LOCAL_PACKAGE="$2"
                shift 2
                ;;
            -o|--output)
                TEST_RESULTS_DIR="$2"
                shift 2
                ;;
            --quick)
                QUICK_MODE="true"
                TEST_TYPES="quick"
                shift
                ;;
            --fail-fast)
                FAIL_FAST="true"
                shift
                ;;
            --no-cleanup)
                CLEANUP_ON_EXIT="false"
                shift
                ;;
            --no-report)
                GENERATE_REPORT="false"
                shift
                ;;
            --format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --timeout)
                TEST_TIMEOUT="$2"
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

# Validate environment and arguments
validate_environment() {
    log "Validating test environment..."

    # Check container engine
    if ! command -v "$CONTAINER_ENGINE" >/dev/null 2>&1; then
        error "Container engine '$CONTAINER_ENGINE' not found"
        log "Please install Podman: https://podman.io/getting-started/installation"
        exit 1
    fi

    # Validate Ubuntu versions
    IFS=',' read -ra VERSIONS_ARRAY <<< "$UBUNTU_VERSIONS"
    for version in "${VERSIONS_ARRAY[@]}"; do
        case "$version" in
            20.04|22.04|24.04) ;;
            *)
                error "Unsupported Ubuntu version: $version"
                log "Supported versions: 20.04, 22.04, 24.04"
                exit 1
                ;;
        esac
    done

    # Validate test types
    IFS=',' read -ra TYPES_ARRAY <<< "$TEST_TYPES"
    for test_type in "${TYPES_ARRAY[@]}"; do
        case "$test_type" in
            quick|installation|upgrade|functionality|security|performance|comprehensive) ;;
            *)
                error "Unknown test type: $test_type"
                log "Valid types: quick, installation, upgrade, functionality, security, performance, comprehensive"
                exit 1
                ;;
        esac
    done

    # Validate parallel jobs
    if ! [[ "$PARALLEL_JOBS" =~ ^[0-9]+$ ]] || [[ "$PARALLEL_JOBS" -lt 1 ]]; then
        error "Invalid parallel jobs: $PARALLEL_JOBS"
        exit 1
    fi

    # Validate local package if specified
    if [[ -n "$LOCAL_PACKAGE" ]] && [[ ! -f "$LOCAL_PACKAGE" ]]; then
        error "Local package file not found: $LOCAL_PACKAGE"
        exit 1
    fi

    # Calculate total tests
    local version_count=${#VERSIONS_ARRAY[@]}
    local type_count=${#TYPES_ARRAY[@]}
    TOTAL_TESTS=$((version_count * type_count))

    debug "Container engine: $CONTAINER_ENGINE"
    debug "Ubuntu versions: ${VERSIONS_ARRAY[*]}"
    debug "Test types: ${TYPES_ARRAY[*]}"
    debug "Parallel jobs: $PARALLEL_JOBS"
    debug "Total tests: $TOTAL_TESTS"
    debug "Output directory: $TEST_RESULTS_DIR"

    success "Environment validation passed"
}

# Setup test environment
setup_test_environment() {
    log "Setting up test environment..."

    # Create output directory
    mkdir -p "$TEST_RESULTS_DIR"

    # Create subdirectories for organization
    mkdir -p "$TEST_RESULTS_DIR/logs"
    mkdir -p "$TEST_RESULTS_DIR/reports"
    mkdir -p "$TEST_RESULTS_DIR/artifacts"

    # Create job tracking file
    echo "timestamp,ubuntu_version,test_type,status,duration,container_name" > "$TEST_RESULTS_DIR/job-tracking.csv"

    success "Test environment setup completed"
}

# Cleanup function
cleanup() {
    local exit_code=$?

    if [[ "$CLEANUP_ON_EXIT" == "true" ]]; then
        log "Cleaning up test environment..."

        # Kill any running jobs
        for job_pid in "${JOBS_RUNNING[@]}"; do
            if kill -0 "$job_pid" 2>/dev/null; then
                warn "Terminating running job: $job_pid"
                kill "$job_pid" 2>/dev/null || true
            fi
        done

        # Clean up any remaining containers
        if command -v "$CONTAINER_ENGINE" >/dev/null 2>&1; then
            local containers
            containers=$($CONTAINER_ENGINE ps -a --filter "name=rxiv-apt-test" --format "{{.Names}}" 2>/dev/null || true)

            if [[ -n "$containers" ]]; then
                warn "Cleaning up remaining test containers..."
                echo "$containers" | xargs -r $CONTAINER_ENGINE rm -f 2>/dev/null || true
            fi
        fi
    else
        log "Container cleanup disabled - containers preserved for debugging"
    fi

    if [[ $exit_code -eq 0 ]]; then
        success "Multi-container testing completed successfully"
    else
        error "Multi-container testing failed with exit code: $exit_code"
    fi

    exit $exit_code
}

# Setup cleanup trap
trap cleanup EXIT

# Run single test job
run_test_job() {
    local ubuntu_version="$1"
    local test_type="$2"
    local job_id="$3"

    local container_name="rxiv-apt-test-${ubuntu_version}-${test_type}-$(date +%s)-$job_id"
    local log_file="$TEST_RESULTS_DIR/logs/${ubuntu_version}-${test_type}-${job_id}.log"
    local start_time end_time duration

    start_time=$(date +%s)

    debug "Starting job $job_id: Ubuntu $ubuntu_version, test type: $test_type"

    # Build test command
    local test_cmd=(
        "$SCRIPT_DIR/test-apt-container.sh"
        "--ubuntu-version" "$ubuntu_version"
        "--test-type" "$test_type"
        "--container-name" "$container_name"
        "--output" "$TEST_RESULTS_DIR/artifacts"
        "--timeout" "$TEST_TIMEOUT"
    )

    if [[ -n "$LOCAL_PACKAGE" ]]; then
        test_cmd+=("--local-package" "$LOCAL_PACKAGE")
    fi

    if [[ "$REPO_BRANCH" != "apt-repo" ]]; then
        test_cmd+=("--repo-branch" "$REPO_BRANCH")
    fi

    if [[ "$QUICK_MODE" == "true" ]]; then
        test_cmd+=("--quick")
    fi

    if [[ "$CLEANUP_ON_EXIT" == "false" ]]; then
        test_cmd+=("--no-cleanup")
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        test_cmd+=("--verbose")
    fi

    if [[ "$DEBUG" == "true" ]]; then
        test_cmd+=("--debug")
    fi

    # Execute test with timeout and logging
    local test_exit_code=0

    {
        echo "=== Starting test job $job_id at $(date) ==="
        echo "Command: ${test_cmd[*]}"
        echo "Ubuntu Version: $ubuntu_version"
        echo "Test Type: $test_type"
        echo "Container Name: $container_name"
        echo ""

        if timeout "$((TEST_TIMEOUT + 60))" "${test_cmd[@]}"; then
            echo "=== Test job $job_id completed successfully at $(date) ==="
        else
            test_exit_code=$?
            echo "=== Test job $job_id failed with exit code $test_exit_code at $(date) ==="
        fi
    } &> "$log_file"

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Record job completion
    local status="passed"
    if [[ $test_exit_code -ne 0 ]]; then
        status="failed"
    fi

    echo "$(date -Iseconds),$ubuntu_version,$test_type,$status,$duration,$container_name" >> "$TEST_RESULTS_DIR/job-tracking.csv"

    if [[ $test_exit_code -eq 0 ]]; then
        debug "Job $job_id completed successfully (${duration}s)"
        return 0
    else
        debug "Job $job_id failed with exit code $test_exit_code (${duration}s)"
        return $test_exit_code
    fi
}

# Wait for job completion
wait_for_jobs() {
    local max_jobs="$1"

    while [[ ${#JOBS_RUNNING[@]} -ge $max_jobs ]]; do
        local new_running=()

        for job_pid in "${JOBS_RUNNING[@]}"; do
            if kill -0 "$job_pid" 2>/dev/null; then
                # Job still running
                new_running+=("$job_pid")
            else
                # Job completed
                local job_exit_code=0
                wait "$job_pid" || job_exit_code=$?

                JOBS_COMPLETED+=("$job_pid")

                if [[ $job_exit_code -eq 0 ]]; then
                    ((TESTS_PASSED++))
                else
                    ((TESTS_FAILED++))
                    JOBS_FAILED+=("$job_pid")

                    if [[ "$FAIL_FAST" == "true" ]]; then
                        error "Test failed and fail-fast mode enabled. Stopping."
                        return 1
                    fi
                fi
            fi
        done

        JOBS_RUNNING=("${new_running[@]}")

        if [[ ${#JOBS_RUNNING[@]} -ge $max_jobs ]]; then
            sleep 1
        fi
    done
}

# Run all test jobs
run_all_tests() {
    step "Starting multi-container test execution"

    local job_counter=0
    IFS=',' read -ra VERSIONS_ARRAY <<< "$UBUNTU_VERSIONS"
    IFS=',' read -ra TYPES_ARRAY <<< "$TEST_TYPES"

    log "Running $TOTAL_TESTS tests across ${#VERSIONS_ARRAY[@]} Ubuntu versions with ${#TYPES_ARRAY[@]} test types"
    log "Parallel jobs: $PARALLEL_JOBS"

    # Generate test matrix
    for ubuntu_version in "${VERSIONS_ARRAY[@]}"; do
        for test_type in "${TYPES_ARRAY[@]}"; do
            ((job_counter++))

            log "Starting test $job_counter/$TOTAL_TESTS: Ubuntu $ubuntu_version, $test_type"

            # Wait for available job slot
            wait_for_jobs "$PARALLEL_JOBS"

            # Start new job in background
            run_test_job "$ubuntu_version" "$test_type" "$job_counter" &
            local job_pid=$!
            JOBS_RUNNING+=("$job_pid")

            debug "Started job $job_counter with PID $job_pid"

            # Small delay to prevent overwhelming the system
            sleep 0.5
        done
    done

    # Wait for all remaining jobs to complete
    log "Waiting for all jobs to complete..."
    wait_for_jobs 0

    # Wait for any final jobs
    for job_pid in "${JOBS_RUNNING[@]}"; do
        if kill -0 "$job_pid" 2>/dev/null; then
            local job_exit_code=0
            wait "$job_pid" || job_exit_code=$?

            JOBS_COMPLETED+=("$job_pid")

            if [[ $job_exit_code -eq 0 ]]; then
                ((TESTS_PASSED++))
            else
                ((TESTS_FAILED++))
                JOBS_FAILED+=("$job_pid")
            fi
        fi
    done

    JOBS_RUNNING=()

    log "Test execution completed: $TESTS_PASSED passed, $TESTS_FAILED failed"

    if [[ $TESTS_FAILED -gt 0 ]]; then
        return 1
    else
        return 0
    fi
}

# Generate comprehensive test report
generate_test_report() {
    if [[ "$GENERATE_REPORT" != "true" ]]; then
        return 0
    fi

    step "Generating comprehensive test report"

    local report_timestamp
    report_timestamp=$(date -Iseconds)

    # Parse job tracking data
    local job_data="$TEST_RESULTS_DIR/job-tracking.csv"

    case "$OUTPUT_FORMAT" in
        json)
            generate_json_report "$report_timestamp"
            ;;
        html)
            generate_html_report "$report_timestamp"
            ;;
        junit)
            generate_junit_report "$report_timestamp"
            ;;
        *)
            warn "Unknown output format: $OUTPUT_FORMAT. Generating JSON report."
            generate_json_report "$report_timestamp"
            ;;
    esac

    success "Test report generated in $OUTPUT_FORMAT format"
}

# Generate JSON report
generate_json_report() {
    local timestamp="$1"
    local report_file="$TEST_RESULTS_DIR/reports/multi-container-report.json"

    # Read job tracking data
    local job_results=""
    if [[ -f "$TEST_RESULTS_DIR/job-tracking.csv" ]]; then
        while IFS=',' read -r ts ubuntu_version test_type status duration container_name; do
            if [[ "$ts" != "timestamp" ]]; then  # Skip header
                if [[ -n "$job_results" ]]; then
                    job_results="${job_results},"
                fi
                job_results="${job_results}
    {
      \"timestamp\": \"$ts\",
      \"ubuntu_version\": \"$ubuntu_version\",
      \"test_type\": \"$test_type\",
      \"status\": \"$status\",
      \"duration\": $duration,
      \"container_name\": \"$container_name\"
    }"
            fi
        done < "$TEST_RESULTS_DIR/job-tracking.csv"
    fi

    cat > "$report_file" << EOF
{
  "test_execution": {
    "timestamp": "$timestamp",
    "total_tests": $TOTAL_TESTS,
    "tests_passed": $TESTS_PASSED,
    "tests_failed": $TESTS_FAILED,
    "success_rate": $(echo "scale=2; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0"),
    "parallel_jobs": $PARALLEL_JOBS
  },
  "configuration": {
    "ubuntu_versions": "$UBUNTU_VERSIONS",
    "test_types": "$TEST_TYPES",
    "container_engine": "$CONTAINER_ENGINE",
    "repo_branch": "$REPO_BRANCH",
    "local_package": "${LOCAL_PACKAGE:-null}",
    "quick_mode": $QUICK_MODE,
    "test_timeout": $TEST_TIMEOUT
  },
  "job_results": [$job_results
  ],
  "environment": {
    "project_root": "$PROJECT_ROOT",
    "output_directory": "$TEST_RESULTS_DIR"
  }
}
EOF

    log "JSON report: $report_file"
}

# Generate HTML report
generate_html_report() {
    local timestamp="$1"
    local report_file="$TEST_RESULTS_DIR/reports/multi-container-report.html"

    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Container APT Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }
        .passed { background: #d4edda; color: #155724; }
        .failed { background: #f8d7da; color: #721c24; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f8f9fa; }
        .status-passed { background: #d4edda; }
        .status-failed { background: #f8d7da; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Multi-Container APT Test Report</h1>
        <p>Generated: $timestamp</p>
        <p>Ubuntu Versions: $UBUNTU_VERSIONS</p>
        <p>Test Types: $TEST_TYPES</p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <div>$TOTAL_TESTS</div>
        </div>
        <div class="metric passed">
            <h3>Passed</h3>
            <div>$TESTS_PASSED</div>
        </div>
        <div class="metric failed">
            <h3>Failed</h3>
            <div>$TESTS_FAILED</div>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <div>$(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")%</div>
        </div>
    </div>

    <table>
        <tr>
            <th>Timestamp</th>
            <th>Ubuntu Version</th>
            <th>Test Type</th>
            <th>Status</th>
            <th>Duration (s)</th>
            <th>Container Name</th>
        </tr>
EOF

    # Add job results
    if [[ -f "$TEST_RESULTS_DIR/job-tracking.csv" ]]; then
        while IFS=',' read -r ts ubuntu_version test_type status duration container_name; do
            if [[ "$ts" != "timestamp" ]]; then  # Skip header
                local status_class="status-$status"
                echo "        <tr class=\"$status_class\">" >> "$report_file"
                echo "            <td>$ts</td>" >> "$report_file"
                echo "            <td>$ubuntu_version</td>" >> "$report_file"
                echo "            <td>$test_type</td>" >> "$report_file"
                echo "            <td>$status</td>" >> "$report_file"
                echo "            <td>$duration</td>" >> "$report_file"
                echo "            <td>$container_name</td>" >> "$report_file"
                echo "        </tr>" >> "$report_file"
            fi
        done < "$TEST_RESULTS_DIR/job-tracking.csv"
    fi

    cat >> "$report_file" << EOF
    </table>
</body>
</html>
EOF

    log "HTML report: $report_file"
}

# Generate JUnit XML report
generate_junit_report() {
    local timestamp="$1"
    local report_file="$TEST_RESULTS_DIR/reports/multi-container-report.xml"

    cat > "$report_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="Multi-Container APT Tests" tests="$TOTAL_TESTS" failures="$TESTS_FAILED" time="0" timestamp="$timestamp">
EOF

    # Add test cases
    if [[ -f "$TEST_RESULTS_DIR/job-tracking.csv" ]]; then
        while IFS=',' read -r ts ubuntu_version test_type status duration container_name; do
            if [[ "$ts" != "timestamp" ]]; then  # Skip header
                local test_name="Ubuntu-${ubuntu_version}-${test_type}"
                echo "  <testcase classname=\"AptContainerTest\" name=\"$test_name\" time=\"$duration\">" >> "$report_file"

                if [[ "$status" == "failed" ]]; then
                    echo "    <failure message=\"Test failed\">Container: $container_name</failure>" >> "$report_file"
                fi

                echo "  </testcase>" >> "$report_file"
            fi
        done < "$TEST_RESULTS_DIR/job-tracking.csv"
    fi

    echo "</testsuite>" >> "$report_file"

    log "JUnit XML report: $report_file"
}

# Main execution
main() {
    log "Starting multi-container APT testing orchestrator"

    validate_environment
    setup_test_environment

    local start_time end_time total_duration
    start_time=$(date +%s)

    if run_all_tests; then
        end_time=$(date +%s)
        total_duration=$((end_time - start_time))

        success "All tests completed successfully in ${total_duration}s"
        generate_test_report

        log "Test Summary:"
        log "  Total Tests: $TOTAL_TESTS"
        log "  Passed: $TESTS_PASSED"
        log "  Failed: $TESTS_FAILED"
        log "  Success Rate: $(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")%"
        log "  Total Duration: ${total_duration}s"

        exit 0
    else
        end_time=$(date +%s)
        total_duration=$((end_time - start_time))

        error "Some tests failed (${total_duration}s total)"
        generate_test_report

        log "Test Summary:"
        log "  Total Tests: $TOTAL_TESTS"
        log "  Passed: $TESTS_PASSED"
        log "  Failed: $TESTS_FAILED"
        log "  Success Rate: $(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")%"
        log "  Total Duration: ${total_duration}s"

        exit 1
    fi
}

# Parse arguments and run
parse_args "$@"
main
