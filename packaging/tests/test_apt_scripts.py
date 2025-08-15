"""Unit tests for APT packaging scripts."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestBuildDebScript:
    """Test build-deb.sh script functionality."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def script_path(self, project_root):
        """Get path to build-deb.sh script."""
        return project_root / "packaging" / "scripts" / "build-deb.sh"

    def test_script_exists_and_executable(self, script_path):
        """Test that build-deb.sh exists and is executable."""
        assert script_path.exists(), "build-deb.sh script does not exist"
        assert os.access(script_path, os.X_OK), "build-deb.sh is not executable"

    def test_script_has_shebang(self, script_path):
        """Test that script has proper shebang."""
        with open(script_path, "r") as f:
            first_line = f.readline().strip()

        assert first_line.startswith("#!/"), "Script missing shebang"
        assert "bash" in first_line, "Script should use bash"

    def test_script_has_set_flags(self, script_path):
        """Test that script has proper error handling flags."""
        content = script_path.read_text()

        # Should have strict error handling
        assert "set -euo pipefail" in content, "Script should use strict error handling"

    def test_script_help_option(self, script_path):
        """Test that script responds to --help option."""
        content = script_path.read_text()

        assert "--help" in content, "Script should support --help option"
        assert "show_help()" in content, "Script should have show_help function"

    def test_script_has_color_output(self, script_path):
        """Test that script includes color output functions."""
        content = script_path.read_text()

        # Check for color definitions
        assert "RED=" in content, "Script should define RED color"
        assert "GREEN=" in content, "Script should define GREEN color"
        assert "BLUE=" in content, "Script should define BLUE color"

        # Check for logging functions
        assert "log()" in content, "Script should have log function"
        assert "success()" in content, "Script should have success function"
        assert "error()" in content, "Script should have error function"

    @patch("subprocess.run")
    def test_validate_environment_function(self, mock_run, script_path):
        """Test environment validation logic."""
        # Mock successful command checks
        mock_run.return_value = MagicMock(returncode=0)

        content = script_path.read_text()

        # Check that validation function exists and checks required tools
        assert "validate_environment()" in content
        assert "dpkg-buildpackage" in content
        assert "debhelper" in content
        assert "python3" in content

    def test_version_extraction(self, script_path):
        """Test that script can extract version from __version__.py."""
        content = script_path.read_text()

        # Check for version extraction logic
        assert "get_version()" in content
        assert "__version__.py" in content
        assert "python3 -c" in content

    def test_update_changelog_function(self, script_path):
        """Test changelog update functionality."""
        content = script_path.read_text()

        assert "update_changelog()" in content
        assert "debian/changelog" in content
        assert "date -R" in content  # RFC 2822 date format

    def test_build_options_handling(self, script_path):
        """Test that script handles various build options."""
        content = script_path.read_text()

        # Check for GPG signing options
        assert "--sign" in content or "-s" in content
        assert "--key" in content or "-k" in content

        # Check for build flags
        assert "dpkg-buildpackage" in content
        assert "-us -uc" in content  # unsigned source and changes

    def test_output_directory_handling(self, script_path):
        """Test output directory configuration."""
        content = script_path.read_text()

        assert "--output" in content or "-o" in content
        assert "OUTPUT_DIR=" in content
        assert "mkdir -p" in content

    def test_post_build_validation(self, script_path):
        """Test post-build validation steps."""
        content = script_path.read_text()

        # Should validate built packages
        assert "post_build()" in content or "validate_package()" in content
        assert "*.deb" in content
        assert "dpkg-deb" in content

    def test_lintian_check(self, script_path):
        """Test that script includes lintian checking."""
        content = script_path.read_text()

        assert "lintian" in content, "Script should include lintian checking"


