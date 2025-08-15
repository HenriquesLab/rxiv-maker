# Container Test Environments

This directory contains container definitions and configurations for testing the rxiv-maker APT packages across different Ubuntu distributions.

## Container Images

### Containerfile.ubuntu-apt-test

Multi-stage container for comprehensive APT package testing with different optimization levels:

#### Available Stages

**base** - Minimal Ubuntu environment with essential tools
- Basic system utilities
- Test user setup
- Essential networking tools

**testing** (default) - Comprehensive testing environment
- LaTeX packages for PDF generation testing
- Python and R for figure generation testing
- Node.js for JavaScript tool testing
- Performance monitoring tools

**minimal** - Lightweight for quick validation
- Only essential tools
- Fast startup for basic tests

**development** - Full development environment
- All testing tools plus development utilities
- Documentation generation tools
- Debugging and profiling tools

**ci** - Optimized for CI/CD environments
- CI-specific tools and report generation
- Artifact handling utilities
- Optimized for automated testing

**performance** - Performance monitoring and profiling
- Performance profiling tools
- Memory and I/O monitoring
- Benchmarking utilities

**security** - Security testing and validation
- Security scanners and tools
- GPG validation utilities
- System integrity checking

## Usage Examples

### Build Container Images

```bash
# Build default testing image for Ubuntu 22.04
podman build -f tests/container/Containerfile.ubuntu-apt-test \
  -t rxiv-apt-test:22.04 .

# Build for different Ubuntu version
podman build -f tests/container/Containerfile.ubuntu-apt-test \
  --build-arg UBUNTU_VERSION=20.04 \
  -t rxiv-apt-test:20.04 .

# Build specific stage
podman build -f tests/container/Containerfile.ubuntu-apt-test \
  --target minimal \
  -t rxiv-apt-test:minimal .
```

### Run Interactive Testing

```bash
# Start interactive testing container
podman run -it --rm \
  --name rxiv-apt-test \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04

# Run with specific test environment
podman run -it --rm \
  --name rxiv-performance-test \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04 --target performance
```

### Automated Testing

```bash
# Run automated test suite
podman run --rm \
  --name rxiv-auto-test \
  -v $(pwd):/workspace \
  -v $(pwd)/test-results:/test-results \
  rxiv-apt-test:22.04 \
  /test-scripts/test-apt-container.sh --test-type comprehensive

# CI/CD testing
podman run --rm \
  --name rxiv-ci-test \
  -e CI=true \
  -v $(pwd):/workspace \
  -v $(pwd)/ci-results:/ci/outputs \
  rxiv-apt-test:22.04 --target ci \
  /ci/ci-test-apt.sh
```

## Container Features

### Test User Environment

All containers include a `testuser` account with:
- Sudo privileges for package installation testing
- Home directory setup with test configurations
- Environment variables for testing

### Mounted Volumes

- `/workspace` - Project source code (read-only recommended)
- `/test-results` - Test output and reports
- `/test-data` - Test manuscripts and data files

### Environment Variables

- `CI` - Set to `true` for CI/CD environments
- `PERFORMANCE_MONITORING` - Enable performance monitoring
- `SECURITY_TESTING` - Enable security testing mode
- `TEST_RESULTS_FORMAT` - Output format (json, junit, html)

### Health Checks

Containers include health checks to ensure proper startup and functionality.

## Testing Workflows

### 1. Fresh Installation Testing

```bash
podman run --rm \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04 \
  bash -c "
    # Add APT repository
    curl -fsSL https://raw.githubusercontent.com/henriqueslab/rxiv-maker/apt-repo/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rxiv-maker.gpg
    echo 'deb [signed-by=/usr/share/keyrings/rxiv-maker.gpg] https://henriqueslab.github.io/rxiv-maker/ stable main' | sudo tee /etc/apt/sources.list.d/rxiv-maker.list
    
    # Install package
    sudo apt update && sudo apt install -y rxiv-maker
    
    # Test functionality
    rxiv --version
    rxiv check-installation
  "
```

### 2. Local Package Testing

