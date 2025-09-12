"""Pytest configuration and fixtures for Rxiv-Maker tests."""

import gc
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

# Import cleanup utilities if available
try:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "nox_utils"))
    # from nox_utils import DiskSpaceMonitor, cleanup_manager

    CLEANUP_AVAILABLE = True
except ImportError:
    CLEANUP_AVAILABLE = False


# --- Helper Class for Local Engine Execution ---


class ExecutionEngine:
    """A helper class for local command execution."""

    def __init__(self, engine_type: str = "local"):
        if engine_type != "local":
            raise ValueError(f"Only local engine is supported, got: {engine_type}")
        self.engine_type = engine_type
        print(f"\n✅ Engine initialized: type={self.engine_type}")

    def run(self, command: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Runs a command using local execution."""
        # Extract check parameter, default to True
        check = kwargs.pop("check", True)

        # Extract timeout parameter, default to 600 seconds (10 minutes) for long operations
        timeout = kwargs.pop("timeout", 600)

        # Common kwargs for local execution
        run_kwargs = {"text": True, "capture_output": True, "check": check, "timeout": timeout, **kwargs}

        return subprocess.run(command, **run_kwargs)

    def rxiv_command(self, *args, **kwargs) -> subprocess.CompletedProcess:
        """Standardized rxiv command execution for local engine."""
        import sys

        try:
            # Try uv run first (modern approach)
            cmd = ["uv", "run", "rxiv"] + list(args)
            return self.run(cmd, **kwargs)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback to python module
            cmd = [sys.executable, "-m", "rxiv_maker.cli"] + list(args)
            return self.run(cmd, **kwargs)


# --- Pytest Hooks and Fixtures ---


def pytest_addoption(parser):
    """Adds the --engine command-line option to pytest (local only)."""
    parser.addoption(
        "--engine",
        action="store",
        default="local",
        help="Specify the execution engine: local (only supported option)",
    )


@pytest.fixture(scope="session")
def execution_engine(request):
    """
    Session-scoped fixture for local execution engine.
    """
    engine_name = request.config.getoption("--engine")

    if engine_name != "local":
        pytest.fail(f"Only local engine is supported. Docker/Podman engines are deprecated. Got: {engine_name}")

    yield ExecutionEngine("local")


# --- Optimized Temporary Directory Fixtures ---


@pytest.fixture(scope="session")
def session_temp_dir():
    """Session-scoped temporary directory for read-only test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="class")
def class_temp_dir():
    """Class-scoped temporary directory for test class isolation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_dir(class_temp_dir):
    """Test-scoped subdirectory within class temp directory."""
    import uuid

    test_dir = class_temp_dir / f"test_{uuid.uuid4().hex[:8]}"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """---
title: "Test Article"
authors:
  - name: "John Doe"
    affiliation: "Test University"
    email: "john@test.com"
keywords: ["test", "article"]
---

# Introduction

This is a test article with **bold** and *italic* text.

## Methods

We used @testcitation2023 for our methodology.

## Results

See @fig:test for results.

