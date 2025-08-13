# Testing Framework Engine Abstraction Guide

This guide explains the new testing framework that supports multiple execution engines (local, Docker, Podman) for exhaustive testing of rxiv-maker.

## Overview

The new testing framework introduces an abstraction layer that allows tests to run seamlessly across different execution environments without modification. This ensures comprehensive testing and better portability.

## Key Components

### 1. ExecutionEngine Class (tests/conftest.py)

The `ExecutionEngine` class provides a unified interface for running commands:

```python
def test_example(execution_engine):
    # This works the same whether running locally or in Docker
    result = execution_engine.run(["rxiv", "--version"])
    assert result.returncode == 0
```

### 2. Pytest Engine Option

Tests can be run with different engines using the `--engine` flag:

```bash
# Run tests locally
pytest --engine=local

# Run tests in Docker
pytest --engine=docker

# Run tests in Podman (when available)
pytest --engine=podman
```

### 3. Nox Sessions

Nox provides convenient session management with engine parameterization:

```bash
# Run tests with specific engine
nox -s tests(engine="docker")

# Run all test combinations
nox -s tests  # Runs all Python versions × all engines

# Run integration tests with Docker
nox -s integration(engine="docker")

# Run coverage analysis
nox -s coverage(engine="local")
```

## Migration Guide

### Converting Existing Tests

**Before (Direct subprocess):**
```python
def test_old_style():
    result = subprocess.run(["rxiv", "--version"], capture_output=True)
    assert result.returncode == 0
```

**After (Engine abstraction):**
```python
def test_new_style(execution_engine):
    result = execution_engine.run(["rxiv", "--version"])
    assert result.returncode == 0
```

### Key Differences

1. **Request the fixture**: Add `execution_engine` parameter to test functions
2. **Use engine.run()**: Replace `subprocess.run()` with `execution_engine.run()`
3. **Remove capture_output**: The engine handles output capture automatically
4. **Handle check parameter**: Use `check=False` for expected failures

## Writing New Tests

### Basic Test Structure

```python
def test_feature(execution_engine):
    """Test description."""
    # Run command through engine
    result = execution_engine.run(["rxiv", "command", "args"])
    
    # Assert on results
    assert result.returncode == 0
    assert "expected" in result.stdout
```

### Testing with Temporary Files

```python
def test_with_files(execution_engine, temp_dir):
    """Test with temporary directory."""
    # Create test file
    test_file = temp_dir / "test.md"
    test_file.write_text("# Test")
    
    # Run command in temp directory
    result = execution_engine.run(
        ["rxiv", "validate"],
        cwd=str(temp_dir)
    )
    
    assert result.returncode == 0
```

### Testing Expected Failures

```python
def test_error_handling(execution_engine):
    """Test error conditions."""
    # Use check=False for expected failures
    result = execution_engine.run(
        ["rxiv", "invalid-command"],
        check=False
    )
    
    assert result.returncode != 0
    assert "error" in result.stderr.lower()
```

## CI/CD Integration

### GitHub Actions

The new CI pipeline (`ci.yml`) automatically tests across:
- Multiple Python versions (3.9, 3.10, 3.11, 3.12)
- Multiple engines (local, docker)
- Multiple operating systems (ubuntu, windows, macos)

### Local Development

For quick development cycles:

```bash
# Quick local tests
nox -s test-quick

# Full test suite with specific engine
nox -s test-all(engine="docker")

# Run specific test file
pytest tests/unit/test_cli_with_engine.py --engine=local
```

## Adding New Engines

To add support for a new container engine (e.g., Podman):

1. **Update ENGINES list in noxfile.py:**
   ```python
   ENGINES = ["local", "docker", "podman"]
   ```

2. **Update ExecutionEngine in conftest.py:**
   - Add engine-specific logic if needed
   - Most container engines use similar commands

3. **Update CI workflow:**
   - Add new engine to test matrix
   - Add installation steps if needed

## Best Practices

1. **Engine-agnostic tests**: Write tests that work across all engines
2. **Use fixtures**: Leverage pytest fixtures for setup/teardown
3. **Handle paths carefully**: Use pathlib for cross-platform paths
4. **Test in CI**: Ensure tests pass in CI before merging
5. **Document engine-specific behavior**: Note any engine-specific quirks

## Troubleshooting

### Docker not available
- Error: "Docker is not available on this system"
- Solution: Install Docker or use `--engine=local`

### Container startup issues
- Error: "Failed to start container"
- Solution: Check Docker daemon is running, verify image availability

### Permission errors
- Error: "Permission denied"
- Solution: Ensure proper file permissions, check Docker socket access

### Slow container tests
- Issue: Docker tests take longer than local
- Solution: Use session-scoped fixtures, enable Docker BuildKit

## Future Enhancements

1. **Podman support**: Full integration once tested
2. **Kubernetes support**: For distributed testing
3. **Cloud testing**: Integration with cloud container services
4. **Performance metrics**: Track test execution times per engine
5. **Parallel execution**: Run engine tests in parallel