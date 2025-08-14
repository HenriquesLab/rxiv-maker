"""Streamlined Nox configuration for Rxiv-Maker testing."""

import nox

# Configure nox to use uv as the default backend for faster environment creation
nox.options.default_venv_backend = "uv"

# Enable environment reuse to reduce disk usage and improve performance
nox.options.reuse_existing_virtualenvs = True

# Set default sessions for local development workflow
nox.options.sessions = ["lint", "test(test_type='full')"]

# Configuration constants
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]
ENGINES = ["local", "docker", "podman"]

# Common dependencies
TEST_DEPS = [
    "pytest>=7.4.0",
    "pytest-cov>=4.0",
    "pytest-timeout>=2.4.0",
    "pytest-xdist>=3.8.0",
]

LINT_DEPS = ["ruff>=0.8.0", "mypy>=1.0.0"]
DOC_DEPS = ["lazydocs>=0.4.8"]
SECURITY_DEPS = ["bandit>=1.7.5", "safety>=2.3.5", "pip-audit>=2.6.1"]


def install_project_deps(session):
    """Install project and test dependencies efficiently using uv."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run("uv", "pip", "install", *TEST_DEPS, external=True)


def check_engine_availability(session, engine):
    """Check if the specified engine is available on the system."""
    if engine != "local":
        try:
            # Check if binary exists
            session.run(engine, "--version", external=True, silent=True)
            # Check if daemon/service is running
            session.run(engine, "ps", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available or daemon not running")


# Core Development Sessions
@nox.session(python="3.11", reuse_venv=True)
def lint(session):
    """Run comprehensive linting checks."""
    session.run("uv", "pip", "install", *LINT_DEPS, external=True)
    session.run("ruff", "check", "src/", "tests/")
    session.run("ruff", "format", "--check", "src/", "tests/")


@nox.session(python="3.11", reuse_venv=True)
def format(session):
    """Format code with ruff (auto-fix)."""
    session.run("uv", "pip", "install", "ruff>=0.8.0", external=True)
    session.run("ruff", "format", "src/", "tests/")
    session.run("ruff", "check", "--fix", "src/", "tests/")


@nox.session(python="3.11", reuse_venv=True)
@nox.parametrize("test_type", ["unit", "integration", "fast", "full"])
def test(session, test_type):
    """Unified test session with different execution modes.

    Usage:
        nox -s test-unit      # Unit tests only (fastest, <1 min)
        nox -s test-integration  # Integration tests only (<5 min)
        nox -s test-fast      # Fast tests only (<2 min)
        nox -s test-full      # Full test suite (<10 min)
        nox -s test           # Default to full test suite
    """
    install_project_deps(session)

    if test_type == "unit":
        # Unit tests only - fastest feedback
        session.run(
            "pytest",
            "tests/unit/",
            "--maxfail=3",
            "--tb=short",
            "-x",  # Stop on first failure for fast feedback
            *session.posargs,
        )
    elif test_type == "integration":
        # Integration tests only - moderate feedback
        session.run(
            "pytest",
            "tests/integration/",
            "--maxfail=5",
            "--tb=short",
            *session.posargs,
        )
    elif test_type == "fast":
        # Quick development feedback - fast tests only
        session.run(
            "pytest",
            "tests/unit/",
            "-m",
            "unit and not ci_exclude",
            "--maxfail=3",
            "--tb=short",
            "-x",  # Stop on first failure for fast feedback
            *session.posargs,
        )
    elif test_type == "full":
        # Primary test session matching CI behavior with coverage enforcement
        session.run(
            "pytest",
            "tests/unit/",
            "tests/integration/",
            "tests/cli/",
            "-m",
            "not slow and not docker and not ci_exclude and not system",
            "--cov=src",
            "--cov-report=term-missing:skip-covered",
            "--cov-fail-under=85",  # Enforce minimum 85% coverage
            "--maxfail=5",
            *session.posargs,
        )


@nox.session(python="3.11", reuse_venv=True)
def test_system(session):
    """Run system tests - comprehensive end-to-end testing (manual trigger only)."""
    install_project_deps(session)

    session.run(
        "pytest",
        "tests/system/",
        "-m",
        "system",
        "--tb=long",
        "--maxfail=3",
        "-v",
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
def build(session):
    """Package building and validation."""
    session.run("uv", "pip", "install", "build>=1.0.0", "twine>=4.0.0", external=True)

    # Clean previous builds
    session.run("rm", "-rf", "dist/", "build/", external=True)

    # Build package
    session.run("python", "-m", "build")

    # Validate package
    session.run("twine", "check", "dist/*")

    # Test installation
    session.run("bash", "-c", "uv pip install dist/*.whl", external=True)
    session.run("rxiv", "--help")


# Matrix/Specialized Sessions
@nox.session(python="3.11", reuse_venv=True)
@nox.parametrize("engine", ENGINES)
def pdf(session, engine):
    """Test PDF generation with different rxiv engines."""
    check_engine_availability(session, engine)
    install_project_deps(session)

    # Set environment variables for engine
    env = {"RXIV_ENGINE": engine.upper(), "MANUSCRIPT_PATH": "EXAMPLE_MANUSCRIPT"}

    # Test rxiv CLI PDF generation with engine environment variable
    session.run("rxiv", "pdf", "EXAMPLE_MANUSCRIPT", env=env)

    # Test make command PDF generation
    session.run("make", "pdf", env=env, external=True)

    # Validate outputs exist
    session.run("ls", "-la", "output/", external=True)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=False)
def test_cross(session):
    """Cross-version testing for releases (all Python versions)."""
    install_project_deps(session)

    session.run(
        "pytest",
        "tests/unit/",
        "tests/integration/",
        "-m",
        "not docker and not slow",
        "--maxfail=3",
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
def test_docker(session):
    """Docker engine testing (manual trigger only)."""
    check_engine_availability(session, "docker")
    install_project_deps(session)

    # Run Docker-specific tests
    session.run(
        "pytest",
        "tests/unit/test_docker_engine_mode.py",
        "-m",
        "docker",
        "--tb=short",
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
def test_podman(session):
    """Podman engine testing (manual trigger only)."""
    check_engine_availability(session, "podman")
    install_project_deps(session)

    # Run with podman engine using existing integration tests
    session.run(
        "pytest",
        "tests/integration/",
        "--engine=podman",
        "-m",
        "not slow",
        "--tb=short",
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
def security(session):
    """Run comprehensive security checks with automated vulnerability detection."""
    session.run("uv", "pip", "install", *SECURITY_DEPS, external=True)

    # Security vulnerability scanning with enhanced configuration
    session.log("Running pip-audit for known vulnerabilities...")
    session.run("pip-audit", "--format", "json", "--output", "pip-audit-report.json", success_codes=[0, 1])

    session.log("Running safety scan for known vulnerabilities...")
    # Use --output json for non-interactive output, continue on failure to not block CI
    session.run("safety", "scan", "--output", "json", success_codes=[0, 1, 2])

    # Static security analysis
    session.log("Running bandit for static security analysis...")
    session.run("bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json", success_codes=[0, 1])

    session.log("Security scanning completed - check report files for details")


@nox.session(python="3.11", reuse_venv=True)
def docs(session):
    """Generate comprehensive API documentation with validation."""
    session.run("uv", "pip", "install", *DOC_DEPS, external=True)
    install_project_deps(session)

    session.log("Cleaning existing documentation...")
    session.run("rm", "-rf", "docs/api/", external=True)
    session.run("mkdir", "-p", "docs/api/", external=True)

    session.log("Generating API documentation...")
    # Generate comprehensive docs with better configuration
    session.run(
        "lazydocs",
        "src/rxiv_maker/",
        "--output-path",
        "docs/api/",
        "--overview-file",
        "README.md",
        "--src-base-url",
        "https://github.com/HenriquesLab/rxiv-maker/blob/main/",
        success_codes=[0, 1],
    )  # Continue on warning/non-critical errors

    session.log("Documentation generation completed - check docs/api/ directory")


# Utility Sessions
@nox.session(python=False)
def clean(session):
    """Clean up nox environments to free disk space."""
    session.run("rm", "-rf", ".nox/", external=True)
    session.log("Nox environments removed.")


@nox.session(python=False)
def clean_all(session):
    """Clean all nox environments - equivalent to 'nox -s clean -- --all'."""
    session.run("rm", "-rf", ".nox/", external=True)
    session.log("All nox environments cleaned.")
