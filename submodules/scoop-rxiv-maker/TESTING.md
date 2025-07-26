# Testing Guide for scoop-rxiv-maker

This document describes the testing infrastructure for the scoop-rxiv-maker bucket.

## Overview

The testing infrastructure follows Scoop's best practices and includes:
- Local testing capabilities
- Comprehensive CI/CD workflows
- Performance monitoring
- Cross-platform compatibility testing

## Local Testing

### Prerequisites
- Windows PowerShell 5.1+ or PowerShell Core
- Scoop installed
- Git (for cloning the repository)

### Running Tests Locally

1. **Basic Test Run**
   ```powershell
   .\bin\test.ps1
   ```

2. **Run Specific Tests**
   ```powershell
   .\bin\test.ps1 -TestPath "Scoop-Bucket.Tests.ps1"
   ```

3. **CI Mode (Detailed Output)**
   ```powershell
   .\bin\test.ps1 -CI
   ```

### Test Structure

- `bin/test.ps1` - Main test runner script
- `Scoop-Bucket.Tests.ps1` - Pester tests for manifest validation
- `.github/workflows/test-formula.yml` - CI workflow configuration

## CI/CD Testing

### GitHub Actions Workflow

The CI workflow (`test-formula.yml`) includes:

1. **Manifest Validation**
   - JSON syntax checking
   - Required fields validation
   - URL verification
   - Version consistency checks

2. **Installation Testing**
   - Multi-Windows version testing (windows-latest, windows-2019)
   - Installation from manifest
   - CLI functionality verification
   - Manuscript operations testing

3. **PowerShell Core Testing**
   - Tests compatibility with pwsh
   - Compares behavior between Windows PowerShell and PowerShell Core

4. **Cache Testing**
   - Verifies Scoop cache functionality
   - Tests offline installation capabilities

5. **Dependency Testing**
   - Tests with suggested dependencies (Git, Make)
   - Tests Python dependency handling
   - Tests interaction with other Scoop packages

6. **LaTeX Integration** (optional)
   - Tests with LaTeX distributions
   - PDF generation workflow

7. **Performance Testing**
   - CLI startup time benchmarks
   - Command execution timing

### Triggering CI Tests

Tests are triggered on:
- Push to main/develop branches
- Pull requests
- Manual workflow dispatch
- Weekly schedule (Sundays at 6 AM UTC)

### Manual Trigger Options

```yaml
workflow_dispatch:
  inputs:
    test-scope:
      options: ['full', 'syntax-only', 'quick', 'comprehensive']
    windows-versions:
      default: 'windows-2022,windows-latest'
    test-latex:
      default: true
```

## Monitoring CI Status

### Using the PowerShell Monitor Script

1. **Continuous Monitoring**
   ```powershell
   .\monitor-ci.ps1
   ```

2. **One-time Status Check**
   ```powershell
   .\monitor-ci.ps1 -Once
   ```

3. **Interactive Mode** (cancel hanging jobs)
   ```powershell
   .\monitor-ci.ps1 -Interactive
   ```

4. **Show Metrics**
   ```powershell
   .\monitor-ci.ps1 -Once
   # Includes 7-day performance metrics
   ```

## Test Categories

### Unit Tests
- Manifest structure validation
- JSON syntax verification
- URL format checking
- Version validation

### Integration Tests
- Scoop installation process
- Python package installation via pip
- CLI command execution
- Dependency resolution

### Performance Tests
- Installation time measurements
- Command execution benchmarks
- Cache efficiency testing

### Compatibility Tests
- Windows PowerShell vs PowerShell Core
- Multiple Windows versions
- Python environment isolation

## Writing New Tests

### Adding Pester Tests

Add new test cases to `Scoop-Bucket.Tests.ps1`:

```powershell
Describe "New Feature Tests" {
    It "Should validate new feature" {
        # Test implementation
        $result | Should -Be $expected
    }
}
```

### Adding CI Test Jobs

Add new jobs to `.github/workflows/test-formula.yml`:

```yaml
new-test-job:
  name: New Test Scenario
  needs: [setup, scoop-installation]
  runs-on: windows-latest
  if: needs.setup.outputs.run-comprehensive == 'true'
  steps:
    - name: Run new tests
      run: |
        # Test implementation
      shell: powershell
```

## Best Practices

1. **Always Test Locally First**
   - Run `.\bin\test.ps1` before pushing
   - Verify manifest changes with local Scoop installation

2. **Use Descriptive Test Names**
   - Clear test descriptions help with debugging
   - Group related tests in contexts/describes

3. **Handle CI Environment Differences**
   - Use conditional logic for CI vs local testing
   - Account for pre-installed software on GitHub runners

4. **Test Error Scenarios**
   - Don't just test happy paths
   - Verify error handling and user feedback

5. **Keep Tests Fast**
   - Use timeouts appropriately
   - Skip expensive tests in quick mode
   - Cache dependencies when possible

## Troubleshooting

### Common Issues

1. **Test Failures on CI but not Locally**
   - Check for environment differences
   - Verify PATH configuration
   - Review GitHub runner specifications

2. **PowerShell Version Issues**
   - Ensure compatibility with PowerShell 5.1
   - Test with both Windows PowerShell and pwsh

3. **Network-Related Failures**
   - Add retry logic for network operations
   - Use appropriate timeouts
   - Handle offline scenarios gracefully

### Debug Commands

```powershell
# Check Scoop environment
scoop config
scoop status

# Verify Python environment
python --version
python -m pip list

# Check PATH
$env:PATH -split ';' | Select-String 'scoop'

# Test manifest manually
scoop install ./bucket/rxiv-maker.json --no-cache
```

## Contributing

When contributing to the test infrastructure:

1. Follow existing patterns and conventions
2. Add tests for new features
3. Update this documentation
4. Ensure CI passes before merging

For more information, see the main [README.md](README.md) and [rxiv-maker documentation](https://github.com/henriqueslab/rxiv-maker).