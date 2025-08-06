#!/bin/bash

# pull-gha-logs.sh - GitHub Actions Log Puller for rxiv-maker and submodules
# Pulls the latest GitHub Actions logs for the main repository and all submodules

set -eo pipefail

# Check if we're running in bash
if [ -z "${BASH_VERSION:-}" ]; then
    echo "Error: This script requires bash" >&2
    exit 1
fi

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly GITHUB_API_BASE="https://api.github.com"
readonly LOG_DIR="$PROJECT_ROOT/.gha-logs"

# Repository configurations
REPO_CONFIGS=(
    "main:HenriquesLab/rxiv-maker:main"
    "docker:HenriquesLab/docker-rxiv-maker:main"
    "homebrew:HenriquesLab/homebrew-rxiv-maker:main"
    "scoop:HenriquesLab/scoop-rxiv-maker:main"
    "vscode:HenriquesLab/vscode-rxiv-maker:main"
)

# GitHub API token (optional, for higher rate limits)
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Default values
DEFAULT_LIMIT=1
DEFAULT_STATUS="all"
VERBOSE=false
DOWNLOAD_ARTIFACTS=false
CLEAN_OLD=false

# Function to print colored output
print_status() {
    local status="$1"
    local message="$2"
    local color=""

    case "$status" in
        "SUCCESS"|"PASS") color="$GREEN" ;;
        "FAILURE"|"FAIL") color="$RED" ;;
        "PENDING"|"RUNNING") color="$YELLOW" ;;
        "INFO") color="$BLUE" ;;
        "DEBUG") color="$CYAN" ;;
        *) color="$NC" ;;
    esac

    echo -e "${color}[$status]${NC} $message"
}

# Function to check if gh CLI is available
check_gh_cli() {
    if ! command -v gh >/dev/null 2>&1; then
        print_status "FAIL" "GitHub CLI (gh) is not installed. Please install it first:"
        echo "  macOS: brew install gh"
        echo "  Linux: See https://github.com/cli/cli#installation"
        echo "  Windows: See https://github.com/cli/cli#installation"
        exit 1
    fi

    # Check if authenticated
    if ! gh auth status >/dev/null 2>&1; then
        print_status "FAIL" "GitHub CLI is not authenticated. Please run: gh auth login"
        exit 1
    fi
}

