"""Streamlined Nox configuration for Rxiv-Maker testing."""

import nox

# Configure nox to use uv as the default backend for faster environment creation
nox.options.default_venv_backend = "uv"

# Enable environment reuse to reduce disk usage and improve performance
nox.options.reuse_existing_virtualenvs = True

# Set default sessions for local development workflow
nox.options.sessions = ["lint", "test_fast"]

# Configuration constants
PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]
ENGINES = ["local", "docker"]

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
    """Install project and test dependencies efficiently."""
    session.run("uv", "pip", "install", "-e", ".", external=True)
    session.run("uv", "pip", "install", *TEST_DEPS, external=True)


def check_engine_availability(session, engine):
    """Check if the specified engine is available on the system."""
    if engine != "local":
        try:
            session.run(engine, "--version", external=True, silent=True)
        except Exception:
            session.skip(f"{engine.capitalize()} is not available on this system")


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
def test_fast(session):
    """Quick development feedback - fast tests only (<2 min target)."""
    install_project_deps(session)

    # Run only fast tests, excluding slow and integration tests
    session.run(
        "pytest",
        "tests/unit/",
        "-m",
        "fast or (not slow and not integration and not docker)",
        "--maxfail=3",
        "--tb=short",
        "-x",  # Stop on first failure for fast feedback
        *session.posargs,
    )


@nox.session(python="3.11", reuse_venv=True)
def test(session):
    """Primary test session matching CI behavior (<10 min target)."""
    install_project_deps(session)

    # Run unit and light integration tests, excluding slow/docker tests
    session.run(
        "pytest",
        "tests/unit/",
        "tests/integration/",
        "--ignore=tests/unit/test_docker_engine_mode.py",
        "--ignore=tests/unit/test_platform_detector.py",
        "--ignore=tests/unit/test_figure_generator.py",
        "--ignore=tests/unit/test_github_actions_integration.py",
        "--ignore=tests/unit/test_error_handling_scenarios.py",
        "-m",
        "not slow and not docker",
        "--cov=src",
        "--cov-report=term-missing:skip-covered",
        "--maxfail=5",
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
def security(session):
    """Run comprehensive security checks."""
    session.run("uv", "pip", "install", *SECURITY_DEPS, external=True)

    # Security vulnerability scanning
    session.run("safety", "check")
    session.run("pip-audit")

    # Static security analysis
    session.run("bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json")


@nox.session(python="3.11", reuse_venv=True)
def docs(session):
    """Generate API documentation."""
    session.run("uv", "pip", "install", *DOC_DEPS, external=True)
    install_project_deps(session)

    # Generate docs
    session.run("lazydocs", "src/", "--output-path", "docs/api/")


# Utility Sessions
@nox.session(python=False)
def clean(session):
    """Clean up nox environments to free disk space."""
    session.run("nox", "--stop-on-first-error", "-s", "clean", external=True)


@nox.session(python=False)
def clean_all(session):
    """Clean all nox environments - equivalent to 'nox -s clean -- --all'."""
    session.run("rm", "-rf", ".nox/", external=True)
    session.log("All nox environments cleaned.")
