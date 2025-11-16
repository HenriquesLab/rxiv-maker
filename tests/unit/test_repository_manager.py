"""Tests for RepositoryManager class."""

from unittest.mock import patch

import pytest
from git import Repo

from src.rxiv_maker.core.repo_config import RepoConfig
from src.rxiv_maker.core.repository import ManuscriptRepository, RepositoryManager


class TestRepositoryManager:
    """Test RepositoryManager class."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config = RepoConfig()
        config.parent_dir = tmp_path
        config.default_github_org = "test-org"
        config.default_editor = "nano"
        return config

    @pytest.fixture
    def repo_manager(self, config):
        """Create a repository manager with test config."""
        return RepositoryManager(config)

    def test_init_with_config(self, config):
        """Test initialization with config."""
        manager = RepositoryManager(config)
        assert manager.config == config

    def test_init_without_config(self):
        """Test initialization without config uses global config."""
        manager = RepositoryManager()
        assert manager.config is not None

    def test_discover_repositories_empty(self, repo_manager, tmp_path):
        """Test discovering repositories in empty directory."""
        repos = repo_manager.discover_repositories(tmp_path)
        assert repos == []

    def test_discover_repositories_with_repos(self, repo_manager, tmp_path):
        """Test discovering multiple repositories."""
        # Create test repositories
        (tmp_path / "manuscript-test1").mkdir()
        (tmp_path / "manuscript-test2").mkdir()
        (tmp_path / "manuscript-abc").mkdir()
        (tmp_path / "regular-dir").mkdir()  # Should be ignored

        repos = repo_manager.discover_repositories(tmp_path)

        assert len(repos) == 3
        repo_names = [r.name for r in repos]
        assert "test1" in repo_names
        assert "test2" in repo_names
        assert "abc" in repo_names

    def test_discover_repositories_sorted(self, repo_manager, tmp_path):
        """Test that repositories are sorted by name."""
        # Create repositories in non-alphabetical order
        (tmp_path / "manuscript-zebra").mkdir()
        (tmp_path / "manuscript-apple").mkdir()
        (tmp_path / "manuscript-banana").mkdir()

        repos = repo_manager.discover_repositories(tmp_path)

        names = [r.name for r in repos]
        assert names == ["apple", "banana", "zebra"]

    def test_discover_repositories_nonexistent_dir(self, repo_manager, tmp_path):
        """Test discovering repositories in non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        repos = repo_manager.discover_repositories(nonexistent)
        assert repos == []

    def test_discover_repositories_uses_config_default(self, repo_manager, tmp_path):
        """Test that discover_repositories uses config parent_dir by default."""
        # Create repo in config parent_dir
        (tmp_path / "manuscript-test").mkdir()

        # Call without argument
        repos = repo_manager.discover_repositories()

        assert len(repos) == 1
        assert repos[0].name == "test"

    def test_get_repository_exists(self, repo_manager, tmp_path):
        """Test getting an existing repository."""
        (tmp_path / "manuscript-test").mkdir()

        repo = repo_manager.get_repository("test", tmp_path)

        assert repo is not None
        assert repo.name == "test"
        assert repo.path == tmp_path / "manuscript-test"

    def test_get_repository_not_exists(self, repo_manager, tmp_path):
        """Test getting a non-existent repository."""
        repo = repo_manager.get_repository("nonexistent", tmp_path)
        assert repo is None

    def test_get_repository_uses_config_default(self, repo_manager, tmp_path):
        """Test that get_repository uses config parent_dir by default."""
        (tmp_path / "manuscript-test").mkdir()

        repo = repo_manager.get_repository("test")

        assert repo is not None
        assert repo.name == "test"

    def test_create_repository_basic(self, repo_manager, tmp_path):
        """Test creating a basic repository."""
        repo = repo_manager.create_repository(
            "test",
            parent_dir=tmp_path,
            init_git=False,
            create_manuscript_dir=False,
        )

        assert repo is not None
        assert repo.name == "test"
        assert repo.path.exists()
        assert (tmp_path / "manuscript-test").exists()

    def test_create_repository_with_manuscript_dir(self, repo_manager, tmp_path):
        """Test creating repository with MANUSCRIPT directory."""
        repo = repo_manager.create_repository(
            "test",
            parent_dir=tmp_path,
            init_git=False,
            create_manuscript_dir=True,
        )

        assert repo.manuscript_dir.exists()
        assert (tmp_path / "manuscript-test" / "MANUSCRIPT").exists()

    def test_create_repository_with_git(self, repo_manager, tmp_path):
        """Test creating repository with git initialization."""
        repo = repo_manager.create_repository(
            "test",
            parent_dir=tmp_path,
            init_git=True,
            create_manuscript_dir=True,
        )

        assert repo.is_git_repository()

    def test_create_repository_creates_gitignore(self, repo_manager, tmp_path):
        """Test that repository creation includes .gitignore."""
        repo = repo_manager.create_repository(
            "test",
            parent_dir=tmp_path,
            init_git=False,
            create_manuscript_dir=False,
        )

        gitignore = repo.path / ".gitignore"
        assert gitignore.exists()

    def test_create_repository_creates_readme(self, repo_manager, tmp_path):
        """Test that repository creation includes README.md."""
        repo = repo_manager.create_repository(
            "test",
            parent_dir=tmp_path,
            init_git=False,
            create_manuscript_dir=False,
        )

        readme = repo.path / "README.md"
        assert readme.exists()

    def test_create_repository_already_exists(self, repo_manager, tmp_path):
        """Test error when creating repository that already exists."""
        (tmp_path / "manuscript-test").mkdir()

        with pytest.raises(ValueError, match="already exists"):
            repo_manager.create_repository("test", parent_dir=tmp_path)

    def test_create_repository_uses_config_default(self, repo_manager, tmp_path):
        """Test that create_repository uses config parent_dir by default."""
        repo = repo_manager.create_repository(
            "test",
            init_git=False,
            create_manuscript_dir=False,
        )

        assert repo.path.parent == tmp_path

    def test_create_repository_creates_parent_dir(self, repo_manager, tmp_path):
        """Test that create_repository creates parent directory if needed."""
        nested = tmp_path / "nested" / "path"

        repo = repo_manager.create_repository(
            "test",
            parent_dir=nested,
            init_git=False,
            create_manuscript_dir=False,
        )

        assert nested.exists()
        assert repo.path == nested / "manuscript-test"

    def test_scan_for_manuscript_repositories_depth_0(self, repo_manager, tmp_path):
        """Test scanning at depth 0."""
        # Create repos at root level
        (tmp_path / "manuscript-test1").mkdir()
        (tmp_path / "manuscript-test1" / "MANUSCRIPT").mkdir()

        # Create nested repo (should not be found at depth 0)
        nested = tmp_path / "subdir"
        nested.mkdir()
        (nested / "manuscript-test2").mkdir()
        (nested / "manuscript-test2" / "MANUSCRIPT").mkdir()

        results = repo_manager.scan_for_manuscript_repositories(tmp_path, max_depth=0)

        assert len(results) == 1
        assert str(tmp_path) in results
        assert len(results[str(tmp_path)]) == 1

    def test_scan_for_manuscript_repositories_depth_2(self, repo_manager, tmp_path):
        """Test scanning at depth 2."""
        # Create repos at different depths
        (tmp_path / "manuscript-test1").mkdir()
        (tmp_path / "manuscript-test1" / "MANUSCRIPT").mkdir()

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "manuscript-test2").mkdir()
        (subdir / "manuscript-test2" / "MANUSCRIPT").mkdir()

        deep_subdir = subdir / "deeper"
        deep_subdir.mkdir()
        (deep_subdir / "manuscript-test3").mkdir()
        (deep_subdir / "manuscript-test3" / "MANUSCRIPT").mkdir()

        results = repo_manager.scan_for_manuscript_repositories(tmp_path, max_depth=2)

        # Should find all three locations
        assert len(results) >= 2  # At least root and subdir

    def test_scan_for_manuscript_repositories_requires_manuscript_dir(self, repo_manager, tmp_path):
        """Test that scan only includes repos with MANUSCRIPT directory."""
        # Create repo without MANUSCRIPT directory
        (tmp_path / "manuscript-incomplete").mkdir()

        # Create repo with MANUSCRIPT directory
        (tmp_path / "manuscript-complete").mkdir()
        (tmp_path / "manuscript-complete" / "MANUSCRIPT").mkdir()

        results = repo_manager.scan_for_manuscript_repositories(tmp_path, max_depth=1)

        # Should only find the complete repo
        if str(tmp_path) in results:
            repos = results[str(tmp_path)]
            assert len(repos) == 1
            assert repos[0].name == "complete"

    def test_get_github_orgs_from_repos_no_repos(self):
        """Test extracting orgs from empty list."""
        orgs = RepositoryManager.get_github_orgs_from_repos([])
        assert orgs == []

    def test_get_github_orgs_from_repos_no_remotes(self, tmp_path):
        """Test extracting orgs from repos without remotes."""
        # Create repo without remote
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()
        Repo.init(repo_path)

        repo = ManuscriptRepository(repo_path)

        orgs = RepositoryManager.get_github_orgs_from_repos([repo])
        assert orgs == []

    def test_get_github_orgs_from_repos_https_url(self, tmp_path):
        """Test extracting org from HTTPS GitHub URL."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()
        git_repo = Repo.init(repo_path)

        # Add GitHub remote with HTTPS URL
        git_repo.create_remote("origin", "https://github.com/test-org/manuscript-test")

        repo = ManuscriptRepository(repo_path)

        orgs = RepositoryManager.get_github_orgs_from_repos([repo])
        assert orgs == ["test-org"]

    def test_get_github_orgs_from_repos_ssh_url(self, tmp_path):
        """Test extracting org from SSH GitHub URL."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()
        git_repo = Repo.init(repo_path)

        # Add GitHub remote with SSH URL
        git_repo.create_remote("origin", "git@github.com:test-org/manuscript-test.git")

        repo = ManuscriptRepository(repo_path)

        orgs = RepositoryManager.get_github_orgs_from_repos([repo])
        assert orgs == ["test-org"]

    def test_get_github_orgs_from_repos_multiple_orgs(self, tmp_path):
        """Test extracting multiple unique orgs."""
        repos = []

        # Create repos with different orgs
        for i, org in enumerate(["org1", "org2", "org1"]):  # org1 repeated
            repo_path = tmp_path / f"manuscript-test{i}"
            repo_path.mkdir()
            git_repo = Repo.init(repo_path)
            git_repo.create_remote("origin", f"https://github.com/{org}/repo{i}")
            repos.append(ManuscriptRepository(repo_path))

        orgs = RepositoryManager.get_github_orgs_from_repos(repos)

        # Should have unique, sorted orgs
        assert orgs == ["org1", "org2"]

    def test_get_github_orgs_from_repos_non_github_url(self, tmp_path):
        """Test that non-GitHub URLs are ignored."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()
        git_repo = Repo.init(repo_path)

        # Add non-GitHub remote
        git_repo.create_remote("origin", "https://gitlab.com/test-org/repo")

        repo = ManuscriptRepository(repo_path)

        orgs = RepositoryManager.get_github_orgs_from_repos([repo])
        assert orgs == []

    def test_create_repository_cleanup_on_failure(self, repo_manager, tmp_path):
        """Test that repository is cleaned up if creation fails."""
        # Mock initialize_git to raise an exception after directory is created
        with patch.object(ManuscriptRepository, "initialize_git") as mock_init_git:
            mock_init_git.side_effect = RuntimeError("Git initialization failed")

            # Try to create repo with git init (will fail due to mock)
            with pytest.raises(RuntimeError, match="Failed to create repository"):
                repo_manager.create_repository(
                    "test",
                    parent_dir=tmp_path,
                    init_git=True,
                    create_manuscript_dir=False,
                )

            # Verify that the directory was cleaned up after failure
            assert not (tmp_path / "manuscript-test").exists()