# Function to get workflow runs and download logs
get_repo_logs() {
    local repo_key="$1"
    local repo_name="$2"
    local branch="$3"
    local limit="${4:-$DEFAULT_LIMIT}"
    local status_filter="${5:-$DEFAULT_STATUS}"

    print_status "INFO" "Processing $repo_key: $repo_name"

    # Get current branch name
    local current_branch
    if [[ "$repo_key" == "main" ]]; then
        # For the main repository, get the actual current branch
        current_branch=$(git branch --show-current 2>/dev/null || echo "$branch")
    else
        # For submodules, use the default branch since we're not in their directory
        current_branch="$branch"
    fi

    print_status "INFO" "Filtering logs for branch: $current_branch"

    # Create repo-specific log directory
    local repo_log_dir="$LOG_DIR/$repo_key"
    mkdir -p "$repo_log_dir"

    # Build gh run list command - filter by current branch
    local gh_args=()
    gh_args+=("--repo" "$repo_name")
    gh_args+=("--limit" "$limit")
    gh_args+=("--branch" "$current_branch")

    if [[ "$status_filter" != "all" ]]; then
        gh_args+=("--status" "$status_filter")
    fi

    gh_args+=("--json" "databaseId,name,status,conclusion,number,createdAt,headBranch")

    if [[ "$VERBOSE" == true ]]; then
        print_status "DEBUG" "Running: gh run list ${gh_args[*]}"
    fi

    # Get workflow runs using gh CLI
    local workflow_runs
    if ! workflow_runs=$(gh run list "${gh_args[@]}" 2>/dev/null); then
        print_status "FAIL" "Failed to fetch workflow runs for $repo_name"
        return 1
    fi

    if [[ "$workflow_runs" == "[]" || -z "$workflow_runs" ]]; then
        print_status "INFO" "No workflow runs found for $repo_name on branch $current_branch"
        return 0
    fi

    # Parse and process workflow runs
    echo "$workflow_runs" | python3 -c "
import json
import sys

try:
    runs = json.load(sys.stdin)

    if not runs:
        print('No workflow runs found')
        sys.exit(0)

    print(f'Found {len(runs)} workflow runs for current branch', file=sys.stderr)

    for run in runs:
        run_id = run['databaseId']
        workflow_name = run['name']
        status = run['status']
        conclusion = run.get('conclusion') or 'N/A'
        run_number = run['number']
        created_at = run['createdAt']
        head_branch = run.get('headBranch', 'unknown')

        print(f'{run_id}|{workflow_name}|{status}|{conclusion}|{run_number}|{created_at}|{head_branch}')

except Exception as e:
    print(f'Error parsing workflow data: {e}', file=sys.stderr)
    sys.exit(1)
" | while IFS='|' read -r run_id workflow_name status conclusion run_number created_at head_branch; do
        if [[ -z "$run_id" ]]; then
            continue
        fi

        local safe_workflow_name=$(echo "$workflow_name" | tr ' /' '_-' | tr -d '()[]{}')
        local timestamp=$(echo "$created_at" | cut -d'T' -f1)
        local log_filename="${timestamp}_${safe_workflow_name}_${run_number}_${status}"

        if [[ "$conclusion" != "N/A" && "$conclusion" != "null" ]]; then
            log_filename="${log_filename}_${conclusion}"
        fi

        log_filename="${log_filename}.log"
        local output_path="$repo_log_dir/$log_filename"

        print_status "INFO" "  Run #$run_number: $workflow_name ($status/$conclusion) [branch: $head_branch]"

        if [[ "$VERBOSE" == true ]]; then
            print_status "DEBUG" "    Downloading logs to: $output_path"
        fi

        # Use gh run view --log for direct log download (simplified approach)
        if gh run view "$run_id" --repo "$repo_name" --log > "$output_path" 2>/dev/null && [[ -s "$output_path" ]]; then
            print_status "SUCCESS" "    Downloaded: $log_filename"
        else
            print_status "FAIL" "    Failed to download logs for run #$run_number"
            rm -f "$output_path"
        fi

        # Download artifacts if requested
        if [[ "$DOWNLOAD_ARTIFACTS" == true ]]; then
            local artifact_count
            artifact_count=$(gh run view "$run_id" --repo "$repo_name" --json "artifacts" --jq ".artifacts | length" 2>/dev/null || echo "0")

            if [[ "$artifact_count" -gt 0 ]]; then
                print_status "INFO" "    Found $artifact_count artifacts"
                local artifact_dir="$repo_log_dir/artifacts_${run_number}"
                mkdir -p "$artifact_dir"
                if gh run download "$run_id" --repo "$repo_name" --dir "$artifact_dir" 2>/dev/null; then
                    print_status "SUCCESS" "    Downloaded artifacts to: artifacts_${run_number}/"
                else
                    print_status "FAIL" "    Failed to download artifacts for run #$run_number"
                    rmdir "$artifact_dir" 2>/dev/null || true
                fi
            fi
        fi
    done

    print_status "SUCCESS" "Completed processing $repo_key"
    echo
}

# Function to clean old logs
clean_old_logs() {
    if [[ -d "$LOG_DIR" ]]; then
        print_status "INFO" "Cleaning old logs from $LOG_DIR"
        find "$LOG_DIR" -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
        find "$LOG_DIR" -type d -empty -delete 2>/dev/null || true
        print_status "SUCCESS" "Cleaned old logs (older than 7 days)"
    fi
}