class TestSetupAptRepoScript:
    """Test setup-apt-repo.sh script functionality."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def script_path(self, project_root):
        """Get path to setup-apt-repo.sh script."""
        return project_root / "packaging" / "scripts" / "setup-apt-repo.sh"

    def test_script_exists_and_executable(self, script_path):
        """Test that setup-apt-repo.sh exists and is executable."""
        assert script_path.exists(), "setup-apt-repo.sh script does not exist"
        assert os.access(script_path, os.X_OK), "setup-apt-repo.sh is not executable"

    def test_script_has_required_tools_check(self, script_path):
        """Test that script checks for required tools."""
        content = script_path.read_text()

        # Should check for reprepro and related tools
        assert "reprepro" in content
        assert "git" in content
        assert "gpg" in content

        # Should have tool validation
        assert "validate_environment()" in content

    def test_repository_initialization(self, script_path):
        """Test repository initialization functionality."""
        content = script_path.read_text()

        assert "initialize_repo()" in content or "--init" in content
        assert "conf/distributions" in content
        assert "conf/options" in content

        # Should handle GPG key export
        assert "gpg --armor --export" in content

    def test_package_addition(self, script_path):
        """Test package addition to repository."""
        content = script_path.read_text()

        assert "add_package()" in content or "includedeb" in content
        assert "reprepro" in content
        assert "stable" in content  # distribution name

    def test_repository_publishing(self, script_path):
        """Test repository publishing to GitHub."""
        content = script_path.read_text()

        assert "publish_repository()" in content or "--publish" in content
        assert "git push" in content
        assert "apt-repo" in content  # branch name

    def test_gpg_key_validation(self, script_path):
        """Test GPG key validation."""
        content = script_path.read_text()

        assert "GPG_KEY_ID" in content
        assert "gpg --list-secret-keys" in content

        # Should validate key existence
        assert "key not found" in content.lower() or "not accessible" in content.lower()

    def test_repository_structure_creation(self, script_path):
        """Test that script creates proper repository structure."""
        content = script_path.read_text()

        # Should create required directories
        assert "dists" in content
        assert "pool" in content
        assert "incoming" in content

    def test_readme_generation(self, script_path):
        """Test README.md generation for repository."""
        content = script_path.read_text()

        assert "README.md" in content
        assert "## Usage" in content or "## Installation" in content

    def test_metadata_update(self, script_path):
        """Test repository metadata updates."""
        content = script_path.read_text()

        assert "update_repository()" in content or "export" in content
        assert "reprepro" in content


class TestDebianConfigFiles:
    """Test Debian configuration files."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def debian_dir(self, project_root):
        """Get debian directory."""
        return project_root / "debian"

    def test_control_file_dependencies(self, debian_dir):
        """Test that control file has correct dependencies."""
        control_file = debian_dir / "control"
        content = control_file.read_text()

        # Check for essential dependencies
        essential_deps = [
            "python3-matplotlib",
            "python3-numpy",
            "python3-pandas",
            "python3-yaml",
            "python3-click",
            "texlive-latex-base",
        ]

        for dep in essential_deps:
            assert dep in content, f"Missing essential dependency: {dep}"

    def test_control_file_architecture(self, debian_dir):
        """Test that control file specifies correct architecture."""
        control_file = debian_dir / "control"
        content = control_file.read_text()

        assert "Architecture: all" in content, "Package should be architecture-independent"

    def test_rules_file_structure(self, debian_dir):
        """Test debian/rules file structure."""
        rules_file = debian_dir / "rules"
        content = rules_file.read_text()

        # Should be a makefile
        assert "#!/usr/bin/make -f" in content

        # Should use dh with python3
        assert "dh $@" in content
        assert "--with python3" in content or "python3" in content

        # Should have proper overrides
        assert "override_dh_auto_build" in content or "dh_auto_build" in content

    def test_postinst_script_safety(self, debian_dir):
        """Test postinst script follows safety guidelines."""
        postinst_file = debian_dir / "rxiv-maker.postinst"
        content = postinst_file.read_text()

        # Should have proper error handling
        assert "set -e" in content

        # Should handle different invocation cases
        assert 'case "$1" in' in content
        assert "configure)" in content

        # Should not have dangerous operations
        dangerous_patterns = [
            "rm -rf /",
            "chmod 777",
            "chown -R root",
        ]

        for pattern in dangerous_patterns:
            assert pattern not in content, f"Dangerous pattern found: {pattern}"

    def test_copyright_file_format(self, debian_dir):
        """Test copyright file follows Debian format."""
        copyright_file = debian_dir / "copyright"
        content = copyright_file.read_text()

        # Should follow machine-readable format
        assert "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/" in content
        assert "Upstream-Name:" in content
        assert "Source:" in content
        assert "License: MIT" in content

    def test_compat_level(self, debian_dir):
        """Test debhelper compatibility level."""
        compat_file = debian_dir / "compat"
        content = compat_file.read_text().strip()

        # Should use modern debhelper
        compat_level = int(content)
        assert compat_level >= 12, f"Debhelper compat level too old: {compat_level}"

    def test_source_format(self, debian_dir):
        """Test source package format."""
        format_file = debian_dir / "source" / "format"
        content = format_file.read_text().strip()

        # Should use modern source format
        assert content == "3.0 (quilt)", f"Unexpected source format: {content}"

    def test_install_file_contents(self, debian_dir):
        """Test install file specifies correct file mappings."""
        install_file = debian_dir / "rxiv-maker.install"
        content = install_file.read_text()

        # Should install LaTeX style files
        assert "src/tex/style/*" in content
        assert "usr/share/texmf" in content

        # Should install templates
        assert "template.tex" in content


class TestWorkflowValidation:
    """Test GitHub Actions workflow validation."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def workflow_file(self, project_root):
        """Get workflow file path."""
        return project_root / ".github" / "workflows" / "publish-apt.yml"

    def test_workflow_yaml_syntax(self, workflow_file):
        """Test that workflow file has valid YAML syntax."""
        import yaml

        try:
            with open(workflow_file, "r") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax: {e}")

    def test_workflow_required_jobs(self, workflow_file):
        """Test that workflow has all required jobs."""
        import yaml

        with open(workflow_file, "r") as f:
            workflow = yaml.safe_load(f)

        jobs = workflow.get("jobs", {})
        required_jobs = ["build-deb", "setup-apt-repo", "deploy-pages", "summary"]

        for job in required_jobs:
            assert job in jobs, f"Missing required job: {job}"

    def test_workflow_secrets_handling(self, workflow_file):
        """Test that workflow properly handles secrets."""
        content = workflow_file.read_text()

        # Should reference required secrets
        assert "GPG_PRIVATE_KEY" in content
        assert "GPG_PASSPHRASE" in content
        assert "secrets." in content

    def test_workflow_conditional_execution(self, workflow_file):
        """Test workflow conditional execution logic."""
        content = workflow_file.read_text()

        # Should have dry-run conditional logic
        assert "if:" in content
        assert "inputs.dry-run" in content

        # Should skip certain jobs in dry-run mode
        assert "!inputs.dry-run" in content

    def test_workflow_artifact_handling(self, workflow_file):
        """Test workflow artifact upload/download."""
        content = workflow_file.read_text()

        # Should upload and download artifacts
        assert "upload-artifact" in content
        assert "download-artifact" in content
        assert "debian-package" in content

    def test_workflow_permissions(self, workflow_file):
        """Test workflow permissions configuration."""
        import yaml

        with open(workflow_file, "r") as f:
            workflow = yaml.safe_load(f)

        permissions = workflow.get("permissions", {})

        # Should have required permissions
        assert "contents" in permissions
        assert "pages" in permissions
        assert "id-token" in permissions
