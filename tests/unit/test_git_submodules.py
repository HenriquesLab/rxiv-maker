"""Tests for checking out git submodules before figure scripts run."""

import shutil
import subprocess
from pathlib import Path

import pytest

from rxiv_maker.utils.git_submodules import ensure_submodules, uninitialized_submodules

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.org")
    git(path, "config", "user.name", "T")
    return path


@pytest.fixture
def allow_file_protocol(monkeypatch):
    # Git refuses file:// submodules by default since 2.38; the code under test
    # inherits the environment, so allow them for these local fixtures only.
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "protocol.file.allow")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "always")


@pytest.fixture
def fresh_clone(tmp_path: Path, allow_file_protocol) -> Path:
    """A clone of a manuscript repo whose data submodule is not checked out."""
    data = init_repo(tmp_path / "data")
    (data / "tools.csv").write_text("tool,count\nimagej,1\n")
    git(data, "add", ".")
    git(data, "commit", "-q", "-m", "data")

    origin = init_repo(tmp_path / "origin")
    (origin / "MANUSCRIPT").mkdir()
    (origin / "MANUSCRIPT" / "00_CONFIG.yml").write_text("title: T\n")
    git(origin, "submodule", "add", "-q", str(data), "scripts")
    git(origin, "add", ".")
    git(origin, "commit", "-q", "-m", "manuscript")

    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    return clone


def test_outside_a_git_repo_is_a_noop(tmp_path: Path):
    assert ensure_submodules(tmp_path) == (True, [], "")


def test_plain_repo_needs_no_checkout(tmp_path: Path):
    repo = init_repo(tmp_path / "repo")
    root, missing = uninitialized_submodules(repo)
    assert root is not None and root.resolve() == repo.resolve()
    assert missing == []


def test_fresh_clone_reports_the_missing_submodule(fresh_clone: Path):
    _, missing = uninitialized_submodules(fresh_clone / "MANUSCRIPT")
    assert missing == ["scripts"]


def test_missing_submodule_is_checked_out(fresh_clone: Path):
    ok, missing, _ = ensure_submodules(fresh_clone / "MANUSCRIPT")

    assert ok
    assert missing == ["scripts"]
    assert (fresh_clone / "scripts" / "tools.csv").is_file()
    assert uninitialized_submodules(fresh_clone)[1] == []


def test_checked_out_submodules_need_nothing(fresh_clone: Path):
    ensure_submodules(fresh_clone)
    assert ensure_submodules(fresh_clone) == (True, [], "")


def test_unreachable_submodule_fails_without_hanging(fresh_clone: Path):
    git(fresh_clone, "config", "submodule.scripts.url", str(fresh_clone.parent / "gone"))

    ok, missing, output = ensure_submodules(fresh_clone)

    assert not ok
    assert missing == ["scripts"]
    assert output