# Function to clean all logs
clean_all_logs() {
    if [[ -d "$LOG_DIR" ]]; then
        print_status "INFO" "Clearing all previous logs from $LOG_DIR"
        rm -rf "$LOG_DIR"/* 2>/dev/null || true
        print_status "SUCCESS" "Cleared all previous logs"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Pull GitHub Actions logs for rxiv-maker and its submodules.

NOTE: This script automatically:
- Clears all previous logs before downloading new ones to avoid accumulating outdated log files
- Filters logs to only include runs from the current branch (dev-no-puppets for main repo)

OPTIONS:
    -h, --help              Show this help message
    -l, --limit NUMBER      Limit number of workflow runs per repo (default: $DEFAULT_LIMIT)
    -s, --status STATUS     Filter by status: all, completed, in_progress, queued (default: $DEFAULT_STATUS)
    -r, --repo REPO         Pull logs for specific repo only (main|docker|homebrew|scoop|vscode)
    -v, --verbose           Verbose output
    -a, --artifacts         Download artifacts
    -c, --clean             Clean old logs before downloading new ones
    --clean-only            Only clean old logs, don't download new ones

EXAMPLES:
    $0                                      # Pull logs for all repositories
    $0 -l 10 -s completed                  # Pull 10 completed runs for all repos
    $0 -r main -v                          # Pull logs for main repo only with verbose output
    $0 -a                                  # Download artifacts along with logs
    $0 --clean-only                        # Clean old logs only

REQUIREMENTS:
    - GitHub CLI (gh) must be installed and authenticated
    - Run 'gh auth login' if not already authenticated

ENVIRONMENT:
    The script uses gh CLI authentication (no additional tokens needed)

OUTPUT:
    Logs are saved to: $LOG_DIR/
    ├── main/              # Main repository logs
    ├── docker/            # Docker submodule logs
    ├── homebrew/          # Homebrew submodule logs
    ├── scoop/             # Scoop submodule logs
    └── vscode/            # VS Code extension logs

EOF
}

# Parse command line arguments
LIMIT="$DEFAULT_LIMIT"
STATUS_FILTER="$DEFAULT_STATUS"
REPO_FILTER=""
CLEAN_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--token)
            # Legacy option - now ignored since we use gh CLI
            print_status "INFO" "Token option ignored - using gh CLI authentication"
            shift 2
            ;;
        -l|--limit)
            LIMIT="$2"
            shift 2
            ;;
        -s|--status)
            STATUS_FILTER="$2"
            shift 2
            ;;
        -r|--repo)
            REPO_FILTER="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -a|--artifacts)
            DOWNLOAD_ARTIFACTS=true
            shift
            ;;
        -c|--clean)
            CLEAN_OLD=true
            shift
            ;;
        --clean-only)
            CLEAN_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

# Validate arguments
if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || [[ "$LIMIT" -lt 1 ]]; then
    echo "Error: Limit must be a positive integer" >&2
    exit 1
fi

if [[ "$STATUS_FILTER" != "all" && "$STATUS_FILTER" != "completed" && "$STATUS_FILTER" != "in_progress" && "$STATUS_FILTER" != "queued" ]]; then
    echo "Error: Status must be one of: all, completed, in_progress, queued" >&2
    exit 1
fi

if [[ -n "$REPO_FILTER" ]]; then
    # Validate repo filter
    valid_repos=("main" "docker" "homebrew" "scoop" "vscode")
    if [[ ! " ${valid_repos[@]} " =~ " ${REPO_FILTER} " ]]; then
        echo "Error: Repository must be one of: ${valid_repos[*]}" >&2
        exit 1
    fi
fi

# Main execution
main() {
    # Check gh CLI availability first
    check_gh_cli

    print_status "INFO" "Starting GitHub Actions log pull for rxiv-maker"
    echo "Configuration:"
    echo "  Log directory: $LOG_DIR"
    echo "  Limit per repo: $LIMIT"
    echo "  Status filter: $STATUS_FILTER"
    echo "  Repository filter: ${REPO_FILTER:-all}"
    echo "  Verbose: $VERBOSE"
    echo "  Download artifacts: $DOWNLOAD_ARTIFACTS"
    echo

    # Always clear previous logs before downloading new ones
    clean_all_logs

    # Clean old logs if specifically requested (for compatibility)
    if [[ "$CLEAN_OLD" == true || "$CLEAN_ONLY" == true ]]; then
        clean_old_logs
        if [[ "$CLEAN_ONLY" == true ]]; then
            print_status "SUCCESS" "Clean-only operation completed"
            exit 0
        fi
    fi

    # Create log directory
    mkdir -p "$LOG_DIR"

    # Process repositories
    local processed_count=0
    local failed_count=0

    for config in "${REPO_CONFIGS[@]}"; do
        IFS=':' read -r repo_key repo_name branch <<< "$config"

        # Skip if repo filter is set and doesn't match
        if [[ -n "$REPO_FILTER" && "$repo_key" != "$REPO_FILTER" ]]; then
            continue
        fi

        if get_repo_logs "$repo_key" "$repo_name" "$branch" "$LIMIT" "$STATUS_FILTER"; then
            ((processed_count++))
        else
            ((failed_count++))
        fi
    done

    # Summary
    echo "=========================================="
    print_status "INFO" "Pull operation completed"
    echo "  Repositories processed: $processed_count"
    echo "  Repositories failed: $failed_count"
    echo "  Logs saved to: $LOG_DIR"

    if [[ -d "$LOG_DIR" ]]; then
        local total_files
        total_files=$(find "$LOG_DIR" -type f -name "*.log" | wc -l)
        echo "  Total log files: $total_files"
    fi

    if [[ "$failed_count" -gt 0 ]]; then
        print_status "FAIL" "Some repositories failed to process"
        exit 1
    else
        print_status "SUCCESS" "All repositories processed successfully"
    fi
}

# Run main function
main "$@"
