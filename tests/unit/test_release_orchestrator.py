"""Tests for the release orchestrator."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add the GitHub scripts path to sys.path
github_scripts_path = Path(__file__).parent.parent.parent / ".github" / "scripts" / "release"
sys.path.insert(0, str(github_scripts_path.parent / "common"))
sys.path.insert(0, str(github_scripts_path))

from orchestrator import ReleaseOrchestrator  # noqa: E402


class TestReleaseOrchestratorChangelogValidation:
    """Test the _validate_changelog method of ReleaseOrchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment variables and dependencies
        self.mock_env = {
            "GITHUB_REPOSITORY": "test/repo",
            "GITHUB_TOKEN": "fake_token",
        }

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [v1.2.3] - 2025-10-29\n### Added\n- New feature\n")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_with_v_prefix_success(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test successful CHANGELOG validation with 'v' prefix."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should not raise exception
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [1.2.3] - 2025-10-29\n### Added\n- New feature\n")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_without_v_prefix_success(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test successful CHANGELOG validation without 'v' prefix."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"  # Version includes 'v' but CHANGELOG doesn't
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should not raise exception
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_file_not_found(self, mock_exists, mock_config_loader, mock_github_token, mock_version):
        """Test CHANGELOG validation when file doesn't exist."""
        # Setup
        mock_exists.return_value = False
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError
        with pytest.raises(ValueError, match="CHANGELOG.md not found in repository root"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [v1.0.0] - 2025-01-01\n### Added\n- Old feature\n")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_version_not_found(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation when version entry is missing."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"  # Different version than in CHANGELOG
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError with helpful message
        with pytest.raises(ValueError) as exc_info:
            orchestrator._validate_changelog()

        assert "No CHANGELOG entry found for version v1.2.3" in str(exc_info.value)
        assert "Please add a CHANGELOG entry before creating a release" in str(exc_info.value)

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_validate_changelog_encoding_error(
        self, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation handles encoding errors gracefully."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Mock file read to raise UnicodeDecodeError
        mock_file.return_value.__enter__.return_value.read.side_effect = UnicodeDecodeError(
            "utf-8", b"", 0, 1, "invalid start byte"
        )

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError with meaningful error message
        with pytest.raises(ValueError, match="Failed to read CHANGELOG.md: encoding error"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="## [v1.2.3]\n### Fixed\n- Bug fix\n## [v1.2.2]\n### Added\n- Feature\n",
    )
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_multiple_versions_present(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with multiple version entries."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should succeed when target version is present
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="## [v1.2.3-beta.1] - 2025-10-29\n### Added\n- Beta feature\n",
    )
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_prerelease_version(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with prerelease version."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3-beta.1"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should succeed with prerelease version
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [  v1.2.3  ] - 2025-10-29\n### Added\n- Feature\n")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_with_whitespace(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation tolerates extra whitespace (updated behavior with regex)."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should now succeed with whitespace (regex-based matching tolerates it)
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_empty_file(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with empty file."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 0

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should fail with empty CHANGELOG
        with pytest.raises(ValueError, match="No CHANGELOG entry found"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("pathlib.Path.resolve")
    @patch("pathlib.Path.exists")
    def test_validate_changelog_path_traversal_protection(
        self, mock_exists, mock_resolve, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation prevents path traversal attacks."""
        # Setup
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Mock Path.resolve to return a path outside repository root
        repo_root = Path("/repo/root")
        outside_path = Path("/etc/passwd")

        # Mock cwd to return repo_root
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value.resolve.return_value = repo_root

            # First resolve call returns repo_root, second returns outside_path
            mock_resolve.side_effect = [repo_root, outside_path]

            # Create orchestrator
            orchestrator = ReleaseOrchestrator(dry_run=True)

            # Test - should raise ValueError with security error message
            with pytest.raises(ValueError, match="Security error.*outside repository root"):
                orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_file_permission_error(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation handles file permission errors gracefully."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Mock file size to be within limits
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise PermissionError
        with pytest.raises(PermissionError):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [V1.2.3] - 2025-10-29\n### Added\n- Feature\n")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_case_insensitive_matching(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation with case-insensitive version matching."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"  # lowercase 'v'
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should succeed with uppercase 'V' in CHANGELOG (case-insensitive)
        orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_file_size_limit(
        self, mock_stat, mock_exists, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation enforces file size limit."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")

        # Mock file size to exceed 10MB limit
        mock_stat.return_value.st_size = 11 * 1024 * 1024  # 11MB

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should raise ValueError about file size
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            orchestrator._validate_changelog()

    @patch("orchestrator.get_current_version")
    @patch("orchestrator.get_github_token")
    @patch("orchestrator.ConfigLoader")
    @patch("builtins.open", new_callable=mock_open, read_data="## [  v1.2.3  ] - 2025-10-29\n### Added\n- Feature\n")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_validate_changelog_whitespace_tolerance(
        self, mock_stat, mock_exists, mock_file, mock_config_loader, mock_github_token, mock_version
    ):
        """Test CHANGELOG validation tolerates whitespace within brackets (new behavior)."""
        # Setup
        mock_exists.return_value = True
        mock_version.return_value = "v1.2.3"
        mock_github_token.return_value = "fake_token"
        mock_config_loader.return_value.load_release_config.return_value = MagicMock(package_name="rxiv-maker")
        mock_stat.return_value.st_size = 1024

        # Create orchestrator
        orchestrator = ReleaseOrchestrator(dry_run=True)

        # Test - should now succeed with whitespace (regex allows \s*)
        orchestrator._validate_changelog()
