# 🐳 Container Development

For users who prefer containerized environments or need isolated dependencies, **docker-rxiv-maker** provides pre-built Docker containers with all dependencies included.

## 🚀 Quick Start

```bash
# Pull the latest image
docker pull henriqueslab/rxiv-maker-base:latest

# Generate PDF
docker run -v $(pwd):/workspace -w /workspace henriqueslab/rxiv-maker-base:latest rxiv pdf

# Validate manuscript
docker run -v $(pwd):/workspace -w /workspace henriqueslab/rxiv-maker-base:latest rxiv validate
```

## 🛠️ Setup

### Prerequisites
- Docker Desktop or Docker Engine
- Your manuscript files in the current directory

### Installation
No installation required! The container includes:
- ✅ Latest rxiv-maker
- ✅ Complete LaTeX distribution
- ✅ Python, R, and Node.js environments
- ✅ All required dependencies

## 📖 Complete Documentation

For comprehensive setup, CI/CD integration, and advanced usage:

**📖 [docker-rxiv-maker Repository →](https://github.com/HenriquesLab/docker-rxiv-maker)**

## 🔄 When to Use Containers

### **Use Containers When:**
- Setting up dependencies is challenging on your system
- You need reproducible builds across different environments
- Working in CI/CD pipelines
- Contributing to rxiv-maker development without system setup

### **Use Standard Installation When:**
- You want the fastest build times
- You prefer working with native tools
- You need to customize the build environment
- You're doing active development on rxiv-maker itself

## 📋 Common Usage Patterns

### Development Workflow
```bash
# Create alias for convenience
alias rxiv-docker='docker run -v $(pwd):/workspace -w /workspace henriqueslab/rxiv-maker-base:latest rxiv'

# Use like normal rxiv commands
rxiv-docker validate
rxiv-docker pdf
rxiv-docker clean
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Generate PDF
  run: |
    docker run -v ${{ github.workspace }}:/workspace -w /workspace \
      henriqueslab/rxiv-maker-base:latest rxiv pdf
```

### Batch Processing
```bash
# Process multiple manuscripts
for dir in manuscript_*/; do
  echo "Processing $dir"
  docker run -v $(pwd)/$dir:/workspace -w /workspace \
    henriqueslab/rxiv-maker-base:latest rxiv pdf
done
```

## 🚨 Troubleshooting

### Permission Issues
```bash
# Fix file ownership after container run
sudo chown -R $(id -u):$(id -g) .
```

### Volume Mounting
```bash
# Ensure your manuscript directory is properly mounted
docker run -v "$(pwd)":/workspace -w /workspace \
  henriqueslab/rxiv-maker-base:latest rxiv pdf
```

### Windows Users
```powershell
# Use PowerShell syntax for volume mounting
docker run -v ${PWD}:/workspace -w /workspace henriqueslab/rxiv-maker-base:latest rxiv pdf
```

## 🔗 Related Resources

- **[Installation Guide](installation.md)** - Standard installation
- **[Troubleshooting](troubleshooting.md)** - Common issues