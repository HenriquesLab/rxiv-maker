# Docker Engine Mode Guide (Cross-Platform)

Docker Engine Mode provides a **minimal dependency** approach to using Rxiv-Maker by running all operations inside pre-configured containers. This eliminates the need to install LaTeX, R, Node.js, or Python packages locally while ensuring reproducible builds across all platforms. Only Docker and Make are required on the host system.

**✅ CROSS-PLATFORM:** Docker Engine Mode now supports **both AMD64 and ARM64 architectures** with native performance. As of v1.8+, we use the mermaid.ink API for diagram generation, eliminating browser dependencies and enabling full cross-platform compatibility.

## Table of Contents
- [Architecture Requirements](#architecture-requirements)
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation & Setup](#installation--setup)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Benefits & Use Cases](#benefits--use-cases)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Architecture Requirements

### Supported Architectures
- **✅ AMD64/x86_64**: Native support with optimal performance  
- **✅ ARM64/aarch64**: Native support with optimal performance (Apple Silicon, etc.)

### Technical Background: Mermaid.ink API Processing

Docker Engine Mode uses the mermaid.ink API for all diagram generation (`.mmd` files):

1. **Mermaid.ink API**: Cloud-based diagram generation from `.mmd` files
2. **Direct PNG/SVG Output**: No local conversion needed
3. **Enhanced Font Support**: Consistent rendering across all platforms

**Architecture Support:**
1. **AMD64 systems**: Native performance with multi-architecture Docker images
2. **Apple Silicon Macs**: Native ARM64 performance (no emulation needed)
3. **ARM64 Linux**: Native ARM64 performance with full feature parity

### Performance Considerations

- **Cloud-Based Processing**: Mermaid.ink API provides consistent results across all architectures
- **No Browser Overhead**: Eliminated Chrome/Chromium dependencies reduce memory usage and startup time
- **Multi-Platform Builds**: Native Docker images for both AMD64 and ARM64 architectures

### Recommendations by Platform

**All Platforms (AMD64 & ARM64):**
```bash
# Docker mode with native performance on all architectures
make pdf RXIV_ENGINE=DOCKER

# Local installation (requires system dependencies)
make setup && make pdf
```

**Key Benefits of Docker Mode:**
- **Consistent Results**: Same output across all platforms and environments
- **Minimal Dependencies**: Only Docker required (no LaTeX, R, Node.js installation)
- **API Performance**: Fast diagram generation via mermaid.ink API
- **No Emulation**: ARM64 images run natively on Apple Silicon and ARM64 Linux

---

## Overview

### What is Docker Engine Mode?

Docker Engine Mode (`RXIV_ENGINE=DOCKER`) runs Rxiv-Maker commands inside containers that include all necessary dependencies:

- **LaTeX** - Complete TeX Live distribution with all packages
- **Python** - Python 3.11 with scientific libraries (matplotlib, numpy, pandas, etc.)
- **R** - R base with graphics support (ggplot2, svglite, etc.)
- **Node.js** - Node.js 18 (mermaid-cli not needed with mermaid.ink API)
- **System tools** - Fonts and SVG processing tools

### Key Advantages

- ✅ **Minimal local dependencies** - Only Docker and Make required (no LaTeX, R, or Python installation needed)
- ✅ **Cross-platform consistency** - Identical output on all architectures via mermaid.ink API
- ✅ **Reproducible builds** - Guaranteed dependency versions
- ✅ **No conflicts** - Isolated from local installations, no browser dependencies
- ✅ **Fast CI/CD** - Pre-compiled images accelerate workflows by ~5x
- ✅ **Enhanced performance** - Cloud-based processing reduces local resource usage

---

## Quick Start

### Prerequisites
- Docker installed and running on your system
- Git for cloning the repository

### 1. Install Docker
Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop) for your platform.

### 2. Clone and Use
```bash
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Generate PDF immediately (no local setup required)
make pdf RXIV_ENGINE=DOCKER

# Validate manuscript
make validate RXIV_ENGINE=DOCKER

# Run tests
make test RXIV_ENGINE=DOCKER
```

That's it! No Python virtual environments, no LaTeX installation, no dependency management.

---

## Installation & Setup

