"""Tests for PathManager class."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.core.path_manager import PathManager, PathResolutionError


class TestPathManager:
    """Test PathManager functionality."""

    def test_initialization_with_manuscript_path(self, tmp_path):
        """Test PathManager initialization with explicit manuscript path."""
        manuscript_dir = tmp_path / "test_manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        assert pm.manuscript_path == manuscript_dir.resolve()

    def test_initialization_with_environment_variable(self, tmp_path):
        """Test PathManager initialization using environment variable."""
        manuscript_dir = tmp_path / "env_manuscript"
        manuscript_dir.mkdir()

        with patch.dict(os.environ, {"MANUSCRIPT_PATH": str(manuscript_dir)}):
            pm = PathManager()
            assert pm.manuscript_path == manuscript_dir.resolve()

    def test_initialization_with_default(self, tmp_path):
        """Test PathManager initialization with default manuscript path."""
        # Create MANUSCRIPT directory in working dir
        working_dir = tmp_path / "working"
        working_dir.mkdir()
        manuscript_dir = working_dir / "MANUSCRIPT"
        manuscript_dir.mkdir()

        with patch.dict(os.environ, {}, clear=True):
            pm = PathManager(working_dir=working_dir)
            assert pm.manuscript_path == manuscript_dir.resolve()

    def test_manuscript_path_nonexistent_raises_error(self, tmp_path):
        """Test that nonexistent manuscript path raises error."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(PathResolutionError, match="Manuscript directory not found"):
            pm = PathManager(manuscript_path=str(nonexistent))
            # Access the property to trigger validation
            _ = pm.manuscript_path

    def test_manuscript_path_file_raises_error(self, tmp_path):
        """Test that file instead of directory raises error."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(PathResolutionError, match="not a directory"):
            pm = PathManager(manuscript_path=str(file_path))
            # Access the property to trigger validation
            _ = pm.manuscript_path


class TestManuscriptNameHandling:
    """Test manuscript name resolution with trailing slash handling."""

    def test_manuscript_name_no_trailing_slash(self, tmp_path):
        """Test manuscript name without trailing slash."""
        manuscript_dir = tmp_path / "test_manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        assert pm.manuscript_name == "test_manuscript"

    def test_manuscript_name_with_trailing_slash(self, tmp_path):
        """Test manuscript name with trailing slash (Issue #100)."""
        manuscript_dir = tmp_path / "CCT8_paper"
        manuscript_dir.mkdir()

        # Test with single trailing slash
        pm = PathManager(manuscript_path=str(manuscript_dir) + "/")
        assert pm.manuscript_name == "CCT8_paper"

        # Test with double trailing slash
        pm2 = PathManager(manuscript_path=str(manuscript_dir) + "//")
        assert pm2.manuscript_name == "CCT8_paper"

    def test_manuscript_name_edge_cases(self, tmp_path):
        """Test manuscript name edge cases."""
        # Test with empty name (should default to MANUSCRIPT)
        root_dir = tmp_path / "empty"
        root_dir.mkdir()

        # Create a manuscript at root level that might resolve to empty name
        with patch("os.path.basename", return_value=""):
            pm = PathManager(manuscript_path=str(root_dir))
            # Should fall back to MANUSCRIPT for invalid names
            assert pm.manuscript_name == "MANUSCRIPT"

    def test_guillaume_exact_case(self, tmp_path):
        """Test Guillaume's exact case: 'rxiv pdf CCT8_paper/'."""
        manuscript_dir = tmp_path / "CCT8_paper"
        manuscript_dir.mkdir()

        # Exact case with trailing slash
        pm = PathManager(manuscript_path=str(manuscript_dir) + "/")
        assert pm.manuscript_name == "CCT8_paper"
        assert pm.get_manuscript_tex_path().name == "CCT8_paper.tex"
        assert pm.get_manuscript_pdf_path().name == "CCT8_paper.pdf"


class TestOutputDirectoryHandling:
    """Test output directory resolution."""

    def test_output_dir_relative_to_manuscript(self, tmp_path):
        """Test output directory relative to manuscript."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), output_dir="output")
        expected_output = manuscript_dir / "output"
        assert pm.output_dir == expected_output.resolve()

    def test_output_dir_absolute(self, tmp_path):
        """Test absolute output directory."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()
        output_dir = tmp_path / "absolute_output"

        pm = PathManager(manuscript_path=str(manuscript_dir), output_dir=str(output_dir))
        assert pm.output_dir == output_dir.resolve()

    def test_output_dir_default(self, tmp_path):
        """Test default output directory."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        expected_output = manuscript_dir / "output"
        assert pm.output_dir == expected_output.resolve()


class TestStandardPaths:
    """Test standard path properties."""

    def test_figures_dir(self, tmp_path):
        """Test figures directory path."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        expected_figures = manuscript_dir / "FIGURES"
        assert pm.figures_dir == expected_figures.resolve()

    def test_references_bib(self, tmp_path):
        """Test references bibliography file path."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        expected_bib = manuscript_dir / "03_REFERENCES.bib"
        assert pm.references_bib == expected_bib.resolve()

    def test_main_md(self, tmp_path):
        """Test main markdown file path."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        expected_main = manuscript_dir / "01_MAIN.md"
        assert pm.main_md == expected_main.resolve()


class TestStyleDirectoryResolution:
    """Test style directory resolution logic."""

    def test_style_dir_resolution_success(self, tmp_path):
        """Test successful style directory resolution."""
        # Create a mock style directory
        style_dir = tmp_path / "style"
        style_dir.mkdir()
        (style_dir / "test.cls").write_text("mock cls file")

        with patch("pathlib.Path.resolve") as mock_resolve:
            # Mock the resolve chain to return our test directory
            mock_resolve.return_value = style_dir.parent.parent

            with patch.object(PathManager, "_resolve_style_dir") as mock_style:
                mock_style.return_value = style_dir

                manuscript_dir = tmp_path / "manuscript"
                manuscript_dir.mkdir()
                pm = PathManager(manuscript_path=str(manuscript_dir))

                assert pm.style_dir == style_dir

    def test_style_dir_resolution_failure(self, tmp_path):
        """Test style directory resolution failure."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        with patch.object(PathManager, "_resolve_style_dir") as mock_style:
            mock_style.side_effect = PathResolutionError("No style directory found")

            pm = PathManager(manuscript_path=str(manuscript_dir))

            with pytest.raises(PathResolutionError, match="No style directory found"):
                _ = pm.style_dir


class TestDockerPathTranslation:
    """Test Docker container path translation."""

    def test_to_container_path_within_workspace(self, tmp_path):
        """Test host to container path translation within workspace."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        # Path within workspace
        test_file = tmp_path / "subfolder" / "file.txt"
        container_path = pm.to_container_path(test_file)

        assert container_path == "/workspace/subfolder/file.txt"

    def test_to_container_path_outside_workspace(self, tmp_path):
        """Test host to container path translation outside workspace."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        # Path outside workspace
        outside_path = Path("/some/other/path")
        container_path = pm.to_container_path(outside_path)

        assert container_path == "/some/other/path"

    def test_to_host_path_within_workspace(self, tmp_path):
        """Test container to host path translation within workspace."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        container_path = "/workspace/subfolder/file.txt"
        host_path = pm.to_host_path(container_path)

        expected = tmp_path / "subfolder" / "file.txt"
        assert host_path == expected

    def test_to_host_path_outside_workspace(self, tmp_path):
        """Test container to host path translation outside workspace."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        container_path = "/some/other/path"
        host_path = pm.to_host_path(container_path)

        assert host_path == Path("/some/other/path")

    def test_get_docker_volume_mounts(self, tmp_path):
        """Test Docker volume mount specifications."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)
        mounts = pm.get_docker_volume_mounts()

        expected = [f"{tmp_path}:/workspace"]
        assert mounts == expected


class TestPathNormalization:
    """Test path normalization functionality."""

    def test_normalize_path_absolute(self, tmp_path):
        """Test normalization of absolute paths."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        test_path = tmp_path / "test.txt"
        normalized = pm.normalize_path(test_path)

        assert normalized == test_path.resolve()

    def test_normalize_path_relative(self, tmp_path):
        """Test normalization of relative paths."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        normalized = pm.normalize_path("relative/path")
        expected = (tmp_path / "relative" / "path").resolve()

        assert normalized == expected

    def test_normalize_path_trailing_slash(self, tmp_path):
        """Test normalization with trailing slashes."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        # Test string with trailing slash
        normalized = pm.normalize_path("test/path/")
        expected = (tmp_path / "test" / "path").resolve()

        assert normalized == expected


class TestUtilityMethods:
    """Test utility methods."""

    def test_ensure_dir_exists(self, tmp_path):
        """Test directory creation."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        new_dir = tmp_path / "new" / "nested" / "dir"
        result = pm.ensure_dir_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir.resolve()

    def test_get_output_file_path(self, tmp_path):
        """Test output file path generation."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))

        file_path = pm.get_output_file_path("test.txt")
        expected = pm.output_dir / "test.txt"

        assert file_path == expected

    def test_clear_cache(self, tmp_path):
        """Test cache clearing."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))

        # Access properties to populate cache
        _ = pm.manuscript_path
        _ = pm.manuscript_name
        _ = pm.output_dir

        # Clear cache
        pm.clear_cache()

        # Verify cache is cleared (internal state)
        assert pm._manuscript_path_cache is None
        assert pm._manuscript_name_cache is None
        assert pm._output_dir_cache is None

    def test_repr(self, tmp_path):
        """Test string representation."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir))
        repr_str = repr(pm)

        assert "PathManager" in repr_str
        assert str(manuscript_dir.resolve()) in repr_str
        assert "manuscript" in repr_str

    def test_repr_unresolved(self, tmp_path):
        """Test string representation with unresolved paths."""
        nonexistent = tmp_path / "nonexistent"

        pm = PathManager(manuscript_path=str(nonexistent))
        repr_str = repr(pm)

        assert "PathManager" in repr_str
        assert "unresolved" in repr_str


class TestCrossPlatformCompatibility:
    """Test cross-platform path handling."""

    @pytest.mark.parametrize(
        "path_with_slash",
        [
            "manuscript/",
            "manuscript//",
            "manuscript///",
        ],
    )
    def test_trailing_slash_variations(self, tmp_path, path_with_slash):
        """Test various trailing slash patterns."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        test_path = str(manuscript_dir) + path_with_slash[len("manuscript") :]
        pm = PathManager(manuscript_path=test_path)

        assert pm.manuscript_name == "manuscript"

    def test_windows_path_separators(self, tmp_path):
        """Test handling of Windows path separators."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        pm = PathManager(manuscript_path=str(manuscript_dir), working_dir=tmp_path)

        # Test container path conversion handles backslashes
        test_file = tmp_path / "folder" / "file.txt"
        container_path = pm.to_container_path(test_file)

        # Should use forward slashes in container
        assert "/" in container_path
        assert "\\" not in container_path
