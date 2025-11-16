"""Tests for GitHub integration utilities."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.rxiv_maker.utils.github import (
    GitHubError,
    check_gh_auth,
    check_gh_cli_installed,
    check_github_repo_exists,
    clone_github_repo,
    create_github_repo,
    list_github_repos,
    validate_github_name,
)


class TestValidateGithubName:
    """Test GitHub name validation function."""

    def test_valid_names(self):
        """Test that valid GitHub names pass validation."""
        valid_names = [
            "valid-repo",
            "ValidRepo",
            "repo123",
            "my-org-name",
            "a",
            "a" * 39,  # Maximum length
        ]
        for name in valid_names:
            # Should not raise
            validate_github_name(name, "repository")

    def test_empty_name(self):
        """Test that empty names are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_github_name("", "repository")

    def test_too_long(self):
        """Test that names exceeding 39 characters are rejected."""
        long_name = "a" * 40
        with pytest.raises(ValueError, match="cannot exceed 39 characters"):
            validate_github_name(long_name, "repository")

    def test_invalid_characters(self):
        """Test that names with invalid characters are rejected."""
        invalid_names = [
            "repo_name",  # underscores not allowed
            "repo.name",  # dots not allowed
            "repo name",  # spaces not allowed
            "repo/name",  # slashes not allowed
            "repo\\name",  # backslashes not allowed
        ]
        for name in invalid_names:
            with pytest.raises(ValueError):
                validate_github_name(name, "repository")

    def test_starts_with_hyphen(self):
        """Test that names starting with hyphen are rejected."""
        with pytest.raises(ValueError, match="cannot start or end with a hyphen"):
            validate_github_name("-repo", "repository")

    def test_ends_with_hyphen(self):
        """Test that names ending with hyphen are rejected."""
        with pytest.raises(ValueError, match="cannot start or end with a hyphen"):
            validate_github_name("repo-", "repository")

    def test_consecutive_hyphens(self):
        """Test that names with consecutive hyphens are rejected."""
        with pytest.raises(ValueError, match="cannot contain consecutive hyphens"):
            validate_github_name("repo--name", "repository")

    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are rejected."""
        dangerous_names = [
            "..",
            "../repo",
            "repo/..",
            "repo/../other",
        ]
        for name in dangerous_names:
            with pytest.raises(ValueError):
                validate_github_name(name, "repository")


class TestCheckGhCliInstalled:
    """Test GitHub CLI installation check."""

    @patch("src.rxiv_maker.utils.github.shutil.which")
    def test_gh_cli_installed(self, mock_which):
        """Test when gh CLI is installed."""
        mock_which.return_value = "/usr/bin/gh"
        assert check_gh_cli_installed() is True
        mock_which.assert_called_once_with("gh")

    @patch("src.rxiv_maker.utils.github.shutil.which")
    def test_gh_cli_not_installed(self, mock_which):
        """Test when gh CLI is not installed."""
        mock_which.return_value = None
        assert check_gh_cli_installed() is False


class TestCheckGhAuth:
    """Test GitHub CLI authentication check."""

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_authenticated(self, mock_installed, mock_run):
        """Test when user is authenticated."""
        mock_installed.return_value = True
        mock_run.return_value = Mock(returncode=0)

        assert check_gh_auth() is True
        mock_run.assert_called_once()

    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_not_installed(self, mock_installed):
        """Test when gh CLI is not installed."""
        mock_installed.return_value = False
        assert check_gh_auth() is False

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_not_authenticated(self, mock_installed, mock_run):
        """Test when user is not authenticated."""
        mock_installed.return_value = True
        mock_run.return_value = Mock(returncode=1)

        assert check_gh_auth() is False


class TestCheckGithubRepoExists:
    """Test GitHub repository existence check."""

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_repo_exists(self, mock_installed, mock_auth, mock_run):
        """Test when repository exists."""
        mock_installed.return_value = True
        mock_auth.return_value = True
        mock_run.return_value = Mock(returncode=0)

        assert check_github_repo_exists("test-org", "test-repo") is True

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_repo_not_exists(self, mock_installed, mock_auth, mock_run):
        """Test when repository does not exist."""
        mock_installed.return_value = True
        mock_auth.return_value = True
        mock_run.return_value = Mock(returncode=1)

        assert check_github_repo_exists("test-org", "test-repo") is False

    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_gh_not_installed(self, mock_installed):
        """Test error when gh CLI not installed."""
        mock_installed.return_value = False

        with pytest.raises(GitHubError, match="GitHub CLI.*is not installed"):
            check_github_repo_exists("test-org", "test-repo")

    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_not_authenticated(self, mock_installed, mock_auth):
        """Test error when not authenticated."""
        mock_installed.return_value = True
        mock_auth.return_value = False

        with pytest.raises(GitHubError, match="Not authenticated"):
            check_github_repo_exists("test-org", "test-repo")

    def test_invalid_org_name(self):
        """Test validation of organization name."""
        with pytest.raises(ValueError):
            check_github_repo_exists("invalid_org", "test-repo")

    def test_invalid_repo_name(self):
        """Test validation of repository name."""
        with pytest.raises(ValueError):
            check_github_repo_exists("test-org", "invalid_repo_name")


class TestCreateGithubRepo:
    """Test GitHub repository creation."""

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_create_public_repo_with_api(self, mock_installed, mock_auth, mock_run):
        """Test creating a public repository with API URL retrieval."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        # Mock successful creation
        create_result = Mock(returncode=0, stdout="Created repository", stderr="")

        # Mock successful API call
        api_result = Mock(returncode=0, stdout="https://github.com/test-org/test-repo\n", stderr="")

        mock_run.side_effect = [create_result, api_result]

        url = create_github_repo("test-org", "test-repo", "public")

        assert url == "https://github.com/test-org/test-repo"
        assert mock_run.call_count == 2

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_create_private_repo(self, mock_installed, mock_auth, mock_run):
        """Test creating a private repository."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        create_result = Mock(returncode=0, stdout="Created repository", stderr="")
        api_result = Mock(returncode=0, stdout="https://github.com/test-org/private-repo\n", stderr="")

        mock_run.side_effect = [create_result, api_result]

        url = create_github_repo("test-org", "private-repo", "private")

        assert url == "https://github.com/test-org/private-repo"

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_create_repo_api_fails_fallback(self, mock_installed, mock_auth, mock_run):
        """Test fallback to constructed URL when API call fails."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        create_result = Mock(returncode=0, stdout="Created repository", stderr="")
        api_result = Mock(returncode=1, stdout="", stderr="API error")

        mock_run.side_effect = [create_result, api_result]

        url = create_github_repo("test-org", "test-repo", "public")

        # Should fall back to constructed URL
        assert url == "https://github.com/test-org/test-repo"

    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_create_repo_not_installed(self, mock_installed):
        """Test error when gh CLI not installed."""
        mock_installed.return_value = False

        with pytest.raises(GitHubError, match="GitHub CLI.*is not installed"):
            create_github_repo("test-org", "test-repo")

    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_invalid_visibility(self, mock_installed, mock_auth):
        """Test error with invalid visibility."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        with pytest.raises(ValueError, match="Invalid visibility"):
            create_github_repo("test-org", "test-repo", "invalid")

    def test_invalid_org_name_create(self):
        """Test validation on create."""
        with pytest.raises(ValueError):
            create_github_repo("invalid_org", "test-repo")


class TestCloneGithubRepo:
    """Test GitHub repository cloning."""

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_clone_success(self, mock_installed, mock_auth, mock_run, tmp_path):
        """Test successful repository cloning."""
        mock_installed.return_value = True
        mock_auth.return_value = True
        mock_run.return_value = Mock(returncode=0)

        target = tmp_path / "cloned-repo"

        clone_github_repo("test-org", "test-repo", target)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "gh" in call_args
        assert "repo" in call_args
        assert "clone" in call_args

    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_clone_target_exists(self, mock_installed, mock_auth, tmp_path):
        """Test error when target path already exists."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        target = tmp_path / "existing"
        target.mkdir()

        with pytest.raises(GitHubError, match="Target path already exists"):
            clone_github_repo("test-org", "test-repo", target)

    def test_clone_invalid_org(self):
        """Test validation on clone."""
        with pytest.raises(ValueError):
            clone_github_repo("invalid_org", "test-repo", Path("/tmp/repo"))


