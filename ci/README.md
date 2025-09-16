# 🐳 Local CI Reproduction System

This directory contains Docker-based CI reproduction infrastructure that allows developers to run the exact same tests locally as those run in GitHub Actions, ensuring early detection of CI failures.

## 📁 Directory Structure

```
ci/
├── README.md              # This documentation
├── Dockerfile.ci          # Docker image matching GitHub Actions environment
└── docker-compose.ci.yml  # Services for different CI test scenarios
```

## 🚀 Quick Start

### Option 1: Orchestration Script (Recommended)

Use the comprehensive orchestration script with all available options:

```bash
# Build the CI environment image
./scripts/run-ci-locally.sh build-image

# Run fast tests (lint + unit subset) - mirrors CI "fast-tests" job
./scripts/run-ci-locally.sh fast

# Run integration tests - mirrors CI "integration-tests" job
./scripts/run-ci-locally.sh integration

# Run build validation - mirrors CI "build-validation" job
./scripts/run-ci-locally.sh build-validation

# Run full coverage tests - mirrors CI "coverage-validation" job
./scripts/run-ci-locally.sh coverage

# Run all tests in sequence (comprehensive validation)
./scripts/run-ci-locally.sh full

# Test across Python 3.11, 3.12, 3.13 (matrix testing)
./scripts/run-ci-locally.sh matrix

# Interactive debugging shell
./scripts/run-ci-locally.sh shell
```

### Option 2: Docker Compose (Direct)

For more control, use docker-compose directly:

```bash
# Build image
docker-compose -f ci/docker-compose.ci.yml build ci-test

# Run specific test scenarios
docker-compose -f ci/docker-compose.ci.yml run --rm ci-test-run        # Fast tests
docker-compose -f ci/docker-compose.ci.yml run --rm ci-test-integration # Integration tests
docker-compose -f ci/docker-compose.ci.yml run --rm ci-test-coverage    # Full coverage tests

# Interactive shell
docker-compose -f ci/docker-compose.ci.yml run --rm ci-test
```

### Option 3: Make Targets (Legacy Support)

Convenient make targets are also available:

```bash
make ci-build-image        # Build CI image
make ci-fast-docker       # Fast tests
make ci-integration-docker # Integration tests
make ci-coverage-docker   # Coverage tests
make ci-full-docker      # Full test sequence
make ci-shell-docker     # Interactive shell
```

## 🛠 How It Works

### Environment Matching
The CI reproduction system creates a Docker environment that exactly matches GitHub Actions:

- **Base Image**: Ubuntu 24.04 (same as `ubuntu-latest`)
- **Python Version**: 3.11 (default CI version)
- **Package Manager**: uv (same as CI)
- **Environment Variables**: Identical to CI (`FORCE_COLOR=1`, `UV_SYSTEM_PYTHON=1`, etc.)
- **Dependencies**: Same versions via `uv.lock`

### Test Session Mapping
Each script command maps directly to a GitHub Actions job:

| Local Command | GitHub Actions Job | Nox Session | Description |
|---------------|-------------------|-------------|-------------|
| `fast` | `fast-tests` | `lint` + `test(test_type='fast')` | Linting + fast unit tests |
| `integration` | `integration-tests` | `test(test_type='integration')` | Integration test suite |
| `build-validation` | `build-validation` | `build` | Package build validation |
| `coverage` | `coverage-validation` | `test(test_type='full')` | Full test suite with coverage |
| `container-pdf` | `container-tests` | `pdf` | PDF generation tests |

### Artifact Collection
The orchestration script can capture detailed logs:

```bash
# Run with log capture (stores in .ci_artifacts/)
./scripts/run-ci-locally.sh fast-logs

# Matrix testing with per-version logs
./scripts/run-ci-locally.sh matrix
```

## 📊 Performance & Optimization

### Caching Strategy
- **Docker Layer Caching**: Dependencies cached in separate layers
- **Volume Mounts**: Source code mounted for fast iteration
- **Nox Environment Reuse**: Virtual environments persist within container lifecycle

