# Common Issues & Troubleshooting Guide

This guide covers the most frequently encountered issues when using Rxiv-Maker, organized by category with step-by-step solutions and prevention strategies.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Environment Setup Problems](#environment-setup-problems)
- [PDF Generation Failures](#pdf-generation-failures)
- [Container Engine Issues](#container-engine-issues)
- [Citation and Bibliography Problems](#citation-and-bibliography-problems)
- [Performance Issues](#performance-issues)
- [Platform-Specific Problems](#platform-specific-problems)
- [Development and Testing Issues](#development-and-testing-issues)

---

## Installation Issues

### Issue: `pip install rxiv-maker` fails

**Symptoms:**
- Package not found
- Permission errors during installation
- Dependency conflicts

**Solutions:**

#### 1. Use UV (Recommended)
```bash
# Install UV first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install rxiv-maker with UV
uv tool install rxiv-maker

# Verify installation
rxiv --version
```

#### 2. Virtual Environment Installation
```bash
# Create and activate virtual environment
python -m venv rxiv-env
source rxiv-env/bin/activate  # On Windows: rxiv-env\Scripts\activate

# Install with pip
pip install --upgrade pip
pip install rxiv-maker

# Verify installation
rxiv --version
```

#### 3. Permission Issues (Linux/macOS)
```bash
# Install for current user only
pip install --user rxiv-maker

# Or use sudo (not recommended)
sudo pip install rxiv-maker
```

### Issue: Command `rxiv` not found after installation

**Symptoms:**
- `rxiv: command not found`
- CLI installed but not accessible

**Solutions:**

#### 1. Check PATH configuration
```bash
# Find where rxiv was installed
which rxiv
pip show -f rxiv-maker

# Add to PATH if needed (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

#### 2. Use python module directly
```bash
# Alternative access method
python -m rxiv_maker.cli --version
python -m rxiv_maker.cli pdf MANUSCRIPT
```

#### 3. UV tool path issues
```bash
# Check UV tool installation
uv tool list

# Add UV tools to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Environment Setup Problems

### Issue: `make setup` fails with dependency errors

**Symptoms:**
- LaTeX installation failures
- Python package conflicts
- R package installation issues

**Solutions:**

#### 1. Container Mode (Easiest)
```bash
# Skip local setup, use containers
export RXIV_ENGINE=DOCKER  # or PODMAN
make pdf  # No local setup required
```

#### 2. Incremental Setup
```bash
# Set up components individually
make setup-python     # Install Python dependencies only
make setup-latex      # Install LaTeX packages only
make setup-r          # Install R packages only
```

#### 3. Platform-Specific Setup
```bash
# macOS with Homebrew
brew install --cask mactex
make setup

# Ubuntu/Debian
sudo apt-get install texlive-full r-base
make setup

# Windows with Chocolatey
choco install miktex r
make setup
```

### Issue: Python environment conflicts

**Symptoms:**
- Import errors
- Package version conflicts
- Virtual environment issues

**Solutions:**

#### 1. Clean Environment
```bash
# Remove existing environment
rm -rf .venv

# Create fresh environment with UV
uv venv
source .venv/bin/activate
uv pip install -e .
```

#### 2. Use UV for dependency management
```bash
# UV handles environment isolation automatically
uv run rxiv pdf MANUSCRIPT
uv run make pdf
```

#### 3. Conda environment (alternative)
```bash
# Create conda environment
conda create -n rxiv python=3.11
conda activate rxiv
pip install rxiv-maker
```

---

## PDF Generation Failures

### Issue: LaTeX compilation errors

**Symptoms:**
- PDF generation stops with LaTeX errors
- Missing packages or style files
- Compilation warnings/errors

**Solutions:**

#### 1. Check LaTeX logs
```bash
# Generate with verbose output
make pdf VERBOSE=true

# Check build logs
cat output/MANUSCRIPT.log
cat output/build_warnings.log
```

#### 2. Missing LaTeX packages
```bash
# Install missing packages (TeX Live)
sudo tlmgr install package-name

# Or use container mode (includes all packages)
make pdf RXIV_ENGINE=DOCKER
```

#### 3. Style file issues
```bash
# Force regeneration of style files
make clean
make pdf

# Check style file presence
ls -la src/tex/style/
```

### Issue: Figure generation failures

**Symptoms:**
- Missing figure files
- Python/R script errors
- Figure validation failures

**Solutions:**

#### 1. Force figure regeneration
```bash
# Regenerate all figures
make pdf FORCE_FIGURES=true

# Generate figures only
rxiv figures MANUSCRIPT --verbose
```

#### 2. Check figure dependencies
```bash
# Test Python environment
python -c "import matplotlib, numpy, pandas"

# Test R environment
Rscript -e "library(ggplot2)"

# Use container mode for dependencies
make pdf RXIV_ENGINE=DOCKER
```

#### 3. Manual figure debugging
```bash
# Navigate to figures directory
cd MANUSCRIPT/FIGURES

# Run individual scripts
python SFigure__example.py
Rscript Figure__example.R

# Check for errors
echo $?  # Should be 0 for success
```

### Issue: Figure positioning and layout problems

**Symptoms:**
- Figures appear on wrong pages or at incorrect positions
- Poor spacing between figure and text  
- Figure panel references have unwanted spaces (e.g., "Fig. 1 A" instead of "Fig. 1A")
- Full-width figures break layout or appear on dedicated pages unexpectedly
- Section headers incorrectly mapped (e.g., "Introduction" becomes "Main")

**Root Cause:**
These issues often stem from incorrect figure positioning attributes, LaTeX positioning conflicts, or missing dependencies (particularly LaTeX packages like `siunitx` and `ifsym`).

**Solutions:**

#### 1. Check figure positioning syntax
```markdown
# Correct syntax with positioning control
![Caption](FIGURES/figure.svg)
{#fig:label tex_position="t" width="0.8\linewidth"}

# For full-width figures spanning two columns
![Caption](FIGURES/workflow.svg)  
{#fig:workflow width="\textwidth" tex_position="t"}
```

#### 2. Fix common positioning issues
```bash
# Install missing LaTeX packages (if using local LaTeX)
sudo tlmgr install siunitx ifsym

# Use container mode to avoid package issues
rxiv pdf --engine docker
```

#### 3. Comprehensive positioning guidance
For complete troubleshooting of figure positioning, panel references, and layout issues, see the **[Figure Positioning Guide](../tutorials/figure-positioning.md)**.

**Prevention:**
- Always use `tex_position="t"` for consistent top placement
- Use `width="\textwidth"` only for figures that should span both columns
- Test figure positioning with `rxiv validate` before building PDF

---

## Container Engine Issues

### Issue: Docker/Podman not available

**Symptoms:**
- `Docker is not available` or `Podman is not available`
- Container engine detection failures

**Solutions:**

#### 1. Check container engine status
```bash
# Docker
docker --version
docker info

# Podman
podman --version
podman info
```

#### 2. Start container services
```bash
# Docker Desktop (macOS/Windows)
# Start Docker Desktop application

# Docker service (Linux)
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add user to docker group

# Podman (Linux)
systemctl --user start podman.socket
```

#### 3. Alternative solutions
```bash
# Use specific engine
make pdf RXIV_ENGINE=DOCKER
make pdf RXIV_ENGINE=PODMAN

# Fall back to local mode
make pdf RXIV_ENGINE=LOCAL
```

### Issue: Container permission problems

**Symptoms:**
- Files created with wrong ownership
- Permission denied errors
- Cannot access output files

**Solutions:**

#### 1. Fix file ownership (Docker)
```bash
# Fix ownership after container run
sudo chown -R $(whoami):$(whoami) output/

# Use user namespace mapping
DOCKER_EXTRA_ARGS="--user $(id -u):$(id -g)" make pdf RXIV_ENGINE=DOCKER
```

#### 2. Use Podman (rootless by default)
```bash
# Podman handles permissions automatically
make pdf RXIV_ENGINE=PODMAN
```

#### 3. Configure container user mapping
```bash
# Add to environment
export DOCKER_EXTRA_ARGS="--user $(id -u):$(id -g)"
make pdf RXIV_ENGINE=DOCKER
```

---

## Citation and Bibliography Problems

### Issue: Citation validation errors

**Symptoms:**
- `Citation 'key' not found in bibliography`
- Undefined references in PDF
- BibTeX compilation failures

**Solutions:**

#### 1. Check citation syntax
```markdown
# Correct syntax
[@smith2023] or @smith2023

# Multiple citations
[@smith2023; @jones2024]

# With page numbers
[@smith2023, p. 42]
```

#### 2. Validate bibliography file
```bash
# Check BibTeX syntax
bibtex --min-crossrefs=1000 03_REFERENCES.bib

# Use validation command
make validate MANUSCRIPT_PATH=MANUSCRIPT
```

#### 3. Update bibliography
```bash
# Add missing references
rxiv bibliography add MANUSCRIPT --doi 10.1000/example

# Fix bibliography formatting
rxiv bibliography fix MANUSCRIPT
```

### Issue: DOI resolution failures

**Symptoms:**
- DOI lookup timeouts
- Invalid DOI format errors
- Bibliography fetch failures

**Solutions:**

#### 1. Check network connectivity
```bash
# Test DOI API access
curl -s "https://api.crossref.org/works/10.1038/nature12373"

# Use offline mode if needed
OFFLINE_MODE=true make pdf
```

#### 2. Manual DOI addition
```bash
# Add DOI manually to 03_REFERENCES.bib
@article{key2023,
  title={Example Title},
  author={Author, Example},
  journal={Example Journal},
  year={2023},
  doi={10.1000/example}
}
```

#### 3. Use bibliography validator
```bash
# Validate and fix bibliography
python -m rxiv_maker.scripts.validate_manuscript --detailed MANUSCRIPT
```

---

## Performance Issues

### Issue: Slow PDF generation

**Symptoms:**
- Build takes several minutes
- Container startup delays
- Figure generation slowness

**Solutions:**

#### 1. Use incremental builds
```bash
# Only regenerate changed figures
make pdf  # Automatic detection

# Force regeneration only when needed
make pdf FORCE_FIGURES=false
```

#### 2. Optimize container usage
```bash
# Pre-pull images
docker pull henriqueslab/rxiv-maker-base:latest

# Use local cache
export RXIV_ENGINE=LOCAL  # After initial setup
```

#### 3. Parallel figure generation
```bash
# Use multiple cores for R/Python scripts
export OMP_NUM_THREADS=4
make pdf
```

### Issue: High memory usage

**Symptoms:**
- System slowdown during builds
- Out of memory errors
- Container resource exhaustion

**Solutions:**

#### 1. Limit container resources
```bash
# Limit Docker memory
DOCKER_EXTRA_ARGS="--memory=2g" make pdf RXIV_ENGINE=DOCKER

# Limit CPU usage
DOCKER_EXTRA_ARGS="--cpus=2.0" make pdf RXIV_ENGINE=DOCKER
```

#### 2. Close unnecessary applications
```bash
# Monitor memory usage
htop
# Close browsers, IDEs, etc. during build
```

#### 3. Use swap space (Linux)
```bash
# Add swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Platform-Specific Problems

### macOS Issues

#### Issue: Permissions and quarantine
```bash
# Allow downloaded binaries
sudo xattr -rd com.apple.quarantine /path/to/rxiv

# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*
```

#### Issue: LaTeX path problems
```bash
# Add TeX Live to PATH
echo 'export PATH="/usr/local/texlive/2023/bin/universal-darwin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Windows Issues

#### Issue: Path separator problems
```bash
# Use forward slashes or escape backslashes
MANUSCRIPT_PATH="C:/Users/username/Documents/paper" make pdf

# Or use WSL2
wsl rxiv pdf MANUSCRIPT
```

#### Issue: LaTeX installation
```bash
# Install MiKTeX
choco install miktex

# Or use TeX Live
choco install texlive
```

### Linux Issues

#### Issue: Package manager conflicts
```bash
# Use system package manager first
sudo apt-get install texlive-full r-base

# Then install rxiv-maker
pip install --user rxiv-maker
```

#### Issue: SELinux restrictions
```bash
# Allow container access (if needed)
setsebool -P container_manage_cgroup on

# Use Podman for better SELinux integration
make pdf RXIV_ENGINE=PODMAN
```

---

## Development and Testing Issues

### Issue: Test failures

**Symptoms:**
- `make test` fails
- Import errors in tests
- Missing test dependencies

**Solutions:**

#### 1. Install test dependencies
```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Or use the development setup
make setup-dev
```

#### 2. Run specific test categories
```bash
# Run only unit tests
pytest tests/unit/ -v

# Skip integration tests
pytest tests/unit/ --ignore=tests/integration/
```

#### 3. Debug test environment
```bash
# Verbose test output
pytest -vvv --tb=long

# Run single test
pytest tests/unit/test_specific.py::TestClass::test_method -v
```

### Issue: Import errors in development

**Symptoms:**
- `ModuleNotFoundError` for rxiv_maker modules
- Path resolution issues

**Solutions:**

#### 1. Development installation
```bash
# Install in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### 2. Use UV for development
```bash
# UV handles development paths automatically
uv run python script.py
uv run pytest
```

---

## Prevention Strategies

### 1. Use Container Mode for Consistency
```bash
# Set as default
echo 'export RXIV_ENGINE=DOCKER' >> ~/.bashrc

# Avoid local dependency issues
```

### 2. Validate Before Building
```bash
# Always validate first
make validate && make pdf
```

### 3. Keep Dependencies Updated
```bash
# Update rxiv-maker
pip install --upgrade rxiv-maker

# Update container images
docker pull henriqueslab/rxiv-maker-base:latest
```

### 4. Use Version Control Effectively
```bash
# Track important files
git add MANUSCRIPT/ output/*.pdf

# Use .gitignore for temporary files
```

### 5. Regular Environment Maintenance
```bash
# Clean up regularly
make clean
docker system prune -f

# Recreate environment periodically
rm -rf .venv && make setup
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check existing documentation:**
   - [Figure Troubleshooting](troubleshooting-missing-figures.md)
   - [Validation Guide](validate_manuscript.md)
   - [Docker Guide](../workflows/docker-engine-mode.md)
   - [Podman Guide](../workflows/podman-engine-mode.md)

2. **Enable verbose output:**
   ```bash
   make pdf VERBOSE=true 2>&1 | tee debug.log
   ```

3. **Check logs:**
   ```bash
   # Build logs
   cat output/build_warnings.log
   cat output/rxiv_maker.log
   
   # System logs
   journalctl --user -u podman.socket
   ```

4. **Create a minimal reproduction:**
   ```bash
   # Use EXAMPLE_MANUSCRIPT for testing
   make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT
   ```

5. **Report issues:**
   - [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
   - Include log files and system information
   - Specify your platform and versions used