"""Tests that the install-deps option reaches the figure generator.

Names avoid the substring "r_" because the shared conftest marks any test whose
name contains it as requiring R, which would silently skip these.
"""

import inspect
from unittest.mock import patch

from rxiv_maker.engines.operations.build_manager import BuildManager
from rxiv_maker.engines.operations.generate_figures import FigureGenerator


def test_build_defaults_to_not_installing():
    signature = inspect.signature(BuildManager.__init__)
    assert signature.parameters["install_deps"].default is False


def test_build_forwards_install_flag_to_generator(tmp_path):
    (tmp_path / "FIGURES").mkdir()

    build = BuildManager(
        manuscript_path=str(tmp_path),
        install_deps=True,
        skip_validation=True,
    )

    captured = {}

    class FakeGenerator:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def process_figures(self):
            return {}

    with patch(
        "rxiv_maker.engines.operations.build_manager.get_figure_generator",
        return_value=FakeGenerator,
    ):
        build.generate_figures()

    assert captured["install_deps"] is True
    assert captured["manuscript_path"] == str(tmp_path)


def test_install_default_off():
    signature = inspect.signature(FigureGenerator.__init__)
    assert signature.parameters["install_deps"].default is False


def test_unset_paths_fall_back_to_figures_parent(tmp_path):
    figures_dir = tmp_path / "FIGURES"
    figures_dir.mkdir()
    generator = FigureGenerator(figures_dir=str(figures_dir), output_dir=str(figures_dir))
    assert generator.manuscript_dir == tmp_path
    assert generator.install_deps is False
