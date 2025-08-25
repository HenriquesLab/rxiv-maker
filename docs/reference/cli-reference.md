# ⚙️ CLI Reference - Complete Command Guide

*Comprehensive reference for all Rxiv-Maker commands, options, and workflows*

---

## 🎯 Quick Command Overview

| Command | Purpose | Time | Common Use |
|---------|---------|------|------------|
| `rxiv init` | Create new manuscript project | 10s | Starting new paper |
| `rxiv pdf` | Generate PDF from manuscript | 30s-2min | Main workflow |
| `rxiv validate` | Check manuscript for errors | 15s | Before submission |
| `rxiv arxiv` | Prepare arXiv submission package | 1min | arXiv uploads |
| `rxiv clean` | Remove generated files | 5s | Fresh start |
| `rxiv track-changes` | Compare manuscript versions | 30s | Revision tracking |

**💡 Pro Tip**: Use `rxiv <command> --help` for detailed help on any command.

---

## 📖 Core Commands

### `rxiv init` - Create New Manuscript

**Purpose**: Initialize a new manuscript project with template structure.

```bash
# Basic usage
rxiv init my-paper

# Initialize with custom template
rxiv init my-paper --template journal-article

# Initialize in existing directory
rxiv init . --force
```

**Options**:
- `<name>` - Project name (creates directory)
- `--force` - Initialize in non-empty directory
- `--no-interactive` - Skip interactive prompts and use defaults

**Generated Files**:
```
my-paper/
├── 00_CONFIG.yml      # Manuscript metadata
├── 01_MAIN.md          # Main manuscript content
├── 03_REFERENCES.bib   # Bibliography file
├── FIGURES/            # Figure generation scripts
└── .gitignore          # Git ignore patterns
```

**Examples**:
```bash
# Research preprint
rxiv init my-research-preprint

# Biomedical preprint
rxiv init covid-analysis

# Computer science preprint
rxiv init ml-algorithm-study
```

---

### `rxiv pdf` - Generate Publication PDF

**Purpose**: Convert Markdown manuscript to professional PDF with LaTeX typesetting.

```bash
# Basic PDF generation
rxiv pdf

# PDF with validation
rxiv pdf --validate

# Force regenerate all figures
rxiv pdf --force-figures

# Use specific engine
rxiv pdf --engine docker
RXIV_ENGINE=DOCKER rxiv pdf
```

**Options**:
- `[manuscript_path]` - Path to manuscript directory (default: current)
- `--output-dir <path>` - Output directory (default: `output/`)
- `--engine <type>` - Build engine (`local`, `docker`, `podman`)
- `--force-figures` - Regenerate all figures regardless of cache
- `--skip-validation` - Skip manuscript validation (faster)
- `--validate` - Run comprehensive validation before build
- `--verbose` - Detailed output for debugging
- `--quiet` - Minimal output
- `--journal-format` - Apply journal-specific formatting
- `--draft` - Generate draft version with watermarks

**Build Engines**:
- **`local`** - Use local LaTeX installation (fastest)
- **`docker`** - Use Docker container (consistent, no local deps)
- **`podman`** - Use Podman container (Docker alternative)

**Examples**:
```bash
# Quick draft for review
rxiv pdf --draft --skip-validation

# High-quality final version
rxiv pdf --validate --force-figures

# Debug failing build
rxiv pdf --verbose --engine local

# Journal submission
rxiv pdf --journal-format --output-dir submission/

# Team consistency
RXIV_ENGINE=DOCKER rxiv pdf
```

**Output Files**:
- `manuscript.pdf` - Main publication PDF
- `manuscript.tex` - Generated LaTeX source
- `Figures/` - Generated figure files
- `output/logs/` - Build logs and diagnostics

---

### `rxiv validate` - Manuscript Quality Check

**Purpose**: Comprehensive validation of manuscript structure, content, and dependencies.

```bash
# Full validation
rxiv validate

# Quick syntax check
rxiv validate --syntax-only

# Detailed report
rxiv validate --detailed

# Specific checks
rxiv validate --citations-only
rxiv validate --figures-only
```

**Options**:
- `[manuscript_path]` - Path to manuscript (default: current)
- `--detailed` - Extended validation report with suggestions
- `--syntax-only` - Check Markdown syntax only
- `--citations-only` - Validate citations and bibliography
- `--figures-only` - Check figure references and files
- `--strict` - Fail on warnings (not just errors)
- `--fix` - Auto-fix issues where possible
- `--output <format>` - Report format (`text`, `json`, `html`)

