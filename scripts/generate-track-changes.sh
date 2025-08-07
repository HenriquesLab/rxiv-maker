#!/bin/bash
set -euo pipefail

# Track Changes PDF Generator for Release Process
# Generates a PDF showing changes between current version and last major version
# Usage: ./generate-track-changes.sh [MANUSCRIPT_PATH] [OUTPUT_DIR]
#
# Output Directory Structure:
# - Temporary work files: ${OUTPUT_DIR}/track_changes_temp/ (cleaned up after completion)
# - Final track changes PDF: ${OUTPUT_DIR}/YYYY__authors__changes_vs_X.Y.Z.pdf
# - Does NOT create directories under MANUSCRIPT_PATH/ (use MANUSCRIPT_PATH/output/ instead)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
MANUSCRIPT_PATH="${1:-EXAMPLE_MANUSCRIPT}"
OUTPUT_DIR="${2:-output}"
WORK_DIR="${OUTPUT_DIR}/track_changes_temp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️ ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ ${1}${NC}"
}

log_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

# Function to detect last major version
detect_last_major_version() {
    log_info "Detecting last major version..." >&2

    # Get current tag if we're on a tag, otherwise use latest
    CURRENT_TAG=$(git describe --exact-match --tags HEAD 2>/dev/null || git tag --sort=-version:refname | head -1)
    log_info "Current version: ${CURRENT_TAG}" >&2

    # Extract major versions (x.y.0 pattern)
    MAJOR_VERSIONS=$(git tag --list | grep -E "^v[0-9]+\.[0-9]+\.0$" | sort -V)

    if [[ -z "$MAJOR_VERSIONS" ]]; then
        log_error "No major versions (x.y.0) found in git tags" >&2
        return 1
    fi

    # Get current major version
    CURRENT_MAJOR=$(echo "$CURRENT_TAG" | sed -E 's/^v([0-9]+\.[0-9]+)\..*/v\1.0/')

    # Find the previous major version
    LAST_MAJOR=$(echo "$MAJOR_VERSIONS" | grep -v "$CURRENT_MAJOR" | tail -1)

    if [[ -z "$LAST_MAJOR" ]]; then
        log_warning "No previous major version found. Using first available version." >&2
        LAST_MAJOR=$(echo "$MAJOR_VERSIONS" | head -1)
    fi

    log_success "Last major version: ${LAST_MAJOR}" >&2
    echo "$LAST_MAJOR"
}

# Function to extract files from git tag
extract_files_from_tag() {
    local tag="$1"
    local target_dir="$2"

    log_info "Extracting files from tag: ${tag}" >&2
    mkdir -p "$target_dir"

    # Extract manuscript files
    for file in "01_MAIN.md" "00_CONFIG.yml" "03_REFERENCES.bib" "02_SUPPLEMENTARY_INFO.md"; do
        if git show "${tag}:${MANUSCRIPT_PATH}/${file}" > "${target_dir}/${file}" 2>/dev/null; then
            log_success "Extracted: ${file}" >&2
        else
            log_warning "File not found in ${tag}: ${file}" >&2
        fi
    done

    # Copy FIGURES directory structure (use current version for figures)
    if [[ -d "${PROJECT_ROOT}/${MANUSCRIPT_PATH}/FIGURES" ]]; then
        cp -r "${PROJECT_ROOT}/${MANUSCRIPT_PATH}/FIGURES" "${target_dir}/"
        log_success "Copied FIGURES directory" >&2
    else
        log_warning "FIGURES directory not found at ${PROJECT_ROOT}/${MANUSCRIPT_PATH}/FIGURES" >&2
    fi
}

