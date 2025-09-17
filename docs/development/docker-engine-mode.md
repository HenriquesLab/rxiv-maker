# Docker Engine Mode - Deprecated

> **⚠️ Important Notice**: Docker and Podman engines have been **deprecated** in rxiv-maker as of version 2.5.0. For containerized execution, please use the dedicated [docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker) repository instead.

## 🐳 Current Docker Solutions

### Recommended: docker-rxiv-maker Repository
The **[docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker)** repository provides:

- **Pre-built Docker images** with all dependencies
- **Weekly automated builds** ensuring latest rxiv-maker version
- **Cross-platform support** (AMD64 and ARM64)
- **Faster startup times** (~2-3s vs 30-60s)
- **Terminal-focused workflow** for direct usage

```bash
# Quick Docker usage with docker-rxiv-maker
docker pull henriqueslab/rxiv-maker-base:latest
docker run -v $(pwd):/workspace -w /workspace henriqueslab/rxiv-maker-base:latest rxiv pdf
```

**📖 [Complete Docker Documentation →](https://github.com/HenriquesLab/docker-rxiv-maker)**

### Local Development (Recommended)
For most users, **local installation** is now the preferred method:

```bash
# Install locally (fastest and most reliable)
pipx install rxiv-maker
rxiv check-installation
```

**📖 [Local Installation Guide →](../quick-start/installation.md)**

## ❓ Why Was Docker Mode Deprecated?

1. **Complexity**: Docker engine required significant maintenance overhead
2. **Performance**: Local execution is 3-5x faster for most workflows
3. **Dependencies**: Modern LaTeX distributions are easier to install locally
4. **Separation of Concerns**: Dedicated docker-rxiv-maker provides better container support

## 🔄 Migration Guide

### From Docker Engine Mode
If you were using rxiv-maker's built-in Docker engine:

```bash
# Old approach (deprecated)
rxiv pdf --engine docker

# New approach: Use docker-rxiv-maker
docker run -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest rxiv pdf
```

### From Local Make Commands
If you were using legacy Make commands with Docker:

```bash
# Old approach
RXIV_ENGINE=DOCKER make pdf

# New approach: Use docker-rxiv-maker
docker run -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest rxiv pdf
```

## 🛠️ Development Workflows

### For Contributors
Contributors should use **local development** for the main repository:

```bash
# Setup local development
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker
pip install -e ".[dev]"
pre-commit install
```

**📖 [Developer Guide →](developer-guide.md)**

### For Container Testing
Use the docker-rxiv-maker repository for containerized testing:

```bash
# Clone docker-rxiv-maker for container development
git clone https://github.com/HenriquesLab/docker-rxiv-maker.git
cd docker-rxiv-maker
# Follow docker-rxiv-maker documentation
```

## 🔗 Related Resources

- **[docker-rxiv-maker Repository](https://github.com/HenriquesLab/docker-rxiv-maker)** - Dedicated Docker infrastructure
- **[Local Installation Guide](../quick-start/installation.md)** - Recommended local setup
- **[Troubleshooting](../troubleshooting/troubleshooting.md)** - Common installation issues
- **[Developer Guide](developer-guide.md)** - Contributing to rxiv-maker

---

**💡 Need Help?**
- **Docker Issues**: [docker-rxiv-maker Issues](https://github.com/HenriquesLab/docker-rxiv-maker/issues)
- **General Issues**: [rxiv-maker Discussions](https://github.com/henriqueslab/rxiv-maker/discussions)