**Validation Checks**:
- ✅ **Syntax**: Markdown structure and formatting
- ✅ **Citations**: BibTeX entries and references
- ✅ **Figures**: File existence and script validity
- ✅ **Cross-references**: Internal links and numbering
- ✅ **Math**: LaTeX math syntax validation
- ✅ **Dependencies**: Required packages and tools
- ✅ **Config**: YAML metadata completeness

**Examples**:
```bash
# Pre-submission check
rxiv validate --strict --detailed

# Fix common issues automatically
rxiv validate --fix

# Generate HTML report
rxiv validate --output html --detailed

# CI/CD pipeline usage
rxiv validate --output json > validation_report.json
```

**Exit Codes**:
- `0` - No issues found
- `1` - Warnings found (proceed with caution)
- `2` - Errors found (must fix before PDF generation)

---

### `rxiv arxiv` - arXiv Submission Package

**Purpose**: Generate arXiv-ready submission package with all required files.

```bash
# Create arXiv package
rxiv arxiv

# Include source files
rxiv arxiv --include-source

# Custom package name
rxiv arxiv --output my-submission.zip
```

**Options**:
- `[manuscript_path]` - Path to manuscript (default: current)
- `--output <filename>` - Output package name (default: `for_arxiv.zip`)
- `--include-source` - Include Markdown source files
- `--include-figures` - Include figure generation scripts
- `--format <type>` - Package format (`zip`, `tar.gz`)
- `--validate` - Validate before packaging

**Package Contents**:
```
for_arxiv.zip
├── manuscript.tex      # LaTeX source
├── manuscript.bbl      # Bibliography
├── Figures/           # All generated figures
├── style/            # LaTeX style files
└── README.txt        # Submission instructions
```

**Examples**:
```bash
# Standard arXiv submission
rxiv arxiv --validate

# Full reproducible package
rxiv arxiv --include-source --include-figures --output reproducible-submission.zip

# Quick resubmission
rxiv arxiv --output v2-submission.zip
```

---

### `rxiv clean` - Cleanup Generated Files

**Purpose**: Remove generated files and caches for fresh start.

```bash
# Clean output directory
rxiv clean

# Clean everything including caches
rxiv clean --all

# Clean specific components
rxiv clean --figures-only
```

**Options**:
- `[manuscript_path]` - Path to manuscript (default: current)
- `--all` - Remove all generated files and caches
- `--figures-only` - Clean generated figures only
- `--output-only` - Clean output directory only
- `--cache-only` - Clean caches only
- `--dry-run` - Show what would be cleaned
- `--force` - Skip confirmation prompts

**Cleaned Items**:
- `output/` directory contents
- Generated figure files
- LaTeX intermediate files
- Figure generation caches
- Validation reports

**Examples**:
```bash
# Safe cleanup (asks confirmation)
rxiv clean

# Complete reset
rxiv clean --all --force

# Preview cleanup
rxiv clean --all --dry-run

# Clean just broken figures
rxiv clean --figures-only
```

---

### `rxiv track-changes` - Version Comparison

**Purpose**: Generate visual diff between manuscript versions for revision tracking.

```bash
# Compare two versions
rxiv track-changes v1.0.0 v2.0.0

# Compare with current state
rxiv track-changes v1.0.0 HEAD

# Custom output location
rxiv track-changes v1.0.0 v2.0.0 --output revisions/
```

**Options**:
- `<old_version>` - Git tag/commit of old version
- `<new_version>` - Git tag/commit of new version
- `--output <dir>` - Output directory (default: `output/track_changes/`)
- `--format <type>` - Diff format (`pdf`, `html`, `text`)
- `--highlight-style <style>` - Diff highlighting style
- `--no-figures` - Skip figure comparison
- `--words-only` - Word-level diff (more precise)

**Output**:
- `changes.pdf` - Visual diff with highlights
- `old_version.pdf` - Original version
- `new_version.pdf` - New version
- `summary.txt` - Change statistics

**Examples**:
```bash
# Journal revision tracking
rxiv track-changes submitted-v1 revision-v1 --format pdf

# Detailed word-level changes
rxiv track-changes v1.0 v1.1 --words-only

# HTML diff for web review
rxiv track-changes draft final --format html --output web-diff/
```

---

## 🔧 Advanced Commands

### `rxiv check-installation` - System Diagnostics

**Purpose**: Verify installation and diagnose dependency issues.

```bash
# Check installation
rxiv check-installation

# Auto-fix issues
rxiv check-installation --fix

# Detailed diagnostics
rxiv check-installation --verbose
```

**Checks Performed**:
- Python version and packages
- LaTeX installation and packages
- Docker/Podman availability
- Node.js for figure generation
- System PATH configuration

---

### `rxiv config` - Configuration Management

