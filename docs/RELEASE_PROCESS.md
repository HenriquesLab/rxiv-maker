# Release Process Guide

This document outlines the complete release process for rxiv-maker, including automated workflows, package manager updates, and manual steps.

## Overview

The rxiv-maker project uses a comprehensive release pipeline that includes:
- Automated testing across multiple platforms
- Binary distribution for major platforms
- PyPI package publishing
- Homebrew formula updates
- Docker image publishing
- GitHub releases with artifacts

## Release Types

### Patch Releases (v1.4.x)
- Bug fixes
- Minor documentation updates
- Performance improvements
- No breaking changes

### Minor Releases (v1.x.0)
- New features
- Non-breaking API additions
- Significant improvements
- Deprecation warnings

### Major Releases (v2.0.0)
- Breaking changes
- Major feature overhauls
- API redesigns
- Requires migration guide

## Automated Release Process

### 1. Trigger Release Workflow

The release process is triggered by pushing a git tag:

```bash
# Create and push a new tag
git tag v1.4.8
git push origin v1.4.8
```

### Track Changes PDF Generation

For tag-triggered releases, the system automatically generates a track changes PDF for the EXAMPLE_MANUSCRIPT showing differences since the last major version:

- **Automatic Detection**: Identifies the previous major version (e.g., v1.3.0 when releasing v1.4.2)
- **File Naming**: Uses format `{year}__{authors}_et_al__changes_vs_{version}.pdf`
- **LaTeX Diff**: Employs `latexdiff` to highlight additions (blue underlined) and deletions (red strikethrough)
- **Release Integration**: Automatically includes track changes PDF in release assets and notes

Or manually via GitHub Actions workflow dispatch:
- Go to Actions → Release and Binary Distribution
- Click "Run workflow"
- Enter the tag (e.g., `v1.4.8`)

### 2. Automated Pipeline Steps

The release pipeline automatically:

1. **Comprehensive Testing**
   - Runs full test suite on Ubuntu, Windows, macOS
   - Tests Python 3.11 and 3.12
   - Validates all execution engines (local, Docker, Podman)

2. **Binary Distribution**
   - Creates standalone binaries using PyInstaller
   - Builds for Linux x64, Windows x64, macOS x64/ARM64
   - Optimizes binaries with UPX compression
   - Uploads artifacts to GitHub release

3. **GitHub Release Creation**
   - Creates release notes from CHANGELOG.md
   - Attaches binary artifacts and PDFs (including track changes)
   - Marks as pre-release or stable based on version

## Package Manager Updates

### PyPI Publishing

**Automated via GitHub Actions:**
- Uses trusted publishing (no API tokens required)
- Builds source and wheel distributions
- Publishes to PyPI on successful release

**Manual Publishing (if needed):**
```bash
# Build distributions
uv build

# Upload to PyPI (requires API token)
uv publish
```

### Homebrew Formula Updates

**Location:** `submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb`

**Automated Process:**
1. Release orchestrator triggers Homebrew update workflow
2. Formula template is updated with new version and SHA256
3. Pull request is created to `homebrew-rxiv-maker` repository
4. CI validates the formula
5. Formula is published after validation

**Manual Update (if needed):**
```bash
# Update Homebrew formula
cd submodules/homebrew-rxiv-maker
./scripts/update-formula.sh v1.4.8

# Test formula locally
brew install --build-from-source ./Formula/rxiv-maker.rb
brew test rxiv-maker
```

### Docker Image Updates

**Location:** `src/docker/images/base/`

**Automated Process:**
1. Docker images are built for multiple platforms (amd64, arm64)
2. Images are tagged with version and latest
3. Images are pushed to Docker Hub
4. Runtime dependency injection system is tested

**Manual Update (if needed):**
```bash
# Build Docker image locally
docker build -t henriqueslab/rxiv-maker-base:v1.4.8 -f src/docker/images/base/Dockerfile .

# Test Docker image
docker run --rm henriqueslab/rxiv-maker-base:v1.4.8 python3 --version
```

