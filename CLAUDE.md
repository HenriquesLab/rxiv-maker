# Claude Instructions & Style Guide

This file provides comprehensive guidance for AI assistants working on rxiv-maker development, including coding standards, security practices, and development workflows.

## 🎯 Core Development Principles

### 1. **Code Quality First**
- Write self-documenting code with clear variable names
- Use type hints consistently throughout Python code
- Follow PEP 8 standards with ruff formatting
- Maintain comprehensive test coverage (aim for >80%)

### 2. **Security by Design**
- Validate all user inputs at boundaries
- Use parameterized queries for database operations
- Sanitize file paths and shell commands
- Follow principle of least privilege

### 3. **Performance Awareness**
- Profile before optimizing
- Use appropriate data structures
- Cache expensive operations
- Consider memory usage for large files

## Development Environment Setup

### Initial Setup
- **NEVER install packages at system level**
- **ALWAYS use the virtual environment (.venv)**
- **Use uv for modern dependency management when available**

```bash
# Recommended setup
pip install -e ".[dev]"
pre-commit install

# Alternative with uv (if available)
uv pip install -e ".[dev]"
```

### Development Dependencies
Install development dependencies for full functionality:
```bash
# Full development environment
pip install -e ".[dev]"  # Includes pytest, ruff, mypy, pre-commit, etc.

# Or specify directly
pip install pytest pytest-cov pytest-xdist ruff mypy pre-commit hatch build
```

## Testing Commands

### Primary Testing (Nox-based - Recommended)
The project uses Nox for automated testing workflows:

```bash
# Main testing commands
nox -s test                    # Full test suite (default)
nox -s test-unit              # Unit tests only (fastest)
nox -s test-integration       # Integration tests only
nox -s test-fast              # Fast tests for development
nox -s test-smoke             # Ultra-fast smoke tests
nox -s test-system            # System tests (manual trigger)

# Cross-platform testing
nox -s test_cross             # Test across Python versions
nox -s test_cli_e2e          # End-to-end CLI testing with package build
```

### Local Testing
```bash
# Test with local engine (only supported engine)
nox -s pdf                    # Test PDF generation (local)
```

### Direct pytest Commands
```bash
# Direct pytest usage
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests
pytest tests/system/ -v                  # System tests
pytest tests/ -m "fast"                  # Fast tests only
pytest tests/ -m "not slow"              # Exclude slow tests
pytest tests/ --maxfail=3               # Stop after 3 failures

# Coverage testing
pytest --cov=src/rxiv_maker tests/
```

### Legacy Commands (Still Supported)
```bash
# rxiv CLI commands
rxiv pdf                      # Generate PDF from manuscript
rxiv clean                    # Clean output files
rxiv check-installation      # Verify installation
```

## Code Quality Commands

### Linting and Formatting
```bash
# Nox-based (recommended)
nox -s lint                   # Run linting checks
nox -s format                 # Format code (auto-fix)

# Direct ruff usage
ruff check src/ tests/        # Lint code
ruff format src/ tests/       # Format code
ruff check --fix src/         # Lint with auto-fix
```

### Type Checking
```bash
# Type checking with mypy
mypy src/rxiv_maker
nox -s type-check            # Via nox (if available)
```

### Security Scanning
```bash
nox -s security              # Security vulnerability scanning
```

## Build and Development Commands

### Package Building
```bash
# Build package
nox -s build                 # Full build and validation
hatch build                  # Build with hatch
python -m build              # Standard build

# Test installation
pip install dist/*.whl       # Install built wheel
```

### Development Validation
```bash
# Check installation and dependencies
rxiv check-installation      # Verify setup
rxiv --version               # Check version
rxiv --help                  # Show help

# Validate manuscript
rxiv validate MANUSCRIPT/    # Validate manuscript structure
```

## Repository Management

rxiv-maker supports managing multiple manuscript repositories with GitHub integration.

### Initial Setup
```bash
# Interactive setup
rxiv repo-init

# Manual configuration
rxiv config set-repo-parent-dir ~/manuscripts
rxiv config set-repo-org HenriquesLab
rxiv config set-repo-editor code
```

### Repository Commands
```bash
# Create new manuscript repository (manuscript-{name} prefix)
rxiv create-repo my-paper            # Local only
rxiv create-repo my-paper --github   # With GitHub repo creation

# List all repositories with status
rxiv repos                           # Shows git status, uncommitted changes

# Search and clone from GitHub
rxiv repos-search my-paper           # Interactive search/clone
```

### Configuration Management
```bash
# Interactive configuration menu (default)
rxiv config

# Non-interactive mode (show current settings)
rxiv config --non-interactive

# Direct configuration commands (non-interactive)
rxiv config show                     # Show manuscript config
rxiv config show-repo                # Show repository config
rxiv config set-repo-parent-dir PATH # Set parent directory
rxiv config set-repo-org ORG         # Set GitHub organization
rxiv config set-repo-editor EDITOR   # Set default editor
```

