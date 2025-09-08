# 🔧 Troubleshooting Guide

*Comprehensive solutions for common issues, debugging techniques, and performance optimization*

---

## 🚨 Emergency Quick Fixes

**Having urgent issues? Try these first:**

```bash
# 🔥 Nuclear option - clean everything and rebuild
rxiv clean --all && rxiv setup && rxiv pdf

# 🔍 Debug mode - see what's failing  
rxiv pdf --verbose

# 🐳 Container mode - bypass local issues
RXIV_ENGINE=DOCKER rxiv pdf

# ⚡ Skip validation - quick build to test
rxiv pdf --skip-validation
```

If none of these work, continue reading for detailed solutions.

---

## 📑 Table of Contents

- [Installation Issues](#installation-issues)
- [Environment Setup Problems](#environment-setup-problems)
- [PDF Generation Failures](#pdf-generation-failures)
- [Figure Generation Failures](#figure-generation-failures)
- [Container Engine Issues](#container-engine-issues)
- [Citation and Bibliography Problems](#citation-and-bibliography-problems)
- [Performance Issues](#performance-issues)
- [Platform-Specific Problems](#platform-specific-problems)
- [Development and Testing Issues](#development-and-testing-issues)
- [Advanced Debugging](#advanced-debugging)
- [Getting Help](#getting-help)
- [Prevention Strategies](#prevention-strategies)

---

## Installation Issues

### Issue: `rxiv` command not found

**Symptoms:** `bash: rxiv: command not found` or similar error

**Solutions:**

#### 1. Check Installation and PATH
```bash
# Check if rxiv-maker is installed
pip show rxiv-maker

# If installed, add to PATH
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
# Add to ~/.bashrc or ~/.zshrc for permanent fix

# Alternative: run directly
python -m rxiv_maker.cli --help
```

#### 2. Virtual Environment Issues
```bash
# Check if you're in the right environment
which python
pip list | grep rxiv

# Activate environment if needed
source venv/bin/activate  # Or your environment path

# Reinstall in current environment
pip install --force-reinstall rxiv-maker
```

#### 3. UV Tool Path Issues
```bash
# Check UV tool installation
uv tool list

# Add UV tools to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: APT Repository Installation Fails (Ubuntu/Debian)

**Symptoms:**
- `apt install rxiv-maker` fails with "package not found"
- GPG key verification errors
- Repository not accessible

**Solutions:**

#### 1. Re-add Repository with Fresh Keys
```bash
# Remove existing repository
sudo rm -f /etc/apt/sources.list.d/rxiv-maker.list
sudo rm -f /usr/share/keyrings/rxiv-maker.gpg

# Re-add repository
sudo apt update && sudo apt install ca-certificates
curl -fsSL https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/rxiv-maker.gpg] https://raw.githubusercontent.com/HenriquesLab/apt-rxiv-maker/apt-repo stable main' | sudo tee /etc/apt/sources.list.d/rxiv-maker.list

# Update and install
sudo apt update && sudo apt install rxiv-maker
```

#### 2. Alternative: Use UV or Pip Installation
```bash
# Install UV (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install rxiv-maker

# Or virtual environment with pip
python -m venv rxiv-env
source rxiv-env/bin/activate
pip install --upgrade pip && pip install rxiv-maker
```

### Issue: Permission denied errors

**Symptoms:** Permission errors during installation or execution

**Solutions:**
```bash
# Fix pip permissions (Linux/macOS)
pip install --user rxiv-maker

# Fix directory permissions
sudo chown -R $USER:$USER ~/.local/
chmod +x ~/.local/bin/rxiv

# Windows: Run Command Prompt as Administrator
# Then: pip install rxiv-maker
```

---

## Environment Setup Problems

### Issue: `rxiv setup` fails with dependency errors

**Symptoms:**
- LaTeX installation failures
- Python package conflicts
- R package installation issues

**Solutions:**

#### 1. Container Mode (Easiest)
```bash
# Skip local setup, use containers
rxiv config set general.default_engine docker  # or podman
rxiv pdf  # No local setup required
```

#### 2. Platform-Specific Setup
```bash
# macOS with Homebrew
brew install --cask mactex
rxiv setup

# Ubuntu/Debian
sudo apt-get install texlive-full r-base
rxiv setup

# Windows with Chocolatey
choco install miktex r
rxiv setup
```

#### 3. Clean Environment Reinstall
```bash
# Reinstall with clean environment
rxiv setup --reinstall

# Or use UV for automatic isolation
uv run rxiv pdf MANUSCRIPT
```

### Issue: Python environment conflicts

**Symptoms:**
- Import errors
- Package version conflicts
- Virtual environment issues

**Solutions:**
```bash
# Check Python version (need 3.11+)
python --version

# Clean reinstall
pip uninstall rxiv-maker
pip cache purge
pip install --upgrade pip
pip install rxiv-maker

# Or use conda environment
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

#### 1. Check LaTeX Installation
```bash
# Test LaTeX availability
pdflatex --version
xelatex --version

# Install missing LaTeX (Ubuntu/Debian)
sudo apt install texlive-full texlive-latex-extra

# Install missing LaTeX (macOS)
brew install texlive
# Or download MacTeX from https://tug.org/mactex/

# Install missing LaTeX (Windows)
choco install miktex
```

#### 2. Check Build Logs
```bash
# Generate with verbose output
rxiv pdf --verbose

# Check build logs
cat output/MANUSCRIPT.log
cat output/build_warnings.log
```

#### 3. Missing LaTeX Packages
```bash
# Auto-install missing packages (MiKTeX)
initexmf --set-config-value=[MPM]AutoInstall=1

# Manual package installation (TeX Live)
sudo tlmgr install missing-package-name

# Use container mode to avoid LaTeX issues
RXIV_ENGINE=DOCKER rxiv pdf
```

### Issue: Build failed with exit code 1

**Symptoms:** PDF generation fails with non-zero exit code

**Debugging Steps:**

#### 1. Enable Verbose Mode
```bash
rxiv pdf --verbose > build.log 2>&1
less build.log  # Examine the full log
```

#### 2. Check Common Issues
```bash
# Validate manuscript first
rxiv validate --detailed

# Check for file permission issues
ls -la output/
chmod -R u+w output/

# Clean and retry
rxiv clean && rxiv pdf --verbose
```

#### 3. Isolate the Problem
```bash
# Skip validation
rxiv pdf --skip-validation --verbose

# Skip figures
rxiv pdf --skip-validation --no-figures

# Use different engine
RXIV_ENGINE=docker rxiv pdf
```

### Issue: Figure positioning and layout problems

**Symptoms:**
- Figures appear on wrong pages or at incorrect positions
- Poor spacing between figure and text  
- Figure panel references have unwanted spaces (e.g., "Fig. 1 A" instead of "Fig. 1A")
- Full-width figures break layout or appear on dedicated pages unexpectedly

**Solutions:**

#### 1. Check Figure Positioning Syntax
```markdown
# Correct syntax with positioning control
![Caption](FIGURES/figure.svg)
{#fig:label tex_position="t" width="0.8\\linewidth"}

# For full-width figures spanning two columns
![Caption](FIGURES/workflow.svg)  
{#fig:workflow width="\\textwidth" tex_position="t"}
```

#### 2. Fix Missing LaTeX Packages
```bash
# Install missing LaTeX packages (if using local LaTeX)
sudo tlmgr install siunitx ifsym

# Use container mode to avoid package issues
rxiv pdf --engine docker
```

For complete troubleshooting of figure positioning, see the **[Complete Figure Guide](../guides/figures-guide.md)**.

---

## Figure Generation Failures

### Issue: Python script failures

**Symptoms:** Figure scripts fail to execute or generate output

**Solutions:**

#### 1. Test Scripts Individually
```bash
# Run script directly to see errors
cd FIGURES/
python my_script.py

# Check Python environment
python --version
pip list | grep matplotlib
pip list | grep numpy
```

#### 2. Common Python Issues
```bash
# Missing packages
pip install matplotlib numpy pandas seaborn

# Virtual environment issues
which python
source venv/bin/activate  # If using virtual environment

# Permission issues
chmod +x FIGURES/*.py
```

#### 3. Script Template for Debugging
```python
# FIGURES/debug_template.py
import sys
import os
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

try:
    import matplotlib.pyplot as plt
    import numpy as np
    print("✅ Core packages available")
    
    # Simple test plot
    x = [1, 2, 3, 4]
    y = [1, 4, 2, 3]
    plt.figure(figsize=(6, 4))
    plt.plot(x, y)
    plt.title("Test Plot")
    plt.show()  # This should trigger Rxiv-Maker to save
    print("✅ Test plot generated")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Script error: {e}")
```

### Issue: R script failures

**Symptoms:** R scripts fail to execute

**Solutions:**
```bash
# Check R installation
R --version
which R

# Test R script directly
cd FIGURES/
Rscript my_analysis.R

# Install missing packages
R -e "install.packages(c('ggplot2', 'dplyr', 'readr'))"
```

### Issue: Figure file problems

**Symptoms:** Figures not appearing in PDF or wrong placement

**Solutions:**

#### 1. Check Figure References
```markdown
# Correct syntax
![Figure caption](FIGURES/my_script.py)
{#fig:label}

# Common mistakes to avoid
![Caption](figures/script.py)          # Wrong path case
![Caption](FIGURES/script.py           # Missing closing )
![Caption](FIGURES/nonexistent.py)    # File doesn't exist
```

#### 2. Verify Generated Files
```bash
# Check if figure files were created
ls -la output/Figures/
ls -la FIGURES/

# Force regenerate figures
rxiv clean --figures-only
rxiv pdf --force-figures
```

### Issue: Memory issues with large figures

**Symptoms:** Out of memory errors, slow figure generation

**Solutions:**
```python
# FIGURES/memory_efficient.py
import matplotlib.pyplot as plt
import numpy as np

# Configure matplotlib for memory efficiency
plt.rcParams['figure.max_open_warning'] = 0
plt.rcParams['agg.path.chunksize'] = 10000

def generate_efficient_plot():
    # Close previous figures
    plt.close('all')
    
    # Use context manager for automatic cleanup
    with plt.subplots(figsize=(8, 6)) as (fig, ax):
        # Your plotting code here
        x = np.random.randn(10000)
        ax.hist(x, bins=50, alpha=0.7)
        plt.tight_layout()
        plt.show()
    
    # Explicitly clean up
    plt.close('all')

if __name__ == "__main__":
    generate_efficient_plot()
```

---

## Container Engine Issues

### Issue: Docker/Podman not available

**Symptoms:**
- `Docker is not available` or `Podman is not available`
- Container engine detection failures

**Solutions:**

#### 1. Check Container Engine Status
```bash
# Docker
docker --version
docker info

# Podman
podman --version
podman info
```

#### 2. Start Container Services
```bash
# Docker Desktop (macOS/Windows)
# Start Docker Desktop application

# Docker service (Linux)
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add user to docker group

# Podman (Linux)
systemctl --user start podman.socket
```

#### 3. Alternative Solutions
```bash
# Use specific engine
rxiv pdf --engine docker
rxiv pdf --engine podman

# Fall back to local mode
rxiv pdf --engine local
```

### Issue: Container permission problems

**Symptoms:**
- Files created with wrong ownership
- Permission denied errors
- Cannot access output files

**Solutions:**
```bash
# Fix ownership after container run (if needed)
sudo chown -R $(whoami):$(whoami) output/

# Use Podman (rootless by default)
rxiv pdf --engine podman

# Modern rxiv handles user mapping automatically
rxiv pdf --engine docker
```

---

## Citation and Bibliography Problems

### Issue: Citation validation errors

**Symptoms:**
- `Citation 'key' not found in bibliography`
- Undefined references in PDF
- BibTeX compilation failures

**Solutions:**

#### 1. Check Citation Syntax
```markdown
# Correct syntax
[@smith2023] or @smith2023

# Multiple citations
[@smith2023; @jones2024]

# With page numbers
[@smith2023, p. 42]
```

#### 2. Validate Bibliography File
```bash
# Check BibTeX syntax
bibtex --min-crossrefs=1000 03_REFERENCES.bib

# Use validation command
rxiv validate MANUSCRIPT
```

#### 3. Common BibTeX Issues
```bibtex
# ✅ Correct format  
@article{smith2023,
    title={My Research Title},
    author={John Smith and Jane Doe},
    journal={Nature},
    volume={123},
    pages={1--10},
    year={2023},
    doi={10.1038/nature12345}
}
```

### Issue: DOI resolution failures

**Symptoms:**
- DOI lookup timeouts
- Invalid DOI format errors
- Bibliography fetch failures

**Solutions:**
```bash
# Check network connectivity
curl -s "https://api.crossref.org/works/10.1038/nature12373"

# Use offline mode if needed
rxiv pdf --offline

# Manual DOI resolution
curl -H "Accept: application/x-bibtex" \
     https://dx.doi.org/10.1038/nature12345
```

### Issue: Bibliography not appearing

**Symptoms:** References section is empty or missing

**Solutions:**
```markdown
# Ensure you have citations in text
Previous work [@smith2023] showed...

# Ensure you have references section
## References
<!-- Bibliography will be automatically generated here -->
```

---

## Performance Issues

### Issue: Slow PDF generation

**Symptoms:**
- Build takes several minutes
- Container startup delays
- Figure generation slowness

**Solutions:**

#### 1. Use Incremental Builds
```bash
# Only regenerate changed figures
rxiv pdf  # Automatic detection

# Skip figure regeneration
rxiv pdf --skip-figures
```

#### 2. Profile Build Time
```bash
# Profile build time
time rxiv pdf --verbose

# Skip expensive operations for testing
time rxiv pdf --skip-validation --no-figures
```

#### 3. Optimize Container Usage
```bash
# Pre-pull images
docker pull henriqueslab/rxiv-maker-base:latest

# Use local mode after setup
rxiv config set general.default_engine local
```

#### 4. Figure Generation Optimization
```bash
# Use figure caching (default, but ensure it's enabled)
export RXIV_CACHE_FIGURES=1

# Parallel figure generation
export RXIV_PARALLEL_JOBS=4  # Adjust based on CPU cores
```

### Issue: High memory usage

**Symptoms:**
- System slowdown during builds
- Out of memory errors
- Container resource exhaustion

**Solutions:**
```bash
# Use local mode for better resource control
rxiv pdf --engine local

# Monitor memory usage
htop

# Add swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Platform-Specific Problems

### macOS Issues

#### Issue: Apple Silicon (M1/M2/M3) compatibility
```bash
# Check architecture
uname -m  # Should show "arm64" for Apple Silicon

# Install native packages
arch -arm64 brew install python@3.11
arch -arm64 pip install rxiv-maker
```

#### Issue: Permission and quarantine problems
```bash
# Allow downloaded binaries
sudo xattr -rd com.apple.quarantine /path/to/rxiv

# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*

# Add TeX Live to PATH
export PATH="/usr/local/texlive/2023/bin/universal-darwin:$PATH"
```

### Windows Issues

#### Issue: WSL2 setup problems
```powershell
# Enable WSL2 in PowerShell (Administrator)
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Set WSL2 as default
wsl --set-default-version 2
```

#### Issue: Path and environment problems
```bash
# Fix PATH in WSL2
echo 'export PATH="/home/$USER/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Access Windows files from WSL2
cd /mnt/c/Users/YourUsername/Documents/
```

### Linux Issues

#### Issue: Package manager conflicts
```bash
# Ubuntu/Debian dependencies
sudo apt update && sudo apt upgrade
sudo apt install python3.11-dev python3.11-venv
sudo apt install texlive-full texlive-latex-extra
sudo apt install nodejs npm make build-essential

# CentOS/RHEL/Fedora
sudo dnf install python3.11 python3.11-pip texlive-scheme-full
sudo dnf groupinstall "Development Tools"

# Arch Linux
sudo pacman -S python python-pip texlive-most nodejs npm make
```

#### Issue: SELinux restrictions
```bash
# Allow container access (if needed)
setsebool -P container_manage_cgroup on

# Use Podman for better SELinux integration
rxiv pdf --engine podman
```

---

## Development and Testing Issues

### Issue: Test failures

**Symptoms:**
- `make test` fails
- Import errors in tests
- Missing test dependencies

**Solutions:**
```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Or use the development setup
rxiv setup --dev

# Run specific test categories
pytest tests/unit/ -v

# Skip integration tests
pytest tests/unit/ --ignore=tests/integration/
```

### Issue: Import errors in development

**Symptoms:**
- `ModuleNotFoundError` for rxiv_maker modules
- Path resolution issues

**Solutions:**
```bash
# Install in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Use UV for development (handles paths automatically)
uv run python script.py
uv run pytest
```

---

## Advanced Debugging

### Enable Debug Mode

```bash
# Maximum verbosity
export RXIV_DEBUG=1
export RXIV_LOG_LEVEL=DEBUG
rxiv pdf --verbose > debug.log 2>&1

# Analyze the debug log
less debug.log
grep -i error debug.log
grep -i warning debug.log
```

### Container Debugging

```bash
# Debug Docker builds
RXIV_ENGINE=DOCKER RXIV_DEBUG=1 rxiv pdf

# Access container for debugging
docker run -it --rm \
  -v $(pwd):/workspace \
  henriqueslab/rxiv-maker:latest \
  bash

# Inside container
cd /workspace
rxiv pdf --verbose
```

### Custom Debug Scripts

```python
# scripts/debug_environment.py
import sys
import os
import subprocess
from pathlib import Path

def debug_environment():
    print("=== Rxiv-Maker Environment Debug ===")
    
    # Python information
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Path information
    print(f"Current directory: {os.getcwd()}")
    print(f"PATH: {os.environ.get('PATH', 'Not set')}")
    
    # Rxiv-Maker installation
    try:
        import rxiv_maker
        print(f"Rxiv-Maker version: {rxiv_maker.__version__}")
        print(f"Rxiv-Maker location: {rxiv_maker.__file__}")
    except ImportError as e:
        print(f"❌ Rxiv-Maker import error: {e}")
    
    # System tools
    tools = ['pdflatex', 'python', 'node', 'docker']
    for tool in tools:
        result = subprocess.run(['which', tool], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {tool}: {result.stdout.strip()}")
        else:
            print(f"❌ {tool}: Not found")
    
    # File system
    paths = ['01_MAIN.md', '03_REFERENCES.bib', 'FIGURES/', 'output/']
    for path in paths:
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_file():
                size = path_obj.stat().st_size
                print(f"✅ {path}: {size} bytes")
            else:
                count = len(list(path_obj.iterdir()))
                print(f"✅ {path}: {count} items")
        else:
            print(f"❌ {path}: Not found")

if __name__ == "__main__":
    debug_environment()
```

---

## Getting Help

### Before Asking for Help

**Please gather this information:**

```bash
# System information
rxiv --version
python --version
uname -a  # Linux/macOS

# Generate debug report
rxiv check-installation > debug_report.txt
rxiv validate --detailed >> debug_report.txt
rxiv pdf --verbose &>> debug_report.txt
```

### Community Resources

#### GitHub Issues
- **🐛 [Report Bug](https://github.com/henriqueslab/rxiv-maker/issues/new?template=bug_report.md)**
- **✨ [Request Feature](https://github.com/henriqueslab/rxiv-maker/issues/new?template=feature_request.md)**
- **📖 [Documentation Issue](https://github.com/henriqueslab/rxiv-maker/issues/new?template=documentation.md)**

#### Community Support
- **💬 [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)** - Ask questions, share tips
- **📚 [Documentation](https://github.com/henriqueslab/rxiv-maker/tree/main/docs)** - Comprehensive guides
- **🔍 [Search Existing Issues](https://github.com/henriqueslab/rxiv-maker/issues)** - Your issue might be solved

### Create Minimal Reproducible Example

```bash
# Create minimal test case
rxiv init test-case
cd test-case

# Minimal 01_MAIN.md that demonstrates issue
echo "# Test Case

This demonstrates the issue...

![Problem figure](FIGURES/test.py)" > 01_MAIN.md

# Minimal figure script
echo "import matplotlib.pyplot as plt
plt.plot([1,2,3], [1,2,3])
plt.show()" > FIGURES/test.py

# Try to reproduce issue
rxiv pdf --verbose
```

---

## Prevention Strategies

### Regular Maintenance
```bash
# Weekly health check
rxiv check-installation
rxiv validate --detailed

# Keep dependencies updated
pip install --upgrade rxiv-maker

# Clean accumulated files
rxiv clean --cache-only
```

### Project Health Monitoring
```bash
# Add to your writing routine
alias morning-check="rxiv validate && rxiv pdf --draft"
alias end-session="rxiv validate --detailed && rxiv clean --cache-only"

# Pre-commit validation (if using git)
echo "rxiv validate" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Use Container Mode for Consistency
```bash
# Set as default to avoid local dependency issues
rxiv config set general.default_engine docker
```

### Always Validate Before Building
```bash
# Make this your standard workflow
rxiv validate && rxiv pdf
```

**🎯 Remember**: Most issues are preventable with regular validation and keeping dependencies updated!

---

**📚 [User Guide](../guides/user_guide.md) | ⚙️ [CLI Reference](../reference/cli-reference.md) | 🚀 [First Manuscript](../quick-start/first-manuscript.md)**