# Installation Guide

This guide covers pip/pipx installation for Rxiv-Maker - the recommended approach for all users.

## 🎯 **Recommended Installation Method**

**Universal Installation with pip/pipx** is the recommended approach for all platforms:
- ✅ **Simple**: Single command installation
- ✅ **Reliable**: Uses standard Python packaging
- ✅ **Consistent**: Same method across all platforms  
- ✅ **Maintainable**: Automatic updates with pip/pipx
- ✅ **Isolated**: pipx installs in separate environments

## 🚀 Universal Installation

**Quick Installation:**
```bash
# Using pipx (recommended - installs in isolated environment)
pipx install rxiv-maker

# Or using pip
pip install rxiv-maker

# Verify installation
rxiv check-installation
```

## 📋 Platform-Specific Setup

### 🐧 **Linux**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip pipx texlive-latex-recommended
pipx install rxiv-maker

# Red Hat/CentOS/Fedora  
sudo dnf install python3-pip texlive-latex
python3 -m pip install --user pipx
pipx install rxiv-maker

# Verify
rxiv check-installation
```

### 🍎 **macOS**

```bash
# Install Homebrew (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install pipx
brew install --cask mactex-no-gui

# Install rxiv-maker
pipx install rxiv-maker
rxiv check-installation
```

### 🪟 **Windows**

**Option 1: WSL2 (Recommended)**
```bash
# Install WSL2 (PowerShell as Administrator)
wsl --install -d Ubuntu-22.04

# Restart, then in Ubuntu:
sudo apt update
sudo apt install python3-pip pipx texlive-latex-recommended
pipx install rxiv-maker
```

**Option 2: Native Windows**
```powershell
# Install Chocolatey (PowerShell as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python pipx miktex
pipx install rxiv-maker
```

## 🚀 Quick Start

After installation, create your first PDF:

```bash
# Create a new manuscript
rxiv init my-paper
cd my-paper

# Generate PDF
rxiv pdf

# Verify everything works
rxiv check-installation --detailed
```

## 🔧 Alternative Workflows

**For specialized use cases:**

- **🐳 Docker Builds**: Use `RXIV_ENGINE=DOCKER` for containerized execution
- **🌐 Google Colab**: [Try in browser](https://colab.research.google.com/github/HenriquesLab/rxiv-maker/blob/main/notebooks/rxiv_maker_colab.ipynb) without installation  
- **⚡ GitHub Actions**: Set up automated cloud builds for team collaboration
- **🔄 Development Setup**: Clone repository with `git clone https://github.com/henriqueslab/rxiv-maker.git` for contributing

## 🆘 Need Help?

- **Quick Questions**: Check [User Guide](../guides/user_guide.md)
- **Installation Issues**: See [Troubleshooting](../troubleshooting/troubleshooting.md)
- **Community Support**: [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)

---

*This streamlined installation focuses on pip/pipx for reliable, consistent setup across all platforms.*