### Repository Structure
- **Naming pattern**: `manuscript-{name}`
- **Structure**: Each repository contains a `MANUSCRIPT/` folder with rxiv-maker content
- **Global config**: `~/.rxiv-maker/config` (separate from manuscript-level config)
- **Parent directory**: All manuscript repos stored in configured parent directory

### Integration with PythonRepoMaster
Repository management is designed to work with [PythonRepoMaster](../PythonRepoMaster) alignment checks. See `../PythonRepoMaster/config/repo_relationships.yaml` for relationship definitions.

## Engine Configuration

### Local Development (Primary Method)
```bash
# Local engine (requires LaTeX installation)
rxiv pdf MANUSCRIPT/

# Or via Make (legacy)
make pdf
```

**LaTeX Requirements for Local Development:**
- Local PDF generation requires a LaTeX installation (pdflatex, bibtex)
- Install via: `brew install texlive` (macOS) or `sudo apt-get install texlive-full` (Linux)
- The Homebrew formula (`brew install rxiv-maker`) includes texlive as a dependency
- Check installation: `rxiv check-installation`

### Docker-based Development (Alternative Method)
For testing without installing LaTeX locally, use the `../docker-rxiv-maker` repository:

```bash
# Using pre-built image (recommended for testing)
docker run -it --rm -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest rxiv pdf .

# Interactive terminal
docker run -it --rm -v $(pwd):/workspace henriqueslab/rxiv-maker-base:latest

# Test the docker-rxiv-maker repository itself
cd ../docker-rxiv-maker
./test-docker-image.sh henriqueslab/rxiv-maker-base:latest
```

**docker-rxiv-maker Details:**
- Repository: `../docker-rxiv-maker` (maintained separately)
- Pre-installed: rxiv-maker + TeX Live + Python + R + all dependencies
- Tags: `latest` (PyPI stable), `dev` (GitHub main), `weekly`, version tags
- Full documentation: See `../docker-rxiv-maker/README.md`
- Use for: CI/CD, testing without local LaTeX, reproducible builds

**Note**: Docker/Podman engine support was removed from the main rxiv-maker codebase. Use docker-rxiv-maker repository for containerized execution.

## Common Development Workflows

### Pre-commit Workflow
```bash
# Install and run pre-commit hooks
pre-commit install
pre-commit run --all-files    # Run on all files
pre-commit run               # Run on staged files
```

### Before Submitting PRs
```bash
# Recommended workflow before committing
nox -s lint                  # Check code quality
nox -s test-fast            # Run fast tests
nox -s test-unit            # Ensure unit tests pass

# Full validation
nox -s test                 # Run full test suite (if time permits)
```

### Testing Specific Components
```bash
# Test specific areas
pytest tests/unit/test_figure_processor.py -v     # Test figure processing
pytest tests/unit/test_citation_processor.py -v   # Test citations
pytest tests/cli/ -v                              # Test CLI commands
pytest tests/integration/test_article_generation.py -v  # Test article generation
```

### Performance and Cleanup
```bash
# Cleanup commands
nox -s clean                 # Clean nox environments  
nox -s clean_all            # Aggressive cleanup
nox -s disk_usage          # Check disk usage
```

## Project Context

### Testing Strategy
- **Unit tests**: Fast, isolated component testing
- **Integration tests**: Component interaction testing  
- **System tests**: End-to-end workflow testing
- **Smoke tests**: Quick validation of basic functionality
- **CLI tests**: Command-line interface testing

### Engine Architecture
- **Local**: Uses system-installed LaTeX/dependencies (primary development method)
- **Containerized**: Use `../docker-rxiv-maker` repository for Docker-based testing and deployment
  - Pre-built images available at `henriqueslab/rxiv-maker-base`
  - Includes full TeX Live installation and all dependencies
  - Recommended for CI/CD and testing without local LaTeX

### Key Tools
- **Nox**: Task automation and testing orchestration
- **Ruff**: Modern Python linting and formatting (replaces black, isort, flake8)
- **MyPy**: Static type checking
- **Pytest**: Testing framework with extensive plugin ecosystem
- **Hatch**: Modern Python build backend
- **uv**: Fast Python package installer (when available)

### Ecosystem Repositories
The rxiv-maker ecosystem consists of interconnected repositories:

**Core Repositories:**
- **rxiv-maker** (this repository): Main Python package and CLI tool
- **docker-rxiv-maker**: Containerized execution with pre-installed environment
- **manuscript-rxiv-maker**: Official preprint (arXiv:2508.00836) and comprehensive example
- **rxiv-maker.henriqueslab.org**: Official documentation website
- **vscode-rxiv-maker**: VS Code extension with syntax highlighting and IntelliSense

