"""GitHub integration utilities for rxiv-maker repository management.

This module provides GitHub CLI (gh) integration for creating, cloning,
and managing manuscript repositories on GitHub.
"""

import json
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Exception for GitHub operation errors."""

    pass


def validate_github_name(name: str, name_type: str = "name") -> None:
    """Validate GitHub organization or repository name.

    GitHub names (orgs and repos) can only contain alphanumeric characters
    and hyphens, cannot start or end with a hyphen, and cannot contain
    consecutive hyphens.

    Args:
        name: The name to validate
        name_type: Type of name for error messages ("organization" or "repository")

    Raises:
        ValueError: If name is invalid
    """
    if not name:
        raise ValueError(f"GitHub {name_type} name cannot be empty")

    # Check length (GitHub limits: 1-39 characters)
    if len(name) > 39:
        raise ValueError(f"GitHub {name_type} name cannot exceed 39 characters")

    # Check valid characters (alphanumeric and hyphens only)
    if not re.match(r"^[a-zA-Z0-9-]+$", name):
        raise ValueError(f"GitHub {name_type} name can only contain alphanumeric characters and hyphens")

    # Check doesn't start or end with hyphen
    if name.startswith("-") or name.endswith("-"):
        raise ValueError(f"GitHub {name_type} name cannot start or end with a hyphen")

    # Check no consecutive hyphens
    if "--" in name:
        raise ValueError(f"GitHub {name_type} name cannot contain consecutive hyphens")

    # Check no path separators, null bytes, or other dangerous characters
    if "\x00" in name or ".." in name or any(char in name for char in ["/", "\\", ".", " "]):
        raise ValueError(f"GitHub {name_type} name cannot contain path separators or special characters")


def check_gh_cli_installed() -> bool:
    """Check if GitHub CLI (gh) is installed.

    Returns:
        True if gh CLI is available in PATH
    """
    return shutil.which("gh") is not None


def check_gh_auth() -> bool:
    """Check if user is authenticated with GitHub CLI.

    Returns:
        True if authenticated
    """
    if not check_gh_cli_installed():
        return False

    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False


def check_git_installed() -> bool:
    """Check if git is installed.

    Returns:
        True if git is available in PATH
    """
    return shutil.which("git") is not None


def check_github_repo_exists(org: str, repo_name: str) -> bool:
    """Check if a GitHub repository exists.

    Args:
        org: GitHub organization or username
        repo_name: Repository name

    Returns:
        True if repository exists

    Raises:
        GitHubError: If gh CLI is not available or not authenticated
        ValueError: If org or repo_name are invalid
    """
    # Validate inputs
    validate_github_name(org, "organization")
    validate_github_name(repo_name, "repository")

    if not check_gh_cli_installed():
        raise GitHubError("GitHub CLI (gh) is not installed")

    if not check_gh_auth():
        raise GitHubError("Not authenticated with GitHub CLI. Run: gh auth login")

    try:
        result = subprocess.run(
            ["gh", "repo", "view", f"{org}/{repo_name}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        raise GitHubError("GitHub operation timed out") from None
    except subprocess.SubprocessError as e:
        raise GitHubError(f"GitHub operation failed: {e}") from e


def create_github_repo(org: str, repo_name: str, visibility: str = "public") -> str:
    """Create a new GitHub repository.

    Args:
        org: GitHub organization or username
        repo_name: Repository name
        visibility: 'public' or 'private'

    Returns:
        Repository URL

    Raises:
        GitHubError: If creation fails
        ValueError: If org, repo_name, or visibility are invalid
    """
    # Validate inputs
    validate_github_name(org, "organization")
    validate_github_name(repo_name, "repository")

    if not check_gh_cli_installed():
        raise GitHubError("GitHub CLI (gh) is not installed")

    if not check_gh_auth():
        raise GitHubError("Not authenticated with GitHub CLI. Run: gh auth login")

    if visibility not in ("public", "private"):
        raise ValueError(f"Invalid visibility: {visibility}. Must be 'public' or 'private'")

    try:
        # Create repository under organization or user account
        cmd = [
            "gh",
            "repo",
            "create",
            f"{org}/{repo_name}",
            f"--{visibility}",
            "--confirm",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            # Check for rate limiting
            if "rate limit" in error_msg.lower() or "api rate limit exceeded" in error_msg.lower():
                raise GitHubError(
                    "GitHub API rate limit exceeded. Please wait a few minutes and try again, "
                    "or check your rate limit status with: gh api rate_limit"
                )
            raise GitHubError(f"Failed to create repository: {error_msg}")

        # Get URL via GitHub API for reliability (more robust than parsing text output)
        try:
            api_result = subprocess.run(
                ["gh", "api", f"repos/{org}/{repo_name}", "--jq", ".html_url"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if api_result.returncode == 0 and api_result.stdout.strip():
                return api_result.stdout.strip()

        except subprocess.SubprocessError as e:
            logger.warning(f"Could not retrieve URL via API: {e}")

        # Fallback: construct URL (only if API call fails)
        logger.info("Using constructed URL as API retrieval failed")
        return f"https://github.com/{org}/{repo_name}"

    except subprocess.TimeoutExpired:
        raise GitHubError("GitHub operation timed out") from None
    except subprocess.SubprocessError as e:
        raise GitHubError(f"GitHub operation failed: {e}") from e


def clone_github_repo(org: str, repo_name: str, target_path: Path) -> None:
    """Clone a GitHub repository.

    Args:
        org: GitHub organization or username
        repo_name: Repository name
        target_path: Target directory path

    Raises:
        GitHubError: If cloning fails
        ValueError: If org or repo_name are invalid
    """
    # Validate inputs
    validate_github_name(org, "organization")
    validate_github_name(repo_name, "repository")

    if not check_gh_cli_installed():
        raise GitHubError("GitHub CLI (gh) is not installed")

    if not check_gh_auth():
        raise GitHubError("Not authenticated with GitHub CLI. Run: gh auth login")

    if target_path.exists():
        raise GitHubError(f"Target path already exists: {target_path}")

    try:
        result = subprocess.run(
            ["gh", "repo", "clone", f"{org}/{repo_name}", str(target_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            # Check for rate limiting
            if "rate limit" in error_msg.lower():
                raise GitHubError("GitHub API rate limit exceeded. Please wait and try again later.")
            raise GitHubError(f"Failed to clone repository: {error_msg}")

        logger.info(f"Cloned {org}/{repo_name} to {target_path}")

    except subprocess.TimeoutExpired:
        raise GitHubError("GitHub operation timed out") from None
    except subprocess.SubprocessError as e:
        raise GitHubError(f"GitHub operation failed: {e}") from e


def list_github_repos(org: str, pattern: str = "manuscript-") -> List[Dict[str, str]]:
    """List GitHub repositories matching a pattern.

    Args:
        org: GitHub organization or username
        pattern: Repository name pattern to match

    Returns:
        List of repository dictionaries with 'name' and 'url' keys

    Raises:
        GitHubError: If listing fails
        ValueError: If org is invalid
    """
    # Validate inputs
    validate_github_name(org, "organization")

    if not check_gh_cli_installed():
        raise GitHubError("GitHub CLI (gh) is not installed")

    if not check_gh_auth():
        raise GitHubError("Not authenticated with GitHub CLI. Run: gh auth login")

    try:
        result = subprocess.run(
            ["gh", "repo", "list", org, "--json", "name,url", "--limit", "1000"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            # Check for rate limiting
            if "rate limit" in error_msg.lower():
                raise GitHubError("GitHub API rate limit exceeded. Please wait and try again later.")
            raise GitHubError(f"Failed to list repositories: {error_msg}")

        # Parse JSON output
        repos = json.loads(result.stdout)

        # Filter by pattern
        matching_repos = [repo for repo in repos if repo["name"].startswith(pattern)]

        return matching_repos

    except subprocess.TimeoutExpired:
        raise GitHubError("GitHub operation timed out") from None
    except subprocess.SubprocessError as e:
        raise GitHubError(f"GitHub operation failed: {e}") from e
    except json.JSONDecodeError as e:
        raise GitHubError(f"Failed to parse GitHub response: {e}") from e


def setup_git_remote(repo_path: Path, remote_url: str, remote_name: str = "origin") -> None:
    """Add a git remote to a repository.

    Args:
        repo_path: Path to git repository
        remote_url: Remote repository URL
        remote_name: Name for the remote (default: origin)

    Raises:
        GitHubError: If adding remote fails
    """
    if not check_git_installed():
        raise GitHubError("git is not installed")

    try:
        # Check if remote already exists
        result = subprocess.run(
            ["git", "remote", "get-url", remote_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode == 0:
            # Remote exists, update it
            subprocess.run(
                ["git", "remote", "set-url", remote_name, remote_url],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
        else:
            # Remote doesn't exist, add it
            subprocess.run(
                ["git", "remote", "add", remote_name, remote_url],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )

        logger.info(f"Set up remote '{remote_name}' -> {remote_url}")

    except subprocess.TimeoutExpired:
        raise GitHubError("Git operation timed out") from None
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise GitHubError(f"Failed to setup git remote: {error_msg}") from e


def push_to_remote(repo_path: Path, branch: str = "main", remote_name: str = "origin") -> None:
    """Push commits to remote repository.

    Args:
        repo_path: Path to git repository
        branch: Branch name to push
        remote_name: Remote name

    Raises:
        GitHubError: If push fails
    """
    if not check_git_installed():
        raise GitHubError("git is not installed")

    try:
        result = subprocess.run(
            ["git", "push", "-u", remote_name, branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            # Check for rate limiting
            if "rate limit" in error_msg.lower():
                raise GitHubError("GitHub API rate limit exceeded. Please wait and try again later.")
            raise GitHubError(f"Failed to push to remote: {error_msg}")

        logger.info(f"Pushed to {remote_name}/{branch}")

    except subprocess.TimeoutExpired:
        raise GitHubError("Git operation timed out") from None
    except subprocess.SubprocessError as e:
        raise GitHubError(f"Git operation failed: {e}") from e


def get_github_orgs() -> List[str]:
    """Get list of GitHub organizations the user has access to.

    Returns:
        List of organization names

    Raises:
        GitHubError: If retrieval fails
    """
    if not check_gh_cli_installed():
        raise GitHubError("GitHub CLI (gh) is not installed")

    if not check_gh_auth():
        raise GitHubError("Not authenticated with GitHub CLI. Run: gh auth login")

    try:
        # Get user's organizations
        result = subprocess.run(
            ["gh", "api", "user/orgs", "--jq", ".[].login"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            # Check for rate limiting
            error_msg = result.stderr.strip() if hasattr(result, "stderr") else ""
            if error_msg and "rate limit" in error_msg.lower():
                raise GitHubError("GitHub API rate limit exceeded. Please wait and try again later.")
            # If API call fails, return empty list (user might not be in any orgs)
            return []

        orgs = [line.strip() for line in result.stdout.split("\n") if line.strip()]

        # Also get current username
        user_result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if user_result.returncode == 0:
            username = user_result.stdout.strip()
            if username:
                orgs.insert(0, username)  # Put user's personal account first

        return orgs

    except subprocess.TimeoutExpired:
        raise GitHubError("GitHub operation timed out") from None
    except subprocess.SubprocessError as e:
        raise GitHubError(f"GitHub operation failed: {e}") from e
