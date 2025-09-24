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

# Initialize in existing directory
rxiv init . --force

# Skip interactive prompts
rxiv init my-paper --no-interactive
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

# All builds use local installation
rxiv pdf
```

**Options**:
- `[manuscript_path]` - Path to manuscript directory (default: current)
- `--output-dir <path>` - Output directory (default: `output/`)
- `--force-figures` - Regenerate all figures regardless of cache
- `--skip-validation` - Skip manuscript validation (faster)
- `--track-changes <tag>` - Track changes against specified git tag
- `--verbose` - Detailed output for debugging
- `--quiet` - Minimal output
- `--debug` - Enable debug output

**Build Engine**:
- **`local`** - Uses local LaTeX installation (only supported engine)

**Examples**:
```bash
# Quick build skipping validation
rxiv pdf --skip-validation

# High-quality build with forced figures
rxiv pdf --force-figures

# Debug failing build
rxiv pdf --verbose

# Preprint submission
rxiv pdf --force-figures --output-dir submission/

# All builds use local installation
rxiv pdf
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

# Detailed validation report
rxiv validate --detailed

# Skip DOI validation
rxiv validate --no-doi
```

**Options**:
- `[manuscript_path]` - Path to manuscript (default: current)
- `--detailed` - Show detailed validation report
- `--no-doi` - Skip DOI validation

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
# Basic validation
rxiv validate

# Detailed validation report
rxiv validate --detailed

# Skip DOI validation for speed
rxiv validate --no-doi
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

# Custom zip filename
rxiv arxiv --zip-filename my-submission.zip

# Don't create zip file
rxiv arxiv --no-zip
```

**Options**:
- `[manuscript_path]` - Path to manuscript (default: current)
- `--output-dir <path>` - Output directory for generated files
- `--arxiv-dir <path>` - Custom arXiv directory path
- `--zip-filename <name>` - Custom zip filename
- `--no-zip` - Don't create zip file

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
rxiv arxiv

# Custom output directory
rxiv arxiv --output-dir submission

# Custom zip filename
rxiv arxiv --zip-filename v2-submission.zip
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
- `--output-dir <path>` - Output directory to clean
- `--figures-only` - Clean generated figures only
- `--output-only` - Clean output directory only
- `--arxiv-only` - Clean only arXiv files
- `--temp-only` - Clean only temporary files
- `--cache-only` - Clean caches only
- `--all` - Clean all generated files and caches

**Cleaned Items**:
- `output/` directory contents
- Generated figure files
- LaTeX intermediate files
- Figure generation caches
- Validation reports

**Examples**:
```bash
# Clean output directory
rxiv clean

# Complete cleanup of all files
rxiv clean --all

# Clean only generated figures
rxiv clean --figures-only

# Clean only arXiv files
rxiv clean --arxiv-only
```

---

### `rxiv track-changes` - Version Comparison

**Purpose**: Generate visual diff between manuscript versions for revision tracking.

```bash
# Track changes against a git tag
rxiv track-changes v1.0.0

# Track changes with custom output
rxiv track-changes v1.0.0 --output-dir revisions/

# Force regenerate figures
rxiv track-changes v1.0.0 --force-figures
```

**Options**:
- `<tag>` - Git tag to track changes against
- `--output-dir <dir>` - Output directory (default: `output/`)
- `--force-figures` - Force regeneration of all figures
- `--skip-validation` - Skip validation step

**Examples**:
```bash
# Journal revision tracking
rxiv track-changes submitted-v1

# Quick changes tracking without validation
rxiv track-changes v1.0 --skip-validation

# Changes with forced figure regeneration
rxiv track-changes draft --force-figures
```

---

## 🔧 Advanced Commands

### `rxiv check-installation` - System Diagnostics

**Purpose**: Verify installation and diagnose dependency issues.

```bash
# Check installation
rxiv check-installation

# Detailed diagnostics
rxiv check-installation --verbose

# Use setup to install missing dependencies
rxiv setup
```

**Checks Performed**:
- Python version and packages
- LaTeX installation and packages
- Node.js for figure generation
- System PATH configuration

---

## 🎯 Workflow Examples

### Complete Paper Workflow
```bash
# 1. Initialize project
rxiv init my-preprint-study

# 2. Write and iterate
cd my-preprint-study
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
rxiv pdf --skip-validation

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
rxiv validate --detailed

# 3. Generate track changes
rxiv track-changes submitted-v1 HEAD

# 4. Prepare resubmission  
rxiv pdf --force-figures
rxiv arxiv --zip-filename resubmission-v2.zip
```

---

## 🚨 Troubleshooting Commands

### Build Issues
```bash
# Verbose build for debugging
rxiv pdf --verbose

# Clean and retry
rxiv clean --all
rxiv pdf

# All builds use local installation
rxiv pdf
```

### Validation Problems
```bash
# Detailed validation report
rxiv validate --detailed

# Skip DOI validation for speed
rxiv validate --no-doi
```

### Figure Generation Issues
```bash
# Force regenerate all figures
rxiv clean --figures-only
rxiv pdf --force-figures

# Test figure scripts individually
python FIGURES/statistical_analysis_plot.py
```

---

## 📚 Environment Variables

### Engine Selection
```bash
# RXIV_ENGINE is no longer configurable - always uses local installation
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
rxiv validate --detailed

# Generate artifacts
rxiv pdf --force-figures
rxiv arxiv
```

### Development Workflow
```bash
# Quick iteration during development
rxiv pdf --skip-validation
# Edit files and re-run for quick feedback
```

**🎓 [Back to First Manuscript](../quick-start/first-manuscript.md) | 📚 [User Guide](../guides/user_guide.md) | 🔧 [Troubleshooting](../troubleshooting/troubleshooting.md)**