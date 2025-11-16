"""Manuscript repository management for rxiv-maker.

This module provides classes for managing manuscript repositories with the
naming pattern 'manuscript-{name}', each containing a MANUSCRIPT folder with
the standard rxiv-maker structure.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo
from git.exc import GitError

from .repo_config import get_repo_config

logger = logging.getLogger(__name__)


class ManuscriptRepository:
    """Represents a manuscript repository.

    A manuscript repository follows the pattern 'manuscript-{name}' and
    contains a MANUSCRIPT folder with the standard rxiv-maker structure.
    """

    def __init__(self, path: Path):
        """Initialize manuscript repository.

        Args:
            path: Path to the manuscript repository directory
        """
        self.path = path.resolve()
        self.name = self._extract_name()
        self.manuscript_dir = self.path / "MANUSCRIPT"

        try:
            self.git_repo = Repo(self.path)
        except InvalidGitRepositoryError:
            self.git_repo = None

    def _extract_name(self) -> str:
        """Extract repository name from directory name.

        Returns:
            Repository name (without 'manuscript-' prefix)
        """
        dir_name = self.path.name
        if dir_name.startswith("manuscript-"):
            return dir_name[11:]  # Remove 'manuscript-' prefix
        return dir_name

    def exists(self) -> bool:
        """Check if repository directory exists.

        Returns:
            True if directory exists
        """
        return self.path.exists()

    def has_manuscript_dir(self) -> bool:
        """Check if MANUSCRIPT directory exists.

        Returns:
            True if MANUSCRIPT directory exists
        """
        return self.manuscript_dir.exists() and self.manuscript_dir.is_dir()

    def is_git_repository(self) -> bool:
        """Check if directory is a git repository.

        Returns:
            True if it's a valid git repository
        """
        return self.git_repo is not None

    def get_git_status(self) -> Optional[Dict[str, Any]]:
        """Get git repository status.

        Returns:
            Dictionary with git status information or None if not a git repo
        """
        if not self.is_git_repository():
            return None

        try:
            repo = self.git_repo

            # Get branch name safely (handle edge cases like detached HEAD, corrupted repo)
            try:
                if repo.head.is_detached:
                    branch_name = "detached"
                else:
                    branch_name = repo.active_branch.name
            except (TypeError, AttributeError):
                # Handle edge cases: corrupted repo, missing refs, etc.
                branch_name = "unknown"

            status = {
                "branch": branch_name,
                "is_dirty": repo.is_dirty(),
                "untracked_files": len(repo.untracked_files),
                "has_remote": len(repo.remotes) > 0,
                "remote_url": None,
                "ahead": 0,
                "behind": 0,
            }

            # Get remote URL if available
            if repo.remotes:
                try:
                    origin = repo.remote("origin")
                    status["remote_url"] = list(origin.urls)[0] if origin.urls else None
                except (GitError, ValueError, IndexError) as e:
                    # Remote might not exist or have no URLs
                    logger.debug(f"Could not get remote URL: {e}")

            # Get ahead/behind counts if tracking remote
            try:
                if not repo.head.is_detached and repo.active_branch.tracking_branch():
                    tracking = repo.active_branch.tracking_branch()
                    commits = repo.iter_commits(f"{tracking}..HEAD")
                    status["ahead"] = sum(1 for _ in commits)
                    commits = repo.iter_commits(f"HEAD..{tracking}")
                    status["behind"] = sum(1 for _ in commits)
            except (GitCommandError, GitError, ValueError) as e:
                # Branch might not have tracking branch or commits might not be comparable
                logger.debug(f"Could not get ahead/behind counts: {e}")

            return status

        except (InvalidGitRepositoryError, GitError) as e:
            logger.debug(f"Error getting git status: {e}")
            return None

    def get_last_modified(self) -> Optional[datetime]:
        """Get last modification time of the repository.

        Returns:
            Last modification datetime or None if unavailable
        """
        try:
            if self.is_git_repository() and self.git_repo.head.is_valid():
                # Use last commit time
                return datetime.fromtimestamp(self.git_repo.head.commit.committed_date)
            elif self.path.exists():
                # Use directory modification time
                return datetime.fromtimestamp(self.path.stat().st_mtime)
        except Exception as e:
            logger.debug(f"Error getting last modified time: {e}")

        return None

    def initialize_git(self, initial_commit_message: str = "Initial commit") -> None:
        """Initialize git repository.

        Args:
            initial_commit_message: Message for initial commit

        Raises:
            RuntimeError: If git initialization fails
        """
        if self.is_git_repository():
            logger.warning(f"Repository already initialized: {self.path}")
            return

        try:
            repo = Repo.init(self.path)
            self.git_repo = repo

            # Create initial commit if there are files
            # Be explicit about what we add to avoid accidentally committing sensitive files
            if list(self.path.iterdir()):
                # Ensure .gitignore exists before adding files
                if not (self.path / ".gitignore").exists():
                    self.create_gitignore()

                # Add specific directories/files that are safe to commit
                files_to_add = []
                safe_paths = ["MANUSCRIPT/", ".gitignore", "README.md", "LICENSE"]

                for safe_path in safe_paths:
                    full_path = self.path / safe_path
                    if full_path.exists():
                        files_to_add.append(safe_path)

                if files_to_add:
                    repo.index.add(files_to_add)
                    repo.index.commit(initial_commit_message)
                    logger.info(f"Created initial commit with: {', '.join(files_to_add)}")

            logger.info(f"Initialized git repository: {self.path}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize git repository: {e}") from e

    def create_gitignore(self) -> None:
        """Create a default .gitignore file for manuscript repositories."""
        gitignore_path = self.path / ".gitignore"

        if gitignore_path.exists():
            logger.debug(f".gitignore already exists: {gitignore_path}")
            return

        gitignore_content = """# rxiv-maker output