### Docker Installation

#### Windows
1. Download Docker Desktop for Windows from [docker.com](https://www.docker.com/products/docker-desktop)
2. Install and start Docker Desktop
3. Ensure WSL 2 is enabled for optimal performance

#### macOS
1. Download Docker Desktop for Mac (Intel or Apple Silicon)
2. Install and start Docker Desktop
3. Grant necessary permissions when prompted

#### Linux
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

### Verify Installation
```bash
# Check Docker is running
docker --version
docker info

# Test Docker functionality
docker run hello-world
```

### Set Default Mode (Optional)
Make Docker mode the default for your session:
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export RXIV_ENGINE=DOCKER

# Now all commands use Docker automatically
make pdf        # Runs in container
make validate   # Runs in container
```

---

## Usage Examples

### Basic Commands
```bash
# PDF generation
make pdf RXIV_ENGINE=DOCKER

# Manuscript validation
make validate RXIV_ENGINE=DOCKER

# Figure generation with forcing
make pdf RXIV_ENGINE=DOCKER FORCE_FIGURES=true

# Clean outputs
make clean RXIV_ENGINE=DOCKER
```

### Custom Manuscript Paths
```bash
# Use different manuscript directory
MANUSCRIPT_PATH=MY_PAPER RXIV_ENGINE=DOCKER make pdf

# Multiple environment variables
MANUSCRIPT_PATH=research/paper1 RXIV_ENGINE=DOCKER make validate
```

### Advanced Workflows
```bash
# Complete workflow in Docker
export RXIV_ENGINE=DOCKER
make validate           # Check for issues
make pdf               # Generate PDF
make arxiv             # Prepare arXiv submission
```

### Testing and Development
```bash
# Run all tests in container
make test RXIV_ENGINE=DOCKER

# Run specific test categories
make test-unit RXIV_ENGINE=DOCKER
make test-integration RXIV_ENGINE=DOCKER

# Linting and formatting
make lint RXIV_ENGINE=DOCKER
make format RXIV_ENGINE=DOCKER
```

---

## Configuration

### Environment Variables

#### Core Configuration
```bash
# Engine mode selection
RXIV_ENGINE=DOCKER                    # Enable Docker mode (default: LOCAL)

# Docker image configuration
DOCKER_IMAGE=henriqueslab/rxiv-maker-base:latest  # Docker image to use
DOCKER_HUB_REPO=henriqueslab/rxiv-maker-base      # Repository name

# Platform targeting (auto-detected)
DOCKER_PLATFORM=linux/amd64          # Force specific platform
DOCKER_PLATFORM=linux/arm64          # For Apple Silicon
```

#### Manuscript Configuration
```bash
# Standard Rxiv-Maker variables work with Docker
MANUSCRIPT_PATH=path/to/manuscript    # Custom manuscript location
FORCE_FIGURES=true                   # Force figure regeneration
VERBOSE=true                         # Enable verbose output
```

### Custom Docker Images
```bash
# Use custom Docker image
DOCKER_IMAGE=myregistry/rxiv-custom:tag RXIV_ENGINE=DOCKER make pdf

# Use development image
DOCKER_IMAGE=henriqueslab/rxiv-maker-base:dev RXIV_ENGINE=DOCKER make pdf
```

### Persistent Configuration
Create a `.env` file in your project root:
```bash
# .env file
RXIV_ENGINE=DOCKER
DOCKER_IMAGE=henriqueslab/rxiv-maker-base:latest
MANUSCRIPT_PATH=my-paper
```

---

## Benefits & Use Cases

### Research Scenarios

#### Multi-Platform Collaboration
**Problem**: Team members use different operating systems with varying LaTeX installations.
**Solution**: Docker engine mode ensures identical builds regardless of host platform.

```bash
# Same command works identically on Windows, macOS, Linux
make pdf RXIV_ENGINE=DOCKER
```

#### Reproducible Research
**Problem**: Need to guarantee exact same output months or years later.
**Solution**: Docker images provide frozen dependency versions.

```bash
# Use specific versioned image for long-term reproducibility
DOCKER_IMAGE=henriqueslab/rxiv-maker-base:v1.4 RXIV_ENGINE=DOCKER make pdf
```

#### CI/CD Integration
**Problem**: GitHub Actions builds are slow due to dependency installation.
**Solution**: Pre-compiled Docker images accelerate workflows.

```yaml
# In .github/workflows/build-pdf.yml
container: henriqueslab/rxiv-maker-base:latest
# Build time: ~2 minutes vs. ~10 minutes with dependency installation
```

#### Clean Development Environment
**Problem**: Don't want to install LaTeX and R libraries system-wide.
**Solution**: Containerized execution keeps host system clean.

```bash
# No local LaTeX installation required
make pdf RXIV_ENGINE=DOCKER
```

### Performance Benefits

#### Build Speed Comparison
| Environment | Dependency Install | Build Time | Total Time |
|-------------|-------------------|------------|------------|
| Local (first time) | 5-15 minutes | 1-2 minutes | 6-17 minutes |
| Local (subsequent) | 0 minutes | 1-2 minutes | 1-2 minutes |
| Docker (first pull) | 2-3 minutes | 1-2 minutes | 3-5 minutes |
| Docker (subsequent) | 0 minutes | 1-2 minutes | 1-2 minutes |
| GitHub Actions (old) | 8-10 minutes | 1-2 minutes | 9-12 minutes |
| GitHub Actions (Docker) | 30 seconds | 1-2 minutes | 2-3 minutes |

#### Resource Usage
- **Memory**: Similar to local execution (~1-2GB during build)
- **Disk**: Docker image ~5GB (one-time download)
- **CPU**: Equivalent performance to local execution

---

## Troubleshooting

### Common Issues

#### Docker Not Running
**Symptoms**: `docker: command not found` or `Cannot connect to Docker daemon`
```bash
# Check Docker status
docker --version
docker info

# Start Docker Desktop (Windows/macOS)
# Start Docker service (Linux)
sudo systemctl start docker
```

#### Image Pull Failures
**Symptoms**: `Error response from daemon: pull access denied`
```bash
# Check internet connection
ping docker.io

# Try manual pull (latest version)
docker pull henriqueslab/rxiv-maker-base:latest

# Or pull specific version (recommended for reproducibility)
docker pull henriqueslab/rxiv-maker-base:v1.4.8

# Use alternative registry if needed
DOCKER_IMAGE=ghcr.io/henriqueslab/rxiv-maker-base:latest RXIV_ENGINE=DOCKER make pdf
```

#### Platform Warnings
**Symptoms**: `WARNING: The requested image's platform does not match`
```bash
# Force platform match
DOCKER_PLATFORM=linux/amd64 RXIV_ENGINE=DOCKER make pdf

# For Apple Silicon
DOCKER_PLATFORM=linux/arm64 RXIV_ENGINE=DOCKER make pdf
```

#### Permission Issues
**Symptoms**: Generated files owned by root, cannot edit
```bash
# Fix file ownership (Linux/macOS)
sudo chown -R $(whoami):$(whoami) output/

# Use user namespace mapping (advanced)
docker run --user $(id -u):$(id -g) ...
```

#### Out of Disk Space
**Symptoms**: `no space left on device` during build
```bash
# Clean up Docker resources
docker system prune -f

# Remove unused images
docker image prune -f

# Check disk usage
docker system df
```

### Performance Issues

#### Slow First Run
Docker needs to download the image (~5GB) on first use:
```bash
# Pre-pull image to avoid delays
docker pull henriqueslab/rxiv-maker-base:latest

# Monitor download progress
docker pull henriqueslab/rxiv-maker-base:latest --progress=plain
```

#### Memory Constraints
For large manuscripts or complex figures:
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or use Docker CLI with memory limits
docker run --memory=8g ...
```

### Debugging Commands

#### Check Container Status
```bash
# Verify image exists locally
docker images henriqueslab/rxiv-maker-base

# Test container functionality
docker run --rm henriqueslab/rxiv-maker-base:latest python --version
docker run --rm henriqueslab/rxiv-maker-base:latest pdflatex --version
```

#### Inspect Build Logs
```bash
# Run with verbose output
make pdf RXIV_ENGINE=DOCKER VERBOSE=true

# Get detailed Docker logs
make pdf RXIV_ENGINE=DOCKER 2>&1 | tee build.log
```

#### Interactive Debugging
```bash
# Start interactive container session (latest)
docker run -it --rm -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest bash

# Or use specific version for debugging
docker run -it --rm -v $(pwd):/workspace henriqueslab/rxiv-maker-base:v1.4.8 bash

# Inside container, run commands manually
rxiv validate MANUSCRIPT
```

---

## Advanced Topics

### Custom Docker Images

#### Building Custom Images
```bash
# Navigate to Docker directory
cd src/docker/images/base

# Build custom image
./build.sh --repo myuser/rxiv-custom --tag latest

# Use custom image
DOCKER_IMAGE=myuser/rxiv-custom:latest RXIV_ENGINE=DOCKER make pdf
```

#### Extending Base Image
Create a custom Dockerfile:
```dockerfile
FROM henriqueslab/rxiv-maker-base:latest

# Add custom packages
RUN apt-get update && apt-get install -y my-package

# Add custom Python packages
RUN pip install my-custom-package

# Add custom LaTeX packages
RUN tlmgr install my-latex-package
```

### Volume Mounting Strategies

#### Custom Mount Points
```bash
# Mount external data directory
docker run --rm \
  -v $(pwd):/workspace \
  -v /path/to/data:/data \
  -w /workspace \
  henriqueslab/rxiv-maker-base:latest \
  python script.py
```

#### Preserving Cache
```bash
# Preserve package manager cache between runs
docker run --rm \
  -v $(pwd):/workspace \
  -v rxiv-cache:/root/.cache \
  -w /workspace \
  henriqueslab/rxiv-maker-base:latest \
  make pdf
```

### Multi-Platform Development

#### Building for Multiple Architectures
```bash
cd src/docker/images/base

# Build for both amd64 and arm64
./build.sh --platform linux/amd64,linux/arm64

# Build platform-specific images
./build.sh --platform linux/amd64  # Intel/AMD processors
./build.sh --platform linux/arm64  # Apple Silicon
```

#### Platform-Specific Optimization
```bash
# Force specific platform for consistency
export DOCKER_PLATFORM=linux/amd64
make pdf RXIV_ENGINE=DOCKER

# Let Docker auto-detect optimal platform
unset DOCKER_PLATFORM
make pdf RXIV_ENGINE=DOCKER
```

### Integration with Development Tools

#### VS Code Integration
1. Install Docker extension for VS Code
2. Use integrated terminal with Docker engine mode:
```bash
export RXIV_ENGINE=DOCKER
make pdf  # Runs in container from VS Code terminal
```

#### Git Hooks Integration
```bash
# .git/hooks/pre-commit
#!/bin/bash
export RXIV_ENGINE=DOCKER
make validate || exit 1
```

### Production Deployment

#### Continuous Integration
```yaml
# .github/workflows/build-pdf.yml
name: Build PDF
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    container: henriqueslab/rxiv-maker-base:latest
    steps:
      - uses: actions/checkout@v4
      - name: Build PDF
        run: make pdf
```

#### Automated Versioning
```bash
# Use git tags for image versions
git tag v1.0.0
DOCKER_IMAGE=henriqueslab/rxiv-maker-base:v1.0.0 RXIV_ENGINE=DOCKER make pdf
```

---

## Conclusion

Docker Engine Mode transforms Rxiv-Maker from a complex multi-dependency system into a simple, portable tool that runs anywhere Docker is available. It provides the perfect balance of ease-of-use, reproducibility, and performance for modern scientific workflows.

**Next Steps:**
- Try Docker mode with your existing manuscripts
- Set up automated workflows with GitHub Actions
- Explore custom Docker images for specialized requirements
- Share reproducible builds with collaborators

**Related Documentation:**
- [Command Reference](../reference/commands.md) - Complete command documentation
- [User Guide](../getting-started/user_guide.md) - Complete usage instructions  
- [GitHub Actions Guide](github-actions.md) - Automated cloud builds
- [Local Development Setup](../platforms/LOCAL_DEVELOPMENT.md) - Platform-specific installation
- [Docker Official Documentation](https://docs.docker.com/) - Docker reference