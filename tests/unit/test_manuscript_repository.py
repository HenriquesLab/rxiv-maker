"""Tests for ManuscriptRepository class."""

from git import Repo

from src.rxiv_maker.core.repository import ManuscriptRepository


class TestManuscriptRepository:
    """Test ManuscriptRepository class."""

    def test_init_with_valid_path(self, tmp_path):
        """Test initialization with a valid path."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.path == repo_path.resolve()
        assert repo.name == "test"
        assert repo.manuscript_dir == repo_path / "MANUSCRIPT"

    def test_init_without_manuscript_prefix(self, tmp_path):
        """Test initialization with path not starting with 'manuscript-'."""
        repo_path = tmp_path / "regular-repo"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        # Should extract name without validation
        assert repo.name == "regular-repo"

    def test_manuscript_dir_property(self, tmp_path):
        """Test manuscript_dir property."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.manuscript_dir == repo_path / "MANUSCRIPT"

    def test_exists_true(self, tmp_path):
        """Test exists method when directory exists."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.exists() is True

    def test_exists_false(self, tmp_path):
        """Test exists method when directory is deleted after initialization."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        # Delete the directory after initialization
        import shutil

        shutil.rmtree(repo_path)

        assert repo.exists() is False

    def test_has_manuscript_dir_true(self, tmp_path):
        """Test has_manuscript_dir when directory exists."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()
        (repo_path / "MANUSCRIPT").mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.has_manuscript_dir() is True

    def test_has_manuscript_dir_false(self, tmp_path):
        """Test has_manuscript_dir when directory doesn't exist."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.has_manuscript_dir() is False

    def test_is_git_repository_true(self, tmp_path):
        """Test is_git_repository when repository exists."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Initialize a git repository
        Repo.init(repo_path)

        repo = ManuscriptRepository(repo_path)

        assert repo.is_git_repository() is True
        assert repo.git_repo is not None

    def test_is_git_repository_false(self, tmp_path):
        """Test is_git_repository when repository doesn't exist."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.is_git_repository() is False
        assert repo.git_repo is None

    def test_get_git_status_no_repo(self, tmp_path):
        """Test get_git_status when no git repository exists."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)
        status = repo.get_git_status()

        assert status is None

    def test_get_git_status_with_repo(self, tmp_path):
        """Test get_git_status with a valid git repository."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Initialize a git repository
        git_repo = Repo.init(repo_path)

        # Create a file and commit it
        test_file = repo_path / "test.txt"
        test_file.write_text("test")
        git_repo.index.add(["test.txt"])
        git_repo.index.commit("Initial commit")

        repo = ManuscriptRepository(repo_path)
        status = repo.get_git_status()

        assert status is not None
        assert "branch" in status
        assert "is_dirty" in status
        assert status["is_dirty"] is False

    def test_initialize_git_creates_repository(self, tmp_path):
        """Test that initialize_git creates a git repository."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)
        assert repo.is_git_repository() is False

        repo.initialize_git()

        # Reload to check
        repo2 = ManuscriptRepository(repo_path)
        assert repo2.is_git_repository() is True

    def test_initialize_git_already_initialized(self, tmp_path):
        """Test that initialize_git handles already initialized repository."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Initialize git repository
        Repo.init(repo_path)

        repo = ManuscriptRepository(repo_path)

        # Should not raise an error
        repo.initialize_git()

        assert repo.is_git_repository() is True

    def test_initialize_git_with_files(self, tmp_path):
        """Test that initialize_git creates initial commit with files."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Create MANUSCRIPT directory
        manuscript_dir = repo_path / "MANUSCRIPT"
        manuscript_dir.mkdir()

        # Create .gitignore
        gitignore = repo_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        repo = ManuscriptRepository(repo_path)
        repo.initialize_git()

        # Check that a commit was created with correct files
        repo2 = ManuscriptRepository(repo_path)
        git_repo = repo2.git_repo
        assert git_repo is not None
        commits = list(git_repo.iter_commits())
        assert len(commits) >= 1

    def test_create_gitignore(self, tmp_path):
        """Test create_gitignore method."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)
        repo.create_gitignore()

        gitignore_path = repo_path / ".gitignore"
        assert gitignore_path.exists()

        content = gitignore_path.read_text()
        # Check for some expected patterns
        assert ".cache/" in content or ".rxiv-cache/" in content
        assert "*.aux" in content

    def test_create_gitignore_already_exists(self, tmp_path):
        """Test create_gitignore when .gitignore already exists."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Create existing .gitignore
        gitignore_path = repo_path / ".gitignore"
        original_content = "# Custom gitignore\n"
        gitignore_path.write_text(original_content)

        repo = ManuscriptRepository(repo_path)
        repo.create_gitignore()

        # Should not overwrite
        content = gitignore_path.read_text()
        assert content == original_content

    def test_create_readme(self, tmp_path):
        """Test create_readme method."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)
        repo.create_readme()

        readme_path = repo_path / "README.md"
        assert readme_path.exists()

        content = readme_path.read_text()
        assert "manuscript-test" in content.lower() or "test" in content

    def test_get_last_modified(self, tmp_path):
        """Test get_last_modified method."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Create a test file
        test_file = repo_path / "test.txt"
        test_file.write_text("test")

        repo = ManuscriptRepository(repo_path)
        last_modified = repo.get_last_modified()

        assert last_modified is not None

    def test_safe_git_add_only_adds_safe_files(self, tmp_path):
        """Test that initialize_git only adds safe files."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        # Create MANUSCRIPT directory
        manuscript_dir = repo_path / "MANUSCRIPT"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_MAIN.md").write_text("# Test")

        # Create .gitignore
        gitignore = repo_path / ".gitignore"
        gitignore.write_text("*.pyc\n.env\n")

        # Create a sensitive file that should NOT be committed
        sensitive_file = repo_path / ".env"
        sensitive_file.write_text("SECRET_KEY=abc123")

        repo = ManuscriptRepository(repo_path)
        repo.initialize_git()

        # Check that .env was NOT added to git
        repo2 = ManuscriptRepository(repo_path)
        git_repo = repo2.git_repo
        committed_files = set()
        for commit in git_repo.iter_commits():
            committed_files.update(commit.stats.files.keys())

        # .env should not be committed
        assert ".env" not in committed_files
        # Safe files should be committed
        assert any(".gitignore" in f for f in committed_files) or ".gitignore" in committed_files

    def test_repr(self, tmp_path):
        """Test string representation."""
        repo_path = tmp_path / "manuscript-test"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)
        repr_str = repr(repo)

        assert "ManuscriptRepository" in repr_str
        assert "test" in repr_str


class TestRepositoryNameParsing:
    """Test repository name parsing logic."""

    def test_extract_name_from_path(self, tmp_path):
        """Test extracting repository name from path."""
        repo_path = tmp_path / "manuscript-my-paper"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.name == "my-paper"

    def test_complex_name(self, tmp_path):
        """Test complex repository name with hyphens."""
        repo_path = tmp_path / "manuscript-my-long-paper-name"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        assert repo.name == "my-long-paper-name"

    def test_name_without_prefix(self, tmp_path):
        """Test extracting name when no manuscript- prefix."""
        repo_path = tmp_path / "regular-repo"
        repo_path.mkdir()

        repo = ManuscriptRepository(repo_path)

        # Returns the full directory name when no prefix
        assert repo.name == "regular-repo"