**Website Documentation:**
- **⚠️ IMPORTANT**: The website-rxiv-maker repository is **private** - do NOT reference it in public documentation
- **Public reference**: Always use https://rxiv-maker.henriqueslab.org (the deployed website)
- **Built with**: MkDocs Material
- **Deployed via**: Cloudflare Pages
- **Purpose**: User guides, tutorials, API reference, and getting started documentation
- **Local development** (for maintainers): `cd ../website-rxiv-maker && mkdocs serve`

## Common Patterns

### When Adding New Features
1. Write unit tests first: `tests/unit/test_new_feature.py`
2. Run tests: `nox -s test-unit`
3. Implement feature in `src/rxiv_maker/`
4. Run integration tests: `nox -s test-integration`
5. Update CLI if needed and test: `nox -s test_cli_e2e`

### When Debugging Issues
1. Run relevant test category: `pytest tests/unit/ -k "test_name" -v`
2. Local testing requires LaTeX installation (check with `rxiv check-installation`)
3. Check logs and use verbose output: `pytest -v -s`
4. For testing without LaTeX: Use docker-rxiv-maker (`cd ../docker-rxiv-maker && ./test-docker-image.sh henriqueslab/rxiv-maker-base:latest`)
5. Verify docker-rxiv-maker works with latest changes before releases

### Before Releases
1. Full test suite: `nox -s test`
2. Cross-platform testing: `nox -s test_cross`
3. Build validation: `nox -s build`
4. CLI end-to-end testing: `nox -s test_cli_e2e`
5. Docker integration testing: Test with docker-rxiv-maker to ensure containerized execution works
   ```bash
   cd ../docker-rxiv-maker
   ./test-docker-image.sh henriqueslab/rxiv-maker-base:dev
   ```

### Testing Best Practices

**Version Bumps and Test Fixtures:**
When bumping the version number for a release, check and update test fixtures that reference version numbers or changelog data:
- Update `sample_changelog` fixtures in `tests/cli/test_changelog_command.py` to include the new version
- Update `__version__` references in test files if they explicitly check version strings
- Example: After bumping to v1.13.6, add the new version entry to changelog test fixtures

**CLI Testing with Rich Formatting:**
The CLI uses Rich library for colored output, which adds ANSI escape codes. When testing CLI output:
- Use the `strip_ansi()` helper function before making string assertions
- Example pattern:
  ```python
def strip_ansi(text):
    """Remove ANSI escape codes from text for testing."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)

# In tests:
output = strip_ansi(result.output)
assert "Expected text" in output
  ```
- Without `strip_ansi()`, assertions may fail because Rich splits text like '📋 Fetching changelog...' into '\x1b[34m📋 Fetching changelog\x1b[0m\x1b[33m...\x1b[0m'

**Test Data Currency:**
- When adding new features with time-sensitive data (versions, dates), ensure test fixtures remain current
- Consider using relative version references or dynamic data generation where appropriate
- Document fixture maintenance requirements in test docstrings

## Homebrew Formula Management

rxiv-maker is distributed via PyPI and Homebrew. After creating a new release, the Homebrew formula must be updated to match.

### ⚠️ IMPORTANT: Automatic Formula Updates (For Claude)

**Claude should automatically monitor for new releases and update the Homebrew formula:**

1. **Monitor for releases**: After any PR is merged or when asked to check releases, verify if a new GitHub release has been published
2. **Detect new PyPI versions**: Check https://pypi.org/project/rxiv-maker/ for new versions
3. **Automatic update**: When a new release is detected, automatically:
   - Navigate to `../homebrew-formulas`
   - Run `just release rxiv-maker` to update the formula
   - Verify the update was successful
4. **Proactive checking**: When asked about releases, project status, or after significant PRs, check for new releases

**This process should happen automatically without explicit user request.**

### Release Process

1. **Release to PyPI** (via GitHub release workflow)
2. **Verify the release is live** on https://pypi.org/project/rxiv-maker/
3. **Update the Homebrew formula** in the `../homebrew-formulas` repository (Claude does this automatically)

### Homebrew Formula Location

The Homebrew formula is maintained in a separate repository located at `../homebrew-formulas`:
- **Repository**: `../homebrew-formulas/`
- **Formula file**: `Formula/rxiv-maker.rb`
- **Automation**: Managed via justfile commands

### Commands

After releasing to PyPI and verifying the release is available:

```bash
cd ../homebrew-formulas

# Option 1: Full automated release workflow (recommended)
# This will update, test, commit, and push in one command
just release rxiv-maker

# Option 2: Manual step-by-step workflow
just update rxiv-maker           # Updates to latest PyPI version
just test rxiv-maker             # Tests the formula installation
just commit rxiv-maker VERSION   # Commits with standardized message
git push                         # Push to remote

# Utility commands
just list                        # List all formulas with current versions
just check-updates               # Check for available PyPI updates
just sha256 rxiv-maker VERSION   # Get SHA256 for a specific version
```

