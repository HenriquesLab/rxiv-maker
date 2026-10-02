"""Tests for declared figure dependency resolution."""

from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.utils.figure_dependencies import (
    FigureDependencyError,
    check_figure_dependencies,
    config_requirements,
    describe_missing,
    ensure_figure_dependencies,
    find_requirements_file,
    install_command,
    install_requirements,
    parse_requirements,
)


@pytest.fixture
def manuscript_dir(tmp_path: Path) -> Path:
    """Create a manuscript directory holding a FIGURES subdirectory."""
    (tmp_path / "FIGURES").mkdir()
    return tmp_path


def test_no_requirements_file_reports_satisfied(manuscript_dir: Path):
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert status.satisfied
    assert status.requirements_file is None
    assert status.declared == []


def test_declaration_file_found_in_figures_dir(manuscript_dir: Path):
    figures_dir = manuscript_dir / "FIGURES"
    (figures_dir / "requirements.txt").write_text("requests\n")
    assert find_requirements_file(manuscript_dir, figures_dir) == figures_dir / "requirements.txt"


def test_declaration_file_found_in_manuscript_root(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("requests\n")
    expected = manuscript_dir / "requirements.txt"
    assert find_requirements_file(manuscript_dir, manuscript_dir / "FIGURES") == expected


def test_parse_declarations_skips_comments_and_options(manuscript_dir: Path):
    path = manuscript_dir / "requirements.txt"
    path.write_text(
        "# data acquisition\n"
        "requests>=2.31  # inline comment\n"
        "\n"
        "-r base.txt\n"
        "--index-url https://example.invalid/simple\n"
        "pandas\n"
    )
    names = [requirement.name for requirement in parse_requirements(path)]
    assert names == ["requests", "pandas"]


def test_missing_package_is_reported(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("definitely-not-installed-xyzzy>=1.0\n")
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert not status.satisfied
    assert [requirement.name for requirement in status.missing] == ["definitely-not-installed-xyzzy"]


def test_installed_package_satisfies_requirement(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("pytest>=7.0\n")
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert status.satisfied


def test_version_mismatch_is_missing(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("pytest>=99.0\n")
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert not status.satisfied
    assert [requirement.name for requirement in status.missing] == ["pytest"]


def test_config_dependencies_are_read(manuscript_dir: Path):
    (manuscript_dir / "00_CONFIG.yml").write_text(
        "title: Test\nauthors:\n  - name: A\nkeywords: [a, b, c]\ncitation_style: numbered\n"
        "figures:\n  dependencies:\n    - pytest>=7.0\n"
    )
    assert config_requirements(manuscript_dir) == ["pytest>=7.0"]

    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert status.satisfied
    assert len(status.declared) == 1


def test_config_only_declaration_names_the_config_as_source(manuscript_dir: Path):
    (manuscript_dir / "00_CONFIG.yml").write_text(
        "title: Test\nauthors:\n  - name: A\nkeywords: [a, b, c]\ncitation_style: numbered\n"
        "figures:\n  dependencies:\n    - definitely-not-installed-xyzzy\n"
    )
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert status.requirements_file == manuscript_dir / "00_CONFIG.yml"
    assert "00_CONFIG.yml" in describe_missing(status)


def test_config_missing_figures_key_is_empty(manuscript_dir: Path):
    (manuscript_dir / "00_CONFIG.yml").write_text(
        "title: Test\nauthors:\n  - name: A\nkeywords: [a, b, c]\ncitation_style: numbered\n"
    )
    assert config_requirements(manuscript_dir) == []


def test_config_and_requirements_file_are_combined(manuscript_dir: Path):
    (manuscript_dir / "00_CONFIG.yml").write_text(
        "title: Test\nauthors:\n  - name: A\nkeywords: [a, b, c]\ncitation_style: numbered\n"
        "figures:\n  dependencies:\n    - pytest>=7.0\n"
    )
    (manuscript_dir / "FIGURES" / "requirements.txt").write_text("pandas>=2.0\n")
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert [requirement.name for requirement in status.declared] == ["pandas", "pytest"]
    assert status.satisfied


def test_missing_dependency_without_install_raises(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("definitely-not-installed-xyzzy\n")
    with pytest.raises(FigureDependencyError) as excinfo:
        ensure_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    message = str(excinfo.value)
    assert "definitely-not-installed-xyzzy" in message
    assert "--no-install-deps" in message


def test_install_command_uses_active_interpreter(manuscript_dir: Path):
    path = manuscript_dir / "requirements.txt"
    path.write_text("definitely-not-installed-xyzzy>=2.0\n")
    command = install_command(parse_requirements(path))
    assert command[1:4] == ["-m", "pip", "install"]
    assert command[-1] == "definitely-not-installed-xyzzy>=2.0"


def test_auto_install_raises_actionable_error(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("definitely-not-installed-xyzzy\n")
    with patch(
        "rxiv_maker.utils.figure_dependencies.install_requirements",
        return_value=(False, "no network"),
    ):
        with pytest.raises(FigureDependencyError) as excinfo:
            ensure_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES", auto_install=True)
    assert "no network" in str(excinfo.value)


def test_auto_install_succeeds_when_package_becomes_available(manuscript_dir: Path):
    requirements = manuscript_dir / "requirements.txt"
    requirements.write_text("pytest>=7.0\n")

    blocked = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    blocked.missing = parse_requirements(requirements)
    resolved = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")

    with patch(
        "rxiv_maker.utils.figure_dependencies.check_figure_dependencies",
        side_effect=[blocked, resolved],
    ):
        with patch(
            "rxiv_maker.utils.figure_dependencies.install_requirements",
            return_value=(True, "installed"),
        ):
            result = ensure_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES", auto_install=True)

    assert result.satisfied


def test_auto_install_that_leaves_package_missing_raises(manuscript_dir: Path):
    (manuscript_dir / "requirements.txt").write_text("definitely-not-installed-xyzzy\n")
    with patch(
        "rxiv_maker.utils.figure_dependencies.install_requirements",
        return_value=(True, "nothing happened"),
    ):
        with pytest.raises(FigureDependencyError) as excinfo:
            ensure_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES", auto_install=True)
    assert "definitely-not-installed-xyzzy" in str(excinfo.value)


def test_declared_gap_fails_before_figure_caching_can_mask_it(manuscript_dir: Path):
    """A missing declared package must fail even when every figure is cached.

    Figure generation skips unchanged scripts, so a dependency error would
    otherwise never surface on a rebuild that has cached checksums.
    """
    from rxiv_maker.engines.operations.generate_figures import FigureGenerator

    figures_dir = manuscript_dir / "FIGURES"
    (figures_dir / "Figure__cached.py").write_text("print('cached')\n")
    (figures_dir / "requirements.txt").write_text("definitely-not-installed-xyzzy\n")

    generator = FigureGenerator(
        figures_dir=str(figures_dir),
        output_dir=str(figures_dir),
        manuscript_path=str(manuscript_dir),
        install_deps=False,
    )

    # Record checksums so regeneration would be skipped for the unchanged script,
    # and give it an output so the cache-skip branch is satisfied.
    (figures_dir / "Figure__cached.pdf").write_text("placeholder\n")
    assert generator.checksum_manager is not None
    generator.checksum_manager.update_file_checksum("Figure__cached.py")
    generator.checksum_manager._save_checksums()
    assert not generator.checksum_manager.has_file_changed("Figure__cached.py")

    with pytest.raises(FigureDependencyError):
        generator._execute_python_files(use_rich=False)


def test_install_requirements_empty_is_noop():
    assert install_requirements([]) == (True, "")


def test_install_requirements_missing_pip_falls_back_to_uv():
    from packaging.requirements import Requirement

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0].endswith("python") or command[0].endswith("python3"):
            raise FileNotFoundError

        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Result()

    with patch("rxiv_maker.utils.figure_dependencies.subprocess.run", side_effect=fake_run):
        ok, _ = install_requirements([Requirement("pytest")])

    assert ok
    assert calls[1][0] == "uv"


def test_describe_missing_is_empty_when_satisfied(manuscript_dir: Path):
    status = check_figure_dependencies(manuscript_dir, manuscript_dir / "FIGURES")
    assert describe_missing(status) == ""
