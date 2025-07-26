# Rxiv-Maker User Guide

This guide covers everything from getting started to advanced workflows, practical examples, and troubleshooting.

## Table of Contents
- [Getting Started](#getting-started)
- [Manuscript Validation](#manuscript-validation)
- [Advanced Usage](#advanced-usage)
- [Examples & Cookbook](#examples--cookbook)
- [Troubleshooting & Debugging](#troubleshooting--debugging)
- [Where to Get Help](#where-to-get-help)

---

## Getting Started

### 🎯 **Choose Your Development Environment (Pick ONE)**

<details>
<summary><strong>🏠 Local Installation (Recommended for All Users)</strong></summary>

**Full control with native performance - works on all architectures**

**Why Local Installation?**
- ✅ **Universal compatibility**: Works on AMD64, ARM64 (Apple Silicon), and all platforms
- ✅ **Better performance**: Native execution, faster builds
- ✅ **Full feature support**: All Mermaid diagrams, R/Python figures work reliably
- ✅ **Easier debugging**: Direct access to logs and intermediate files
- ✅ **Incremental development**: Faster iteration when developing manuscripts

**Prerequisites:** 
- Python 3.11+ (check with `python --version`)
- LaTeX distribution (TeX Live, MacTeX, or MiKTeX) - or use Docker mode
- Make (typically pre-installed on macOS/Linux, see [platform guide](../platforms/LOCAL_DEVELOPMENT.md) for Windows)

**Quick Start with Modern CLI:**
```bash
# Install from PyPI
pip install rxiv-maker

# Initialize new manuscript
rxiv init MY_PAPER/

# Build PDF
rxiv pdf MY_PAPER/
```

**Development Setup:**
```bash
# Clone and set up local environment
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Install in development mode
pip install -e .

# Or use traditional setup
make setup

# Generate your first PDF
rxiv pdf  # Modern CLI
# OR
make pdf  # Legacy command
```

</details>

<details>
<summary><strong>🐳 Docker Engine Mode (AMD64 only)</strong></summary>

**Only Docker + Make required - no LaTeX, Python, or R installation needed**

**⚠️ Technical Note:** Docker mode uses AMD64 base images due to Google Chrome ARM64 Linux limitations. Apple Silicon Macs can run these via Rosetta emulation, though local installation provides better performance.

**Why Docker Mode?**
- ✅ **Minimal dependencies**: Only Docker and Make needed locally
- ✅ **Reproducible builds**: Exact same environment every time
- ✅ **CI/CD ready**: Perfect for GitHub Actions on AMD64 runners
- ❌ **AMD64 only**: Google Chrome dependency limits architecture support

**Prerequisites:** 
- AMD64/x86_64 system (Intel/AMD processors only)
- Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- Install Make (typically pre-installed on macOS/Linux, see [platform guide](../platforms/LOCAL_DEVELOPMENT.md) for Windows)

```bash
# Clone and use immediately with Docker
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Modern CLI with Docker
rxiv pdf --engine docker           # Generate PDF in container
rxiv validate --engine docker      # Validate in container

# Or legacy commands
make pdf RXIV_ENGINE=DOCKER        # Generate PDF in container
make validate RXIV_ENGINE=DOCKER   # Validate in container
```

**Benefits**: Cross-platform consistency, no dependency conflicts, matches CI environment (AMD64 only)

</details>

<details>
<summary><strong>☁️ Cloud-Based Options</strong></summary>

**No local installation required**

- **🌐 Google Colab**: [Tutorial](../tutorials/google_colab.md) - Browser-based, perfect for trying Rxiv-Maker
- **⚡ GitHub Actions**: [Setup Guide](../workflows/github-actions.md) - Automated builds on every commit

</details>

---

## Manuscript Validation

Rxiv-Maker includes a comprehensive validation system that checks your manuscript for errors before PDF generation. This helps catch issues early and provides actionable feedback.

### Quick Validation
```bash
# Basic validation check
make validate

# Validate specific manuscript
make validate MANUSCRIPT_PATH=MY_PAPER

# Recommended workflow: validate then build
rxiv validate && rxiv pdf

# Or with legacy commands
make validate && make pdf
```

### Detailed Validation
```bash
# Get comprehensive feedback with suggestions
rxiv validate --detailed

# Advanced validation with specific manuscript
rxiv validate MY_PAPER/ --verbose
```

### What Gets Validated

**Content & Structure:**
- Required files (`00_CONFIG.yml`, `01_MAIN.md`, `03_REFERENCES.bib`)
- YAML configuration syntax and required fields
- File readability and basic format checks

**Citations & References:**
- Citation syntax (`@citation`, `[@cite1;@cite2]`)
- Cross-references (`@fig:label`, `@tbl:label`, `@eq:label`)
- Bibliography entries against citations
- Undefined references and unused definitions

**Figures & Math:**
- Figure file existence and accessibility
- Mathematical expression syntax (`$...$`, `$$...$$`)
- LaTeX command validity
- Figure generation script errors

**Build Issues:**
- LaTeX compilation error analysis
- Common error pattern recognition
- User-friendly error explanations

### Understanding Validation Output

**Error Levels:**
- 🔴 **ERROR**: Critical issues preventing PDF generation
- 🟡 **WARNING**: Potential problems or quality issues  
- 🔵 **INFO**: Statistics and informational messages

**Example Output:**
```
ERROR: Citation 'smith2023' not found in bibliography
  File: 01_MAIN.md:42
  Context: > See @smith2023 for details
  Suggestion: Add reference to 03_REFERENCES.bib or check spelling

WARNING: Figure file FIGURES/plot.png not found
  Suggestion: Create the figure or update the path
```

### Integration with Build Process

Validation runs automatically before PDF generation:
```bash
rxiv pdf  # Includes validation step

# Or skip validation (for debugging)
rxiv pdf --skip-validation
```

For more detailed validation information, see [Manuscript Validation Guide](validate_manuscript.md).

---

## Advanced Usage

- **Custom Manuscript Paths:**
  ```bash
  # Modern CLI
  rxiv pdf MY_ARTICLE/
  
  # Legacy command
  MANUSCRIPT_PATH=MY_ARTICLE make pdf
  ```
- **Docker Engine Mode (Only Docker Required):**
  Run any command in a containerized environment without installing LaTeX, R, or Python locally (Docker must be installed):
  ```bash
  # Modern CLI with Docker
  rxiv pdf --engine docker
  rxiv validate --engine docker
  
  # Legacy commands with RXIV_ENGINE=DOCKER
  make pdf RXIV_ENGINE=DOCKER
  make validate RXIV_ENGINE=DOCKER
  
  # Use custom Docker image
  DOCKER_IMAGE=my/custom:tag RXIV_ENGINE=DOCKER make pdf
  
  # Make Docker mode default for session
  export RXIV_ENGINE=DOCKER
  make pdf  # Now runs in Docker automatically
  ```
  Benefits: Cross-platform consistency, no dependency conflicts, reproducible builds, faster CI/CD.
- **Advanced Figure Generation:**
  - Place Python or Mermaid files in `MANUSCRIPT/FIGURES/`
  - Force regeneration:
    ```bash
    # Modern CLI
    rxiv pdf --force-figures
    
    # Legacy command
    make pdf FORCE_FIGURES=true
    ```
- **Custom LaTeX Templates:**
  - Add `.sty`, `.cls`, or `.tex` files to `src/tex/style/`
  - Reference your custom style in `00_CONFIG.yml`
- **Continuous Integration (CI):**
  - GitHub Actions builds PDFs via manual trigger or git tags
  - Accelerated with pre-compiled Docker images (~2 min vs. ~10 min builds)
  - See [GitHub Actions Guide](../workflows/github-actions.md) for step-by-step instructions
  - Customize workflows in `.github/workflows/`
- **Environment Variables:**
  - Use a `.env` file for persistent settings
- **Debugging and Verbose Output:**
  - Use `VERBOSE=true` for detailed logs:
    ```bash
    make pdf VERBOSE=true
    ```
- **Pre-commit Hooks and Linting:**
  - Install hooks: `pre-commit install`
  - Run all checks: `pre-commit run --all-files`

---

## Examples & Cookbook

### Local Development Examples
- **Basic PDF Generation:**
  ```bash
  make validate  # Check for issues first
  make pdf       # Generate PDF
  ```
- **Custom Manuscript Directory:**
  ```bash
  MANUSCRIPT_PATH=MY_PAPER make pdf
  ```

### Docker Engine Mode Examples
- **Basic PDF Generation (No Dependencies):**
  ```bash
  # Modern CLI
  rxiv validate --engine docker  # Check for issues first
  rxiv pdf --engine docker       # Generate PDF in container
  
  # Legacy commands
  make validate RXIV_ENGINE=DOCKER  # Check for issues first
  make pdf RXIV_ENGINE=DOCKER       # Generate PDF in container
  ```
- **Custom Manuscript with Docker:**
  ```bash
  # Modern CLI
  rxiv pdf MY_PAPER/ --engine docker
  
  # Legacy command
  MANUSCRIPT_PATH=MY_PAPER RXIV_ENGINE=DOCKER make pdf
  ```
- **Set Docker as Default:**
  ```bash
  export RXIV_ENGINE=DOCKER
  rxiv validate && rxiv pdf  # Both run in containers
  # OR
  make validate && make pdf  # Both run in containers
  ```
- **Adding Figures:**
  - Place `.py` or `.mmd` files in `MANUSCRIPT/FIGURES/`
  - Reference in Markdown:
    ```markdown
    ![My Plot](FIGURES/my_plot.py){#fig:plot}
    See @fig:plot for details.
    ```
- **Customizing Templates:**
  - Add `.sty` or `.cls` files to `src/tex/style/`
  - Reference in `00_CONFIG.yml`
- **Using Mermaid Diagrams:**
  - Place `.mmd` files in `FIGURES/`
  - Example:
    ```mermaid
    graph TD;
      A-->B;
      B-->C;
    ```
- **Citations and Bibliography:**
  - Add references to `03_REFERENCES.bib`
  - Use `[@cite1;@cite2]` in Markdown
- **CI/CD Automation:**
  - GitHub Actions builds PDFs on manual trigger or tags
  - See [GitHub Actions Guide](../workflows/github-actions.md) for complete instructions

---

## Troubleshooting & Debugging

- **Validation Errors:**
  - Error: Various validation failures
  - Solution: Run `rxiv validate` to see specific issues and suggestions
  - Debug: Use `rxiv validate --detailed` for comprehensive feedback
- **LaTeX Not Found:**
  - Error: `LaTeX Error: File not found`
  - Solution: Install LaTeX (see [platforms/LOCAL_DEVELOPMENT.md](platforms/LOCAL_DEVELOPMENT.md))
  - Check: Is `pdflatex` in your PATH?
- **Python Import Errors:**
  - Error: `ModuleNotFoundError` or similar
  - Solution: Run `rxiv setup` or `make setup` to install dependencies
  - Check: Is your virtual environment activated?
- **Figure Generation Fails:**
  - Error: Figures not generated or missing in PDF
  - Solution:
    - Check Python scripts in `FIGURES/` for errors
    - Use `rxiv pdf --force-figures` or `make pdf FORCE_FIGURES=true`
    - Check for missing data files
- **Build Fails on GitHub Actions:**
  - Check: Is the manuscript directory path correct?
  - Check: Are all dependencies listed in `pyproject.toml`?
  - Check: Does the manuscript have required files (`00_CONFIG.yml`, `01_MAIN.md`)?
  - Solution: Review workflow logs in Actions tab → Click failed run → Click "build-pdf" job
  - See [GitHub Actions Guide](../workflows/github-actions.md) for detailed troubleshooting
- **Debugging Tips:**
  - Always start with `rxiv validate` to catch issues early
  - Use `rxiv pdf --verbose` for more output
  - Check `output/ARTICLE.log` for LaTeX errors
  - Use detailed validation: `rxiv validate --detailed`
  - Use `pytest` for running tests

---

## Where to Get Help
- [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- [Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)
- [Contributing Guide](../CONTRIBUTING.md)

---

## Related Documentation
- [Command Reference](../reference/commands.md) - Complete command documentation
- [GitHub Actions Guide](../workflows/github-actions.md) - Automated cloud builds
- [Docker Guide](../workflows/docker-engine-mode.md) - Containerized builds
- [Change Tracking Guide](../workflows/change-tracking.md) - Version comparison
- [Local Development Setup](../platforms/LOCAL_DEVELOPMENT.md) - Platform-specific installation