### Resource Usage
- **Disk Space**: ~2GB for full image with dependencies
- **Build Time**: ~3-5 minutes for clean build, ~30 seconds for incremental
- **Test Time**:
  - Fast tests: ~1-2 minutes
  - Integration: ~5-10 minutes
  - Full coverage: ~10-15 minutes

## 🔧 Advanced Usage

### Custom Test Selection
Pass additional pytest arguments:

```bash
# Test specific modules
./scripts/run-ci-locally.sh fast -- tests/unit/test_figure_processor.py

# Run with specific markers
./scripts/run-ci-locally.sh integration -- -m "not slow"

# Increase verbosity
./scripts/run-ci-locally.sh coverage -- -v --tb=long
```

### Debugging Failed Tests
```bash
# Run the exact failing test with maximum detail
./scripts/run-ci-locally.sh fast -- -k "test_specific_failure" -v --tb=long --pdb

# Interactive debugging session
./scripts/run-ci-locally.sh shell
# Inside container:
# pytest tests/unit/test_failing.py -v --pdb
```

### Multi-Version Testing
```bash
# Test across all Python versions (3.11, 3.12, 3.13)
./scripts/run-ci-locally.sh matrix

# Results stored in .ci_artifacts/ with timestamps
ls .ci_artifacts/
# 20241201-143022_fast_py3.11.log
# 20241201-143045_fast_py3.12.log
# 20241201-143108_fast_py3.13.log
```

## 🐛 Troubleshooting

### Common Issues

**Docker Build Fails**
```bash
# Clean and rebuild
docker image rm rxiv-maker-ci:local
./scripts/run-ci-locally.sh build-image
```

**Permission Errors**
```bash
# Ensure script is executable
chmod +x scripts/run-ci-locally.sh
```

**Out of Disk Space**
```bash
# Clean up Docker resources
./scripts/run-ci-locally.sh clean
docker system prune -f
```

**Tests Pass Locally but Fail in CI**
- Check environment variables match CI exactly
- Verify uv.lock is up to date
- Test with the exact CI command:
  ```bash
  ./scripts/run-ci-locally.sh fast -- -m 'unit and not ci_exclude' --maxfail=3 --tb=short -x
  ```

### Debug Mode
For maximum debugging information:

```bash
# Enable verbose Docker output
DOCKER_BUILDKIT=0 ./scripts/run-ci-locally.sh build-image

# Run with full pytest verbosity
./scripts/run-ci-locally.sh fast -- -vvv --tb=long --showlocals
```

## 🔄 Maintenance

### Updating CI Environment
When CI configuration changes:

1. Update `ci/Dockerfile.ci` to match new CI base image/dependencies
2. Update `noxfile.py` if test sessions change
3. Update `ci/docker-compose.ci.yml` if new test scenarios needed
4. Rebuild image: `./scripts/run-ci-locally.sh build-image`

### Keeping in Sync with GitHub Actions
- Monitor `.github/workflows/ci.yml` for changes
- Update Python versions in `scripts/run-ci-locally.sh` matrix function
- Ensure nox session parameters match CI exactly

## 📈 Integration with Development Workflow

### Pre-Commit Hooks
Add local CI check to pre-commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: local-ci-fast
        name: Local CI Fast Tests
        entry: ./scripts/run-ci-locally.sh fast
        language: system
        pass_filenames: false
```

### IDE Integration
Configure your IDE to run local CI tests:

```json
// VS Code tasks.json
{
    "label": "Run Local CI Fast",
    "type": "shell",
    "command": "./scripts/run-ci-locally.sh fast",
    "group": "test"
}
```

## 🎯 Best Practices

1. **Run fast tests frequently** during development for immediate feedback
2. **Run full test suite** before pushing to main branches
3. **Use matrix testing** when changing core functionality
4. **Capture logs** when investigating CI failures
5. **Clean up regularly** to avoid disk space issues

## 📚 See Also

- [GitHub Actions CI Configuration](../.github/workflows/ci.yml)
- [Nox Configuration](../noxfile.py)
- [Main Project Documentation](../README.md)
- [Docker Rxiv-Maker Repository](https://github.com/HenriquesLab/docker-rxiv-maker) for production containers