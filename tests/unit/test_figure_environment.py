"""Tests for the per-manuscript figure environment."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from packaging.requirements import Requirement

from rxiv_maker.utils import figure_dependencies as fd
from rxiv_maker.utils.figure_dependencies import (
    BASE_FIGURE_PACKAGES,
    FigureDependencyError,
    ensure_figure_environment,
    environment_requirements,
    figure_env_dir,
)


def names(requirements):
    return [requirement.name for requirement in requirements]


def test_base_packages_join_declared_ones():
    combined = environment_requirements([Requirement("scikit-learn>=1.3")])
    assert names(combined) == ["scikit-learn", *BASE_FIGURE_PACKAGES]


def test_declared_version_replaces_base_entry():
    combined = environment_requirements([Requirement("Matplotlib>=3.9")])
    assert [str(r) for r in combined if r.name.lower() == "matplotlib"] == ["Matplotlib>=3.9"]
    assert len(combined) == len(BASE_FIGURE_PACKAGES)


def test_env_lives_in_manuscript_cache(tmp_path: Path):
    assert figure_env_dir(tmp_path) == tmp_path / ".rxiv_cache" / "figure-env"


class FakeEnv:
    """Stands in for venv creation and package installs."""

    def __init__(self, env_dir: Path):
        self.env_dir = env_dir
        self.installed: set[str] = set()
        self.created = 0
        self.install_calls: list[list[str]] = []

    def create(self, env_dir):
        self.created += 1
        python = fd._env_python(env_dir)
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("")
        self.installed = set()
        return True, ""

    def install(self, python, requirements):
        self.install_calls.append([r.name for r in requirements])
        self.installed.update(r.name for r in requirements)
        return True, "installed"

    def missing(self, python, requirements):
        if not Path(python).exists():
            return None
        return [r for r in requirements if r.name not in self.installed]


@pytest.fixture
def fake(tmp_path: Path):
    env = FakeEnv(figure_env_dir(tmp_path))
    with (
        patch.object(fd, "_create_environment", side_effect=env.create),
        patch.object(fd, "_install_into", side_effect=env.install),
        patch.object(fd, "_missing_in", side_effect=env.missing),
    ):
        yield env


def test_first_build_creates_env_and_installs_everything(tmp_path: Path, fake: FakeEnv):
    python = ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])

    assert python == fd._env_python(figure_env_dir(tmp_path))
    assert fake.created == 1
    assert fake.install_calls == [["scikit-learn", *BASE_FIGURE_PACKAGES]]
    marker = json.loads((figure_env_dir(tmp_path) / fd.FIGURE_ENV_MARKER).read_text())
    assert "fingerprint" in marker


def test_unchanged_env_is_reused_without_installing(tmp_path: Path, fake: FakeEnv):
    ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])
    ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])

    assert fake.created == 1
    assert len(fake.install_calls) == 1


def test_missing_package_is_topped_up_in_place(tmp_path: Path, fake: FakeEnv):
    ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])
    fake.installed.discard("scikit-learn")

    ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])

    assert fake.created == 1
    assert fake.install_calls[-1] == ["scikit-learn"]


def test_changed_declarations_rebuild_the_env(tmp_path: Path, fake: FakeEnv):
    ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])
    ensure_figure_environment(tmp_path, [Requirement("scikit-learn"), Requirement("scipy")])

    assert fake.created == 2
    assert "scipy" in fake.install_calls[-1]


def test_python_upgrade_rebuilds_the_env(tmp_path: Path, fake: FakeEnv):
    ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])
    newer = SimpleNamespace(major=sys.version_info.major, minor=sys.version_info.minor + 1)
    with patch.object(sys, "version_info", newer):
        ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])

    assert fake.created == 2


def test_failed_install_raises_with_package_names(tmp_path: Path, fake: FakeEnv):
    with patch.object(fd, "_install_into", return_value=(False, "No matching distribution")):
        with pytest.raises(FigureDependencyError) as excinfo:
            ensure_figure_environment(tmp_path, [Requirement("not-a-real-package-xyzzy")])

    message = str(excinfo.value)
    assert "not-a-real-package-xyzzy" in message
    assert "No matching distribution" in message


def test_failed_env_creation_raises(tmp_path: Path):
    with patch.object(fd, "_create_environment", return_value=(False, "venv module missing")):
        with pytest.raises(FigureDependencyError) as excinfo:
            ensure_figure_environment(tmp_path, [Requirement("scikit-learn")])
    assert "venv module missing" in str(excinfo.value)


def test_uv_is_used_when_available(tmp_path: Path):
    calls = []
    with (
        patch.object(fd.shutil, "which", return_value="/usr/bin/uv"),
        patch.object(fd, "_run", side_effect=lambda cmd: calls.append(cmd) or (True, "")),
    ):
        fd._create_environment(tmp_path / "env")
        fd._install_into(tmp_path / "env" / "bin" / "python", [Requirement("numpy")])
    assert calls[0][:2] == ["uv", "venv"]
    assert calls[1][:3] == ["uv", "pip", "install"]


def test_venv_and_pip_are_used_without_uv(tmp_path: Path):
    calls = []
    with (
        patch.object(fd.shutil, "which", return_value=None),
        patch.object(fd, "_run", side_effect=lambda cmd: calls.append(cmd) or (True, "")),
    ):
        fd._create_environment(tmp_path / "env")
        fd._install_into(tmp_path / "env" / "bin" / "python", [Requirement("numpy")])
    assert calls[0][1:3] == ["-m", "venv"]
    assert calls[1][1:4] == ["-m", "pip", "install"]


def test_probe_reads_versions_via_subprocess():
    versions = fd._installed_versions(Path(sys.executable), ["packaging", "definitely-absent-xyzzy"])
    assert versions is not None
    assert versions["packaging"]
    assert versions["definitely-absent-xyzzy"] is None


def test_probe_of_absent_python_returns_none(tmp_path: Path):
    assert fd._installed_versions(tmp_path / "nope" / "python", ["numpy"]) is None


# --- generator wiring ---------------------------------------------------


def make_generator(tmp_path: Path, **kwargs):
    from rxiv_maker.engines.operations.generate_figures import FigureGenerator

    figures_dir = tmp_path / "FIGURES"
    figures_dir.mkdir(exist_ok=True)
    return FigureGenerator(
        figures_dir=str(figures_dir),
        output_dir=str(figures_dir),
        manuscript_path=str(tmp_path),
        enable_content_caching=False,
        **kwargs,
    )


def test_undeclared_manuscript_keeps_running_interpreter(tmp_path: Path):
    generator = make_generator(tmp_path)
    with patch("rxiv_maker.engines.operations.generate_figures.ensure_figure_environment") as build:
        python = generator._script_interpreter(use_rich=False)
    assert python == Path(sys.executable)
    build.assert_not_called()


def test_declared_manuscript_uses_its_environment(tmp_path: Path):
    generator = make_generator(tmp_path)
    (tmp_path / "FIGURES" / "requirements.txt").write_text("scikit-learn\n")
    env_python = tmp_path / "env" / "bin" / "python"
    with patch(
        "rxiv_maker.engines.operations.generate_figures.ensure_figure_environment",
        return_value=env_python,
    ) as build:
        assert generator._script_interpreter(use_rich=False) == env_python
        assert generator._script_interpreter(use_rich=False) == env_python
    build.assert_called_once()


def test_install_off_keeps_running_interpreter(tmp_path: Path):
    generator = make_generator(tmp_path, install_deps=False)
    (tmp_path / "FIGURES" / "requirements.txt").write_text("scikit-learn\n")
    with patch("rxiv_maker.engines.operations.generate_figures.ensure_figure_environment") as build:
        assert generator._script_interpreter(use_rich=False) == Path(sys.executable)
    build.assert_not_called()


def test_scripts_run_with_the_environment_python(tmp_path: Path):
    generator = make_generator(tmp_path)
    (tmp_path / "FIGURES" / "requirements.txt").write_text("scikit-learn\n")
    (tmp_path / "FIGURES" / "Figure__a.py").write_text("print('a')\n")
    env_python = tmp_path / "env" / "bin" / "python"

    class Done:
        returncode = 0
        stdout = ""
        stderr = ""

    with (
        patch(
            "rxiv_maker.engines.operations.generate_figures.ensure_figure_environment",
            return_value=env_python,
        ),
        patch("rxiv_maker.engines.operations.generate_figures.subprocess.run", return_value=Done()) as run,
    ):
        generator._execute_python_files(use_rich=False)

    assert run.call_args.args[0][0] == str(env_python)


def test_cached_rebuild_builds_no_environment(tmp_path: Path):
    from rxiv_maker.engines.operations.generate_figures import FigureGenerator

    figures_dir = tmp_path / "FIGURES"
    figures_dir.mkdir()
    (figures_dir / "requirements.txt").write_text("scikit-learn\n")
    (figures_dir / "Figure__cached.py").write_text("print('cached')\n")
    (figures_dir / "Figure__cached.pdf").write_text("placeholder\n")

    generator = FigureGenerator(
        figures_dir=str(figures_dir), output_dir=str(figures_dir), manuscript_path=str(tmp_path)
    )
    generator.checksum_manager.update_file_checksum("Figure__cached.py")
    generator.checksum_manager._save_checksums()

    with patch("rxiv_maker.engines.operations.generate_figures.ensure_figure_environment") as build:
        generator._execute_python_files(use_rich=False)
    build.assert_not_called()
