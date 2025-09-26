# Migration Guide: v1.7.9 Ecosystem Streamlining

This guide helps users migrate from deprecated functionality removed in rxiv-maker v1.7.9 as part of the ecosystem streamlining effort.

## 🎯 Overview

**v1.7.9** focuses the rxiv-maker ecosystem around two core pillars:
- **Local development** with system LaTeX installation
- **Containerized execution** via [docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker)

## ⚠️ Removed Features

### Package Manager Repositories
**Removed:**
- Homebrew formula repository
- APT package repository
- Direct package manager installation support

**Migration:**
```bash
# OLD (no longer supported)
brew install rxiv-maker
sudo apt install rxiv-maker

# NEW (recommended)
pipx install rxiv-maker
# or
pip install rxiv-maker
```

### Container Engine Support
**Removed:**
- Docker/Podman engine execution within main CLI
- `RXIV_ENGINE` environment variable
- Built-in container orchestration

**Migration:**
For containerized execution, use the dedicated [docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker) repository:

```bash
# OLD (no longer supported)
export RXIV_ENGINE=docker
rxiv pdf

# NEW (recommended)
# Use docker-rxiv-maker repository
git clone https://github.com/HenriquesLab/docker-rxiv-maker.git
cd docker-rxiv-maker
# Follow repository instructions
```

### Cross-Repository Coordination Scripts
**Removed:**
- Automated ecosystem health monitoring
- Cross-repository release coordination
- Legacy workflow templates

**Impact:** These were internal development tools and do not affect end users.

## 🚀 Recommended Workflow

### For Local Development
```bash
# 1. Install LaTeX distribution
# macOS: Download MacTeX from https://tug.org/mactex/
# Windows: Download MiKTeX from https://miktex.org/
# Linux: sudo apt install texlive-full  # or equivalent

# 2. Install rxiv-maker
pipx install rxiv-maker

# 3. Verify installation
rxiv check-installation

# 4. Create and build manuscript
rxiv init my-paper
cd my-paper
rxiv pdf
```

### For Containerized Execution
```bash
# Use the dedicated docker-rxiv-maker repository
git clone https://github.com/HenriquesLab/docker-rxiv-maker.git
cd docker-rxiv-maker

# Follow the repository's README for setup
# This provides isolated environments without system LaTeX
```

### For CI/CD Pipelines
Update your GitHub Actions or CI configuration:

```yaml
# .github/workflows/build-manuscript.yml
name: Build Manuscript
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Option 1: Local LaTeX installation
      - name: Install LaTeX
        run: |
          sudo apt-get update
          sudo apt-get install -y texlive-full

      - name: Install rxiv-maker
        run: pipx install rxiv-maker

      - name: Build PDF
        run: rxiv pdf

      # Option 2: Use docker-rxiv-maker action (if available)
      # - uses: HenriquesLab/docker-rxiv-maker@main
```

## 🛠️ Troubleshooting

### LaTeX Installation Issues
**Linux users:** If you encounter LaTeX-related errors:

```bash
# Install comprehensive LaTeX distribution
sudo apt-get install texlive-full

# For minimal installation
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended

# Verify installation
latex --version
pdflatex --version
```

### Python Environment Issues
Ensure you're using Python 3.11+:

```bash
python --version  # Should be 3.11+
pipx install --python python3.11 rxiv-maker
```

### Container Migration
If you were using Docker/Podman engines:

1. **Clone docker-rxiv-maker**: `git clone https://github.com/HenriquesLab/docker-rxiv-maker.git`
2. **Follow repository setup**: Each container solution has specific setup instructions
3. **Update scripts**: Replace `rxiv` calls with container-specific commands

## 📞 Getting Help

If you encounter issues during migration:

1. **Check Documentation**: [Installation Guide](installation.md) | [CLI Reference](cli-reference.md)
2. **Validate Setup**: Run `rxiv check-installation` to diagnose issues
3. **GitHub Discussions**: [Ask questions](https://github.com/henriqueslab/rxiv-maker/discussions)
4. **Report Bugs**: [File issues](https://github.com/henriqueslab/rxiv-maker/issues) for migration problems

## 🎯 Benefits of Streamlined Architecture

The v1.7.9 changes provide:

- **Simpler Maintenance**: Focused codebase with fewer dependencies
- **Better Performance**: Native LaTeX execution for faster builds
- **Clearer Separation**: Local development vs. containerized execution
- **Improved Reliability**: Reduced complexity means fewer failure points
- **Enhanced Security**: Removed legacy coordination scripts and deprecated engines

## 🔄 Version Compatibility

- **Breaking Changes**: Container engine support, package manager repositories
- **Non-Breaking**: All core functionality (Markdown processing, PDF generation, citations)
- **Forward Compatible**: New features will build on this streamlined foundation

---

*This migration guide covers changes in rxiv-maker v1.7.9. For general usage, see the [User Guide](user_guide.md).*