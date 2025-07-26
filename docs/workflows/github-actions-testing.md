# GitHub Actions Testing Workflow

This document describes the GitHub Actions configuration for testing the Homebrew installation of rxiv-maker from test-pypi.

## Overview

The GitHub Actions workflow tests:
1. **Homebrew installation** from test-pypi using the `--with-test-pypi` option
2. **Basic CLI functionality** to ensure the package works correctly
3. **Verification logic** to ensure the dependency checking works
4. **No automatic system dependency installation** during pip install
5. **Matrix testing** for both test-pypi and default installation modes

## Configuration

### Environment
- **Image**: macOS (latest GitHub Actions runner)
- **Homebrew**: Configured with minimal analytics and auto-update disabled
- **Python**: System Python 3.11 (installed via Homebrew)
- **Trigger**: Manual workflow dispatch with configurable options

### Workflow Features

#### Manual Trigger Options
- **Test mode**: Choose between 'both', 'test-pypi', or 'default'
- **Skip dependencies**: Option to skip system dependency installation for faster testing
- **Matrix testing**: Runs tests for both installation modes in parallel

#### Test Phases

##### 1. Environment Setup
```bash
# Set Homebrew environment variables
export HOMEBREW_NO_AUTO_UPDATE=1
export HOMEBREW_NO_INSTALL_CLEANUP=1
export HOMEBREW_NO_ANALYTICS=1

# System information collection
sw_vers -productVersion
uname -m
```

##### 2. Homebrew Configuration Fix
```bash
# Fix Homebrew configuration issues in CI
brew untap homebrew/homebrew-cask-versions || true
brew cleanup || true

# Update Homebrew
brew update
```

##### 3. System Dependencies Installation
```bash
# Install LaTeX distribution
brew install --cask basictex

# Install other dependencies
brew install python@3.11 node@20 r make
```

##### 4. rxiv-maker Installation
```bash
# Install from local formula with test-pypi option
brew install --build-from-source ./homebrew-rxiv-maker/Formula/rxiv-maker.rb --with-test-pypi

# Or install from default source
brew install --build-from-source ./homebrew-rxiv-maker/Formula/rxiv-maker.rb
```

##### 5. Verification Tests
```bash
# Basic verification
which rxiv
rxiv --version
rxiv --help

# Package information
pip show rxiv-maker

# CLI functionality tests
rxiv check-installation --json
rxiv config show
rxiv setup --check-deps-only

# Manuscript operations
rxiv init test-manuscript
rxiv validate --detailed
```

## Workflow Features

### ✅ What the Workflow Tests
- Package installs from test-pypi via Homebrew
- CLI commands work without errors
- Verification logic detects system dependencies
- No automatic system dependency installation occurs during pip install
- Matrix testing for both test-pypi and default installation modes
- Manuscript initialization and validation

### ❌ What Should NOT Happen
- Automatic LaTeX/Node.js installation during pip install
- Package installation from main PyPI (should use test-pypi)
- CLI import errors or missing dependencies

## Formula Configuration

The Homebrew formula supports a `--with-test-pypi` option:

```ruby
# Install from test PyPI
brew install --build-from-source ./homebrew-rxiv-maker/Formula/rxiv-maker.rb --with-test-pypi

# Install from source (default)
brew install --build-from-source ./homebrew-rxiv-maker/Formula/rxiv-maker.rb
```

### Test PyPI Installation
When using `--with-test-pypi`, the formula:
1. Installs from `https://test.pypi.org/simple/`
2. Falls back to `https://pypi.org/simple/` for dependencies
3. Installs `rxiv-maker` package specifically from test-pypi

## Artifacts

