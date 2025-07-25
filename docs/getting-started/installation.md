# Installation Guide

This is the comprehensive installation guide for Rxiv-Maker. **Choose ONE method below** based on your needs and technical preferences.

## 🎯 **Which Installation Method is Right for You?**

| Method | Best For | Requirements | Setup Time | Skill Level |
|--------|----------|--------------|------------|-------------|
| **🌐 Google Colab** | First-time users, quick experiments | Google account | 2 minutes | Beginner |
| **📦 Modern CLI** | Quick start, modern interface | Python 3.11+ | 2-3 minutes | Beginner |
| **🐳 Docker Engine** | Consistent environment, teams | Docker + Make | 3-5 minutes | Beginner |
| **🏠 Local Development** | Advanced users, offline work | Python, LaTeX, Make | 10-30 minutes | Advanced |
| **⚡ GitHub Actions** | Team collaboration, automation | GitHub account | 5 minutes | Intermediate |

---

## 🌐 Google Colab (Recommended for Beginners)

**Perfect for trying Rxiv-Maker without any local installation.**

### Quick Start
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb)

### Benefits
- ✅ No local installation required
- ✅ Works in any web browser
- ✅ Free LaTeX environment included
- ✅ Easy sharing with collaborators
- ✅ GPU acceleration available

### Complete Tutorial
For detailed instructions, see: [Google Colab Tutorial](../tutorials/google_colab.md)

---

## 🐳 Docker Engine Mode (Recommended for Most Users)

**Containerized execution with minimal local requirements - only Docker and Make needed.**

### Prerequisites

<details>
<summary><strong>📦 Install Docker Desktop</strong></summary>

**Windows:**
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Run the installer and follow setup wizard
3. Restart your computer when prompted
4. Verify installation: `docker --version`

**macOS:**
1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Drag Docker.app to Applications folder
3. Launch Docker Desktop and complete setup
4. Verify installation: `docker --version`

**Linux (Ubuntu/Debian):**
```bash
# Install Docker Engine
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
docker --version
```

</details>

<details>
<summary><strong>🔧 Install Make</strong></summary>

**Windows:**
```powershell
# Option 1: Chocolatey (recommended)
choco install make

# Option 2: Scoop
scoop install make

# Option 3: Visual Studio Build Tools (if you have VS installed)
# Make is included with "Desktop development with C++" workload
```

**macOS:**
```bash
# Usually pre-installed, if not:
xcode-select --install
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install -y make

# Red Hat/CentOS/Fedora  
sudo yum install -y make
# or
sudo dnf install -y make
```

</details>

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# 2. Generate your first PDF using Docker
make pdf RXIV_ENGINE=DOCKER MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT

# 3. Set Docker mode as default (optional)
export RXIV_ENGINE=DOCKER
echo 'export RXIV_ENGINE=DOCKER' >> ~/.bashrc  # Linux/macOS
# For Windows PowerShell, add to your profile
```

### Benefits
- ✅ No LaTeX, Python, or R installation needed locally
- ✅ Cross-platform consistency (same on Windows, macOS, Linux)
- ✅ No dependency conflicts with existing installations
- ✅ Matches CI/CD environment exactly
- ✅ 5x faster than traditional dependency installation

### Complete Guide
For detailed Docker information, see: [Docker Engine Mode Guide](../workflows/docker-engine-mode.md)

---

## 📦 Modern CLI Installation (Recommended)

**The easiest way to get started with Rxiv-Maker using the modern command-line interface.**

### Quick Install
```bash
# Install from PyPI
pip install rxiv-maker

# Verify installation
rxiv check-installation

# Install system dependencies (if needed)
rxiv check-installation --fix

# Initialize your first manuscript
rxiv init MY_PAPER/

# Build PDF
rxiv pdf MY_PAPER/
```

### Benefits
- ✅ Beautiful terminal output with progress indicators
- ✅ Auto-completion for bash/zsh/fish shells
- ✅ Unified command interface replacing complex Make commands
- ✅ Intelligent error messages and suggestions
- ✅ Works on Windows, macOS, and Linux

### Installation Options
```bash
# Standard installation
pip install rxiv-maker

# Development installation (for contributing)
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e .

# Enable shell auto-completion
rxiv --install-completion bash  # or zsh, fish
```

### System Dependencies
The CLI will automatically detect and help install required system dependencies:
```bash
# Check what's missing
rxiv check-installation --detailed