**Purpose**: Manage global and project-specific settings.

```bash
# Show current config
rxiv config show

# Set global default
rxiv config set author "Dr. Jane Smith"
rxiv config set engine docker

# Project-specific config
rxiv config set --local citation-style nature
```

**Common Settings**:
- `author` - Default author name
- `engine` - Default build engine
- `citation-style` - Default citation format
- `figure-dpi` - Default figure resolution
- `latex-engine` - LaTeX compiler choice

---

### `rxiv serve` - Development Server

**Purpose**: Live preview server for manuscript development.

```bash
# Start development server
rxiv serve

# Custom port and host
rxiv serve --port 8080 --host 0.0.0.0

# Auto-reload on changes
rxiv serve --watch
```

**Features**:
- Live PDF preview in browser
- Auto-reload on file changes
- Figure regeneration on script changes
- Validation warnings in browser

---

## 🎯 Workflow Examples

### Complete Paper Workflow
```bash
# 1. Initialize project
rxiv init nature-submission --template journal-article

# 2. Write and iterate
cd nature-submission
# ... edit 01_MAIN.md and add figures ...

# 3. Validate and generate
rxiv validate --detailed
rxiv pdf --force-figures

# 4. Prepare submission
rxiv arxiv --include-source
```

### Collaboration Workflow  
```bash
# 1. Clone and setup
git clone https://github.com/team/paper-repo.git
cd paper-repo
rxiv check-installation --fix

# 2. Work on revisions
git checkout -b my-revisions
# ... make changes ...
rxiv pdf --draft

# 3. Track changes
rxiv track-changes main HEAD --output my-changes/

# 4. Share results
git add . && git commit -m "Updated methodology section"
git push origin my-revisions
```

### Revision and Resubmission
```bash
# 1. Create revision branch
git checkout -b revision-v2
git tag submitted-v1  # Mark original submission

# 2. Make revisions based on reviews
# ... edit manuscript ...
rxiv validate --strict

# 3. Generate track changes
rxiv track-changes submitted-v1 HEAD

# 4. Prepare resubmission
rxiv pdf --journal-format
rxiv arxiv --output resubmission-v2.zip
```

---

## 🚨 Troubleshooting Commands

### Build Issues
```bash
# Verbose build for debugging
rxiv pdf --verbose --engine local

# Clean and retry
rxiv clean --all
rxiv pdf

# Try different engine
RXIV_ENGINE=DOCKER rxiv pdf
```

### Validation Problems
```bash
# Detailed validation report
rxiv validate --detailed --output html

# Fix what's possible automatically
rxiv validate --fix

# Check specific issues
rxiv validate --citations-only --verbose
```

### Figure Generation Issues
```bash
# Force regenerate all figures
rxiv clean --figures-only
rxiv pdf --force-figures

# Test figure scripts individually
python FIGURES/my_plot.py
```

---

## 📚 Environment Variables

### Engine Selection
```bash
export RXIV_ENGINE=docker    # Use Docker by default
export RXIV_ENGINE=local     # Use local tools by default
export RXIV_ENGINE=podman    # Use Podman by default
```

### Build Customization
```bash
export RXIV_LATEX_ENGINE=xelatex     # LaTeX engine choice
export RXIV_FIGURE_DPI=300           # Figure resolution
export RXIV_PARALLEL_FIGURES=4       # Parallel figure generation
```

### Debug Settings
```bash
export RXIV_DEBUG=1           # Enable debug output
export RXIV_VERBOSE=1         # Verbose output by default
export RXIV_LOG_LEVEL=DEBUG   # Detailed logging
```

---

## 🔍 Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue workflow |
| 1 | Warning | Review output, may proceed |
| 2 | Error | Must fix issues before continuing |
| 3 | System Error | Check installation/permissions |
| 4 | User Error | Check command syntax/arguments |

---

## 💡 Pro Tips

### Performance Optimization
```bash
# Skip validation for quick iterations
rxiv pdf --skip-validation

# Use figure caching
# Figures are cached by default - only regenerated when scripts change

# Parallel processing
export RXIV_PARALLEL_FIGURES=8  # Use 8 cores for figure generation
```

### CI/CD Integration
```bash
# Automated validation in CI
rxiv validate --output json --strict

# Generate artifacts
rxiv pdf --validate
rxiv arxiv --include-source
```

### Development Workflow
```bash
# Live preview during writing
rxiv serve --watch &
# Edit in your favorite editor, see live changes in browser
```

**🎓 [Back to First Manuscript](../quick-start/first-manuscript.md) | 📚 [User Guide](../guides/user_guide.md) | 🔧 [Troubleshooting](../troubleshooting/troubleshooting.md)**