# Function to generate LaTeX files using rxiv-maker
generate_latex_files() {
    local manuscript_dir="$1"
    local output_subdir="$2"
    local base_name="$3"

    log_info "Generating LaTeX files for: ${manuscript_dir}" >&2

    local original_cwd
    original_cwd=$(pwd)

    # Use absolute paths throughout to avoid nesting issues
    local abs_manuscript_dir
    local abs_output_subdir

    # Ensure we have absolute paths
    if [[ "$manuscript_dir" = /* ]]; then
        abs_manuscript_dir="$manuscript_dir"
    else
        abs_manuscript_dir="${PROJECT_ROOT}/${manuscript_dir}"
    fi

    if [[ "$output_subdir" = /* ]]; then
        abs_output_subdir="$output_subdir"
    else
        abs_output_subdir="${PROJECT_ROOT}/${output_subdir}"
    fi

    mkdir -p "$abs_output_subdir"

    # Change to the manuscript directory to avoid path resolution issues
    cd "$(dirname "$abs_manuscript_dir")"
    local manuscript_basename
    manuscript_basename="$(basename "$abs_manuscript_dir")"

    export MANUSCRIPT_PATH="$manuscript_basename"
    export PYTHONPATH="${PROJECT_ROOT}/src"

    # Generate PDF to get LaTeX files (skip validation to speed up)
    log_info "Running: MANUSCRIPT_PATH=${manuscript_basename} python -m rxiv_maker.cli pdf ${manuscript_basename} -o ${abs_output_subdir} -s" >&2

    # Run the command and capture result, but don't fail immediately
    MANUSCRIPT_PATH="$manuscript_basename" python -m rxiv_maker.cli pdf "$manuscript_basename" -o "$abs_output_subdir" -s
    rxiv_exit_code=$?

    if [[ $rxiv_exit_code -ne 0 ]]; then
        log_warning "rxiv command returned error code $rxiv_exit_code, but checking for LaTeX files anyway..." >&2
    fi

    # Check if LaTeX file was generated - look for the manuscript name or base_name
    local tex_file="${abs_output_subdir}/${manuscript_basename}.tex"
    local alt_tex_file="${abs_output_subdir}/${base_name}.tex"

    if [[ -f "$tex_file" ]]; then
        # Rename to expected name if using manuscript name
        if [[ "$tex_file" != "$alt_tex_file" ]]; then
            mv "$tex_file" "$alt_tex_file" 2>/dev/null || cp "$tex_file" "$alt_tex_file"
            log_info "Renamed ${tex_file} to ${alt_tex_file}" >&2
        fi
    elif [[ ! -f "$alt_tex_file" ]]; then
        log_error "Expected LaTeX file not found: ${alt_tex_file} or ${tex_file}" >&2
        log_info "Files in output directory:" >&2
        ls -la "${abs_output_subdir}" >&2 || echo "Output directory does not exist" >&2
        log_info "Searching for .tex files in output directory tree:" >&2
        find "${abs_output_subdir}" -name "*.tex" -type f 2>/dev/null | sed 's/^/  /' >&2 || echo "No .tex files found" >&2
        cd "$original_cwd"
        return 1
    fi

    log_success "Generated LaTeX files in: ${abs_output_subdir}" >&2
    cd "$original_cwd"
}

# Function to generate track changes PDF
generate_track_changes_pdf() {
    local last_major="$1"
    local manuscript_path="$2"
    local output_dir="$3"

    log_info "Generating track changes PDF against: ${last_major}" >&2
    log_info "Parameters: last_major=${last_major}, manuscript_path=${manuscript_path}, output_dir=${output_dir}" >&2

    # Create output directory and clean up any previous work directory
    mkdir -p "$OUTPUT_DIR"
    rm -rf "$WORK_DIR"
    mkdir -p "${WORK_DIR}/old" "${WORK_DIR}/new"

    # Extract files from last major version
    log_info "About to extract files from ${last_major}..." >&2
    local old_manuscript_dir="${WORK_DIR}/old/${manuscript_path}"
    mkdir -p "$old_manuscript_dir"
    if ! extract_files_from_tag "$last_major" "$old_manuscript_dir"; then
        log_error "Failed to extract files from ${last_major}" >&2
        return 1
    fi

    # Copy current files
    local new_manuscript_dir="${WORK_DIR}/new/${manuscript_path}"
    mkdir -p "$new_manuscript_dir"
    cp -r "${PROJECT_ROOT}/${manuscript_path}"/* "$new_manuscript_dir/"

    # Generate LaTeX files for both versions
    log_info "Generating LaTeX files for old version (${last_major})" >&2
    if ! generate_latex_files "$old_manuscript_dir" "${WORK_DIR}/old_output" "old"; then
        log_error "Failed to generate LaTeX for old version" >&2
        return 1
    fi

    log_info "Generating LaTeX files for new version (current)" >&2
    if ! generate_latex_files "$new_manuscript_dir" "${WORK_DIR}/new_output" "new"; then
        log_error "Failed to generate LaTeX for new version" >&2
        return 1
    fi

    # Check if latexdiff is available
    if ! command -v latexdiff >/dev/null 2>&1; then
        log_error "latexdiff is not installed. Please install TeX Live with latexdiff."
        return 1
    fi

    # Generate diff LaTeX file
    log_info "Running latexdiff to generate track changes..." >&2
    if ! latexdiff "${WORK_DIR}/old_output/old.tex" "${WORK_DIR}/new_output/new.tex" > "${WORK_DIR}/diff.tex"; then
        log_error "latexdiff failed" >&2
        return 1
    fi

    # Set up compilation directory
    local compile_dir="${WORK_DIR}/compile"
    mkdir -p "$compile_dir"

    # Copy necessary files for compilation
    cp "${WORK_DIR}/diff.tex" "$compile_dir/"
    cp -r "${WORK_DIR}/new_output/Figures" "$compile_dir/" 2>/dev/null || true
    cp "${WORK_DIR}/new_output"/*.bib "$compile_dir/" 2>/dev/null || true
    cp "${WORK_DIR}/new_output"/*.cls "$compile_dir/" 2>/dev/null || true
    cp "${WORK_DIR}/new_output"/*.bst "$compile_dir/" 2>/dev/null || true
    cp "${WORK_DIR}/new_output"/*.sty "$compile_dir/" 2>/dev/null || true
    cp "${WORK_DIR}/new_output/Supplementary.tex" "$compile_dir/" 2>/dev/null || true

    # Copy style files from the source package if not already copied
    if [[ ! -f "$compile_dir/rxiv_maker_style.cls" ]]; then
        log_info "Copying style files from source package..." >&2
        local style_source="${PROJECT_ROOT}/src/tex/style"
        if [[ -d "$style_source" ]]; then
            cp "$style_source"/*.cls "$compile_dir/" 2>/dev/null || true
            cp "$style_source"/*.bst "$compile_dir/" 2>/dev/null || true
            cp "$style_source"/*.sty "$compile_dir/" 2>/dev/null || true
            log_success "Copied style files from source" >&2
        else
            log_warning "Style source directory not found at ${style_source}" >&2
        fi
    fi

    # Compile the diff PDF
    log_info "Compiling track changes PDF..."
    cd "$compile_dir"

    # Run LaTeX compilation sequence
    if ! pdflatex -interaction=nonstopmode diff.tex >/dev/null 2>&1; then
        log_warning "First pdflatex pass had warnings, continuing..."
    fi

    if ! bibtex diff >/dev/null 2>&1; then
        log_warning "BibTeX had warnings, continuing..."
    fi

    if ! pdflatex -interaction=nonstopmode diff.tex >/dev/null 2>&1; then
        log_warning "Second pdflatex pass had warnings, continuing..."
    fi

    if ! pdflatex -interaction=nonstopmode diff.tex >/dev/null 2>&1; then
        log_warning "Final pdflatex pass had warnings, continuing..."
    fi

    # Check if PDF was generated
    if [[ ! -f "diff.pdf" ]]; then
        log_error "Track changes PDF was not generated"
        cd "$PROJECT_ROOT"
        return 1
    fi

    # Generate custom filename
    local custom_filename
    custom_filename=$(generate_custom_filename "$last_major")

    # Copy to output directory
    mkdir -p "${PROJECT_ROOT}/${output_dir}"
    cp "diff.pdf" "${PROJECT_ROOT}/${output_dir}/${custom_filename}"

    cd "$PROJECT_ROOT"

    log_success "Track changes PDF generated: ${output_dir}/${custom_filename}"
    echo "${custom_filename}"
}

# Function to generate custom filename
generate_custom_filename() {
    local last_major="$1"

    # Extract year from config file or use current year
    local year
    local config_file="${PROJECT_ROOT}/${MANUSCRIPT_PATH}/00_CONFIG.yml"

    if [[ -f "$config_file" ]] && command -v python3 >/dev/null 2>&1; then
        year=$(python3 -c "
import yaml
try:
    with open('${config_file}', 'r') as f:
        data = yaml.safe_load(f) or {}
    date = data.get('date', '')
    if isinstance(date, str) and len(date) >= 4:
        print(date[:4])
    else:
        import datetime
        print(datetime.datetime.now().year)
except:
    import datetime
    print(datetime.datetime.now().year)
" 2>/dev/null)
    else
        year=$(date +%Y)
    fi

    # Generate filename following convention
    local version_clean
    version_clean=$(echo "$last_major" | sed 's/^v//')
    echo "${year}__saraiva_et_al__changes_vs_${version_clean}.pdf"
}

# Main function
main() {
    log_info "Starting track changes PDF generation..."
    log_info "Manuscript path: ${MANUSCRIPT_PATH}"
    log_info "Output directory: ${OUTPUT_DIR}"

    # Change to project root
    cd "$PROJECT_ROOT"

    # Check if manuscript directory exists
    if [[ ! -d "${MANUSCRIPT_PATH}" ]]; then
        log_error "Manuscript directory not found: ${MANUSCRIPT_PATH}"
        exit 1
    fi

    # Detect last major version
    local last_major
    log_info "About to detect last major version..."
    if ! last_major=$(detect_last_major_version); then
        log_error "Failed to detect last major version"
        exit 1
    fi
    log_success "Detected last major version: ${last_major}"

    # Generate track changes PDF
    local output_filename
    log_info "About to call generate_track_changes_pdf..."
    if ! output_filename=$(generate_track_changes_pdf "$last_major" "$MANUSCRIPT_PATH" "$OUTPUT_DIR"); then
        log_error "Failed to generate track changes PDF"
        exit 1
    fi

    # Clean up work directory
    rm -rf "$WORK_DIR"

    log_success "Track changes PDF generation completed!"
    log_success "Output file: ${OUTPUT_DIR}/${output_filename}"
    log_success "Shows changes from ${last_major} to current version"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
