#!/bin/bash
# validate-submodules.sh - Comprehensive submodule validation script
# Prevents repository corruption by validating submodule structure and content

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ERRORS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    ((ERRORS++))
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

# Validate submodule URLs are correct
validate_submodule_urls() {
    log_info "Validating submodule URLs..."

    local expected_urls=(
        "submodules/homebrew-rxiv-maker:https://github.com/henriqueslab/homebrew-rxiv-maker.git"
        "submodules/scoop-rxiv-maker:https://github.com/henriqueslab/scoop-rxiv-maker.git"
        "submodules/vscode-rxiv-maker:https://github.com/HenriquesLab/vscode-rxiv-maker.git"
    )

    for entry in "${expected_urls[@]}"; do
        local path="${entry%%:*}"
        local expected_url="${entry#*:}"

        if [[ -f "${REPO_ROOT}/.gitmodules" ]]; then
            local actual_url=$(git config -f "${REPO_ROOT}/.gitmodules" --get "submodule.${path}.url" 2>/dev/null || echo "")

            if [[ "$actual_url" != "$expected_url" ]]; then
                log_error "Submodule ${path} has incorrect URL: '${actual_url}' (expected: '${expected_url}')"
            else
                log_success "Submodule ${path} URL is correct"
            fi
        else
            log_error ".gitmodules file not found"
        fi
    done
}

# Validate submodule content signatures
validate_content_signatures() {
    log_info "Validating submodule content signatures..."

    # Homebrew submodule should have Formula directory and .rb files
    if [[ -d "${REPO_ROOT}/submodules/homebrew-rxiv-maker" ]]; then
        if [[ -d "${REPO_ROOT}/submodules/homebrew-rxiv-maker/Formula" ]] && \
           [[ -f "${REPO_ROOT}/submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb" ]]; then
            log_success "Homebrew submodule has correct structure"
        else
            log_error "Homebrew submodule missing expected Formula directory or .rb file"
        fi

        # Check for contamination - shouldn't have Python files
        if find "${REPO_ROOT}/submodules/homebrew-rxiv-maker" -name "*.py" -type f | grep -q .; then
            log_error "Homebrew submodule contaminated with Python files"
        fi
    fi

    # Scoop submodule should have bucket directory and .json files
    if [[ -d "${REPO_ROOT}/submodules/scoop-rxiv-maker" ]]; then
        if [[ -d "${REPO_ROOT}/submodules/scoop-rxiv-maker/bucket" ]] && \
           [[ -f "${REPO_ROOT}/submodules/scoop-rxiv-maker/bucket/rxiv-maker.json" ]]; then
            log_success "Scoop submodule has correct structure"
        else
            log_error "Scoop submodule missing expected bucket directory or .json file"
        fi

        # Check for contamination - shouldn't have Python files
        if find "${REPO_ROOT}/submodules/scoop-rxiv-maker" -name "*.py" -type f | grep -q .; then
            log_error "Scoop submodule contaminated with Python files"
        fi
    fi

    # VSCode submodule should have package.json and extension.ts
    if [[ -d "${REPO_ROOT}/submodules/vscode-rxiv-maker" ]]; then
        if [[ -f "${REPO_ROOT}/submodules/vscode-rxiv-maker/package.json" ]] && \
           [[ -f "${REPO_ROOT}/submodules/vscode-rxiv-maker/src/extension.ts" ]]; then
            log_success "VSCode submodule has correct structure"

            # Validate package.json contains VSCode extension markers
            if grep -q '"vscode"' "${REPO_ROOT}/submodules/vscode-rxiv-maker/package.json" && \
               grep -q '"engines"' "${REPO_ROOT}/submodules/vscode-rxiv-maker/package.json"; then
                log_success "VSCode submodule package.json is valid extension manifest"
            else
                log_error "VSCode submodule package.json doesn't look like a VSCode extension"
            fi
        else
            log_error "VSCode submodule missing expected package.json or extension.ts"
        fi

        # Check for contamination - shouldn't have main rxiv-maker files
        if [[ -f "${REPO_ROOT}/submodules/vscode-rxiv-maker/pyproject.toml" ]] || \
           [[ -f "${REPO_ROOT}/submodules/vscode-rxiv-maker/Makefile" ]] || \
           [[ -d "${REPO_ROOT}/submodules/vscode-rxiv-maker/src/rxiv_maker" ]]; then
            log_error "VSCode submodule contaminated with main rxiv-maker project files"
        fi
    fi
}

# Check for reverse contamination (submodule content in main repo)
validate_no_reverse_contamination() {
    log_info "Checking for reverse contamination..."

    # Main repo shouldn't have Homebrew Formula files outside submodules
    if find "${REPO_ROOT}" -path "*/submodules" -prune -o -name "Formula" -type d -print | grep -q .; then
        log_error "Found Formula directory outside of submodules (reverse contamination)"
    fi

    # Main repo shouldn't have Scoop bucket files outside submodules
    if find "${REPO_ROOT}" -path "*/submodules" -prune -o -name "bucket" -type d -print | grep -q . && \
       find "${REPO_ROOT}" -path "*/submodules" -prune -o -name "rxiv-maker.json" -type f -print | grep -q .; then
        log_error "Found Scoop bucket files outside of submodules (reverse contamination)"
    fi

    # Check for VSCode extension files in wrong places
    local vscode_files=("language-configuration.json" ".vscodeignore" "*.tmLanguage.json")
    for pattern in "${vscode_files[@]}"; do
        if find "${REPO_ROOT}" -path "*/submodules" -prune -o -name "$pattern" -type f -print | grep -q .; then
            log_error "Found VSCode extension file '$pattern' outside of submodules (reverse contamination)"
        fi
    done
}

# Validate submodule git configuration
validate_submodule_git_config() {
    log_info "Validating submodule git configuration..."

    for submodule_path in submodules/*/; do
        if [[ -d "${REPO_ROOT}/${submodule_path}" ]]; then
            local submodule_name=$(basename "$submodule_path")
            local git_file="${REPO_ROOT}/${submodule_path}/.git"

            if [[ -f "$git_file" ]]; then
                local gitdir=$(cat "$git_file" | sed 's/gitdir: //')
                local full_gitdir="${REPO_ROOT}/${submodule_path}/${gitdir}"

                if [[ -d "$full_gitdir" ]]; then
                    log_success "Submodule ${submodule_name} has correct git configuration"
                else
                    log_error "Submodule ${submodule_name} gitdir points to non-existent directory: ${full_gitdir}"
                fi
            else
                log_error "Submodule ${submodule_name} missing .git file"
            fi
        fi
    done
}

# Main execution
main() {
    cd "${REPO_ROOT}"

    log_info "Starting comprehensive submodule validation..."
    log_info "Repository root: ${REPO_ROOT}"

    validate_submodule_urls
    validate_content_signatures
    validate_no_reverse_contamination
    validate_submodule_git_config

    echo
    if [[ $ERRORS -eq 0 ]]; then
        log_success "✅ All submodule validations passed successfully!"
        exit 0
    else
        log_error "❌ Found ${ERRORS} validation error(s). Repository integrity may be compromised."
        log_error "Please review the errors above and fix any issues before proceeding."
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