```bash
# Build local package first
./scripts/build-deb.sh --output dist/

# Test in container
podman run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/dist:/packages \
  rxiv-apt-test:22.04 \
  bash -c "
    sudo dpkg -i /packages/rxiv-maker_*.deb || true
    sudo apt-get install -f -y
    rxiv --version
  "
```

### 3. Upgrade Testing

```bash
podman run --rm \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04 \
  bash -c "
    # Install older version (if available)
    sudo apt install rxiv-maker=1.5.9-1
    
    # Upgrade to newer version
    sudo apt update && sudo apt upgrade rxiv-maker
    
    # Test functionality
    rxiv --version
  "
```

### 4. Performance Testing

```bash
podman run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/performance-results:/performance/reports \
  rxiv-apt-test:22.04 --target performance \
  bash -c "
    # Install package with timing
    time sudo apt install rxiv-maker
    
    # Benchmark operations
    time rxiv pdf EXAMPLE_MANUSCRIPT
    
    # Generate performance report
    /performance/performance-report.sh
  "
```

### 5. Security Testing

```bash
podman run --rm \
  -v $(pwd):/workspace \
  -v $(pwd)/security-results:/security/reports \
  rxiv-apt-test:22.04 --target security \
  bash -c "
    # Install package
    sudo apt update && sudo apt install rxiv-maker
    
    # Security validation
    /security/security-scan.sh
    
    # GPG verification
    /security/verify-signatures.sh
  "
```

## Multi-Architecture Testing

```bash
# Test on AMD64
podman run --platform linux/amd64 --rm \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04 \
  /test-scripts/test-apt-container.sh

# Test on ARM64 (if available)
podman run --platform linux/arm64 --rm \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04 \
  /test-scripts/test-apt-container.sh
```

## Development and Debugging

### Interactive Development

```bash
# Start development container
podman run -it --rm \
  --name rxiv-dev \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04 --target development

# Inside container
cd /workspace
sudo apt install rxiv-maker
gdb --args rxiv pdf EXAMPLE_MANUSCRIPT
```

### Debug Failed Tests

```bash
# Run container without cleanup
podman run -it \
  --name rxiv-debug \
  -v $(pwd):/workspace \
  rxiv-apt-test:22.04

# In another terminal, inspect running container
podman exec -it rxiv-debug bash

# Check logs and system state
journalctl -xe
dpkg -l | grep rxiv
apt-cache policy rxiv-maker
```

## Container Maintenance

### Update Base Images

```bash
# Pull latest Ubuntu images
podman pull ubuntu:20.04
podman pull ubuntu:22.04
podman pull ubuntu:24.04

# Rebuild containers
for version in 20.04 22.04 24.04; do
  podman build \
    --build-arg UBUNTU_VERSION=$version \
    -t rxiv-apt-test:$version \
    -f tests/container/Containerfile.ubuntu-apt-test .
done
```

### Cleanup Test Containers

```bash
# Remove test containers
podman container prune -f

# Remove test images
podman rmi $(podman images -f "reference=rxiv-apt-test*" -q)

# Clean system
podman system prune -f
```

## CI/CD Integration

These containers integrate with the GitHub Actions workflow for automated testing:

```yaml
# Example workflow step
- name: Test APT Package
  run: |
    podman run --rm \
      -v ${{ github.workspace }}:/workspace \
      -v ${{ github.workspace }}/test-results:/test-results \
      rxiv-apt-test:22.04 \
      /test-scripts/test-apt-container.sh --test-type comprehensive
```

## Troubleshooting

### Common Issues

**Container build failures:**
- Check disk space: `df -h`
- Update base images: `podman pull ubuntu:22.04`
- Check network connectivity

**Test execution failures:**
- Check container logs: `podman logs <container>`
- Verify volume mounts: `podman inspect <container>`
- Check file permissions

**Package installation failures:**
- Verify repository accessibility
- Check GPG key installation
- Validate package dependencies

### Debug Commands

```bash
# Container information
podman inspect rxiv-apt-test:22.04

# Running container status
podman ps -a

# Container resource usage
podman stats --all

# Container filesystem
podman exec -it <container> df -h

# Network connectivity
podman exec -it <container> ping henriqueslab.github.io
```

---

These container environments provide comprehensive testing capabilities for the rxiv-maker APT packages across multiple Ubuntu distributions and testing scenarios.