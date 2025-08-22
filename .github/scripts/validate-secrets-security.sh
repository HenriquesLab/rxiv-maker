#!/bin/bash
set -euo pipefail

# Security Validation Script for GitHub Actions Secrets
# This script validates the security posture of secrets and permissions

# Configuration
OUTPUT_FORMAT="${OUTPUT_FORMAT:-summary}"  # json, summary, github-actions
WORKFLOW_DIR="${WORKFLOW_DIR:-.github/workflows}"
SECURITY_LEVEL="${SECURITY_LEVEL:-medium}"  # strict, medium, relaxed

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Security findings
SECURITY_ISSUES=()
SECURITY_WARNINGS=()
SECURITY_RECOMMENDATIONS=()

log_info() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${BLUE}[SECURITY-INFO]${NC} $1" >&2
    fi
}

log_warning() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${YELLOW}[SECURITY-WARN]${NC} $1" >&2
    fi
    SECURITY_WARNINGS+=("$1")
}

log_issue() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${RED}[SECURITY-ISSUE]${NC} $1" >&2
    fi
    SECURITY_ISSUES+=("$1")
}

log_recommendation() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${GREEN}[SECURITY-REC]${NC} $1" >&2
    fi
    SECURITY_RECOMMENDATIONS+=("$1")
}

validate_secret_usage() {
    log_info "🔍 Validating secret usage patterns..."
    
    # Find all secret references
    SECRET_REFS=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -H "secrets\." {} \; 2>/dev/null || true)
    
    if [ -z "$SECRET_REFS" ]; then
        log_warning "No secrets found in workflows - this may indicate missing authentication"
        return
    fi
    
    # Analyze secret patterns
    local pat_count=$(echo "$SECRET_REFS" | grep -c "DISPATCH_PAT\|PAT\|TOKEN" || echo 0)
    local docker_count=$(echo "$SECRET_REFS" | grep -c "DOCKER_" || echo 0)
    local github_token_count=$(echo "$SECRET_REFS" | grep -c "GITHUB_TOKEN" || echo 0)
    
    log_info "Secret usage summary:"
    log_info "  Personal Access Tokens: $pat_count"
    log_info "  Docker credentials: $docker_count"
    log_info "  GitHub tokens: $github_token_count"
    
    # Validate secret best practices
    if [ "$pat_count" -gt 0 ]; then
        if echo "$SECRET_REFS" | grep -q "secrets\..*PAT.*||"; then
            log_recommendation "Good: Found fallback patterns for PAT usage"
        else
            log_warning "Personal Access Tokens used without fallback mechanisms"
        fi
        
        if [ "$pat_count" -gt 3 ]; then
            log_issue "Excessive PAT usage detected ($pat_count instances) - consider GitHub Apps"
        fi
    fi
    
    # Check for hardcoded secrets (security anti-pattern)
    local hardcoded_secrets=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -H -E "(password:|token:|secret:).*(ghp_|gho_|ghu_|ghs_|ghr_)" {} \; 2>/dev/null || true)
    if [ -n "$hardcoded_secrets" ]; then
        log_issue "CRITICAL: Hardcoded secrets detected in workflow files!"
        echo "$hardcoded_secrets" | while read -r line; do
            log_issue "  $line"
        done
    fi
}

validate_permissions() {
    log_info "🔐 Validating workflow permissions..."
    
    # Check for overly permissive workflows
    local broad_perms=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -l "permissions:.*write-all\|permissions:.*admin" {} \; 2>/dev/null || true)
    if [ -n "$broad_perms" ]; then
        log_issue "Workflows with overly broad permissions found:"
        echo "$broad_perms" | while read -r file; do
            log_issue "  $(basename "$file")"
        done
    fi
    
    # Check for minimal permission patterns
    local minimal_perms=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -l "contents: read" {} \; 2>/dev/null | wc -l)
    local total_workflows=$(find "$WORKFLOW_DIR" -name "*.yml" | wc -l)
    
    if [ "$minimal_perms" -gt 0 ]; then
        log_recommendation "Good: $minimal_perms/$total_workflows workflows use minimal permissions"
    fi
    
    # Check for job-level permission elevation
    local job_elevation=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -A 5 -B 5 "permissions:" {} \; | grep -c "contents: write\|packages: write\|id-token: write" || echo 0)
    if [ "$job_elevation" -gt 0 ]; then
        log_info "Found $job_elevation job-level permission elevations (review for necessity)"
    fi
}

