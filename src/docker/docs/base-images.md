# Rxiv-Maker Docker Base Image

This directory contains the Docker configuration for the Rxiv-Maker base image, which is designed to accelerate GitHub Actions workflows by pre-installing all system dependencies.

## Overview

The Docker base image includes:
- **Ubuntu 22.04** as the base operating system
- **Complete LaTeX distribution** (texlive-full with all packages)
- **Python 3.11** with essential tools
- **Node.js 18 LTS** with Mermaid CLI
- **R base** with system libraries
- **System dependencies** for graphics, fonts, and development

**What's NOT included:**
- Rxiv-maker Python code or dependencies
- User manuscripts or data
- Project-specific configurations

## Quick Start

### Building the Image

```bash
# Build and push to Docker Hub
cd src/docker
./build.sh

# Build locally only
./build.sh --local

# Build with specific tag
./build.sh --tag v1.0
```

### Using the Image

```bash
# Run interactively
docker run -it rxivmaker/base:latest

# Mount current directory for development
docker run -it --rm -v $(pwd):/workspace rxivmaker/base:latest

# Use in GitHub Actions
container: rxivmaker/base:latest
```

## File Structure

```
src/docker/
├── Dockerfile          # Multi-stage build configuration
├── .dockerignore       # Excludes all rxiv-maker code
├── build.sh            # Build and deployment script
└── README.md           # This documentation
```

## Dockerfile Architecture

The Dockerfile uses a multi-stage build approach for optimization:

1. **base** - Ubuntu 22.04 with essential configuration
2. **system-deps** - System libraries and development tools
3. **latex-deps** - Complete LaTeX distribution
4. **python-deps** - Python 3.11 and tools
5. **nodejs-deps** - Node.js 18 and Mermaid CLI
6. **r-deps** - R base with system libraries
7. **final** - Optimized final image with security hardening

## Build Script Options

The `build.sh` script supports various options:

```bash
./build.sh --help           # Show all options
./build.sh --local          # Build locally only
./build.sh --tag v1.0       # Use specific tag
./build.sh --platform linux/amd64  # Single platform
./build.sh --repo user/repo # Different repository
```

## Image Specifications

- **Base OS**: Ubuntu 22.04 LTS
- **Size**: ~2-3GB (compressed)
- **Platforms**: linux/amd64, linux/arm64
- **User**: Non-root user `rxivmaker`
- **Working Directory**: `/workspace`

## Dependencies Included

### LaTeX Packages
- texlive-latex-base, texlive-latex-recommended, texlive-latex-extra
- texlive-fonts-recommended, texlive-fonts-extra
- texlive-science, texlive-pictures, texlive-bibtex-extra
- biber, texlive-xetex, texlive-luatex

### Python Tools
- Python 3.11 (default python3)
- pip, setuptools, wheel (latest versions)
- Virtual environment support


### R Environment
- R base and R development packages
- System libraries for R packages

### System Libraries
- Font libraries: libfontconfig1-dev, libfreetype6-dev, libharfbuzz-dev
- Graphics: libpango1.0-dev, libjpeg-dev, libpng-dev
- Build tools: build-essential, make, pkg-config

## Maintenance

### Updating Dependencies

1. **System packages**: Modify the `apt-get install` commands in the Dockerfile
2. **Node.js version**: Update the NodeSource setup script URL
3. **Python version**: Update the python3.11 package name and alternatives
4. **LaTeX packages**: Add or remove texlive-* packages as needed

### Rebuilding the Image

```bash
# After making changes, rebuild and push
./build.sh --tag v1.1

# Test locally first
./build.sh --local --tag test
docker run -it rxivmaker/base:test
```

### Version Management

Use semantic versioning for tags:
- `latest` - Current stable version
- `v1.0`, `v1.1`, etc. - Specific versions
- `dev` - Development builds

## GitHub Actions Integration

The image is designed to be used in GitHub Actions workflows:

```yaml
jobs:
  build-pdf:
    runs-on: ubuntu-latest
    container: rxivmaker/base:latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Install Python dependencies
      run: |
        python3 -m pip install -e ".[dev]"
    
    - name: Generate PDF
      run: |
        make pdf
```

## Performance Benefits

Using this Docker image in GitHub Actions provides:

- **Speed**: ~7-8 minutes saved per workflow run
- **Reliability**: Eliminates dependency installation failures
- **Consistency**: Same environment across all builds
- **Caching**: Docker layer caching for faster subsequent pulls

## Security Considerations

- Non-root user `rxivmaker` for improved security
- Minimal attack surface (no unnecessary packages)
- Regular base image updates with Ubuntu 22.04 LTS
- No secrets or sensitive data in the image

## Troubleshooting

### Common Issues

1. **Build failures**: Check Docker buildx is installed and configured
2. **Permission errors**: Ensure Docker daemon is running and user has permissions
3. **Push failures**: Verify Docker Hub login with `docker login`
4. **Size concerns**: Use `docker images` to check image size

### Testing the Image

```bash
# Test basic functionality
docker run -it rxivmaker/base:latest bash

# Verify dependencies
docker run rxivmaker/base:latest python3 --version
docker run rxivmaker/base:latest node --version
docker run rxivmaker/base:latest pdflatex --version
docker run rxivmaker/base:latest python3 -c "import requests; print('Mermaid.ink API ready')"
docker run rxivmaker/base:latest R --version
```

### Debugging Build Issues

```bash
# Build with verbose output
./build.sh --local 2>&1 | tee build.log

# Inspect intermediate layers
docker buildx build --target system-deps -t debug:system-deps .
docker run -it debug:system-deps bash
```

## Contributing

When contributing to the Docker configuration:

1. Test changes locally first with `./build.sh --local`
2. Ensure all required dependencies are included
3. Maintain multi-stage build structure for optimization
4. Update this README with any changes
5. Use semantic versioning for new releases

## Links

- [Docker Hub Repository](https://hub.docker.com/r/rxivmaker/base)
- [GitHub Actions Workflow](../../.github/workflows/build-pdf.yml)
- [Rxiv-Maker Documentation](../../README.md)

---

**Note**: This Docker image is specifically designed for CI/CD acceleration and should not include any rxiv-maker source code or user data. All Python dependencies are installed at runtime in the GitHub Actions workflow.