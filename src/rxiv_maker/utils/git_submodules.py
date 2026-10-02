"""Check out git submodules a manuscript's figure scripts read from.

Manuscript repositories often keep figure data in a submodule. A plain
``git clone`` leaves submodules empty, so figure scripts fail on missing
files. Checking them out before the scripts run lets a fresh clone build.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

SUBMODULE_TIMEOUT_SECONDS = 600


def _git(args: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess | None:
    """Run a git command without prompting, returning None when git is unavailable."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        return subprocess.run(  # nosec # Fixed git subcommands on the user's own repository
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def uninitialized_submodules(path: Path) -> tuple[Path | None, list[str]]:
    """List submodules of the repository holding ``path`` that are not checked out.

    Args:
        path: Any directory inside the repository

    Returns:
        Tuple of (repository root, submodule paths); the root is None when
        ``path`` is outside a git repository
    """
    toplevel = _git(["rev-parse", "--show-toplevel"], cwd=path)
    if toplevel is None or toplevel.returncode != 0:
        return None, []

    root = Path(toplevel.stdout.strip())
    if not (root / ".gitmodules").is_file():
        return root, []

    status = _git(["submodule", "status", "--recursive"], cwd=root)
    if status is None or status.returncode != 0:
        return root, []

    # git prefixes an uninitialised submodule's status line with "-".
    missing = [line[1:].split()[1] for line in status.stdout.splitlines() if line.startswith("-")]
    return root, missing


def ensure_submodules(path: Path) -> tuple[bool, list[str], str]:
    """Check out any submodule of the repository holding ``path`` that is missing.

    Only the commits the repository already pins are checked out. Git runs with
    prompts disabled, so a submodule that needs credentials fails quickly with
    git's message instead of waiting for input.

    Args:
        path: Any directory inside the repository

    Returns:
        Tuple of (succeeded, submodule paths that were missing, git output)
    """
    root, missing = uninitialized_submodules(path)
    if root is None or not missing:
        return True, [], ""

    result = _git(
        ["submodule", "update", "--init", "--recursive"],
        cwd=root,
        timeout=SUBMODULE_TIMEOUT_SECONDS,
    )
    if result is None:
        return False, missing, "git submodule update timed out or git is not installed"
    return result.returncode == 0, missing, (result.stdout + result.stderr).strip()