output/
*.pdf

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# R
.Rproj.user/
.Rhistory
.RData
.Ruserdata

# LaTeX
*.aux
*.log
*.out
*.toc
*.bbl
*.blg
*.fls
*.fdb_latexmk
*.synctex.gz
*.bcf
*.run.xml

# OS
.DS_Store
Thumbs.db
.directory

# Editor
.vscode/
.idea/
*.swp
*.swo
*~

# Cache
.cache/
.rxiv-cache/
"""

        try:
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            logger.info(f"Created .gitignore: {gitignore_path}")
        except Exception as e:
            logger.warning(f"Failed to create .gitignore: {e}")

    def create_readme(self) -> None:
        """Create a default README.md file."""
        readme_path = self.path / "README.md"

        if readme_path.exists():
            logger.debug(f"README.md already exists: {readme_path}")
            return

        readme_content = f"""# {self.name}

Scientific manuscript created with [rxiv-maker](https://github.com/HenriquesLab/rxiv-maker).

## Structure

- `MANUSCRIPT/` - Manuscript content and figures
  - `00_CONFIG.yml` - Manuscript configuration
  - `01_MAIN.md` - Main manuscript content
  - `03_REFERENCES.bib` - Bibliography
  - `FIGURES/` - Figure generation scripts
- `output/` - Generated PDFs

## Usage

Generate the manuscript PDF:

```bash
rxiv pdf MANUSCRIPT/
```

## Requirements

- [rxiv-maker](https://github.com/HenriquesLab/rxiv-maker)
- LaTeX distribution (for local PDF generation)
"""

        try:
            readme_path.write_text(readme_content, encoding="utf-8")
            logger.info(f"Created README.md: {readme_path}")
        except Exception as e:
            logger.warning(f"Failed to create README.md: {e}")

    def __repr__(self) -> str:
        """String representation of the repository."""
        return f"ManuscriptRepository(name='{self.name}', path='{self.path}')"


class RepositoryManager:
    """Manager for discovering and managing manuscript repositories."""

    def __init__(self, config: Optional[Any] = None):
        """Initialize repository manager.

        Args:
            config: RepoConfig instance (uses global if None)
        """
        self.config = config or get_repo_config()

    def discover_repositories(self, parent_dir: Optional[Path] = None) -> List[ManuscriptRepository]:
        """Discover all manuscript repositories in parent directory.

        Args:
            parent_dir: Parent directory to search (uses config if None)

        Returns:
            List of ManuscriptRepository instances
        """
        if parent_dir is None:
            parent_dir = self.config.parent_dir

        if not parent_dir.exists():
            logger.warning(f"Parent directory does not exist: {parent_dir}")
            return []

        repos = []

        try:
            for item in parent_dir.iterdir():
                if item.is_dir() and item.name.startswith("manuscript-"):
                    repo = ManuscriptRepository(item)
                    repos.append(repo)
                    logger.debug(f"Discovered repository: {repo.name}")

        except Exception as e:
            logger.error(f"Error discovering repositories: {e}")

        # Sort by name
        repos.sort(key=lambda r: r.name.lower())

        return repos

    def get_repository(self, name: str, parent_dir: Optional[Path] = None) -> Optional[ManuscriptRepository]:
        """Get a specific repository by name.

        Args:
            name: Repository name (without 'manuscript-' prefix)
            parent_dir: Parent directory (uses config if None)

        Returns:
            ManuscriptRepository instance or None if not found
        """
        if parent_dir is None:
            parent_dir = self.config.parent_dir

        repo_path = parent_dir / f"manuscript-{name}"

        if repo_path.exists():
            return ManuscriptRepository(repo_path)

        return None

    def create_repository(
        self,
        name: str,
        parent_dir: Optional[Path] = None,
        init_git: bool = True,
        create_manuscript_dir: bool = True,
    ) -> ManuscriptRepository:
        """Create a new manuscript repository.

        Args:
            name: Repository name (without 'manuscript-' prefix)
            parent_dir: Parent directory (uses config if None)
            init_git: Whether to initialize as git repository
            create_manuscript_dir: Whether to create MANUSCRIPT directory

        Returns:
            ManuscriptRepository instance

        Raises:
            ValueError: If repository already exists
            RuntimeError: If creation fails
        """
        if parent_dir is None:
            parent_dir = self.config.parent_dir

        # Ensure parent directory exists
        parent_dir.mkdir(parents=True, exist_ok=True)

        repo_path = parent_dir / f"manuscript-{name}"

        if repo_path.exists():
            raise ValueError(f"Repository already exists: {repo_path}")

        try:
            # Create repository directory
            repo_path.mkdir(parents=True)
            logger.info(f"Created repository directory: {repo_path}")

            repo = ManuscriptRepository(repo_path)

            # Create MANUSCRIPT directory if requested
            if create_manuscript_dir:
                repo.manuscript_dir.mkdir(exist_ok=True)
                logger.info(f"Created MANUSCRIPT directory: {repo.manuscript_dir}")

            # Create .gitignore and README
            repo.create_gitignore()
            repo.create_readme()

            # Initialize git if requested
            if init_git:
                repo.initialize_git()

            return repo

        except Exception as e:
            # Clean up on failure
            if repo_path.exists():
                import shutil

                shutil.rmtree(repo_path, ignore_errors=True)

            raise RuntimeError(f"Failed to create repository: {e}") from e

    def scan_for_manuscript_repositories(
        self, search_path: Path, max_depth: int = 3
    ) -> Dict[str, List[ManuscriptRepository]]:
        """Scan for manuscript repositories in a directory tree.

        Args:
            search_path: Root path to search
            max_depth: Maximum directory depth to search

        Returns:
            Dictionary mapping directory paths to lists of repositories found
        """
        repos_by_location: Dict[str, List[ManuscriptRepository]] = {}

        def scan_directory(path: Path, depth: int) -> None:
            if depth > max_depth or not path.exists():
                return

            try:
                found_repos = []

                for item in path.iterdir():
                    if not item.is_dir():
                        continue

                    # Check if this is a manuscript repository
                    if item.name.startswith("manuscript-"):
                        repo = ManuscriptRepository(item)
                        if repo.has_manuscript_dir():
                            found_repos.append(repo)
                            logger.debug(f"Found manuscript repository: {repo.name} at {item}")
                    elif depth < max_depth:
                        # Recurse into subdirectories
                        scan_directory(item, depth + 1)

                if found_repos:
                    repos_by_location[str(path)] = found_repos

            except PermissionError:
                logger.debug(f"Permission denied: {path}")
            except Exception as e:
                logger.debug(f"Error scanning {path}: {e}")

        scan_directory(search_path, 0)

        return repos_by_location

    @staticmethod
    def get_github_orgs_from_repos(repos: List[ManuscriptRepository]) -> List[str]:
        """Extract GitHub organizations from repository remotes.

        Args:
            repos: List of ManuscriptRepository instances

        Returns:
            List of unique organization names
        """
        orgs = set()

        for repo in repos:
            if repo.is_git_repository():
                status = repo.get_git_status()
                if status and status.get("remote_url"):
                    url = status["remote_url"]
                    # Extract org from GitHub URL
                    # Format: https://github.com/org/repo or git@github.com:org/repo
                    if "github.com" in url:
                        if "github.com/" in url:
                            parts = url.split("github.com/")[1].split("/")
                        elif "github.com:" in url:
                            parts = url.split("github.com:")[1].split("/")
                        else:
                            continue

                        if len(parts) >= 2:
                            org = parts[0]
                            orgs.add(org)

        return sorted(orgs)
