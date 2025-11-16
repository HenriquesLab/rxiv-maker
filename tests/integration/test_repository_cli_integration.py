"""Integration tests for repository management CLI commands.

Tests the complete workflow for repository management including:
- repo-init: Configure repository settings
- create-repo: Create local manuscript repositories
- repos: List and manage repositories
- repos-search: Search and clone from GitHub
"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.xdist_group(name="repo_cli_integration")
class TestRepoInitCLI:
    """Test rxiv repo-init command."""

    def test_repo_init_non_interactive(self, temp_dir, monkeypatch):
        """Test repo-init in non-interactive mode."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        # Backup existing config if present
        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            result = subprocess.run(
                [
                    "rxiv",
                    "repo-init",
                    "--parent-dir",
                    str(temp_dir / "manuscripts"),
                    "--github-org",
                    "test-org",
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"repo-init failed: {result.stderr}"

            # Verify config was created
            assert config_file.exists(), "Config file not created"

            # Verify parent directory was created
            assert (temp_dir / "manuscripts").exists(), "Parent directory not created"

        finally:
            # Restore backup
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()

    def test_repo_init_creates_parent_dir(self, temp_dir, monkeypatch):
        """Test that repo-init creates parent directory if needed."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            nested_path = temp_dir / "nested" / "manuscripts"

            result = subprocess.run(
                [
                    "rxiv",
                    "repo-init",
                    "--parent-dir",
                    str(nested_path),
                    "--github-org",
                    "test-org",
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"repo-init failed: {result.stderr}"
            assert nested_path.exists(), "Nested parent directory not created"

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()


@pytest.mark.xdist_group(name="repo_cli_integration")
class TestCreateRepoCLI:
    """Test rxiv create-repo command."""

    def test_create_repo_basic(self, temp_dir, monkeypatch):
        """Test creating a basic repository."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            # First configure parent directory
            subprocess.run(
                [
                    "rxiv",
                    "repo-init",
                    "--parent-dir",
                    str(temp_dir),
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            result = subprocess.run(
                ["rxiv", "create-repo", "test-paper", "--no-github", "--no-interactive"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"create-repo failed: {result.stderr}"

            # Verify repository was created
            repo_path = temp_dir / "manuscript-test-paper"
            assert repo_path.exists(), "Repository directory not created"
            assert (repo_path / "MANUSCRIPT").exists(), "MANUSCRIPT directory not created"
            assert (repo_path / ".gitignore").exists(), ".gitignore not created"
            assert (repo_path / "README.md").exists(), "README.md not created"

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()

    def test_create_repo_already_exists(self, temp_dir, monkeypatch):
        """Test error when repository already exists."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            # Configure parent directory
            subprocess.run(
                [
                    "rxiv",
                    "repo-init",
                    "--parent-dir",
                    str(temp_dir),
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Create repository manually
            (temp_dir / "manuscript-existing").mkdir()

            result = subprocess.run(
                ["rxiv", "create-repo", "existing", "--no-github", "--no-interactive"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode != 0, "Should fail when repository exists"
            output = (result.stdout + result.stderr).lower()
            assert "already exists" in output or "exists" in output

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()

    def test_create_repo_invalid_name(self, temp_dir, monkeypatch):
        """Test error with invalid repository name."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            # Configure parent directory
            subprocess.run(
                [
                    "rxiv",
                    "repo-init",
                    "--parent-dir",
                    str(temp_dir),
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            result = subprocess.run(
                ["rxiv", "create-repo", "invalid_name", "--no-github", "--no-interactive"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode != 0, "Should fail with underscore in name"

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()


@pytest.mark.xdist_group(name="repo_cli_integration")
class TestReposCLI:
    """Test rxiv repos command."""

    def test_repos_empty(self, temp_dir, monkeypatch):
        """Test listing repositories when directory is empty."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "repos", "--parent-dir", str(temp_dir), "--format", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Command should succeed even with no repos
        assert result.returncode == 0, f"repos failed: {result.stderr}"

    def test_repos_list_repositories(self, temp_dir, monkeypatch):
        """Test listing multiple repositories."""
        monkeypatch.chdir(temp_dir)

        # Create test repositories
        (temp_dir / "manuscript-paper1").mkdir()
        (temp_dir / "manuscript-paper1" / "MANUSCRIPT").mkdir()
        (temp_dir / "manuscript-paper2").mkdir()
        (temp_dir / "manuscript-paper2" / "MANUSCRIPT").mkdir()

        result = subprocess.run(
            ["rxiv", "repos", "--parent-dir", str(temp_dir), "--format", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"repos failed: {result.stderr}"

        # Verify repositories are mentioned in output
        assert "paper1" in result.stdout or "manuscript-paper1" in result.stdout
        assert "paper2" in result.stdout or "manuscript-paper2" in result.stdout


@pytest.mark.xdist_group(name="repo_cli_integration")
class TestReposSearchCLI:
    """Test rxiv repos-search command."""

    def test_repos_search_requires_org(self, temp_dir, monkeypatch):
        """Test that repos-search requires organization argument."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "repos-search", "--no-interactive"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail or prompt for organization
        # Either exit code != 0 or help message shown
        assert result.returncode != 0 or "usage" in result.stderr.lower() or "organization" in result.stdout.lower()


@pytest.mark.xdist_group(name="repo_cli_integration")
class TestConfigCLI:
    """Test rxiv config command."""

    def test_config_non_interactive(self, temp_dir, monkeypatch):
        """Test config in non-interactive mode."""
        monkeypatch.chdir(temp_dir)

        result = subprocess.run(
            ["rxiv", "config", "--non-interactive"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should succeed or show current config
        assert result.returncode == 0, f"config failed: {result.stderr}"

    def test_config_show_repo(self, temp_dir, monkeypatch):
        """Test config show-repo command."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            # First set config
            subprocess.run(
                [
                    "rxiv",
                    "config",
                    "set-repo-parent-dir",
                    str(temp_dir / "manuscripts"),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Then show it
            result = subprocess.run(
                ["rxiv", "config", "show-repo"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"config show-repo failed: {result.stderr}"
            # Verify configuration is shown
            assert "parent directory" in result.stdout.lower()
            assert "config file" in result.stdout.lower()

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()

    def test_config_set_repo_org(self, temp_dir, monkeypatch):
        """Test setting default GitHub organization."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            result = subprocess.run(
                ["rxiv", "config", "set-repo-org", "test-org"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"set-repo-org failed: {result.stderr}"

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()


@pytest.mark.xdist_group(name="repo_cli_integration")
class TestRepositoryWorkflow:
    """Test complete repository management workflows."""

    def test_full_workflow_local(self, temp_dir, monkeypatch):
        """Test complete workflow: init config -> create repo -> list repos."""
        monkeypatch.chdir(temp_dir)
        config_file = Path.home() / ".rxiv-maker" / "config"

        backup = None
        if config_file.exists():
            backup = config_file.read_text()

        try:
            # Step 1: Configure repository settings
            init_result = subprocess.run(
                [
                    "rxiv",
                    "repo-init",
                    "--parent-dir",
                    str(temp_dir / "manuscripts"),
                    "--github-org",
                    "test-org",
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert init_result.returncode == 0, f"repo-init failed: {init_result.stderr}"

            # Step 2: Create a repository
            create_result = subprocess.run(
                ["rxiv", "create-repo", "paper1", "--no-github", "--no-interactive"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert create_result.returncode == 0, f"create-repo failed: {create_result.stderr}"

            # Step 3: Create another repository
            create_result2 = subprocess.run(
                ["rxiv", "create-repo", "paper2", "--no-github", "--no-interactive"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert create_result2.returncode == 0, f"create-repo failed: {create_result2.stderr}"

            # Step 4: List repositories
            list_result = subprocess.run(
                ["rxiv", "repos", "--parent-dir", str(temp_dir / "manuscripts"), "--format", "list"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert list_result.returncode == 0, f"repos failed: {list_result.stderr}"

            # Verify both repositories are listed
            assert "paper1" in list_result.stdout or "manuscript-paper1" in list_result.stdout
            assert "paper2" in list_result.stdout or "manuscript-paper2" in list_result.stdout

        finally:
            if backup:
                config_file.write_text(backup)
            elif config_file.exists():
                config_file.unlink()