The workflow collects:
- **test-manuscript/** - Generated test manuscript directory
- **system-info.txt** - System and package information
- **Build logs** - Full installation and test output
- **Test artifacts** - Separate artifacts for each test mode

## Notifications

GitHub Actions provides notifications through:
- GitHub web interface
- Email notifications (if configured)
- Integration with GitHub issues and pull requests

## Cache Configuration

GitHub Actions caches:
- Homebrew packages and dependencies
- Python pip cache
- Test artifacts

This reduces build times by avoiding re-downloading unchanged components.

## Troubleshooting

### Common Issues

#### Homebrew Configuration Issues in CI
```bash
# Fix: Remove problematic homebrew-cask-versions tap
brew untap homebrew/homebrew-cask-versions || true

# Fix: Clean up existing Homebrew configuration
brew cleanup || true

# Error: "fatal: could not read Username for 'https://github.com'"
# Solution: The above commands fix authentication issues in CI environments
```

#### Formula Installation Fails
```bash
# Check formula syntax
brew audit --strict ./homebrew-rxiv-maker/Formula/rxiv-maker.rb

# Test formula locally
brew install --build-from-source ./homebrew-rxiv-maker/Formula/rxiv-maker.rb --with-test-pypi
```

#### Package Not Found on test-pypi
```bash
# Check if package exists
curl -s https://test.pypi.org/simple/rxiv-maker/ | grep -i "rxiv-maker"

# Verify package was uploaded
pip install --index-url https://test.pypi.org/simple/ rxiv-maker
```

#### CLI Import Errors
```bash
# Check Python path
python3 -c "import sys; print('\\n'.join(sys.path))"

# Check package installation
pip show rxiv-maker

# Test direct import
python3 -c "import rxiv_maker; print('Import successful')"
```

### Recovery Steps

1. **Check GitHub Actions logs** for detailed error messages
2. **Test formula locally** on macOS system
3. **Verify test-pypi package** is available and correct
4. **Check dependencies** are properly resolved
5. **Download artifacts** from failed runs for debugging

## Integration with Development Workflow

This GitHub Actions configuration integrates with:
1. **Test PyPI publishing** - Tests packages before main PyPI release
2. **Homebrew formula updates** - Validates formula changes
3. **CI/CD pipeline** - Manual testing on-demand
4. **GitHub ecosystem** - Better integration with issues, PRs, and releases

## Usage

To trigger GitHub Actions testing:
1. Go to the GitHub repository
2. Navigate to Actions tab
3. Select "Test Homebrew Installation" workflow
4. Click "Run workflow" and configure options:
   - **Test mode**: Choose 'both', 'test-pypi', or 'default'
   - **Skip dependencies**: Option to skip system dependency installation
5. Review results and download artifacts

### Manual Testing Commands
```bash
# Test both installation modes
# This is done automatically by the matrix strategy

# Test only test-pypi installation
# Select "test-pypi" from the test_mode dropdown

# Test only default installation
# Select "default" from the test_mode dropdown

# Fast testing without system dependencies
# Check the "skip_dependencies" option
```

## Workflow Security

The workflow is designed with security in mind:
- **Manual trigger only** - No automatic execution on commits
- **No secrets required** - Uses public repositories and packages
- **Isolated environment** - Each run uses a fresh macOS runner
- **Artifact retention** - Test results kept for 30 days

## Status

### ✅ Completed
- **GitHub Actions migration** - Replaced AppVeyor with GitHub Actions
- **Matrix testing** - Test both test-pypi and default installation modes
- **Manual workflow dispatch** - On-demand testing with configurable options
- **Comprehensive testing** - All AppVeyor functionality migrated and enhanced
- **Artifact collection** - Improved collection and organization of test results

### 🔄 Available Features
- **Manual triggering** - Run tests on-demand via GitHub Actions
- **Matrix testing** - Test both test-pypi and default installation modes
- **Configurable options** - Skip dependencies or test specific modes
- **Artifact collection** - Separate artifacts for each test mode
- **Detailed logging** - Comprehensive test output and system information

### 🔗 Links
- **Test-PyPI Package**: https://test.pypi.org/project/rxiv-maker/1.4.0.dev0/
- **GitHub Actions**: https://github.com/HenriquesLab/rxiv-maker/actions
- **GitHub Repository**: https://github.com/HenriquesLab/rxiv-maker

### Recent Changes
- **Migrated to GitHub Actions** - Replaced AppVeyor with GitHub Actions workflow
- **Added matrix testing** - Test both test-pypi and default installation modes
- **Enhanced manual control** - Workflow dispatch with configurable options
- **Improved artifacts** - Better collection and organization of test results
- **Fixed Homebrew CI issues** - Added tap cleanup and configuration fixes

## Comparison with AppVeyor

| Feature | AppVeyor | GitHub Actions |
|---------|----------|----------------|
| **Trigger** | Automatic on push | Manual on-demand |
| **Cost** | External service | Free with GitHub |
| **Integration** | Separate platform | Native GitHub |
| **Customization** | Limited | Extensive |
| **Artifacts** | Basic | Enhanced |
| **Matrix Testing** | No | Yes |
| **Security** | Auto-execution | Manual control |
| **Maintenance** | Separate config | Unified workflow |

## Best Practices

1. **Use manual triggers** for testing to avoid unnecessary resource usage
2. **Test both modes** to ensure compatibility with both test-pypi and default installation
3. **Review artifacts** after each test run to verify expected behavior
4. **Skip dependencies** when doing rapid testing of CLI functionality
5. **Monitor logs** for any new issues or changes in behavior

The GitHub Actions workflow provides better control, integration, and flexibility compared to the previous AppVeyor setup while maintaining all the same testing capabilities.