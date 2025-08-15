"""Test for style file path resolution in BuildManager."""

from pathlib import Path
from unittest.mock import patch

from rxiv_maker.engine.build_manager import BuildManager


class TestStyleFileResolution:
    """Test style file path resolution for different installation scenarios."""

    def setup_manuscript_dir(self, temp_dir, name):
        """Set up a minimal manuscript directory for testing."""
        manuscript_dir = temp_dir / name
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal required files
        (manuscript_dir / "01_MAIN.md").write_text("# Test Manuscript")
        (manuscript_dir / "00_CONFIG.yml").write_text("title: Test")

        return manuscript_dir

    def test_style_directory_detection_in_development(self, temp_dir):
        """Test that BuildManager correctly detects style directory in development environment."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # In development environment, should find the actual style directory
        assert build_manager.style_dir is not None
        # Should either find a real style directory or use fallback
        assert isinstance(build_manager.style_dir, Path)

    def test_style_directory_fallback_when_not_found(self, temp_dir):
        """Test that BuildManager uses fallback when no style directory is found."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"

        # Mock all style directories as non-existent
        with patch.object(Path, "exists", return_value=False), patch.object(Path, "glob", return_value=[]):
            build_manager = BuildManager(
                manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
            )

            # Should use the first option as fallback
            assert build_manager.style_dir is not None
            assert "rxiv_maker/tex/style" in str(build_manager.style_dir)

    def test_copy_style_files_handles_none_style_dir(self, temp_dir):
        """Test that copy_style_files handles None style_dir gracefully."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # Manually set style_dir to None to test edge case
        build_manager.style_dir = None

        # Should handle None gracefully and return True
        result = build_manager.copy_style_files()
        assert result is True

    def test_copy_style_files_handles_nonexistent_style_dir(self, temp_dir):
        """Test that copy_style_files handles non-existent style_dir gracefully."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # Set style_dir to a non-existent path
        build_manager.style_dir = temp_dir / "nonexistent" / "style"

        # Should handle non-existent directory gracefully and return True
        result = build_manager.copy_style_files()
        assert result is True