validate_oidc_usage() {
    log_info "🎫 Validating OIDC authentication usage..."
    
    # Check for OIDC usage (modern best practice)
    local oidc_usage=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -l "id-token: write" {} \; 2>/dev/null | wc -l)
    if [ "$oidc_usage" -gt 0 ]; then
        log_recommendation "Good: OIDC authentication detected in $oidc_usage workflow(s)"
    fi
    
    # Check for PyPI OIDC specifically
    local pypi_oidc=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -A 10 -B 10 "pypa/gh-action-pypi-publish" {} \; | grep -c "id-token: write" || echo 0)
    if [ "$pypi_oidc" -gt 0 ]; then
        log_recommendation "Excellent: PyPI OIDC authentication configured"
    else
        local pypi_usage=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -l "pypa/gh-action-pypi-publish\|twine upload" {} \; | wc -l)
        if [ "$pypi_usage" -gt 0 ]; then
            log_warning "PyPI publishing detected without OIDC - consider upgrading"
        fi
    fi
}

validate_environment_usage() {
    log_info "🌍 Validating environment protection usage..."
    
    # Check for environment-protected deployments
    local env_usage=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -c "environment:" {} \; | paste -sd+ | bc || echo 0)
    if [ "$env_usage" -gt 0 ]; then
        log_recommendation "Good: Environment protection detected in workflows"
    else
        # Check if there are deployment workflows that should use environments
        local deploy_workflows=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -l "deploy\|publish\|release" {} \; | wc -l)
        if [ "$deploy_workflows" -gt 0 ]; then
            log_warning "Deployment workflows detected without environment protection"
        fi
    fi
}

validate_secret_scanning() {
    log_info "🔎 Checking for secret scanning bypass patterns..."
    
    # Check for patterns that might bypass secret scanning
    local bypass_patterns=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -H -E "(echo.*\\\$\{|base64.*decode|printf.*%s)" {} \; 2>/dev/null || true)
    if [ -n "$bypass_patterns" ]; then
        log_warning "Potential secret scanning bypass patterns detected:"
        echo "$bypass_patterns" | while read -r line; do
            log_warning "  $line"
        done
    fi
}

check_external_dependencies() {
    log_info "🔗 Validating external action dependencies..."
    
    # Check for unpinned actions (security risk)
    local unpinned_actions=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -H "uses:.*@main\|uses:.*@master\|uses:.*@latest" {} \; 2>/dev/null || true)
    if [ -n "$unpinned_actions" ]; then
        log_warning "Unpinned external actions detected (security risk):"
        echo "$unpinned_actions" | while read -r line; do
            log_warning "  $line"
        done
    fi
    
    # Count pinned vs unpinned
    local total_actions=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -c "uses:" {} \; | paste -sd+ | bc || echo 0)
    local pinned_actions=$(find "$WORKFLOW_DIR" -name "*.yml" -exec grep -c "uses:.*@v[0-9]\|uses:.*@[a-f0-9]\{40\}" {} \; | paste -sd+ | bc || echo 0)
    
    if [ "$total_actions" -gt 0 ]; then
        local pinned_percent=$(( pinned_actions * 100 / total_actions ))
        log_info "Action pinning: $pinned_actions/$total_actions ($pinned_percent%)"
        
        if [ "$pinned_percent" -ge 80 ]; then
            log_recommendation "Good: Most external actions are pinned"
        elif [ "$pinned_percent" -ge 60 ]; then
            log_warning "Moderate: Some external actions are unpinned"
        else
            log_issue "Poor: Many external actions are unpinned (security risk)"
        fi
    fi
}