# Auto-install missing dependencies (admin rights may be required)
rxiv check-installation --fix
```

---

## 🏠 Local Development (Advanced Users)

**Complete local environment setup for maximum control and performance.**

### Benefits
- ✅ Fastest iteration cycles
- ✅ Full IDE integration and debugging
- ✅ Offline development capability
- ✅ Custom modifications and extensions
- ✅ No container overhead

### Platform-Specific Setup

<details>
<summary><strong>🍎 macOS Installation</strong></summary>

**Prerequisites:**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 node@20 git make
brew install --cask mactex-no-gui  # For LaTeX support
```

**Setup:**
```bash
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
make setup

# Generate your first PDF
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT
```

</details>

<details>
<summary><strong>🐧 Linux Installation (Ubuntu/Debian)</strong></summary>

**Prerequisites:**
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git make curl

# Install LaTeX (choose one)
sudo apt install -y texlive-full  # Complete installation (~4GB)
# OR
sudo apt install -y texlive-latex-recommended texlive-fonts-recommended  # Minimal (~500MB)
```

**Setup:**
```bash
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
make setup

# Generate your first PDF
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT
```

</details>

<details>
<summary><strong>🪟 Windows Installation</strong></summary>

**Prerequisites (PowerShell as Administrator):**
```powershell
# Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required tools
choco install -y python311 nodejs git make

# Install MikTeX for LaTeX
choco install -y miktex
```

**Setup (PowerShell):**
```powershell
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
make setup

# Generate your first PDF
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT
```

**Alternative: WSL2 (Recommended)**
```bash
# Install Ubuntu in WSL2 first
wsl --install -d Ubuntu-22.04

# Then follow Linux instructions inside WSL2
```

</details>

### Complete Platform Guide
For detailed platform-specific instructions and troubleshooting, see: [Local Development Guide](../platforms/LOCAL_DEVELOPMENT.md)

---

## ⚡ GitHub Actions (Automated Cloud Builds)

**Automatic PDF generation with zero local setup - perfect for teams and collaboration.**

### Quick Setup

1. **Fork the Repository**
   - Go to [https://github.com/henriqueslab/rxiv-maker](https://github.com/henriqueslab/rxiv-maker)
   - Click "Fork" in the top-right corner

2. **Trigger PDF Generation**
   - Go to Actions tab → "Build and Release PDF"
   - Click "Run workflow" → Select manuscript path → "Run workflow"

3. **Download Your PDF**
   - Wait for workflow completion (~2 minutes)
   - Download from workflow artifacts or releases

### Benefits
- ✅ Zero local installation required
- ✅ Automatic builds on every commit
- ✅ Team collaboration with version control
- ✅ 5x faster builds with pre-compiled Docker images
- ✅ Automatic backup and archival
- ✅ Works with private repositories

### Complete Guide
For detailed GitHub Actions setup and workflows, see: [GitHub Actions Guide](../workflows/github-actions.md)

---

## 📝 VS Code Extension (Enhanced Editing)

**After choosing any installation method above, enhance your editing experience:**

### Installation
1. Install [Rxiv-Maker VS Code Extension](https://github.com/HenriquesLab/vscode-rxiv-maker)
2. Open your rxiv-maker project in VS Code
3. Enjoy enhanced editing features

### Features
- ✅ Syntax highlighting for rxiv-markdown
- ✅ Intelligent autocompletion for citations
- ✅ Cross-reference suggestions
- ✅ Integrated project commands
- ✅ Schema validation for YAML configs

---

## 🔧 First PDF Generation

After completing any installation method, test your setup:

```bash
# Clone the repository (if not already done)
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Generate example PDF
make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT

# For Docker mode, add:
# make pdf MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT RXIV_ENGINE=DOCKER

# For Google Colab and GitHub Actions, follow the specific workflows above
```

## 🆘 Need Help?

- **Quick Questions**: Check [User Guide](user_guide.md)
- **Installation Issues**: See [Troubleshooting](../troubleshooting/troubleshooting-missing-figures.md) 
- **Platform Problems**: Visit [Local Development Guide](../platforms/LOCAL_DEVELOPMENT.md)
- **Docker Issues**: Read [Docker Engine Mode Guide](../workflows/docker-engine-mode.md)
- **Community Support**: [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)

---

*This installation guide serves as the single source of truth for all Rxiv-Maker setup methods. For method-specific details, follow the linked guides above.*