class TestListGithubRepos:
    """Test GitHub repository listing."""

    @patch("src.rxiv_maker.utils.github.subprocess.run")
    @patch("src.rxiv_maker.utils.github.check_gh_auth")
    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_list_repos_success(self, mock_installed, mock_auth, mock_run):
        """Test successful repository listing."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        repos_json = '[{"name": "manuscript-test1", "url": "https://github.com/org/manuscript-test1"}, {"name": "manuscript-test2", "url": "https://github.com/org/manuscript-test2"}, {"name": "other-repo", "url": "https://github.com/org/other-repo"}]'
        mock_run.return_value = Mock(returncode=0, stdout=repos_json)

        repos = list_github_repos("test-org", "manuscript-")

        assert len(repos) == 2
        assert all(r["name"].startswith("manuscript-") for r in repos)

    @patch("src.rxiv_maker.utils.github.check_gh_cli_installed")
    def test_list_repos_not_installed(self, mock_installed):
        """Test error when gh CLI not installed."""
        mock_installed.return_value = False

        with pytest.raises(GitHubError, match="GitHub CLI.*is not installed"):
            list_github_repos("test-org")

    def test_list_repos_invalid_org(self):
        """Test validation on list."""
        with pytest.raises(ValueError):
            list_github_repos("invalid_org")