![Test Figure](FIGURES/test.png){#fig:test width="0.8"}
"""


@pytest.fixture
def sample_yaml_metadata():
    """Sample YAML metadata for testing."""
    return {
        "title": "Test Article",
        "authors": [
            {
                "name": "John Doe",
                "affiliation": "Test University",
                "email": "john@test.com",
            }
        ],
        "keywords": ["test", "article"],
    }


@pytest.fixture
def sample_tex_template():
    """Sample LaTeX template for testing."""
    return """\\documentclass{article}
\\title{<PY-RPL:LONG-TITLE-STR>}
\\author{<PY-RPL:AUTHORS-AND-AFFILIATIONS>}
\\begin{document}
\\maketitle
\\begin{abstract}
<PY-RPL:ABSTRACT>
\\end{abstract}
<PY-RPL:MAIN-CONTENT>
\\end{document}
"""


# --- Optimized Manuscript Fixtures ---


@pytest.fixture(scope="session")
def example_manuscript_template():
    """Session-scoped read-only reference to EXAMPLE_MANUSCRIPT."""
    return Path("EXAMPLE_MANUSCRIPT")


@pytest.fixture
def example_manuscript_copy(example_manuscript_template, temp_dir):
    """Fast copy of example manuscript using optimized copying."""
    dst = temp_dir / "manuscript"
    copy_tree_optimized(example_manuscript_template, dst)
    return dst


@pytest.fixture(scope="class")
def class_example_manuscript_copy(example_manuscript_template, class_temp_dir):
    """Class-scoped copy of example manuscript for shared use."""
    dst = class_temp_dir / "class_manuscript"
    copy_tree_optimized(example_manuscript_template, dst)
    return dst


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-mark tests based on path patterns to simplify selection and CI runtime."""
    from pathlib import PurePath

    for item in items:
        p = PurePath(item.nodeid)

        # Mark test categories by directory structure
        if "tests/unit/" in item.nodeid:
            item.add_marker(pytest.mark.unit)
            item.add_marker(pytest.mark.fast)  # Unit tests should be fast

        if "tests/integration/" in item.nodeid:
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)  # Integration tests are typically slower

        if "tests/system/" in item.nodeid:
            item.add_marker(pytest.mark.system)
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.ci_exclude)  # System tests excluded from regular CI

        if "tests/cli/" in item.nodeid:
            item.add_marker(pytest.mark.cli)
            item.add_marker(pytest.mark.integration)  # CLI tests are integration-level

        # Mark binary tests (now in system directory)
        if any(pattern in str(p) for pattern in ["test_ci_matrix", "test_end_to_end", "test_package_managers"]):
            item.add_marker(pytest.mark.binary)

        # Mark tests that require specific dependencies
        test_name_lower = item.name.lower()
        test_file = str(p).lower()

        # LaTeX dependency detection
        if (
            "latex" in test_name_lower
            or "pdf" in test_name_lower
            or "pdflatex" in test_name_lower
            or "tex" in test_name_lower
            or "test_install_verification" in test_file
        ):
            item.add_marker(requires_latex)

        # Docker dependency detection (deprecated - for cleanup identification)
        if "docker" in test_name_lower or "container" in test_name_lower or "docker_engine" in test_file:
            item.add_marker(pytest.mark.skip(reason="Docker engine deprecated - use local execution only"))

        # Podman dependency detection (deprecated - for cleanup identification)
        if "podman" in test_name_lower or "podman_engine" in test_file:
            item.add_marker(pytest.mark.skip(reason="Podman engine deprecated - use local execution only"))

        # R dependency detection
        if "r_" in test_name_lower or "_r_" in test_name_lower or "test_r" in test_name_lower:
            item.add_marker(requires_r)

        # Heavier or brittle unit tests to exclude by default in CI
        heavy_unit_files = {
            "tests/unit/test_platform_detector.py",
            "tests/unit/test_figure_generator.py",
            "tests/unit/test_github_actions_integration.py",
            "tests/unit/test_error_handling_scenarios.py",
        }
        if any(str(p).endswith(name) for name in heavy_unit_files):
            item.add_marker(pytest.mark.ci_exclude)

        # Mark slow integration tests that involve network calls or heavy processing
        slow_integration_patterns = {"doi_validation", "network", "api", "download", "install_verification"}
        if any(pattern in test_file for pattern in slow_integration_patterns):
            item.add_marker(pytest.mark.slow)


def copy_tree_optimized(src: Path, dst: Path, use_hardlinks: bool = True):
    """Enhanced optimized tree copying with better hardlink strategy."""

    dst.mkdir(parents=True, exist_ok=True)

    # Static file extensions that can use hardlinks safely
    STATIC_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".eps", ".gif"}
    # Text file extensions that should be copied (may be modified)
    TEXT_EXTENSIONS = {".md", ".yml", ".yaml", ".bib", ".tex", ".cls", ".bst", ".txt"}

    for item in src.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(src)
            dst_item = dst / rel_path
            dst_item.parent.mkdir(parents=True, exist_ok=True)

            # Strategy selection based on file type and size
            if use_hardlinks and item.suffix.lower() in STATIC_EXTENSIONS:
                # Use hardlinks for static binary files
                try:
                    os.link(item, dst_item)
                    continue
                except (OSError, AttributeError):
                    pass
            elif item.suffix.lower() in TEXT_EXTENSIONS:
                # Always copy text files (they may be modified)
                shutil.copy2(item, dst_item)
                continue
            elif use_hardlinks and item.stat().st_size > 1024:  # Files > 1KB
                # Use hardlinks for large files to save space/time
                try:
                    os.link(item, dst_item)
                    continue
                except (OSError, AttributeError):
                    pass

            # Fallback to regular copy
            shutil.copy2(item, dst_item)


@pytest.fixture(scope="session")
def minimal_manuscript_template():
    """Session-scoped minimal manuscript template for fast tests."""
    return {
        "config": """title: "Test Article"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    email: "test@example.com"
keywords: ["test"]
""",
        "content": """# Introduction

This is a minimal test manuscript.

## Methods

Simple methodology section.

## Results

Test results here.
""",
        "bibliography": """@article{test2023,
  title={Test Article},
  author={Test Author},
  year={2023}
}""",
    }


@pytest.fixture(scope="session")
def lightweight_manuscript_template():
    """Ultra-lightweight manuscript for fast unit tests."""
    return {
        "config": "title: Fast Test\nauthors: [{name: Test, email: test@test.com}]",
        "content": "# Test\nSimple content.",
        "bibliography": "@article{test2023, title={Test}, year={2023}}",
    }


@pytest.fixture
def fast_manuscript(lightweight_manuscript_template, temp_dir):
    """Create minimal manuscript in <100ms."""
    manuscript_dir = temp_dir / "fast_manuscript"
    manuscript_dir.mkdir()

    # Create files with minimal content
    (manuscript_dir / "00_CONFIG.yml").write_text(lightweight_manuscript_template["config"])
    (manuscript_dir / "01_MAIN.md").write_text(lightweight_manuscript_template["content"])
    (manuscript_dir / "03_REFERENCES.bib").write_text(lightweight_manuscript_template["bibliography"])

    # Create minimal figures directory
    (manuscript_dir / "FIGURES").mkdir()

    return manuscript_dir


@pytest.fixture
def minimal_manuscript(minimal_manuscript_template, temp_dir):
    """Create minimal manuscript in temp directory for fast tests."""
    manuscript_dir = temp_dir / "minimal_manuscript"
    manuscript_dir.mkdir()

    # Create files
    (manuscript_dir / "00_CONFIG.yml").write_text(minimal_manuscript_template["config"])
    (manuscript_dir / "01_MAIN.md").write_text(minimal_manuscript_template["content"])
    (manuscript_dir / "03_REFERENCES.bib").write_text(minimal_manuscript_template["bibliography"])

    # Create basic figures directory
    figures_dir = manuscript_dir / "FIGURES"
    figures_dir.mkdir()

    return manuscript_dir


def check_latex_available():
    """Check if LaTeX is available in the system."""
    try:
        # First check if pdflatex exists and runs
        result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False

        # Additional check: try to compile a minimal LaTeX document
        import tempfile

        test_content = r"""
\documentclass{article}
\begin{document}
Test
\end{document}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.tex"
            test_file.write_text(test_content)

            compile_result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(test_file)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check if PDF was created successfully
            pdf_file = Path(tmpdir) / "test.pdf"
            return compile_result.returncode == 0 and pdf_file.exists() and pdf_file.stat().st_size > 0

    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


def check_r_available():
    """Check if R is available in the system."""
    try:
        result = subprocess.run(["R", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, OSError):
        return False


# Docker and Podman availability checks removed - engines deprecated
# These functions kept as no-op for backward compatibility
def check_docker_available():
    """Docker availability check (deprecated - always returns False)."""
    return False


def check_podman_available():
    """Podman availability check (deprecated - always returns False)."""
    return False


# Markers for conditional test execution
requires_latex = pytest.mark.skipif(not check_latex_available(), reason="LaTeX not available")
requires_r = pytest.mark.skipif(not check_r_available(), reason="R not available")
requires_docker = pytest.mark.skip(reason="Docker engine deprecated - use local execution")
requires_podman = pytest.mark.skip(reason="Podman engine deprecated - use local execution")

# Test category markers (don't skip, just mark for selection)
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration  # Already defined by auto-marking
pytest.mark.system = pytest.mark.system
pytest.mark.fast = pytest.mark.fast
pytest.mark.slow = pytest.mark.slow
pytest.mark.performance = pytest.mark.performance
pytest.mark.memory_test = pytest.mark.memory_test
pytest.mark.smoke = pytest.mark.smoke


# --- Class-Scoped Fixtures for Performance ---
# (Already defined above in optimized fixtures section)


@pytest.fixture(scope="class")
def class_manuscript_structure(class_temp_dir):
    """Create a standard manuscript directory structure for the entire test class."""
    manuscript_dir = class_temp_dir / "TEST_MANUSCRIPT"
    manuscript_dir.mkdir()

    # Create FIGURES directory
    figures_dir = manuscript_dir / "FIGURES"
    figures_dir.mkdir()

    class ManuscriptStructure:
        def __init__(self, manuscript_dir, figures_dir, temp_dir):
            self.manuscript_dir = manuscript_dir
            self.figures_dir = figures_dir
            self.temp_dir = temp_dir

        def create_valid_manuscript(self):
            """Create a complete valid manuscript for testing."""
            # Create config file
            config_content = """
title: "Integration Test Article"
authors:
  - name: "Test Author"
    affiliation: "Test University"
    email: "test@example.com"
abstract: "This is a test abstract for integration testing."
keywords: ["test", "integration", "validation"]
"""
            config_file = self.manuscript_dir / "00_CONFIG.yml"
            config_file.write_text(config_content)

            # Create main content file
            main_content = """
# Introduction

This is a test manuscript for integration testing.

## Methods

We used standard testing procedures.

## Results

All tests passed successfully.

## Conclusion

The validation workflow works correctly.
"""
            main_file = self.manuscript_dir / "01_MAIN.md"
            main_file.write_text(main_content)

            # Create bibliography file
            bib_content = """
@article{test2023,
    title = {Test Article for Integration},
    author = {Test Author},
    journal = {Test Journal},
    year = {2023},
    volume = {1},
    number = {1},
    pages = {1--10}
}
"""
            bib_file = self.manuscript_dir / "03_REFERENCES.bib"
            bib_file.write_text(bib_content)

        def create_invalid_manuscript(self):
            """Create an invalid manuscript for testing validation failures."""
            # Create incomplete config file (missing required fields)
            config_content = """
title: "Incomplete Test Article"
# Missing authors, abstract, etc.
"""
            config_file = self.manuscript_dir / "00_CONFIG.yml"
            config_file.write_text(config_content)

            # Create main content with issues
            main_content = """
# Introduction

This manuscript has validation issues.

[Missing reference here](@invalid_citation)

## Methods

Missing proper structure.
"""
            main_file = self.manuscript_dir / "01_MAIN.md"
            main_file.write_text(main_content)

    yield ManuscriptStructure(manuscript_dir, figures_dir, class_temp_dir)


@pytest.fixture(scope="class")
def class_execution_engine(request):
    """Class-scoped fixture for local execution engine."""
    engine_name = request.config.getoption("--engine")

    if engine_name != "local":
        pytest.fail(f"Only local engine is supported. Docker/Podman engines are deprecated. Got: {engine_name}")

    yield ExecutionEngine("local")


@pytest.fixture(autouse=True)
def test_isolation():
    """Basic test isolation - optimized for performance."""
    yield

    # Lightweight post-test cleanup
    # Clear any lingering environment variables
    test_env_vars = [var for var in os.environ if var.startswith("RXIV_TEST_")]
    for var in test_env_vars:
        os.environ.pop(var, None)

    # Force garbage collection
    gc.collect()
