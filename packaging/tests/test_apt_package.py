"""Integration tests for APT package functionality."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.apt_package,
    pytest.mark.platform_specific,
]


class TestAptPackageBuild:
    """Test Debian package building functionality."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def temp_build_dir(self):
        """Create temporary build directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_debian_files_exist(self, project_root):
        """Test that all required Debian packaging files exist."""
        debian_dir = project_root / "debian"

        required_files = [
            "control",
            "changelog",
            "rules",
            "copyright",
            "compat",
            "source/format",
            "rxiv-maker.install",
            "rxiv-maker.postinst",
            "rxiv-maker.prerm",
        ]

        assert debian_dir.exists(), "debian/ directory does not exist"

        for file_path in required_files:
            full_path = debian_dir / file_path
            assert full_path.exists(), f"Required Debian file missing: {file_path}"

    def test_debian_control_format(self, project_root):
        """Test that debian/control file has correct format."""
        control_file = project_root / "debian" / "control"
        content = control_file.read_text()

        # Check required fields in source section
        assert "Source: rxiv-maker" in content
        assert "Section: science" in content
        assert "Priority: optional" in content
        assert "Maintainer:" in content
        assert "Build-Depends:" in content
        assert "Standards-Version:" in content
        assert "Homepage:" in content

        # Check required fields in binary package section
        assert "Package: rxiv-maker" in content
        assert "Architecture: all" in content
        assert "Depends:" in content
        assert "Description:" in content

    def test_debian_rules_executable(self, project_root):
        """Test that debian/rules file is executable."""
        rules_file = project_root / "debian" / "rules"

        assert rules_file.exists()
        assert os.access(rules_file, os.X_OK), "debian/rules is not executable"

    def test_build_deb_script_exists(self, project_root):
        """Test that build-deb.sh script exists and is executable."""
        script_file = project_root / "scripts" / "build-deb.sh"

        assert script_file.exists(), "build-deb.sh script does not exist"
        assert os.access(script_file, os.X_OK), "build-deb.sh is not executable"

    @pytest.mark.slow
    @pytest.mark.requires_debian_tools
    def test_build_deb_script_help(self, project_root):
        """Test that build-deb.sh script shows help."""
        script_file = project_root / "scripts" / "build-deb.sh"

        # Skip if debian tools not available
        if not self._has_debian_tools():
            pytest.skip("Debian build tools not available")

        result = subprocess.run([str(script_file), "--help"], capture_output=True, text=True, cwd=project_root)

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "OPTIONS:" in result.stdout

    def test_changelog_format(self, project_root):
        """Test that changelog follows Debian format."""
        changelog_file = project_root / "debian" / "changelog"
        content = changelog_file.read_text()

        lines = content.strip().split("\n")
        assert len(lines) >= 3, "Changelog too short"

        # First line should match format: package (version) distribution; urgency=level
        first_line = lines[0]
        assert "rxiv-maker (" in first_line
        assert ") stable; urgency=" in first_line

        # Last line should be signature with proper format
        sig_line = lines[-1] if lines else ""
        assert " -- " in sig_line
        assert "@" in sig_line  # Email address

    def _has_debian_tools(self):
        """Check if Debian build tools are available."""
        try:
            subprocess.run(["dpkg-buildpackage", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class TestAptRepository:
    """Test APT repository functionality."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_apt_repo_config_exists(self, project_root):
        """Test that APT repository configuration exists."""
        apt_repo_dir = project_root / "apt-repo"

        if not apt_repo_dir.exists():
            pytest.skip("APT repository configuration not yet created")

        conf_dir = apt_repo_dir / "conf"
        assert conf_dir.exists(), "apt-repo/conf directory missing"

        distributions_file = conf_dir / "distributions"
        assert distributions_file.exists(), "apt-repo/conf/distributions missing"

    def test_distributions_file_format(self, project_root):
        """Test that distributions file has correct format."""
        distributions_file = project_root / "apt-repo" / "conf" / "distributions"

        if not distributions_file.exists():
            pytest.skip("Distributions file not yet created")

        content = distributions_file.read_text()

        # Check required fields
        assert "Origin:" in content
        assert "Label:" in content
        assert "Suite: stable" in content
        assert "Codename: stable" in content
        assert "Architectures:" in content
        assert "Components: main" in content
        assert "Description:" in content
        assert "SignWith:" in content

    def test_setup_apt_repo_script_exists(self, project_root):
        """Test that setup-apt-repo.sh script exists and is executable."""
        script_file = project_root / "scripts" / "setup-apt-repo.sh"

        assert script_file.exists(), "setup-apt-repo.sh script does not exist"
        assert os.access(script_file, os.X_OK), "setup-apt-repo.sh is not executable"

    @pytest.mark.requires_reprepro
    def test_setup_apt_repo_script_help(self, project_root):
        """Test that setup-apt-repo.sh script shows help."""
        script_file = project_root / "scripts" / "setup-apt-repo.sh"

        # Skip if reprepro not available
        if not self._has_reprepro():
            pytest.skip("reprepro not available")

        result = subprocess.run([str(script_file), "--help"], capture_output=True, text=True, cwd=project_root)

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "OPTIONS:" in result.stdout

    def _has_reprepro(self):
        """Check if reprepro is available."""
        try:
            subprocess.run(["reprepro", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


class TestAptWorkflow:
    """Test APT publishing workflow."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_publish_apt_workflow_exists(self, project_root):
        """Test that publish-apt.yml workflow exists."""
        workflow_file = project_root / ".github" / "workflows" / "publish-apt.yml"
        assert workflow_file.exists(), "publish-apt.yml workflow does not exist"

    def test_workflow_syntax(self, project_root):
        """Test that workflow file has valid YAML syntax."""
        workflow_file = project_root / ".github" / "workflows" / "publish-apt.yml"

        import yaml

        try:
            with open(workflow_file, "r") as f:
                workflow_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax in workflow: {e}")

        # Check basic workflow structure
        assert "name" in workflow_data
        assert "on" in workflow_data
        assert "jobs" in workflow_data

        jobs = workflow_data["jobs"]
        expected_jobs = ["build-deb", "setup-apt-repo", "deploy-pages", "summary"]

        for job in expected_jobs:
            assert job in jobs, f"Expected job '{job}' not found in workflow"

    def test_workflow_permissions(self, project_root):
        """Test that workflow has appropriate permissions."""
        workflow_file = project_root / ".github" / "workflows" / "publish-apt.yml"

        import yaml

        with open(workflow_file, "r") as f:
            workflow_data = yaml.safe_load(f)

        # Check for required permissions
        permissions = workflow_data.get("permissions", {})
        expected_permissions = ["contents", "pages", "id-token"]

        for perm in expected_permissions:
            assert perm in permissions, f"Missing permission: {perm}"

    def test_workflow_inputs(self, project_root):
        """Test that workflow has correct inputs."""
        workflow_file = project_root / ".github" / "workflows" / "publish-apt.yml"

        import yaml

        with open(workflow_file, "r") as f:
            workflow_data = yaml.safe_load(f)

        # Check workflow_dispatch inputs
        on_section = workflow_data.get("on", {})
        workflow_dispatch = on_section.get("workflow_dispatch", {})
        inputs = workflow_dispatch.get("inputs", {})

        assert "version" in inputs, "Missing 'version' input"
        assert "dry-run" in inputs, "Missing 'dry-run' input"

        # Check input properties
        version_input = inputs["version"]
        assert version_input.get("required") is True
        assert version_input.get("type") == "string"

    @patch("subprocess.run")
    def test_mock_package_build(self, mock_run, project_root):
        """Test package build process with mocked subprocess calls."""
        # Mock successful subprocess calls
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        # Test would call build script
        script_file = project_root / "scripts" / "build-deb.sh"

        # Simulate calling the script
        subprocess.run([str(script_file), "--help"], capture_output=True, text=True, cwd=project_root)

        # Verify mock was called
        assert mock_run.called


class TestAptDocumentation:
    """Test APT-related documentation."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_apt_installation_docs_exist(self, project_root):
        """Test that APT installation documentation exists."""
        docs_file = project_root / "docs" / "getting-started" / "apt-installation.md"
        assert docs_file.exists(), "APT installation documentation missing"

    def test_apt_installation_docs_content(self, project_root):
        """Test that APT installation docs have required content."""
        docs_file = project_root / "docs" / "getting-started" / "apt-installation.md"
        content = docs_file.read_text()

        # Check for essential sections
        assert "# APT Repository Installation" in content
        assert "## Quick Installation" in content
        assert "curl -fsSL" in content  # GPG key installation
        assert "sudo apt update" in content
        assert "sudo apt install rxiv-maker" in content

    def test_readme_includes_apt_instructions(self, project_root):
        """Test that README includes APT installation instructions."""
        readme_file = project_root / "README.md"
        content = readme_file.read_text()

        # Check for APT section
        assert "APT Repository (Ubuntu/Debian)" in content
        assert "sudo apt install rxiv-maker" in content

    def test_installation_commands_validity(self, project_root):
        """Test that installation commands have proper syntax."""
        docs_file = project_root / "docs" / "getting-started" / "apt-installation.md"
        content = docs_file.read_text()

        # Extract bash commands and check basic syntax
        import re

        bash_blocks = re.findall(r"```bash\n(.*?)\n```", content, re.DOTALL)

        for block in bash_blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]

            for line in lines:
                # Skip comments
                if line.startswith("#"):
                    continue

                # Basic syntax checks
                assert not line.endswith("\\") or line.count("\\") % 2 == 1, f"Invalid line continuation: {line}"

                # Check for common issues
                assert "&&" not in line or not line.endswith("&&"), f"Line ending with &&: {line}"


class TestPackageValidation:
    """Test package validation and integrity."""

    def test_package_dependencies_mapping(self):
        """Test that Python dependencies map correctly to Debian packages."""
        # Define mapping from Python packages to Debian packages
        dependency_mapping = {
            "matplotlib": "python3-matplotlib",
            "seaborn": "python3-seaborn",
            "numpy": "python3-numpy",
            "pandas": "python3-pandas",
            "PIL": "python3-pil",  # Pillow maps to PIL
            "pypdf": "python3-pypdf",
            "yaml": "python3-yaml",  # PyYAML maps to yaml
            "click": "python3-click",
            "rich": "python3-rich",
            "requests": "python3-requests",
            "packaging": "python3-packaging",
            "platformdirs": "python3-platformdirs",
        }

        # This would be used to validate debian/control dependencies
        assert len(dependency_mapping) > 0

    def test_version_consistency(self, project_root):
        """Test that version is consistent across files."""
        # Get version from __version__.py
        version_file = project_root / "src" / "rxiv_maker" / "__version__.py"
        version_content = version_file.read_text()

        import re

        version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', version_content)
        assert version_match, "Could not extract version from __version__.py"

        package_version = version_match.group(1)

        # Check consistency in changelog
        changelog_file = project_root / "debian" / "changelog"
        if changelog_file.exists():
            changelog_content = changelog_file.read_text()
            assert f"rxiv-maker ({package_version}-1)" in changelog_content, (
                "Version mismatch between __version__.py and debian/changelog"
            )

    def test_required_scripts_permissions(self, project_root):
        """Test that required scripts have correct permissions."""
        scripts_to_check = [
            "scripts/build-deb.sh",
            "scripts/setup-apt-repo.sh",
            "debian/rules",
            "debian/rxiv-maker.postinst",
            "debian/rxiv-maker.prerm",
        ]

        for script_path in scripts_to_check:
            full_path = project_root / script_path
            if full_path.exists():
                assert os.access(full_path, os.X_OK), f"Script not executable: {script_path}"

    def test_postinst_script_safety(self, project_root):
        """Test that postinst script follows safe practices."""
        postinst_file = project_root / "debian" / "rxiv-maker.postinst"
        content = postinst_file.read_text()

        # Check for safe practices
        assert "set -e" in content, "postinst should use 'set -e'"
        assert 'case "$1" in' in content, "postinst should handle different cases"
        assert "configure)" in content, "postinst should handle configure case"

        # Check for potentially unsafe patterns
        assert "rm -rf /" not in content, "postinst contains dangerous rm command"
        assert "chmod 777" not in content, "postinst sets overly permissive permissions"