### Workflow Notes

- **Always verify PyPI first**: The formula update pulls package info from PyPI, so the release must be live
- **Automatic metadata**: The `just update` command automatically fetches the version, download URL, and SHA256 checksum from PyPI
- **Full automation**: The `just release` command runs the complete workflow: update → test → commit → push
- **Standardized commits**: Formula updates use consistent commit message format
- **Testing**: The `just test` command uninstalls and reinstalls the formula to verify it works correctly

## Changelog Display Feature

The update checker now includes changelog display functionality:

**Files:**
- `src/rxiv_maker/utils/changelog_parser.py` - Parses CHANGELOG.md and extracts version information
- `src/rxiv_maker/utils/update_checker.py` - Enhanced with changelog integration
- `src/rxiv_maker/cli/commands/changelog.py` - New CLI command for browsing changelog
- `src/rxiv_maker/cli/commands/upgrade.py` - Shows changelog before/after upgrades

**Key Features:**
- Automatically shows 2-3 highlights when update is available
- Prominently displays breaking changes with ⚠️ warnings
- Supports multi-version updates (shows all intermediate versions)
- `rxiv changelog` command for browsing version history
- Caches changelog data to avoid repeated API calls

**Commands:**
```bash
rxiv changelog              # Show current version changes
rxiv changelog v1.13.0      # Show specific version
rxiv changelog --recent 3   # Show last 3 versions
rxiv changelog --since v1.10.0  # Show all since v1.10.0
rxiv changelog --breaking-only  # Filter to breaking changes only
```

**Testing:**
- 35 tests in `test_changelog_parser.py`
- 20 tests in `test_changelog_command.py`
- 5 integration tests in `test_update_checker.py`

### CHANGELOG.md Format Requirements

The changelog parser (used by `rxiv changelog` and update notifications) requires a specific format. **Always follow this format when updating CHANGELOG.md**:

**Version Header Format:**
```markdown
## [vX.Y.Z] - YYYY-MM-DD
```

**Section Headers (must be level 3):**
- `### Added` - New features
- `### Changed` - Changes in existing functionality
- `### Fixed` - Bug fixes
- `### Removed` - Removed features
- `### Documentation` - Documentation changes
- `### Security` - Security fixes

**Breaking Changes:**
Mark breaking changes prominently using one of these methods:
```markdown
### Changed
- **BREAKING**: Description of breaking change

### Security
- ⚠️ Description of security issue
```

**Important:** The parser depends on this exact format to extract and display changelog information. Changes to the format may break the `rxiv changelog` command and update notifications.

## Release Process Overview

Rxiv-maker is distributed through multiple channels. Understanding the release ecosystem helps when making changes that might affect releases:

**Distribution Channels:**
- **PyPI**: Python package index (`pip install rxiv-maker`)
- **Homebrew**: macOS package manager (`brew install rxiv-maker`)
- **Docker**: Containerized environment via `../docker-rxiv-maker` repository (`henriqueslab/rxiv-maker-base`)
- **Website**: Documentation at rxiv-maker.henriqueslab.org via `../website-rxiv-maker`

**Pre-Release Testing Requirements:**
Before any release, these must pass:
- Full test suite: `nox -s test`
- Cross-platform tests: `nox -s test_cross`
- CLI end-to-end tests: `nox -s test_cli_e2e`
- Linting: `nox -s lint`
- Type checking: `nox -s type-check`
- Docker integration: Test with `../docker-rxiv-maker`
- Example manuscript: Test with `../manuscript-rxiv-maker`

**Version Numbering (Semantic Versioning):**
- **MAJOR** (1.0.0 → 2.0.0): Breaking API changes, removal of deprecated features, changes requiring migration
- **MINOR** (1.1.0 → 1.2.0): New features (backward compatible), new commands, deprecation warnings
- **PATCH** (1.1.1 → 1.1.2): Bug fixes, documentation updates, security patches

**Release Workflow:**
1. GitHub release is created → triggers GitHub Actions
2. Actions build and upload to PyPI automatically
3. Maintainer updates Homebrew formula in `../homebrew-formulas` using `just release rxiv-maker`
4. Docker builds automatically trigger for `latest`, `dev`, and version tags
5. Documentation website updated in `../website-rxiv-maker` if needed

**Note for Claude:** You don't need to perform releases, but understanding this process helps when:
- Updating CHANGELOG.md (must follow correct format)
- Making changes that affect Docker or Homebrew packaging
- Testing changes across the ecosystem before suggesting PRs
- Understanding why certain tests are required

