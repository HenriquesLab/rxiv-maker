#!/bin/bash
set -euo pipefail

# Cross-Repository Health Check Script
# This script provides a quick health check of the rxiv-maker ecosystem
# Can be called from other workflows or used standalone

# Configuration
MAIN_REPO="${MAIN_REPO:-HenriquesLab/rxiv-maker}"
HOMEBREW_REPO="${HOMEBREW_REPO:-HenriquesLab/homebrew-rxiv-maker}"
APT_REPO="${APT_REPO:-HenriquesLab/apt-rxiv-maker}"
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

    # Check Homebrew formula version (if accessible)
    local homebrew_version="unknown"
    if gh api "repos/$HOMEBREW_REPO/contents/Formula/rxiv-maker.rb" >/dev/null 2>&1; then
        homebrew_version=$(gh api "repos/$HOMEBREW_REPO/contents/Formula/rxiv-maker.rb" \
            | jq -r '.content' \
            | base64 -d \
            | grep -o 'version "[^"]*"' \
            | cut -d'"' -f2 2>/dev/null || echo "unknown")
    fi

    log_info "Homebrew formula version: $homebrew_version"

    # Check version alignment
    if [ "$main_version" != "unknown" ] && [ "$homebrew_version" != "unknown" ]; then
        if [ "$main_version" == "$homebrew_version" ]; then
            log_success "Version alignment: Main and Homebrew are aligned ($main_version)"
        else
            log_warning "Version misalignment: Main ($main_version) != Homebrew ($homebrew_version)"
        fi
    elif [ "$main_version" != "unknown" ]; then
        log_warning "Cannot verify Homebrew version alignment"
    else
        log_warning "Cannot determine main repository version"
    fi

    # Return version info
    echo "$main_version:$homebrew_version"
}

generate_json_output() {
    local main_failures="$1"
    local homebrew_failures="$2"
    local apt_failures="$3"
    local version_info="$4"

    local main_version="${version_info%%:*}"
    local homebrew_version="${version_info##*:}"

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
    "homebrew": {
      "name": "$HOMEBREW_REPO",
      "accessible": true,
      "recent_failures": $homebrew_failures,
      "version": "$homebrew_version",
      "status": "$([ "$homebrew_failures" -eq 0 ] && echo "healthy" || [ "$homebrew_failures" -le 2 ] && echo "warning" || echo "critical")"
    },
    "apt": {
      "name": "$APT_REPO",
      "accessible": true,
      "recent_failures": $apt_failures,
      "status": "$([ "$apt_failures" -eq 0 ] && echo "healthy" || [ "$apt_failures" -le 2 ] && echo "warning" || echo "critical")"
    }
  },
  "issues": $(printf '%s\n' "${HEALTH_ISSUES[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))'),
  "warnings": $(printf '%s\n' "${HEALTH_WARNINGS[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))'),
  "summary": {
    "total_failures": $(( main_failures + homebrew_failures + apt_failures )),
    "critical_issues": ${#HEALTH_ISSUES[@]},
    "warnings": ${#HEALTH_WARNINGS[@]}
  }
}
EOF
}

generate_github_actions_output() {
    local main_failures="$1"
    local homebrew_failures="$2"
    local apt_failures="$3"
    local version_info="$4"

    echo "overall_health=$OVERALL_HEALTH"
    echo "main_failures=$main_failures"
    echo "homebrew_failures=$homebrew_failures"
    echo "apt_failures=$apt_failures"
    echo "total_failures=$(( main_failures + homebrew_failures + apt_failures ))"
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
    local homebrew_accessible=1
    local apt_accessible=1

    check_repository_access "$MAIN_REPO" "main" || main_accessible=0
    check_repository_access "$HOMEBREW_REPO" "homebrew" || homebrew_accessible=0
    check_repository_access "$APT_REPO" "apt" || apt_accessible=0

    # Check workflow health for accessible repositories
    local main_failures=999
    local homebrew_failures=999
    local apt_failures=999

    if [ $main_accessible -eq 1 ]; then
        main_failures=$(check_workflow_health "$MAIN_REPO" "main repository")
    fi

    if [ $homebrew_accessible -eq 1 ]; then
        homebrew_failures=$(check_workflow_health "$HOMEBREW_REPO" "homebrew repository")
    else
        homebrew_failures=0  # Don't count as failures if inaccessible
    fi

    if [ $apt_accessible -eq 1 ]; then
        apt_failures=$(check_workflow_health "$APT_REPO" "apt repository")
    else
        apt_failures=0  # Don't count as failures if inaccessible
    fi

    # Check release alignment
    local version_info="unknown:unknown"
    if [ $main_accessible -eq 1 ] && [ $homebrew_accessible -eq 1 ]; then
        version_info=$(check_release_alignment)
    fi

    # Generate output based on format
    case "$OUTPUT_FORMAT" in
        "json")
            generate_json_output "$main_failures" "$homebrew_failures" "$apt_failures" "$version_info"
            ;;
        "github-actions")
            generate_github_actions_output "$main_failures" "$homebrew_failures" "$apt_failures" "$version_info"
            ;;
        "summary"|*)
            echo ""
            echo "🎯 Health Check Summary:"
            echo "  Overall Health: $OVERALL_HEALTH"
            echo "  Main Repository: $main_failures recent failures"
            echo "  Homebrew Repository: $homebrew_failures recent failures"
            echo "  APT Repository: $apt_failures recent failures"
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
