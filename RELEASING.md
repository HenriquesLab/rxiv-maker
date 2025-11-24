# Release Process for Rxiv-Maker

This document provides a comprehensive checklist for maintainers releasing new versions of rxiv-maker across all platforms and distribution channels.

## 📋 Overview

Rxiv-maker is distributed through multiple channels:
- **PyPI**: Python package index (`pip install rxiv-maker`)
- **Homebrew**: macOS package manager (`brew install rxiv-maker`)
- **Docker**: Containerized environment (`henriqueslab/rxiv-maker-base`)
- **Website**: Documentation at rxiv-maker.henriqueslab.org

## 🎯 Pre-Release Checklist

### Code Quality

- [ ] All tests passing locally (`nox -s test`)
- [ ] Cross-platform testing complete (`nox -s test_cross`)
- [ ] CLI end-to-end tests passing (`nox -s test_cli_e2e`)
- [ ] No linting errors (`nox -s lint`)
- [ ] Type checking passes (`nox -s type-check`)
- [ ] Documentation builds without errors

### Version Preparation

- [ ] CHANGELOG.md updated with all changes
- [ ] Version number decided (following SemVer)
- [ ] Breaking changes clearly documented
- [ ] Migration guide written (if breaking changes)

### Testing with Ecosystem

- [ ] Test with manuscript-rxiv-maker example
  ```bash
  cd ../manuscript-rxiv-maker/MANUSCRIPT
  rxiv pdf
  ```
- [ ] Test with docker-rxiv-maker `dev` tag
  ```bash
  cd ../docker-rxiv-maker
  ./test-docker-image.sh henriqueslab/rxiv-maker-base:dev
  ```
- [ ] VS Code extension tested with latest changes

## 🚀 Release Steps

### Step 1: Create GitHub Release

1. Go to https://github.com/HenriquesLab/rxiv-maker/releases/new
2. Click "Choose a tag" and create new tag: `v1.X.Y`
3. Set release title: `v1.X.Y - Brief Description`
4. Copy relevant CHANGELOG.md entries to release notes
5. Add highlights and breaking changes at top
6. Check "Set as the latest release"
7. Click "Publish release"

**Result**: GitHub Actions automatically:
- Builds Python package
- Uploads to PyPI
- Creates release artifacts

### Step 2: Verify PyPI Release

1. Wait 5-10 minutes for GitHub Actions to complete
2. Check https://pypi.org/project/rxiv-maker/
3. Verify new version is live
4. Test installation:
   ```bash
   pip install --upgrade rxiv-maker
   rxiv --version
   ```

### Step 3: Update Homebrew Formula

**Location**: `../homebrew-formulas` repository

```bash
cd ../homebrew-formulas

# Option 1: Full automated workflow (recommended)
just release rxiv-maker

# Option 2: Manual step-by-step
just update rxiv-maker           # Updates to latest PyPI version
just test rxiv-maker             # Tests the formula
just commit rxiv-maker VERSION   # Commits with standardized message
git push                         # Push to remote
```

**What this does**:
- Fetches latest version from PyPI
- Updates formula file with new version and SHA256
- Tests installation in clean environment
- Creates standardized commit message
- Pushes to GitHub

**Verify**:
```bash
brew update
brew upgrade rxiv-maker
rxiv --version
```

### Step 4: Verify Docker Integration

**Location**: `../docker-rxiv-maker` repository

The docker-rxiv-maker repository automatically:
- Builds `dev` tag on main branch pushes
- Builds `latest` tag on GitHub releases
- Builds version tags (e.g., `v1.8.1`) on releases

**Test the release**:
```bash
cd ../docker-rxiv-maker

# Wait ~30 minutes for multi-platform build to complete
# Check https://hub.docker.com/r/henriqueslab/rxiv-maker-base/tags

# Test latest tag
./test-docker-image.sh henriqueslab/rxiv-maker-base:latest

# Test version tag
./test-docker-image.sh henriqueslab/rxiv-maker-base:v1.X.Y
```

### Step 5: Update Documentation Website

**Location**: `../website-rxiv-maker` repository

Check if documentation needs updates:
- [ ] New features documented in user guides
- [ ] API reference updated (if API changes)
- [ ] Installation instructions still accurate
- [ ] Troubleshooting updated with known issues
- [ ] Migration guide added (if breaking changes)

