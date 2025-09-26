#!/bin/bash
set -euo pipefail

# Cross-Repository Health Check Script
# This script provides a quick health check of the rxiv-maker ecosystem
# Can be called from other workflows or used standalone

# Configuration
MAIN_REPO="${MAIN_REPO:-HenriquesLab/rxiv-maker}"
DOCKER_REPO="${DOCKER_REPO:-HenriquesLab/docker-rxiv-maker}"
VSCODE_REPO="${VSCODE_REPO:-HenriquesLab/vscode-rxiv-maker}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-30}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-json}"  # json, summary, or github-actions

# Colors for output (when not in JSON mode)
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health status tracking
OVERALL_HEALTH="healthy"
HEALTH_ISSUES=()
HEALTH_WARNINGS=()

log_info() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${BLUE}[INFO]${NC} $1" >&2
    fi
}

log_warning() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${YELLOW}[WARN]${NC} $1" >&2
    fi
    HEALTH_WARNINGS+=("$1")
    if [ "$OVERALL_HEALTH" == "healthy" ]; then
        OVERALL_HEALTH="warning"
    fi
}

log_error() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${RED}[ERROR]${NC} $1" >&2
    fi
    HEALTH_ISSUES+=("$1")
    OVERALL_HEALTH="critical"
}

log_success() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${GREEN}[OK]${NC} $1" >&2
    fi
}

check_repository_access() {
    local repo="$1"
    local name="$2"

    log_info "Checking access to $name repository..."

    if timeout "$TIMEOUT_SECONDS" gh repo view "$repo" >/dev/null 2>&1; then
        log_success "$name repository is accessible"
        return 0
    else
        log_error "$name repository is not accessible or does not exist"
        return 1
    fi
}

check_workflow_health() {
    local repo="$1"
    local name="$2"

    log_info "Checking recent workflow health for $name..."

    # Check for recent failures (last 24 hours)
    local failed_runs
    failed_runs=$(gh run list --repo "$repo" \
        --status failure \
        --created "$(date -d '24 hours ago' -I 2>/dev/null || date -v-1d '+%Y-%m-%d')" \
        --limit 10 \
        --json workflowName,status,createdAt 2>/dev/null || echo "[]")

    local failed_count
    failed_count=$(echo "$failed_runs" | jq length 2>/dev/null || echo 0)

    if [ "$failed_count" -eq 0 ]; then
        log_success "$name has no recent workflow failures"
    elif [ "$failed_count" -le 2 ]; then
        log_warning "$name has $failed_count recent workflow failures"
    else
        log_error "$name has $failed_count recent workflow failures (concerning)"
    fi

    echo "$failed_count"
}

check_release_alignment() {
    log_info "Checking release version alignment..."

    # Get main repository version
    local main_version
    if [ -f "src/rxiv_maker/__version__.py" ]; then
        main_version=$(python3 -c "exec(open('src/rxiv_maker/__version__.py').read()); print(__version__)" 2>/dev/null || echo "unknown")
    else
        main_version="unknown"
    fi

    log_info "Main repository version: $main_version"

    # Check Docker repository latest release (if accessible)
    local docker_version="unknown"
    if gh release list --repo "$DOCKER_REPO" --limit 1 >/dev/null 2>&1; then
        docker_version=$(gh release list --repo "$DOCKER_REPO" --limit 1 | head -1 | awk '{print $3}' | sed 's/v//' 2>/dev/null || echo "unknown")
    fi

    log_info "Docker repository version: $docker_version"

    # Check version alignment
    if [ "$main_version" != "unknown" ] && [ "$docker_version" != "unknown" ]; then
        if [ "$main_version" == "$docker_version" ]; then
            log_success "Version alignment: Main and Docker are aligned ($main_version)"
        else
            log_warning "Version misalignment: Main ($main_version) != Docker ($docker_version)"
        fi
    elif [ "$main_version" != "unknown" ]; then
        log_warning "Cannot verify Docker version alignment"
    else
        log_warning "Cannot determine main repository version"
    fi

    # Return version info
    echo "$main_version:$docker_version"
}

