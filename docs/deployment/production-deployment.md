# Production Deployment Guide

This guide provides step-by-step instructions for deploying the updated rxiv-maker package to production after successful test-pypi validation.

## Prerequisites

- ✅ Test PyPI deployment completed successfully
- ✅ AppVeyor tests passing
- ✅ Homebrew formula tested with test-pypi
- ✅ All functionality verified

## Deployment Steps

### 1. Final Testing

Before production deployment, run the complete test suite:

```bash
# Run all tests
nox -s tests

# Test CLI functionality
source .venv/bin/activate
rxiv --help
rxiv check-installation --json

# Test manual system dependency installation
rxiv-install-deps --help

# Verify no automatic system dependencies
python setup.py --help-commands  # Should not trigger system installs
```

### 2. Version Management

Update version for production release:

```bash
# Create release tag
git tag v1.4.0
git push origin v1.4.0

# Build with production version
hatch build
```

### 3. Production PyPI Deployment

```bash
# Set up production PyPI authentication
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-production-token-here

# Deploy to production PyPI
hatch publish

# Verify deployment
pip install --upgrade rxiv-maker
rxiv --version
```

### 4. Update Homebrew Formula

```bash
# Update formula for production
cd homebrew-rxiv-maker/Formula/

# Remove test-pypi option (optional)
# Or keep it for future testing

# Update version and URL
# This will be done automatically by the update workflow
```

### 5. GitHub Release

Create a GitHub release with changelog:

```bash
# Create release via GitHub CLI
gh release create v1.4.0 \
  --title "v1.4.0 - Remove automatic system dependency installation" \
  --notes-file CHANGELOG.md \
  --generate-notes
```

### 6. Update Documentation

Update all documentation to reflect changes:

```bash
# Update README.md
# Update installation instructions
# Update troubleshooting guides

# Commit documentation updates
git add docs/ README.md
git commit -m "Update documentation for v1.4.0 release"
git push origin main
```

## Post-Deployment Verification

### 1. Test Production Installation

```bash
# Test pip install (should only install Python dependencies)
pip install --upgrade rxiv-maker

# Test manual system dependencies
rxiv-install-deps --mode full

# Test CLI functionality
rxiv init test-project
cd test-project
rxiv validate
```

### 2. Test Homebrew Installation

```bash
# Test Homebrew installation
brew upgrade rxiv-maker

# Or fresh install
brew uninstall rxiv-maker
brew install rxiv-maker
```

### 3. Monitor for Issues

- Check GitHub Issues for reports
- Monitor PyPI download statistics
- Review AppVeyor build logs
- Test on different platforms

## Rollback Procedure

If critical issues are discovered:

### 1. Immediate Actions

```bash
# Create hotfix branch
git checkout -b hotfix/v1.4.1

# Fix critical issues
# Run tests
nox -s tests

# Deploy hotfix
git tag v1.4.1
hatch build
hatch publish

# Update Homebrew formula
```

### 2. Communication

- Post issue updates on GitHub
- Notify users via release notes
- Update documentation with known issues

## Success Metrics

- ✅ PyPI deployment successful
- ✅ No automatic system dependency installation
- ✅ All CLI commands functional
- ✅ Homebrew formula working
- ✅ No breaking changes reported
- ✅ Documentation updated

## Security Considerations

- API tokens stored securely
- Package signatures verified
- No sensitive information in package
- Dependencies security scanned

## Maintenance

### Regular Updates

- Monitor for security updates
- Update dependencies regularly
- Test with new Python versions
- Keep documentation current

### Monitoring

- PyPI download statistics
- GitHub issue reports
- User feedback
- Performance metrics

## Support

For deployment issues:
- Check GitHub Issues
- Review deployment logs
- Contact maintainers
- Consult documentation

## Automated Deployment (Future)

Consider setting up:
- GitHub Actions for automated releases
- Automated testing pipeline
- Dependency update automation
- Security scanning integration

This completes the production deployment process for the updated rxiv-maker package with removed automatic system dependency installation.