```bash
cd ../website-rxiv-maker

# Make necessary updates
vim docs/...

# Test locally
mkdocs serve

# Commit and push (deployment is automatic)
git add .
git commit -m "docs: Update for v1.X.Y release"
git push
```

**Note**: Cloudflare Pages automatically deploys on push to `main`

### Step 6: Announce Release

- [ ] Post in GitHub Discussions
- [ ] Update README badges if needed
- [ ] Tweet/social media (if significant release)
- [ ] Notify collaborators using manuscript-rxiv-maker

## 📊 Post-Release Verification

### 24 Hours After Release

- [ ] Monitor GitHub Issues for bug reports
- [ ] Check PyPI download stats
- [ ] Verify Homebrew installation working
- [ ] Check Docker Hub pull counts
- [ ] Review any user feedback

### 1 Week After Release

- [ ] Address any critical bugs with patch release
- [ ] Update documentation based on user questions
- [ ] Plan next release cycle

## 🐛 Hotfix Releases

For critical bugs requiring immediate fix:

1. **Create hotfix branch** from latest release tag
   ```bash
   git checkout -b hotfix/v1.X.Y+1 v1.X.Y
   ```

2. **Fix the bug** with minimal changes
3. **Test thoroughly** - focus on the fix
4. **Update CHANGELOG** with hotfix entry
5. **Follow normal release process** with patch version bump
6. **Merge hotfix** back to main
   ```bash
   git checkout main
   git merge hotfix/v1.X.Y+1
   git push
   ```

## 🔄 Release Cadence

- **Patch releases** (bug fixes): As needed
- **Minor releases** (new features): Monthly or when features ready
- **Major releases** (breaking changes): Quarterly or as needed

## 📝 Version Numbering Guide

Following [Semantic Versioning](https://semver.org/):

**MAJOR version** (1.0.0 → 2.0.0):
- Breaking API changes
- Removal of deprecated features
- Major architectural changes
- Changes requiring user migration

**MINOR version** (1.1.0 → 1.2.0):
- New features (backward compatible)
- Significant enhancements
- New commands or options
- Deprecation warnings (not removal)

**PATCH version** (1.1.1 → 1.1.2):
- Bug fixes
- Documentation updates
- Minor improvements
- Security patches

## 🛠️ Rollback Procedure

If a release has critical issues:

1. **Yank from PyPI** (doesn't delete, just hides)
   - Only do this for security issues
   - Otherwise, release a hotfix

2. **Revert Homebrew formula**
   ```bash
   cd ../homebrew-formulas
   git revert HEAD
   git push
   ```

3. **Update Docker tags**
   - Cannot remove tags, push new build with ` old version
   - Update `latest` tag to previous version

4. **Announce** via GitHub Issues and Discussions

## 📞 Emergency Contacts

For release issues:
- **PyPI access**: Contact project maintainers
- **Homebrew tap**: Maintainers have push access to homebrew-formulas
- **Docker Hub**: Automated via GitHub Actions
- **Cloudflare Pages**: Automatic deployment, check Cloudflare dashboard

## ✅ Release Checklist Template

Copy this for each release:

```markdown
## Release vX.Y.Z Checklist

### Pre-Release
- [ ] Tests passing
- [ ] CHANGELOG updated
- [ ] Version decided
- [ ] Ecosystem tested

### Release
- [ ] GitHub release created
- [ ] PyPI verified
- [ ] Homebrew formula updated
- [ ] Docker integration verified
- [ ] Documentation updated
- [ ] Release announced

### Post-Release (24h)
- [ ] Issues monitored
- [ ] Downloads verified
- [ ] User feedback reviewed

### Post-Release (1 week)
- [ ] Critical bugs addressed
- [ ] Documentation refined
```

## 🎓 First-Time Release Guide

For maintainers doing their first release:

1. **Shadow a release** - Watch experienced maintainer
2. **Read this document** thoroughly
3. **Do a test run** on a fork
4. **Start with patch release** - Lower stakes
5. **Ask questions** - Better to clarify than mess up

## 📚 Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - General contribution guidelines
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [../homebrew-formulas/README.md](../homebrew-formulas/README.md) - Homebrew management
- [../docker-rxiv-maker/README.md](../docker-rxiv-maker/README.md) - Docker details
- [../website-rxiv-maker/README.md](../website-rxiv-maker/README.md) - Website documentation

---

**Last Updated**: November 2025
**Maintainer**: Rxiv-Maker Team
