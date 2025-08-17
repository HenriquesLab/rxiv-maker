# Podman Engine Mode Guide (Cross-Platform)

Podman Engine Mode provides a **rootless and secure** approach to using Rxiv-Maker by running all operations inside containers without requiring daemon privileges. As a Docker-compatible alternative, Podman eliminates the need to install LaTeX, R, Node.js, or Python packages locally while providing enhanced security and performance benefits over traditional container solutions.

**✅ SECURITY-FIRST:** Podman runs containers without root privileges and doesn't require a daemon, making it ideal for academic environments, HPC clusters, and security-conscious workflows.

## Table of Contents
- [Architecture & Security](#architecture--security)
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation & Setup](#installation--setup)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Benefits & Use Cases](#benefits--use-cases)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Architecture & Security

### Supported Platforms
- **✅ Linux**: Native support with optimal performance and full rootless capabilities
- **✅ macOS**: Via Podman Desktop with Linux VM integration
- **✅ Windows**: Via Podman Desktop with WSL2 integration

### Security Model: Rootless Containers

Podman's architecture provides significant security advantages:

1. **No Daemon**: Unlike Docker, Podman doesn't require a privileged daemon
2. **Rootless Operation**: Containers run with user privileges, not root
3. **Enhanced Isolation**: User namespaces provide additional container isolation
4. **Academic-Friendly**: Ideal for shared systems and HPC environments

**Security Benefits:**
- **No Privilege Escalation**: Containers can't gain root access to host
- **User Namespace Mapping**: Container root maps to unprivileged user
- **Daemon-Free**: No background service with root privileges
- **SELinux Integration**: Enhanced security on supported systems

### Performance Characteristics

- **Memory Efficiency**: Lower overhead without persistent daemon
- **Startup Speed**: Faster container startup (no daemon communication)
- **Resource Isolation**: Better resource management with cgroups v2
- **HPC Compatibility**: Designed for multi-user environments

---

## Overview

### What is Podman Engine Mode?

Podman Engine Mode (`RXIV_ENGINE=PODMAN`) runs Rxiv-Maker commands inside rootless containers that include all necessary dependencies:

- **LaTeX** - Complete TeX Live distribution with all packages
- **Python** - Python 3.11 with scientific libraries (matplotlib, numpy, pandas)
- **R** - R base with graphics support (ggplot2, svglite)
- **Node.js** - Node.js 18 for web-based processing
- **System tools** - Fonts and SVG processing tools

### Key Advantages over Docker

- ✅ **Enhanced Security** - Rootless containers, no daemon required
- ✅ **Academic Environment Friendly** - Works on shared systems without admin rights
- ✅ **Better Resource Management** - Improved memory and CPU isolation
- ✅ **HPC Compatible** - Designed for multi-user computing environments
- ✅ **Docker Compatibility** - Drop-in replacement for Docker workflows
- ✅ **Faster Cold Starts** - No daemon overhead

---

## Quick Start

### Prerequisites
- Podman installed on your system
- Git for cloning the repository

### 1. Install Podman

#### Linux (Recommended)
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y podman

# Fedora/RHEL/CentOS
sudo dnf install podman

# Arch Linux
sudo pacman -S podman
```

#### macOS/Windows
Download Podman Desktop from [podman-desktop.io](https://podman-desktop.io/)

### 2. Clone and Use
```bash
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Generate PDF immediately (no local setup required)
make pdf RXIV_ENGINE=PODMAN

# Validate manuscript
make validate RXIV_ENGINE=PODMAN

# Run tests
make test RXIV_ENGINE=PODMAN
```

That's it! No Python virtual environments, no LaTeX installation, no daemon configuration.

---

## Installation & Setup

### Platform-Specific Installation

#### Linux (Native Rootless Setup)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y podman uidmap slirp4netns

# Configure rootless mode
podman system migrate
echo "$USER:100000:65536" | sudo tee /etc/subuid
echo "$USER:100000:65536" | sudo tee /etc/subgid

# Enable linger for rootless containers
sudo loginctl enable-linger $USER

# Start user services
systemctl --user enable --now podman.socket
```

#### macOS
```bash
# Install via Homebrew
brew install podman

# Or download Podman Desktop
# https://podman-desktop.io/downloads/macos

# Initialize Podman machine
podman machine init
podman machine start
```

#### Windows
```bash
# Install via Chocolatey
choco install podman-desktop

# Or download installer from podman-desktop.io
# Enable WSL2 integration during setup
```

### Verify Installation
```bash
# Check Podman version
podman --version

# Test rootless operation
podman info --format "{{.Host.Security.Rootless}}"
# Should return: true

# Test container functionality
podman run --rm hello-world
```

### Configure for Rxiv-Maker
```bash
# Set default engine mode
export RXIV_ENGINE=PODMAN

# Add to shell profile for persistence
echo 'export RXIV_ENGINE=PODMAN' >> ~/.bashrc  # or ~/.zshrc

# Test with Rxiv-Maker
make pdf        # Runs in rootless container
```

---

## Usage Examples

### Basic Commands
```bash
# PDF generation with Podman
make pdf RXIV_ENGINE=PODMAN

# Manuscript validation
make validate RXIV_ENGINE=PODMAN

# Figure generation with forcing
make pdf RXIV_ENGINE=PODMAN FORCE_FIGURES=true

# Clean outputs
make clean RXIV_ENGINE=PODMAN
```

### Security-Enhanced Workflows
```bash
# Run with additional security constraints
PODMAN_EXTRA_ARGS="--security-opt no-new-privileges:true" make pdf RXIV_ENGINE=PODMAN

# Use read-only root filesystem
PODMAN_EXTRA_ARGS="--read-only --tmpfs /tmp" make validate RXIV_ENGINE=PODMAN

# Limit system resources
PODMAN_EXTRA_ARGS="--memory=1g --cpus=1.0" make pdf RXIV_ENGINE=PODMAN
```

### Multi-User Environment Usage
```bash
# Each user gets isolated containers
user1$ make pdf RXIV_ENGINE=PODMAN  # Runs as user1
user2$ make pdf RXIV_ENGINE=PODMAN  # Runs as user2 (completely isolated)

# HPC cluster usage
srun --partition=compute make pdf RXIV_ENGINE=PODMAN
```

### Advanced Workflows
```bash
# Complete workflow with rootless containers
export RXIV_ENGINE=PODMAN
make validate           # Security-enhanced validation
make pdf               # Rootless PDF generation
make arxiv             # Prepare arXiv submission
```

---

## Configuration

### Environment Variables

#### Core Podman Configuration
```bash
# Engine mode selection
RXIV_ENGINE=PODMAN                    # Enable Podman mode (default: LOCAL)

# Container image configuration
PODMAN_IMAGE=henriqueslab/rxiv-maker-base:latest  # Container image to use
PODMAN_EXTRA_ARGS="--security-opt label=disable"  # Additional Podman arguments

# Platform targeting (auto-detected)
PODMAN_PLATFORM=linux/amd64          # Force specific platform
PODMAN_PLATFORM=linux/arm64          # For Apple Silicon
```

#### Security Configuration
```bash
# Enhanced security settings
PODMAN_EXTRA_ARGS="--security-opt no-new-privileges:true --cap-drop ALL --cap-add SETUID,SETGID"

# Read-only root filesystem
PODMAN_EXTRA_ARGS="--read-only --tmpfs /tmp --tmpfs /var/tmp"

# Resource limiting
PODMAN_EXTRA_ARGS="--memory=2g --cpus=2.0 --pids-limit=100"
```

#### Academic Environment Configuration
```bash
# HPC cluster configuration
PODMAN_EXTRA_ARGS="--userns keep-id --group-add keep-groups"

# Shared storage mounting
PODMAN_EXTRA_ARGS="--volume /shared/data:/data:ro"

# Network isolation
PODMAN_EXTRA_ARGS="--network none"  # For air-gapped environments
```

### Persistent Configuration

Create a `.env` file in your project root:
```bash
# .env file for Podman mode
RXIV_ENGINE=PODMAN
PODMAN_IMAGE=henriqueslab/rxiv-maker-base:latest
PODMAN_EXTRA_ARGS=--security-opt no-new-privileges:true
MANUSCRIPT_PATH=my-paper
```

Create Podman-specific configuration:
```bash
# ~/.config/containers/containers.conf
[containers]
default_ulimits = [
  "nofile=1024:2048",
]
netns = "bridge"
userns = "auto"
```

---

## Benefits & Use Cases

### Academic & Research Scenarios

#### Multi-User HPC Environments
**Problem**: Need containerized workflows on shared systems without root access.
**Solution**: Podman's rootless design works perfectly on HPC clusters.

```bash
# Each user runs isolated containers without conflicting
user@cluster:~$ make pdf RXIV_ENGINE=PODMAN
# No daemon conflicts, no permission issues
```

#### Security-Conscious Institutions
**Problem**: Docker daemon poses security risks for shared academic systems.
**Solution**: Podman eliminates daemon-based vulnerabilities.

```bash
# Rootless execution with enhanced security
PODMAN_EXTRA_ARGS="--security-opt no-new-privileges:true" make pdf RXIV_ENGINE=PODMAN
```

#### Reproducible Research with Enhanced Security
**Problem**: Need both reproducibility and security compliance.
**Solution**: Podman provides containers with academic-grade security.

```bash
# Reproducible builds with security constraints
PODMAN_IMAGE=henriqueslab/rxiv-maker-base:v1.4 RXIV_ENGINE=PODMAN make pdf
```

### Performance & Security Benefits

#### Resource Management Comparison
| Feature | Docker | Podman | Benefit |
|---------|--------|--------|---------|
| Daemon overhead | High | None | Lower memory usage |
| Root privileges | Required | Optional | Enhanced security |
| User namespace | Limited | Native | Better isolation |
| Startup time | ~2-3s | ~1-2s | Faster execution |
| Security model | Daemon-based | Process-based | Reduced attack surface |

#### Security Model Comparison
| Security Aspect | Docker | Podman | Academic Advantage |
|----------------|--------|--------|-------------------|
| Root requirements | Daemon needs root | Fully rootless | HPC compatible |
| Container escape | Possible via daemon | Limited scope | Safer for shared systems |
| Privilege escalation | Via socket | Not possible | Institutional compliance |
| SELinux integration | Basic | Advanced | Research data protection |

---

## Troubleshooting

### Common Issues

#### Podman Not Available
**Symptoms**: `podman: command not found` or `Podman is not available`
```bash
# Check Podman installation
podman --version
podman info

# Install on Linux
sudo apt-get install podman  # Debian/Ubuntu
sudo dnf install podman      # Fedora/RHEL

# Start Podman machine (macOS/Windows)
podman machine start
```

#### Rootless Configuration Issues
**Symptoms**: `Error: cannot setup namespace: user namespaces are not enabled`
```bash
# Check rootless configuration
podman info --format "{{.Host.Security.Rootless}}"

# Configure subuid/subgid (Linux)
echo "$USER:100000:65536" | sudo tee -a /etc/subuid
echo "$USER:100000:65536" | sudo tee -a /etc/subgid

# Restart user session
podman system migrate
```

#### Image Pull Failures
**Symptoms**: `Error: error pulling image` or registry access issues
```bash
# Check registry configuration
podman info --format "{{.Registries}}"

# Add Docker Hub registry
echo 'unqualified-search-registries = ["docker.io"]' | sudo tee -a /etc/containers/registries.conf

# Manual image pull
podman pull docker.io/henriqueslab/rxiv-maker-base:latest
```

#### Permission Issues
**Symptoms**: Generated files have wrong ownership
```bash
# Check user namespace mapping
podman unshare cat /proc/self/uid_map

# Fix file ownership (automatically handled in rootless mode)
# Files are created with correct user ownership

# For persistent volumes
podman run --userns keep-id --volume $(pwd):/workspace ...
```

### Performance Issues

#### Slow Network Access
**Symptoms**: Slow image pulls or network operations
```bash
# Configure faster DNS
echo 'dns_servers = ["8.8.8.8", "8.8.4.4"]' >> ~/.config/containers/containers.conf

# Use local registry mirror
podman pull localhost:5000/henriqueslab/rxiv-maker-base:latest
```

#### Resource Constraints
**Symptoms**: Out of memory or CPU limitations
```bash
# Increase user limits
echo "$USER soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "$USER hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Configure cgroups v2 (modern systems)
echo 'cgroup_manager = "systemd"' >> ~/.config/containers/containers.conf
```

### Debugging Commands

#### Check Rootless Status
```bash
# Verify rootless operation
podman info --format "{{.Host.Security.Rootless}}"
podman unshare id

# Check namespace configuration
podman info --format "{{.Host.IDMappings}}"
```

#### Test Container Functionality
```bash
# Basic functionality test
podman run --rm henriqueslab/rxiv-maker-base:latest python --version

# Security test
podman run --rm --security-opt no-new-privileges:true henriqueslab/rxiv-maker-base:latest id

# Network test
podman run --rm henriqueslab/rxiv-maker-base:latest ping -c1 google.com
```

#### Interactive Debugging
```bash
# Start interactive rootless container
podman run -it --rm --volume $(pwd):/workspace:Z henriqueslab/rxiv-maker-base:latest bash

# Check security context
podman run --rm henriqueslab/rxiv-maker-base:latest cat /proc/self/status | grep -i cap
```

---

## Advanced Topics

### Rootless Container Optimization

#### User Namespace Configuration
```bash
# Optimize namespace mapping
echo "$USER:100000:65536" | sudo tee /etc/subuid
echo "$USER:100000:65536" | sudo tee /etc/subgid

# Enable lingering for persistent services
sudo loginctl enable-linger $USER

# Configure automatic cleanup
echo 'stop_timeout = 10' >> ~/.config/containers/containers.conf
```

#### Resource Management
```bash
# Configure cgroups v2 for better resource control
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/podman-resource.slice << EOF
[Unit]
Description=Podman Resource Management Slice

[Slice]
MemoryMax=4G
CPUQuota=200%
EOF

# Enable user slice
systemctl --user daemon-reload
systemctl --user enable podman-resource.slice
```

### Security Hardening

#### SELinux Integration
```bash
# Enable SELinux for containers (Linux)
setsebool -P container_manage_cgroup on

# Use SELinux labels for volumes
podman run --volume $(pwd):/workspace:Z henriqueslab/rxiv-maker-base:latest
```

#### Custom Security Profiles
```bash
# Create restricted security profile
cat > ~/.config/containers/seccomp.json << EOF
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "execve"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# Use custom profile
PODMAN_EXTRA_ARGS="--security-opt seccomp=~/.config/containers/seccomp.json" make pdf RXIV_ENGINE=PODMAN
```

### HPC Integration

#### SLURM Integration
```bash
# SLURM job script for Podman
#!/bin/bash
#SBATCH --job-name=rxiv-build
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

# Load user environment
source ~/.bashrc

# Run Podman rootless
export RXIV_ENGINE=PODMAN
make pdf MANUSCRIPT_PATH=$MANUSCRIPT
```

#### Singularity Conversion
```bash
# Convert Podman container to Singularity for HPC
podman save henriqueslab/rxiv-maker-base:latest | singularity build rxiv-maker.sif docker-archive:/dev/stdin

# Use with Singularity
singularity exec rxiv-maker.sif rxiv pdf MANUSCRIPT
```

### Podman Desktop Integration

#### GUI Management
1. Install Podman Desktop from [podman-desktop.io](https://podman-desktop.io/)
2. Configure container resources through GUI
3. Monitor Rxiv-Maker containers in real-time
4. Manage images and volumes visually

#### IDE Integration
```bash
# VS Code with Podman extension
code --install-extension ms-vscode-remote.remote-containers

# Configure for Podman in settings.json
{
  "dev.containers.dockerPath": "podman",
  "dev.containers.dockerComposePath": "podman-compose"
}
```

---

## Conclusion

Podman Engine Mode represents the future of secure containerized workflows for academic research. By eliminating the need for privileged daemons while maintaining full Docker compatibility, Podman provides the perfect balance of security, performance, and usability for modern scientific computing environments.

**Key Advantages:**
- **Enhanced Security**: Rootless containers with user namespace isolation
- **Academic-Friendly**: Works on HPC clusters and shared systems
- **Docker Compatible**: Drop-in replacement for existing workflows
- **Better Performance**: Lower overhead and faster startup times

**Next Steps:**
- Migrate existing Docker workflows to Podman
- Implement rootless containers in your HPC environment
- Explore advanced security configurations for institutional compliance
- Share secure, reproducible workflows with collaborators

**Related Documentation:**
- [Docker Engine Mode](docker-engine-mode.md) - Docker comparison and migration
- [Command Reference](../reference/commands.md) - Complete command documentation
- [Security Guide](../security/SECURITY.md) - Security best practices
- [HPC Integration](../platforms/LOCAL_DEVELOPMENT.md) - Platform-specific setup
- [Podman Official Documentation](https://docs.podman.io/) - Podman reference