generate_json_output() {
    local main_failures="$1"
    local docker_failures="$2"
    local vscode_failures="$3"
    local version_info="$4"

    local main_version="${version_info%%:*}"
    local docker_version="${version_info##*:}"

    cat << EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "overall_health": "$OVERALL_HEALTH",
  "repositories": {
    "main": {
      "name": "$MAIN_REPO",
      "accessible": true,
      "recent_failures": $main_failures,
      "version": "$main_version",
      "status": "$([ "$main_failures" -eq 0 ] && echo "healthy" || [ "$main_failures" -le 2 ] && echo "warning" || echo "critical")"
    },
    "docker": {
      "name": "$DOCKER_REPO",
      "accessible": true,
      "recent_failures": $docker_failures,
      "version": "$docker_version",
      "status": "$([ "$docker_failures" -eq 0 ] && echo "healthy" || [ "$docker_failures" -le 2 ] && echo "warning" || echo "critical")"
    },
    "vscode": {
      "name": "$VSCODE_REPO",
      "accessible": true,
      "recent_failures": $vscode_failures,
      "status": "$([ "$vscode_failures" -eq 0 ] && echo "healthy" || [ "$vscode_failures" -le 2 ] && echo "warning" || echo "critical")"
    }
  },
  "issues": $(printf '%s\n' "${HEALTH_ISSUES[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))'),
  "warnings": $(printf '%s\n' "${HEALTH_WARNINGS[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))'),
  "summary": {
    "total_failures": $(( main_failures + docker_failures + vscode_failures )),
    "critical_issues": ${#HEALTH_ISSUES[@]},
    "warnings": ${#HEALTH_WARNINGS[@]}
  }
}
EOF
}

generate_github_actions_output() {
    local main_failures="$1"
    local docker_failures="$2"
    local vscode_failures="$3"
    local version_info="$4"

    echo "overall_health=$OVERALL_HEALTH"
    echo "main_failures=$main_failures"
    echo "docker_failures=$docker_failures"
    echo "vscode_failures=$vscode_failures"
    echo "total_failures=$(( main_failures + docker_failures + vscode_failures ))"
    echo "critical_issues=${#HEALTH_ISSUES[@]}"
    echo "warnings=${#HEALTH_WARNINGS[@]}"
    echo "version_info=$version_info"
}

main() {
    log_info "🔍 Starting rxiv-maker ecosystem health check..."

    # Check required tools
    for tool in gh jq; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool '$tool' is not installed"
            exit 1
        fi
    done

    # Check repository access
    local main_accessible=1
    local docker_accessible=1
    local vscode_accessible=1

    check_repository_access "$MAIN_REPO" "main" || main_accessible=0
    check_repository_access "$DOCKER_REPO" "docker" || docker_accessible=0
    check_repository_access "$VSCODE_REPO" "vscode" || vscode_accessible=0

    # Check workflow health for accessible repositories
    local main_failures=999
    local docker_failures=999
    local vscode_failures=999

    if [ $main_accessible -eq 1 ]; then
        main_failures=$(check_workflow_health "$MAIN_REPO" "main repository")
    fi

    if [ $docker_accessible -eq 1 ]; then
        docker_failures=$(check_workflow_health "$DOCKER_REPO" "docker repository")
    else
        docker_failures=0  # Don't count as failures if inaccessible
    fi

    if [ $vscode_accessible -eq 1 ]; then
        vscode_failures=$(check_workflow_health "$VSCODE_REPO" "vscode repository")
    else
        vscode_failures=0  # Don't count as failures if inaccessible
    fi

    # Check release alignment
    local version_info="unknown:unknown"
    if [ $main_accessible -eq 1 ] && [ $docker_accessible -eq 1 ]; then
        version_info=$(check_release_alignment)
    fi

    # Generate output based on format
    case "$OUTPUT_FORMAT" in
        "json")
            generate_json_output "$main_failures" "$docker_failures" "$vscode_failures" "$version_info"
            ;;
        "github-actions")
            generate_github_actions_output "$main_failures" "$docker_failures" "$vscode_failures" "$version_info"
            ;;
        "summary"|*)
            echo ""
            echo "🎯 Health Check Summary:"
            echo "  Overall Health: $OVERALL_HEALTH"
            echo "  Main Repository: $main_failures recent failures"
            echo "  Docker Repository: $docker_failures recent failures"
            echo "  VSCode Repository: $vscode_failures recent failures"
            echo "  Critical Issues: ${#HEALTH_ISSUES[@]}"
            echo "  Warnings: ${#HEALTH_WARNINGS[@]}"
            ;;
    esac

    # Set exit code based on health
    case "$OVERALL_HEALTH" in
        "healthy")
            exit 0
            ;;
        "warning")
            exit 1
            ;;
        "critical")
            exit 2
            ;;
        *)
            exit 3
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