## Release Checklist

### Pre-Release

- [ ] All tests passing in CI
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with new version
- [ ] Version bumped in `src/rxiv_maker/__version__.py`
- [ ] No open critical issues
- [ ] Dependencies up to date

### During Release

- [ ] Tag created and pushed
- [ ] GitHub Actions workflow completed successfully
- [ ] All artifacts uploaded to GitHub release (including track changes PDF)
- [ ] PyPI package published
- [ ] Package managers updated (Homebrew)
- [ ] Docker images published
- [ ] Release notes reviewed and published

### Post-Release

- [ ] Homebrew formula working (test installation)
- [ ] PyPI installation working (`pip install rxiv-maker`)
- [ ] Docker images working (`docker run henriqueslab/rxiv-maker-base:latest`)
- [ ] Documentation site updated
- [ ] Social media/community announcements

## Version Management

### Version File
Update version in `src/rxiv_maker/__version__.py`:
```python
__version__ = "1.4.8"
```

### Version Detection
The release workflow automatically detects version from:
1. Git tag (preferred): `v1.4.8`
2. Version file: `src/rxiv_maker/__version__.py`
3. pyproject.toml (dynamic versioning)

## Troubleshooting Release Issues

### Failed Binary Builds
- Check PyInstaller compatibility with new dependencies
- Verify UPX compression works on all platforms
- Review build logs in GitHub Actions

### Package Manager Update Failures
- **Homebrew**: Check formula syntax and dependency changes
- **Docker**: Verify image builds and pushes correctly
- **PyPI**: Ensure wheel builds correctly on all platforms

### Release Rollback
If a release has critical issues:

1. **Remove from PyPI** (if possible within 72 hours)
2. **Revert Homebrew formula** to previous version
3. **Revert Docker images** by promoting previous tag to latest
4. **Mark GitHub release** as pre-release
5. **Create hotfix release** with fixes

## Manual Release Steps (Emergency)

If automated systems fail, manual release can be performed:

### 1. Build and Test Locally
```bash
# Run full test suite
nox -s tests

# Build package
uv build

# Test installation
pip install dist/rxiv_maker-*.whl
```

### 2. Upload to PyPI
```bash
# Upload to PyPI
uv publish
```

### 3. Create GitHub Release
- Go to GitHub → Releases → Create a new release
- Add tag and release notes
- Upload binary artifacts manually

### 4. Update Package Managers
```bash
# Update Homebrew
cd submodules/homebrew-rxiv-maker
./scripts/update-formula.sh v1.4.8

# Update Docker images
docker build -t henriqueslab/rxiv-maker-base:v1.4.8 -f src/docker/images/base/Dockerfile .
docker push henriqueslab/rxiv-maker-base:v1.4.8
```

## Release Monitoring

### Automated Monitoring
The release orchestrator monitors:
- Package manager update status
- Installation success rates
- User reports and issues

### Manual Verification
After each release, verify:
- Installation from all package managers
- Basic functionality tests
- Documentation accessibility
- No broken links or references

## Contact and Support

For release-related issues:
- **GitHub Issues**: Technical problems with releases
- **Email**: rxiv.maker@gmail.com for urgent release issues
- **Discussions**: GitHub Discussions for release feedback

---

## Appendix: Release Automation Scripts

### Key Scripts
- `scripts/orchestrate-release.py`: Main release orchestration
- `scripts/generate-track-changes.sh`: Generate track changes PDFs for releases
- `scripts/fetch-package-sha256.py`: SHA256 calculation for packages
- `scripts/update-package-templates.py`: Update package manager templates
- `scripts/validate-package-templates.py`: Validate package configurations

### Configuration Files
- `.github/workflows/release.yml`: Main release workflow  
- `submodules/homebrew-rxiv-maker/Formula/rxiv-maker.rb`: Homebrew formula
- `src/docker/images/base/Dockerfile`: Docker image configuration

This process ensures reliable, automated releases while maintaining flexibility for manual intervention when needed.