calculate_security_score() {
    local issues_count=${#SECURITY_ISSUES[@]}
    local warnings_count=${#SECURITY_WARNINGS[@]}
    local recommendations_count=${#SECURITY_RECOMMENDATIONS[@]}
    
    # Base score
    local score=100
    
    # Deduct points for issues and warnings
    score=$(( score - (issues_count * 20) ))
    score=$(( score - (warnings_count * 5) ))
    
    # Add points for good practices (recommendations indicate good findings)
    score=$(( score + (recommendations_count * 2) ))
    
    # Ensure score is in valid range
    if [ "$score" -lt 0 ]; then
        score=0
    elif [ "$score" -gt 100 ]; then
        score=100
    fi
    
    echo "$score"
}

determine_security_level() {
    local score="$1"
    
    if [ "$score" -ge 90 ]; then
        echo "excellent"
    elif [ "$score" -ge 80 ]; then
        echo "good"
    elif [ "$score" -ge 70 ]; then
        echo "fair"
    elif [ "$score" -ge 60 ]; then
        echo "poor"
    else
        echo "critical"
    fi
}

generate_json_output() {
    local score="$1"
    local level="$2"
    
    cat << EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "security_score": $score,
  "security_level": "$level",
  "summary": {
    "issues": ${#SECURITY_ISSUES[@]},
    "warnings": ${#SECURITY_WARNINGS[@]},
    "recommendations": ${#SECURITY_RECOMMENDATIONS[@]}
  },
  "findings": {
    "issues": $(printf '%s\n' "${SECURITY_ISSUES[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))'),
    "warnings": $(printf '%s\n' "${SECURITY_WARNINGS[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))'),
    "recommendations": $(printf '%s\n' "${SECURITY_RECOMMENDATIONS[@]:-}" | jq -R -s -c 'split("\n") | map(select(length > 0))')
  },
  "audit_info": {
    "workflow_directory": "$WORKFLOW_DIR",
    "security_level": "$SECURITY_LEVEL"
  }
}
EOF
}

generate_github_actions_output() {
    local score="$1"
    local level="$2"
    
    echo "security_score=$score"
    echo "security_level=$level"
    echo "issues_count=${#SECURITY_ISSUES[@]}"
    echo "warnings_count=${#SECURITY_WARNINGS[@]}"
    echo "recommendations_count=${#SECURITY_RECOMMENDATIONS[@]}"
}

main() {
    log_info "🔒 Starting GitHub Actions security validation..."
    
    # Check required tools
    for tool in grep find jq bc; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_issue "Required tool '$tool' is not installed"
            exit 1
        fi
    done
    
    # Validate workflow directory exists
    if [ ! -d "$WORKFLOW_DIR" ]; then
        log_issue "Workflow directory '$WORKFLOW_DIR' does not exist"
        exit 1
    fi
    
    # Run security validations
    validate_secret_usage
    validate_permissions
    validate_oidc_usage
    validate_environment_usage
    validate_secret_scanning
    check_external_dependencies
    
    # Calculate final score and level
    local score
    score=$(calculate_security_score)
    local level
    level=$(determine_security_level "$score")
    
    # Generate output
    case "$OUTPUT_FORMAT" in
        "json")
            generate_json_output "$score" "$level"
            ;;
        "github-actions")
            generate_github_actions_output "$score" "$level"
            ;;
        "summary"|*)
            echo ""
            echo "🔒 Security Validation Summary:"
            echo "  Security Score: $score/100"
            echo "  Security Level: $level"
            echo "  Issues: ${#SECURITY_ISSUES[@]}"
            echo "  Warnings: ${#SECURITY_WARNINGS[@]}"
            echo "  Good Practices: ${#SECURITY_RECOMMENDATIONS[@]}"
            ;;
    esac
    
    # Set exit code based on security level
    case "$level" in
        "excellent"|"good")
            exit 0
            ;;
        "fair")
            exit 1
            ;;
        "poor")
            exit 2
            ;;
        "critical")
            exit 3
            ;;
        *)
            exit 4
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi