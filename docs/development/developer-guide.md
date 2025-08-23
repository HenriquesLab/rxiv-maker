# 👩‍💻 Developer Guide

*Comprehensive development reference for Rxiv-Maker contributors and maintainers*

**Prerequisites**: Read [CONTRIBUTING.md](CONTRIBUTING.md) first for contribution guidelines and setup basics.

---

## 📑 Table of Contents

1. [Development Environment Setup](#-development-environment-setup)
2. [Architecture & Code Organization](#-architecture--code-organization)
3. [Testing Strategy & Implementation](#-testing-strategy--implementation)
4. [Build Systems & Engine Modes](#-build-systems--engine-modes)
5. [Release Process & Automation](#-release-process--automation)
6. [Package Management & Distribution](#-package-management--distribution)
7. [CI/CD Workflows & GitHub Actions](#-cicd-workflows--github-actions)
8. [Docker & Container Development](#-docker--container-development)
9. [Debugging & Performance](#-debugging--performance)
10. [Maintenance & Operations](#-maintenance--operations)

---

## 🛠️ Development Environment Setup

### Local Development Setup

#### Quick Setup (Recommended)
```bash
# Clone repository
git clone https://github.com/henriqueslab/rxiv-maker.git
cd rxiv-maker

# Setup development environment
pip install -e ".[dev]"
pre-commit install

# Verify setup
rxiv check-installation
rxiv --version

# Run tests to verify everything works
python -m pytest tests/ -v
```

#### Advanced Setup with Virtual Environment
```bash
# Create isolated development environment
python -m venv .venv-dev
source .venv-dev/bin/activate  # Linux/macOS
# .venv-dev\Scripts\activate.bat  # Windows

# Install with all development dependencies
pip install --upgrade pip
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install --install-hooks

# Setup git hooks
echo "#!/bin/bash
python -m pytest tests/unit/ --disable-warnings -q" > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

### Development Dependencies

#### Core Dependencies
```bash
# Runtime dependencies (automatically installed)
pip install pyyaml requests click rich pandas matplotlib

# Development dependencies
pip install pytest pytest-cov pytest-xdist
pip install black isort mypy ruff
pip install pre-commit
pip install build twine

# Documentation dependencies
pip install mkdocs mkdocs-material
pip install sphinx sphinx-rtd-theme
```

#### Platform-Specific Dependencies
```bash
# macOS development setup
brew install pandoc texlive node
brew install --cask docker

# Ubuntu/Debian development setup
sudo apt update
sudo apt install texlive-full pandoc nodejs npm docker.io
sudo usermod -aG docker $USER

# Windows development (WSL2 recommended)
# Follow WSL2 setup, then use Ubuntu instructions
```

### IDE Configuration

#### Visual Studio Code
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv-dev/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": false,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".mypy_cache": true,
        "*.egg-info": true
    }
}
```

#### PyCharm Configuration
```python
# pytest.ini (for PyCharm test runner)
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --tb=short --strict-markers
markers = 
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests (skip in CI)
```

---

## 🏗️ Architecture & Code Organization

### Project Structure

```
rxiv-maker/
├── src/rxiv_maker/              # Main package
│   ├── __init__.py              # Package facade
│   ├── cli/                     # Command-line interface
│   ├── core/                    # Core business logic
│   │   ├── managers/            # Resource management
│   │   ├── cache/               # Caching system
│   │   └── validators/          # Validation logic
│   ├── services/                # Service layer
│   ├── engines/                 # Build engines (local, docker, etc.)
│   ├── converters/              # Content processing
│   ├── processors/              # Content processors
│   └── utils/                   # Utility functions
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data
├── docs/                        # Documentation
├── scripts/                     # Build and utility scripts
└── examples/                    # Example manuscripts
```

### Architecture Patterns

#### Service Layer Architecture
```python
# src/rxiv_maker/services/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')

class ServiceResult(Generic[T]):
    """Standardized service response"""
    def __init__(self, success: bool, data: Optional[T] = None, 
                 errors: Optional[List[str]] = None):
        self.success = success
        self.data = data
        self.errors = errors or []

class BaseService(ABC):
    """Base class for all services"""
    
    @abstractmethod
    def validate(self) -> ServiceResult[bool]:
        """Validate service requirements"""
        pass
    
    @abstractmethod  
    def execute(self, *args, **kwargs) -> ServiceResult[T]:
        """Execute main service logic"""
        pass
```

#### Manager Pattern for Resource Handling
```python
# src/rxiv_maker/core/managers/base.py
from contextlib import contextmanager
from abc import ABC, abstractmethod

class BaseManager(ABC):
    """Base class for resource managers"""
    
    def __init__(self):
        self._initialized = False
    
    @abstractmethod
    def setup(self):
        """Initialize manager resources"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up manager resources"""
        pass
    
    @contextmanager
    def managed_resource(self):
        """Context manager for resource lifecycle"""
        try:
            self.setup()
            yield self
        finally:
            self.cleanup()
```

#### Engine Abstraction Pattern
```python
# src/rxiv_maker/engines/abstract.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class AbstractBuildEngine(ABC):
    """Abstract base for build engines"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available on system"""
        pass
    
    @abstractmethod
    def build_pdf(self, manuscript_path: Path, 
                  output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Build PDF from manuscript"""
        pass
    
    @abstractmethod
    def generate_figures(self, figures_dir: Path) -> List[Path]:
        """Generate figures from scripts"""
        pass
```

### Code Style & Standards

#### Python Style Guide
```python
# Follow PEP 8 with these specific conventions:

# 1. Line length: 88 characters (Black default)
# 2. Imports: isort with Black compatibility
# 3. Type hints: Required for public APIs
# 4. Docstrings: Google style

def process_manuscript(
    manuscript_path: Path,
    output_directory: Path,
    force_rebuild: bool = False,
    **options: Any
) -> ProcessingResult:
    """Process manuscript to generate PDF.
    
    Args:
        manuscript_path: Path to manuscript directory
        output_directory: Where to place generated files
        force_rebuild: Whether to ignore cache
        **options: Additional processing options
    
    Returns:
        ProcessingResult containing status and generated files
        
    Raises:
        ManuscriptError: If manuscript is invalid
        ProcessingError: If processing fails
    """
    # Implementation here
    pass
```

#### Error Handling Patterns
```python
# Custom exception hierarchy
class RxivMakerError(Exception):
    """Base exception for Rxiv-Maker errors"""
    pass

class ValidationError(RxivMakerError):
    """Validation related errors"""
    pass

class BuildError(RxivMakerError):
    """Build process related errors"""
    pass

class ConfigurationError(RxivMakerError):
    """Configuration related errors"""
    pass

# Error handling pattern
def safe_operation(operation_name: str):
    """Decorator for safe operation execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RxivMakerError:
                raise  # Re-raise known errors
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}")
                raise RxivMakerError(f"Failed to {operation_name}: {e}") from e
        return wrapper
    return decorator
```

---

## 🧪 Testing Strategy & Implementation

### Testing Architecture Overview

Our testing strategy uses a three-tier approach:
1. **Unit Tests** (65% of test files) - Fast, isolated component testing
2. **Integration Tests** (25% of test files) - Cross-component interaction testing  
3. **End-to-End Tests** (10% of test files) - Complete workflow validation

### Consolidated Test Suites

#### Unit Test Suite Structure
```python
# tests/unit/test_validation_suite.py
import pytest
import unittest
from unittest.mock import Mock, patch

# Test configuration
VALIDATORS_AVAILABLE = True
try:
    from rxiv_maker.validators import ValidationLevel, BaseValidator
except ImportError:
    VALIDATORS_AVAILABLE = False

@pytest.mark.unit
@unittest.skipUnless(VALIDATORS_AVAILABLE, "Validators not available")
class TestValidationSuite(unittest.TestCase):
    """Consolidated validation testing suite"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.test_manuscript = Path("tests/fixtures/valid_manuscript.md")
        self.validator = BaseValidator()
    
    def test_citation_validation(self):
        """Test citation parsing and validation"""
        # Test implementation
        pass
    
    def test_figure_validation(self):
        """Test figure reference validation"""
        # Test implementation  
        pass
```

#### Integration Test Patterns
```python
# tests/integration/test_infrastructure_suite.py
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.mark.integration
class TestInfrastructureIntegration:
    """Infrastructure-dependent integration tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_manuscript = self._create_test_manuscript()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.skipif(not is_docker_available(), 
                       reason="Docker not available")
    def test_docker_build_integration(self):
        """Test complete Docker-based build process"""
        # Test implementation
        pass
```

### Test Execution Framework

#### Test Configuration (pytest.ini)
```ini
[tool:pytest]
minversion = 6.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test markers for categorization
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (slower, may need external services)
    slow: Slow tests (skip in development)
    docker: Tests requiring Docker
    network: Tests requiring network access
    
# Execution settings
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    -ra

# Parallel execution
addopts = -n auto

# Coverage settings
addopts = --cov=src/rxiv_maker --cov-report=html --cov-report=term
```

#### Test Scripts
```bash
# scripts/run-tests.sh - Cross-platform test execution
#!/bin/bash

# Test categories with timing estimates
case $1 in
    "smoke")
        pytest -m "unit and not slow" --maxfail=5 -q
        ;;
    "unit")  
        pytest -m "unit" -v
        ;;
    "integration")
        pytest -m "integration" -v --timeout=300
        ;;
    "all")
        pytest -v --timeout=600
        ;;
    *)
        echo "Usage: $0 {smoke|unit|integration|all}"
        ;;
esac
```

### Test Data Management

#### Fixture Organization
```python
# tests/conftest.py - Shared fixtures
import pytest
from pathlib import Path
import tempfile

@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def temp_manuscript(test_data_dir):
    """Create temporary manuscript for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy test manuscript
        shutil.copytree(test_data_dir / "EXAMPLE_MANUSCRIPT", 
                       temp_path / "manuscript")
        
        yield temp_path / "manuscript"

@pytest.fixture  
def mock_latex_environment():
    """Mock LaTeX environment for testing"""
    with patch('rxiv_maker.utils.latex.check_latex_installation') as mock:
        mock.return_value = True
        yield mock
```

---

## 🔧 Build Systems & Engine Modes

### Engine Architecture

Rxiv-Maker supports multiple build engines for different environments:

#### Local Engine (Default)
```python
# src/rxiv_maker/engines/local.py
class LocalBuildEngine(AbstractBuildEngine):
    """Local build using system-installed tools"""
    
    def is_available(self) -> bool:
        """Check if local tools are available"""
        return all([
            self._check_python(),
            self._check_latex(),
            self._check_pandoc()
        ])
    
    def build_pdf(self, manuscript_path: Path, 
                  output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Build PDF using local tools"""
        
        # Generate figures
        figure_results = self.generate_figures(manuscript_path / "FIGURES")
        
        # Process manuscript
        tex_file = self._markdown_to_latex(manuscript_path)
        
        # Compile PDF
        pdf_file = self._compile_latex(tex_file, output_dir)
        
        return {
            "success": True,
            "pdf_file": pdf_file,
            "figures": figure_results,
            "build_log": self._get_build_log()
        }
```

#### Docker Engine
```python
# src/rxiv_maker/engines/docker.py
class DockerBuildEngine(AbstractBuildEngine):
    """Build using Docker container for consistency"""
    
    def __init__(self):
        self.image_name = "henriqueslab/rxiv-maker:latest"
        self.container_timeout = 300  # 5 minutes
    
    def is_available(self) -> bool:
        """Check if Docker is available"""
        try:
            import docker
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False
    
    def build_pdf(self, manuscript_path: Path, 
                  output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Build PDF in Docker container"""
        
        import docker
        client = docker.from_env()
        
        # Mount manuscript directory
        volumes = {
            str(manuscript_path.absolute()): {
                'bind': '/workspace',
                'mode': 'rw'
            }
        }
        
        # Run build in container
        container = client.containers.run(
            self.image_name,
            command="rxiv pdf /workspace",
            volumes=volumes,
            working_dir="/workspace",
            timeout=self.container_timeout,
            remove=True,
            detach=True
        )
        
        # Wait for completion and get logs
        result = container.wait()
        logs = container.logs().decode('utf-8')
        
        return {
            "success": result["StatusCode"] == 0,
            "build_log": logs,
            "container_output": result
        }
```

### Build Process Pipeline

#### Build Orchestration
```python
# src/rxiv_maker/core/build_manager.py
class BuildManager:
    """Orchestrates the complete build process"""
    
    def __init__(self, engine_type: str = "auto"):
        self.engine = self._select_engine(engine_type)
        self.validators = ValidationManager()
        self.cache = CacheManager()
    
    def build_manuscript(self, manuscript_path: Path, **options) -> BuildResult:
        """Complete manuscript build process"""
        
        # Phase 1: Validation
        if not options.get('skip_validation', False):
            validation_result = self.validators.validate_all(manuscript_path)
            if not validation_result.success:
                return BuildResult(False, errors=validation_result.errors)
        
        # Phase 2: Figure Generation
        figures_result = self._generate_figures(manuscript_path)
        if not figures_result.success:
            return BuildResult(False, errors=figures_result.errors)
        
        # Phase 3: PDF Compilation
        build_result = self.engine.build_pdf(
            manuscript_path, 
            output_dir=options.get('output_dir', manuscript_path / 'output'),
            **options
        )
        
        # Phase 4: Post-processing
        if build_result['success']:
            self._post_process(build_result, options)
        
        return BuildResult(
            success=build_result['success'],
            pdf_file=build_result.get('pdf_file'),
            build_log=build_result.get('build_log', ''),
            figures=figures_result.figures
        )
```

#### Engine Selection Logic
```python
def select_optimal_engine() -> AbstractBuildEngine:
    """Select best available engine for current environment"""
    
    # Check environment variable override
    engine_override = os.environ.get('RXIV_ENGINE')
    if engine_override:
        return _create_engine(engine_override)
    
    # Auto-selection logic
    if DockerBuildEngine().is_available():
        logger.info("Using Docker engine for consistent builds")
        return DockerBuildEngine()
    
    if PodmanBuildEngine().is_available():
        logger.info("Using Podman engine as Docker alternative")
        return PodmanBuildEngine()
    
    if LocalBuildEngine().is_available():
        logger.info("Using local engine with system tools")
        return LocalBuildEngine()
    
    raise EnvironmentError("No suitable build engine available")
```

---

## 🚀 Release Process & Automation

### Release Workflow Overview

Our release process is fully automated through GitHub Actions and supports multiple distribution channels:

#### Release Types & Versioning
```yaml
# Release types and their triggers
patch_release:  # v1.2.3 -> v1.2.4
  - Bug fixes
  - Documentation updates  
  - Performance improvements
  - Security patches

minor_release:  # v1.2.0 -> v1.3.0  
  - New features
  - API additions (non-breaking)
  - Significant improvements
  - Deprecation notices

major_release:  # v1.0.0 -> v2.0.0
  - Breaking API changes
  - Major architecture changes
  - Significant new capabilities
```

#### Automated Release Pipeline
```bash
# Release trigger process
# 1. Create and push version tag
git tag v1.2.3
git push origin v1.2.3

# 2. GitHub Actions automatically:
#    - Builds and tests across platforms
#    - Generates release notes
#    - Publishes to PyPI
#    - Updates Homebrew formula
#    - Updates APT repository
#    - Builds and pushes Docker images
#    - Creates GitHub release with assets
```

### Release Automation Scripts

#### Version Management
```python
# scripts/release/version_manager.py
import re
import subprocess
from pathlib import Path

class VersionManager:
    """Manage version numbers across the project"""
    
    VERSION_FILES = [
        "src/rxiv_maker/__init__.py",
        "pyproject.toml", 
        "package.json",
        "Dockerfile"
    ]
    
    def get_current_version(self) -> str:
        """Get current version from main package"""
        init_file = Path("src/rxiv_maker/__init__.py")
        content = init_file.read_text()
        match = re.search(r'__version__ = [\'"]([^\'"]+)[\'"]', content)
        if not match:
            raise ValueError("Could not find version in __init__.py")
        return match.group(1)
    
    def bump_version(self, version_type: str) -> str:
        """Bump version number"""
        current = self.get_current_version()
        major, minor, patch = map(int, current.split('.'))
        
        if version_type == "patch":
            patch += 1
        elif version_type == "minor":
            minor += 1
            patch = 0
        elif version_type == "major":
            major += 1
            minor = patch = 0
        else:
            raise ValueError(f"Invalid version type: {version_type}")
        
        new_version = f"{major}.{minor}.{patch}"
        self._update_version_files(new_version)
        return new_version
    
    def _update_version_files(self, new_version: str):
        """Update version in all relevant files"""
        for file_path in self.VERSION_FILES:
            if Path(file_path).exists():
                self._update_file_version(Path(file_path), new_version)
```

#### Release Orchestration
```python
# scripts/release/orchestrator.py
class ReleaseOrchestrator:
    """Orchestrate the complete release process"""
    
    def __init__(self, version: str, dry_run: bool = True):
        self.version = version
        self.dry_run = dry_run
        self.github_token = os.environ.get('GITHUB_TOKEN')
    
    def execute_release(self):
        """Execute complete release process"""
        
        # Phase 1: Pre-release validation
        self._validate_release_conditions()
        
        # Phase 2: Build and test
        self._run_complete_test_suite()
        
        # Phase 3: Generate release artifacts  
        self._build_release_artifacts()
        
        # Phase 4: Publish to distribution channels
        self._publish_to_pypi()
        self._update_homebrew_formula()
        self._update_apt_repository()
        self._push_docker_images()
        
        # Phase 5: Create GitHub release
        self._create_github_release()
        
        # Phase 6: Post-release tasks
        self._update_documentation()
        self._notify_stakeholders()
```

### Distribution Channels

#### PyPI Publishing
```python
# scripts/release/pypi_publisher.py
def publish_to_pypi(version: str, test_pypi: bool = False):
    """Publish package to PyPI using OIDC authentication"""
    
    # Build package
    subprocess.run(["python", "-m", "build"], check=True)
    
    # Configure repository
    repository_url = (
        "https://test.pypi.org/legacy/" if test_pypi 
        else "https://upload.pypi.org/legacy/"
    )
    
    # Publish using twine with OIDC
    env = os.environ.copy()
    env["TWINE_USERNAME"] = "__token__"
    env["TWINE_PASSWORD"] = os.environ["PYPI_API_TOKEN"]
    
    subprocess.run([
        "python", "-m", "twine", "upload",
        "--repository-url", repository_url,
        "dist/*"
    ], env=env, check=True)
```

#### Homebrew Formula Updates
```ruby
# Formula/rxiv-maker.rb (auto-generated)
class RxivMaker < Formula
  include Language::Python::Virtualenv

  desc "Transform Markdown manuscripts into publication-ready PDFs"
  homepage "https://github.com/henriqueslab/rxiv-maker"
  url "https://files.pythonhosted.org/packages/.../rxiv-maker-1.2.3.tar.gz"
  sha256 "abcd1234..."
  license "MIT"

  depends_on "python@3.11"
  depends_on "node@20"
  depends_on "pandoc"

  def install
    virtualenv_install_with_resources
    
    # Install additional tools
    system libexec/"bin/pip", "install", "matplotlib", "numpy"
  end

  test do
    system bin/"rxiv", "--version"
    system bin/"rxiv", "check-installation"
  end
end
```

---

## 📦 Package Management & Distribution

### Multi-Platform Distribution Strategy

#### Package Formats
```yaml
distribution_channels:
  python:
    primary: PyPI (pip install rxiv-maker)
    test: Test PyPI (for pre-releases)
    
  macos:
    primary: Homebrew (brew install henriqueslab/rxiv-maker/rxiv-maker)
    alternative: MacPorts (port install rxiv-maker)
    
  linux:
    debian_ubuntu: APT repository (apt install rxiv-maker)
    arch: AUR package (yay -S rxiv-maker)
    fedora: RPM repository (dnf install rxiv-maker)
    universal: AppImage, Snap, Flatpak
    
  windows:
    primary: Chocolatey (choco install rxiv-maker)
    alternative: Scoop (scoop install rxiv-maker)
    manual: MSI installer
    
  containers:
    docker: henriqueslab/rxiv-maker:latest
    podman: Compatible with Docker images
```

#### Dependency Management
```toml
# pyproject.toml - Python packaging configuration
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "rxiv-maker"
dynamic = ["version"]
description = "Transform Markdown manuscripts into publication-ready PDFs"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Bruno M. Saraiva", email = "bruno.saraiva@research.fchampalimaud.org"},
    {name = "Ricardo Henriques", email = "ricardo.henriques@research.fchampalimaud.org"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.11"

# Core dependencies (minimal for basic functionality)
dependencies = [
    "click>=8.0.0",
    "pyyaml>=6.0.0",
    "requests>=2.25.0",
    "rich>=10.0.0",
]

# Optional dependencies for different use cases
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-xdist>=3.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "pre-commit>=3.0.0",
]

figures = [
    "matplotlib>=3.5.0",
    "numpy>=1.21.0", 
    "pandas>=1.3.0",
    "seaborn>=0.11.0",
]

latex = [
    "pygments>=2.10.0",
    "bibtexparser>=1.2.0",
]

all = [
    "rxiv-maker[dev,figures,latex]",
]
```

### Container Distribution

#### Docker Images
```dockerfile
# Dockerfile - Multi-stage build for optimized images
FROM python:3.11-slim as builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Build Python package
COPY . /src
WORKDIR /src
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /src/wheels .

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    pandoc \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Python package from wheel
COPY --from=builder /src/wheels /wheels
RUN pip install --no-cache /wheels/*

# Setup working directory
WORKDIR /workspace
VOLUME ["/workspace"]

# Default command
CMD ["rxiv", "--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD rxiv check-installation || exit 1
```

#### Container Build Pipeline
```python
# scripts/docker/build_images.py
class DockerBuilder:
    """Build and publish Docker images"""
    
    IMAGES = {
        "base": {
            "dockerfile": "Dockerfile", 
            "tags": ["latest", "stable"]
        },
        "dev": {
            "dockerfile": "Dockerfile.dev",
            "tags": ["dev", "development"]  
        },
        "minimal": {
            "dockerfile": "Dockerfile.minimal",
            "tags": ["minimal", "slim"]
        }
    }
    
    def build_all_images(self, version: str):
        """Build all Docker image variants"""
        for image_name, config in self.IMAGES.items():
            self._build_image(image_name, config, version)
    
    def _build_image(self, name: str, config: dict, version: str):
        """Build single Docker image with multiple tags"""
        dockerfile = config["dockerfile"]
        base_tag = f"henriqueslab/rxiv-maker"
        
        # Build image
        build_cmd = [
            "docker", "build",
            "-f", dockerfile,
            "-t", f"{base_tag}:{version}",
            "."
        ]
        
        for tag in config["tags"]:
            build_cmd.extend(["-t", f"{base_tag}:{tag}"])
        
        subprocess.run(build_cmd, check=True)
        
        # Push to registry
        for tag in [version] + config["tags"]:
            push_cmd = ["docker", "push", f"{base_tag}:{tag}"]
            subprocess.run(push_cmd, check=True)
```

---

## 🔄 CI/CD Workflows & GitHub Actions

### GitHub Actions Architecture

#### Workflow Organization
```yaml
# .github/workflows/ structure
workflows:
  ci.yml:           # Continuous Integration (PR checks)
  release.yml:      # Release automation  
  docker.yml:       # Container builds
  docs.yml:         # Documentation updates
  security.yml:     # Security scanning
  performance.yml:  # Performance benchmarks
```

#### Primary CI Workflow
```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]
        
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: Setup Node.js ${{ env.NODE_VERSION }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        
    - name: Install system dependencies (Ubuntu)
      if: matrix.os == 'ubuntu-latest'
      run: |
        sudo apt-get update
        sudo apt-get install -y texlive-latex-recommended pandoc
        
    - name: Install system dependencies (macOS)  
      if: matrix.os == 'macos-latest'
      run: |
        brew install pandoc
        # LaTeX installation via MacTeX is too slow for CI
        
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev,test]"
        
    - name: Run linting
      run: |
        ruff check src/ tests/
        black --check src/ tests/
        mypy src/
        
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src/rxiv_maker --cov-report=xml
        
    - name: Run integration tests (Linux only)
      if: matrix.os == 'ubuntu-latest'
      run: |
        pytest tests/integration/ -v --timeout=300
        
    - name: Upload coverage to Codecov
      if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
```

#### Release Workflow
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Run complete test suite
      run: |
        pip install -e ".[dev,test]"
        pytest tests/ -v --timeout=600
        
  publish-pypi:
    needs: build-and-test
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write  # For PyPI OIDC
      contents: read
      
    steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Build package
      run: |
        pip install build
        python -m build
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://upload.pypi.org/legacy/
        
  update-homebrew:
    needs: publish-pypi
    runs-on: ubuntu-latest
    steps:
    - name: Update Homebrew formula
      run: |
        # Automated Homebrew formula update logic
        ./scripts/homebrew/update_formula.sh ${{ github.ref_name }}
        
  create-release:
    needs: [publish-pypi, update-homebrew]
    runs-on: ubuntu-latest
    permissions:
      contents: write
      
    steps:
    - uses: actions/checkout@v4
    - name: Generate release notes
      run: |
        ./scripts/release/generate_notes.sh ${{ github.ref_name }}
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v1
      with:
        body_path: release-notes.md
        files: |
          dist/*.tar.gz
          dist/*.whl
        draft: false
        prerelease: false
```

### Advanced Workflow Features

#### Performance Benchmarking
```yaml
# .github/workflows/performance.yml
name: Performance Benchmarks

on:
  pull_request:
    paths:
      - 'src/rxiv_maker/**'
      - 'tests/benchmarks/**'
      
jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        pip install pytest-benchmark
    - name: Run benchmarks
      run: |
        pytest tests/benchmarks/ --benchmark-json=benchmark.json
    - name: Store benchmark results
      uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: benchmark.json
        github-token: ${{ secrets.GITHUB_TOKEN }}
        auto-push: true
```

#### Security Scanning
```yaml
# .github/workflows/security.yml  
name: Security Scanning

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Mondays

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run Snyk to check for vulnerabilities
      uses: snyk/actions/python@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        
  code-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Initialize CodeQL
      uses: github/codeql-action/init@v2
      with:
        languages: python
    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2
```

---

## 🐳 Docker & Container Development

### Container Strategy

#### Multi-Stage Build Optimization
```dockerfile
# Dockerfile - Production-optimized multi-stage build
ARG PYTHON_VERSION=3.11
ARG DEBIAN_VERSION=bookworm

# Stage 1: Build environment
FROM python:${PYTHON_VERSION}-${DEBIAN_VERSION} as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create build directory
WORKDIR /build

# Copy source and build wheel
COPY . .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels .

# Stage 2: Runtime environment
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    pandoc \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python package from wheel
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir --find-links /tmp/wheels rxiv-maker[all] \
    && rm -rf /tmp/wheels

# Create non-root user
RUN useradd --create-home --shell /bin/bash rxiv
USER rxiv
WORKDIR /home/rxiv

# Setup environment
ENV PATH="/home/rxiv/.local/bin:$PATH"
ENV PYTHONPATH="/home/rxiv/.local/lib/python3.11/site-packages"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD rxiv check-installation || exit 1

# Default command
CMD ["rxiv", "--help"]
```

#### Development Container
```dockerfile
# Dockerfile.dev - Development environment
FROM python:3.11-bookworm

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-full \
    pandoc \
    nodejs \
    npm \
    git \
    vim \
    tmux \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --no-cache-dir \
    pytest pytest-cov pytest-xdist \
    black isort mypy ruff \
    pre-commit \
    jupyter \
    ipython

# Setup development environment
WORKDIR /workspace
VOLUME ["/workspace"]

# Install package in development mode
RUN echo '#!/bin/bash\ncd /workspace && pip install -e ".[dev,test]"' > /usr/local/bin/setup-dev \
    && chmod +x /usr/local/bin/setup-dev

# Development aliases
RUN echo 'alias ll="ls -la"' >> ~/.bashrc \
    && echo 'alias pytest="python -m pytest"' >> ~/.bashrc \
    && echo 'alias rxiv="python -m rxiv_maker.cli"' >> ~/.bashrc

CMD ["/bin/bash"]
```

### Container Testing & Validation

#### Container Test Suite
```python
# tests/containers/test_docker_integration.py
import pytest
import docker
import tempfile
from pathlib import Path

@pytest.mark.integration
@pytest.mark.docker
class TestDockerIntegration:
    """Test Docker container functionality"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture"""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception:
            pytest.skip("Docker not available")
    
    @pytest.fixture
    def test_manuscript(self):
        """Create test manuscript in temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manuscript_dir = Path(temp_dir) / "test_manuscript"
            manuscript_dir.mkdir()
            
            # Create minimal manuscript
            (manuscript_dir / "01_MAIN.md").write_text("""
# Test Manuscript

This is a test manuscript for Docker validation.

## Introduction
Testing Docker container functionality.
""")
            
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Docker Test Manuscript"
authors:
  - name: "Test Author"
""")
            
            yield manuscript_dir
    
    def test_container_build_process(self, docker_client, test_manuscript):
        """Test complete build process in container"""
        
        # Run container with manuscript
        volumes = {
            str(test_manuscript): {
                'bind': '/workspace',
                'mode': 'rw'
            }
        }
        
        container = docker_client.containers.run(
            "henriqueslab/rxiv-maker:latest",
            command="rxiv pdf /workspace --verbose",
            volumes=volumes,
            working_dir="/workspace",
            remove=True,
            detach=True
        )
        
        # Wait for completion
        result = container.wait(timeout=300)
        logs = container.logs().decode('utf-8')
        
        # Verify success
        assert result["StatusCode"] == 0, f"Container failed: {logs}"
        
        # Verify output file exists
        pdf_file = test_manuscript / "output" / "test_manuscript.pdf"
        assert pdf_file.exists(), "PDF output not generated"
        assert pdf_file.stat().st_size > 1000, "PDF file too small"
```

#### Container Health Monitoring
```python
# scripts/docker/health_monitor.py
class ContainerHealthMonitor:
    """Monitor container health and performance"""
    
    def __init__(self, image_name: str):
        self.image_name = image_name
        self.client = docker.from_env()
    
    def run_health_checks(self) -> dict:
        """Run comprehensive health checks"""
        
        results = {
            "image_available": self._check_image_available(),
            "container_startup": self._check_container_startup(),
            "command_execution": self._check_command_execution(),
            "resource_usage": self._check_resource_usage(),
            "cleanup": self._check_cleanup()
        }
        
        return results
    
    def _check_container_startup(self) -> bool:
        """Test container startup time"""
        start_time = time.time()
        
        container = self.client.containers.run(
            self.image_name,
            command="rxiv --version",
            detach=True,
            remove=True
        )
        
        result = container.wait(timeout=60)
        startup_time = time.time() - start_time
        
        # Should start within 10 seconds
        return result["StatusCode"] == 0 and startup_time < 10
```

---

## 🔍 Debugging & Performance

### Debugging Infrastructure

#### Logging System
```python
# src/rxiv_maker/utils/logging.py
import logging
import sys
from pathlib import Path
from typing import Optional

class RxivLogger:
    """Centralized logging system for Rxiv-Maker"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers"""
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_file = Path.home() / ".rxiv-maker" / "logs" / "rxiv-maker.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatters
        console_format = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

# Usage throughout codebase
logger = RxivLogger(__name__).logger
```

#### Debug Mode Implementation
```python
# src/rxiv_maker/core/debug.py
import os
import time
import traceback
from contextlib import contextmanager
from functools import wraps

class DebugManager:
    """Manage debug mode and performance profiling"""
    
    def __init__(self):
        self.debug_enabled = os.environ.get('RXIV_DEBUG', '').lower() == '1'
        self.profile_enabled = os.environ.get('RXIV_PROFILE', '').lower() == '1'
        self.trace_file = Path.home() / ".rxiv-maker" / "debug" / "trace.log"
    
    @contextmanager
    def debug_context(self, operation_name: str):
        """Context manager for debug operations"""
        if not self.debug_enabled:
            yield
            return
        
        start_time = time.time()
        self._log_debug(f"Starting {operation_name}")
        
        try:
            yield
        except Exception as e:
            self._log_debug(f"Error in {operation_name}: {e}")
            self._log_debug(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            duration = time.time() - start_time
            self._log_debug(f"Completed {operation_name} in {duration:.2f}s")

def debug_performance(func):
    """Decorator for performance debugging"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        debug_manager = DebugManager()
        
        with debug_manager.debug_context(func.__name__):
            if debug_manager.profile_enabled:
                import cProfile
                profiler = cProfile.Profile()
                profiler.enable()
            
            result = func(*args, **kwargs)
            
            if debug_manager.profile_enabled:
                profiler.disable()
                profiler.dump_stats(f"/tmp/rxiv_{func.__name__}.prof")
        
        return result
    return wrapper
```

### Performance Optimization

#### Caching System
```python
# src/rxiv_maker/core/cache/manager.py
import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Optional, Callable

class CacheManager:
    """Intelligent caching for expensive operations"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path.home() / ".rxiv-maker" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age = 86400  # 24 hours default
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        cache_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve from cache if valid"""
        cache_file = self.cache_dir / f"{key}.cache"
        
        if not cache_file.exists():
            return None
        
        # Check age
        if time.time() - cache_file.stat().st_mtime > self.max_age:
            cache_file.unlink()
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            cache_file.unlink()  # Remove corrupted cache
            return None
    
    def set(self, key: str, value: Any):
        """Store in cache"""
        cache_file = self.cache_dir / f"{key}.cache"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"Failed to cache {key}: {e}")

def cached_operation(cache_manager: CacheManager, max_age: int = 3600):
    """Decorator for caching expensive operations"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_manager.get_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing")
            result = func(*args, **kwargs)
            cache_manager.set(key, result)
            
            return result
        return wrapper
    return decorator
```

#### Resource Monitoring
```python
# src/rxiv_maker/utils/monitoring.py
import psutil
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

@dataclass
class ResourceUsage:
    """Resource usage metrics"""
    cpu_percent: float
    memory_mb: float
    disk_io_mb: float
    duration_seconds: float

class ResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self):
        self.process = psutil.Process()
    
    @contextmanager
    def monitor_operation(self, operation_name: str) -> Generator[ResourceUsage, None, None]:
        """Context manager to monitor resource usage"""
        
        # Initial measurements
        start_time = time.time()
        start_cpu_times = self.process.cpu_times()
        start_memory = self.process.memory_info().rss
        start_io = self.process.io_counters()
        
        # Create usage tracker
        usage = ResourceUsage(0, 0, 0, 0)
        
        try:
            yield usage
        finally:
            # Final measurements  
            end_time = time.time()
            end_cpu_times = self.process.cpu_times()
            end_memory = self.process.memory_info().rss
            end_io = self.process.io_counters()
            
            # Calculate usage
            usage.duration_seconds = end_time - start_time
            usage.cpu_percent = self.process.cpu_percent()
            usage.memory_mb = (end_memory - start_memory) / 1024 / 1024
            usage.disk_io_mb = (
                (end_io.read_bytes + end_io.write_bytes) - 
                (start_io.read_bytes + start_io.write_bytes)
            ) / 1024 / 1024
            
            # Log if significant usage
            if usage.duration_seconds > 1 or usage.memory_mb > 100:
                logger.info(
                    f"{operation_name} used {usage.memory_mb:.1f}MB memory, "
                    f"{usage.cpu_percent:.1f}% CPU, "
                    f"{usage.disk_io_mb:.1f}MB I/O in {usage.duration_seconds:.1f}s"
                )
```

---

## 🛠️ Maintenance & Operations

### Automated Maintenance

#### Dependency Updates
```python
# scripts/maintenance/update_dependencies.py
import subprocess
import json
from pathlib import Path

class DependencyUpdater:
    """Automated dependency management"""
    
    def __init__(self):
        self.pyproject_file = Path("pyproject.toml")
        self.package_json = Path("package.json")
    
    def check_outdated_packages(self) -> dict:
        """Check for outdated Python packages"""
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return {}
        
        return json.loads(result.stdout)
    
    def update_python_dependencies(self, dry_run: bool = True):
        """Update Python dependencies"""
        outdated = self.check_outdated_packages()
        
        for package in outdated:
            name = package["name"]
            current = package["version"]
            latest = package["latest_version"]
            
            print(f"Would update {name}: {current} -> {latest}")
            
            if not dry_run:
                subprocess.run([
                    "pip", "install", "--upgrade", name
                ], check=True)
    
    def run_security_audit(self):
        """Run security audit on dependencies"""
        # Python security audit
        subprocess.run([
            "pip-audit", "--format=json", "--output=security-audit.json"
        ], check=False)
        
        # Node.js security audit
        if self.package_json.exists():
            subprocess.run([
                "npm", "audit", "--json", "> npm-audit.json"
            ], shell=True, check=False)
```

#### Health Monitoring
```python
# scripts/maintenance/health_monitor.py
import requests
import subprocess
from datetime import datetime, timedelta

class HealthMonitor:
    """Monitor project health across different metrics"""
    
    def __init__(self):
        self.github_api = "https://api.github.com/repos/henriqueslab/rxiv-maker"
        self.pypi_api = "https://pypi.org/pypi/rxiv-maker/json"
    
    def check_build_status(self) -> dict:
        """Check CI/CD build status"""
        response = requests.get(f"{self.github_api}/actions/runs")
        runs = response.json()["workflow_runs"]
        
        recent_runs = [
            run for run in runs[:10] 
            if datetime.fromisoformat(run["created_at"].replace("Z", "")) 
               > datetime.now() - timedelta(days=7)
        ]
        
        return {
            "total_runs": len(recent_runs),
            "successful": len([r for r in recent_runs if r["conclusion"] == "success"]),
            "failed": len([r for r in recent_runs if r["conclusion"] == "failure"]),
            "latest_status": recent_runs[0]["conclusion"] if recent_runs else None
        }
    
    def check_package_downloads(self) -> dict:
        """Check PyPI download statistics"""
        response = requests.get(self.pypi_api)
        package_info = response.json()
        
        # Get download stats from pypistats API
        stats_response = requests.get(
            f"https://pypistats.org/api/packages/rxiv-maker/recent"
        )
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            return {
                "last_day": stats["data"]["last_day"],
                "last_week": stats["data"]["last_week"],
                "last_month": stats["data"]["last_month"]
            }
        
        return {"error": "Could not fetch download stats"}
    
    def generate_health_report(self) -> str:
        """Generate comprehensive health report"""
        
        build_status = self.check_build_status()
        download_stats = self.check_package_downloads()
        
        report = f"""
# Rxiv-Maker Health Report - {datetime.now().strftime('%Y-%m-%d')}

## Build Health
- Recent builds: {build_status['successful']}/{build_status['total_runs']} successful
- Latest build: {build_status['latest_status']}

## Usage Metrics  
- Downloads last day: {download_stats.get('last_day', 'N/A')}
- Downloads last week: {download_stats.get('last_week', 'N/A')}
- Downloads last month: {download_stats.get('last_month', 'N/A')}

## Repository Health
- Open issues: [Check GitHub](https://github.com/henriqueslab/rxiv-maker/issues)
- Open PRs: [Check GitHub](https://github.com/henriqueslab/rxiv-maker/pulls)

Generated at: {datetime.now().isoformat()}
"""
        
        return report
```

### Documentation Maintenance

#### Link Validation
```python
# scripts/maintenance/validate_links.py
import re
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

class LinkValidator:
    """Validate all links in documentation"""
    
    def __init__(self):
        self.doc_dirs = ["docs/", "./"]
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.url_pattern = re.compile(r'https?://[^\s]+')
    
    def extract_links_from_file(self, file_path: Path) -> list:
        """Extract all links from markdown file"""
        if not file_path.suffix == '.md':
            return []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return []
        
        # Extract markdown links
        markdown_links = self.link_pattern.findall(content)
        
        # Extract plain URLs  
        plain_urls = self.url_pattern.findall(content)
        
        links = []
        
        # Process markdown links
        for text, url in markdown_links:
            if url.startswith(('http://', 'https://')):
                links.append({
                    'file': file_path,
                    'text': text,
                    'url': url,
                    'type': 'external'
                })
            elif not url.startswith(('#', 'mailto:')):
                links.append({
                    'file': file_path,
                    'text': text,
                    'url': url,
                    'type': 'internal'
                })
        
        # Process plain URLs
        for url in plain_urls:
            links.append({
                'file': file_path,
                'text': url,
                'url': url,
                'type': 'external'
            })
        
        return links
    
    def validate_external_link(self, link: dict) -> dict:
        """Validate external link"""
        try:
            response = requests.head(link['url'], timeout=10, allow_redirects=True)
            return {
                **link,
                'status': response.status_code,
                'valid': response.status_code < 400
            }
        except Exception as e:
            return {
                **link,
                'status': None,
                'valid': False,
                'error': str(e)
            }
    
    def validate_all_links(self) -> dict:
        """Validate all links in documentation"""
        all_links = []
        
        # Collect all links
        for doc_dir in self.doc_dirs:
            for md_file in Path(doc_dir).glob('**/*.md'):
                all_links.extend(self.extract_links_from_file(md_file))
        
        # Separate external and internal links
        external_links = [l for l in all_links if l['type'] == 'external']
        internal_links = [l for l in all_links if l['type'] == 'internal']
        
        # Validate external links in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            external_results = list(executor.map(self.validate_external_link, external_links))
        
        # Validate internal links
        internal_results = []
        for link in internal_links:
            # Check if internal file exists
            file_path = link['file'].parent / link['url']
            valid = file_path.exists()
            internal_results.append({
                **link,
                'valid': valid
            })
        
        return {
            'external': external_results,
            'internal': internal_results,
            'summary': {
                'total_external': len(external_results),
                'valid_external': len([r for r in external_results if r['valid']]),
                'total_internal': len(internal_results),
                'valid_internal': len([r for r in internal_results if r['valid']])
            }
        }
```

---

## 🎓 Contributing Guidelines Summary

### Development Workflow

#### Standard Contribution Process
```bash
# 1. Fork and clone
git clone https://github.com/yourusername/rxiv-maker.git
cd rxiv-maker

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Setup development environment
pip install -e ".[dev]"
pre-commit install

# 4. Make changes and test
# ... edit code ...
pytest tests/ -v
ruff check src/ tests/
black --check src/ tests/

# 5. Commit with conventional commits
git add .
git commit -m "feat: add new validation feature

- Add DOI validation for citations
- Improve error messages for malformed references
- Update tests for new validation logic"

# 6. Push and create PR
git push origin feature/your-feature-name
# Create PR through GitHub UI
```

#### Code Quality Standards
- **Test Coverage**: Maintain >85% test coverage
- **Code Style**: Follow Black formatting, pass Ruff linting
- **Type Hints**: Required for all public APIs
- **Documentation**: Update docs for user-facing changes
- **Performance**: Profile performance-critical changes

### Architecture Principles

1. **Service-Oriented**: Business logic in service layer
2. **Engine Abstraction**: Support multiple build environments
3. **Graceful Degradation**: Fallback when dependencies missing
4. **Local-First**: Validate locally before CI/CD
5. **Container-Ready**: Support Docker/Podman workflows

**🚀 Ready to contribute?** Check [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines and [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues) for tasks to work on.

---

**📚 [User Guide](USER_GUIDE.md) | ⚙️ [CLI Reference](CLI_REFERENCE.md) | 🔧 [Troubleshooting](TROUBLESHOOTING.md) | 🚀 [Getting Started](GETTING_STARTED.md)**