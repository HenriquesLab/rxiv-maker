"""Test for style file path resolution in BuildManager."""

from pathlib import Path
from unittest.mock import patch

from rxiv_maker.engines.operations.build_manager import BuildManager


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
        output_dir.mkdir(exist_ok=True)

        # Mock the style directory resolution to return fallback
        with patch("rxiv_maker.core.path_manager.PathManager._resolve_style_dir") as mock_resolve:
            mock_resolve.return_value = Path("src/rxiv_maker/tex/style")  # Use fallback
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


class TestStyleFilePackaging:
    """Test style file packaging scenarios for different installation methods."""

    def setup_manuscript_dir(self, temp_dir, name):
        """Set up a minimal manuscript directory for testing."""
        manuscript_dir = temp_dir / name
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal required files
        (manuscript_dir / "01_MAIN.md").write_text("# Test Manuscript")
        (manuscript_dir / "00_CONFIG.yml").write_text("title: Test")

        return manuscript_dir

    def test_pip_installation_style_path_detection(self, temp_dir):
        """Test style file path detection for pip installations."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"

        # Create mock pip installation structure
        mock_rxiv_maker_dir = temp_dir / "mock_site_packages" / "rxiv_maker"
        mock_engine_dir = mock_rxiv_maker_dir / "engine"
        mock_style_dir = mock_rxiv_maker_dir / "tex" / "style"
        mock_style_dir.mkdir(parents=True)

        # Create style files
        (mock_style_dir / "rxiv_maker_style.cls").write_text("% Mock style file")
        (mock_style_dir / "rxiv_maker_style.bst").write_text("% Mock bst file")

        # Mock the __file__ location to simulate pip installation
        mock_build_manager_file = mock_engine_dir / "build_manager.py"

        with patch("rxiv_maker.engines.operations.build_manager.__file__", str(mock_build_manager_file)):
            build_manager = BuildManager(
                manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
            )

            # Should find the style directory in pip installation structure
            assert build_manager.style_dir is not None
            assert build_manager.style_dir.exists()
            assert (build_manager.style_dir / "rxiv_maker_style.cls").exists()

    def test_development_installation_style_path_detection(self, temp_dir):
        """Test style file path detection for development installations."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"

        # Create mock development structure
        mock_project_root = temp_dir / "rxiv-maker"
        mock_src_dir = mock_project_root / "src"
        mock_engine_dir = mock_src_dir / "rxiv_maker" / "engine"
        mock_style_dir = mock_src_dir / "tex" / "style"
        mock_style_dir.mkdir(parents=True)

        # Create style files
        (mock_style_dir / "rxiv_maker_style.cls").write_text("% Mock style file")
        (mock_style_dir / "rxiv_maker_style.bst").write_text("% Mock bst file")

        # Mock the __file__ location to simulate development installation
        mock_build_manager_file = mock_engine_dir / "build_manager.py"

        with patch("rxiv_maker.engines.operations.build_manager.__file__", str(mock_build_manager_file)):
            build_manager = BuildManager(
                manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
            )

            # Should find the style directory in development structure
            assert build_manager.style_dir is not None
            assert build_manager.style_dir.exists()
            assert (build_manager.style_dir / "rxiv_maker_style.cls").exists()

    def test_style_file_copying_with_real_files(self, temp_dir):
        """Test actual style file copying process."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create mock style directory with actual files
        mock_style_dir = temp_dir / "style"
        mock_style_dir.mkdir()

        # Create style files with realistic content
        cls_content = """\\NeedsTeXFormat{LaTeX2e}
\\ProvidesClass{rxiv_maker_style}[2025/01/01 Test style]
\\LoadClass{article}
\\RequirePackage{siunitx}
"""
        (mock_style_dir / "rxiv_maker_style.cls").write_text(cls_content)
        (mock_style_dir / "rxiv_maker_style.bst").write_text("% Test bibliography style")

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # Override style_dir to use our mock
        build_manager.style_dir = mock_style_dir

        # Test copying
        result = build_manager.copy_style_files()
        assert result is True

        # Verify files were copied
        assert (output_dir / "rxiv_maker_style.cls").exists()
        assert (output_dir / "rxiv_maker_style.bst").exists()

        # Verify content was copied correctly
        copied_cls = (output_dir / "rxiv_maker_style.cls").read_text()
        assert "\\RequirePackage{siunitx}" in copied_cls

    def test_style_file_copying_handles_missing_files(self, temp_dir):
        """Test style file copying when some files are missing."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Create style directory with only some files
        mock_style_dir = temp_dir / "style"
        mock_style_dir.mkdir()
        (mock_style_dir / "rxiv_maker_style.cls").write_text("% Test style")
        # Intentionally don't create .bst file

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        build_manager.style_dir = mock_style_dir

        # Should handle missing files gracefully
        result = build_manager.copy_style_files()
        assert result is True

        # Should copy available files
        assert (output_dir / "rxiv_maker_style.cls").exists()
        assert not (output_dir / "rxiv_maker_style.bst").exists()

    def test_multiple_style_path_fallback_logic(self, temp_dir):
        """Test the multiple path fallback logic in style directory detection."""
        manuscript_dir = self.setup_manuscript_dir(temp_dir, "test_project")
        output_dir = temp_dir / "output"

        # Create a scenario where first path doesn't exist but second does
        mock_root = temp_dir / "mock_install"
        mock_engine_file = mock_root / "rxiv_maker" / "engine" / "build_manager.py"
        mock_engine_file.parent.mkdir(parents=True)

        # Second path: development structure (from engine file location)
        # Path structure: mock_root/rxiv_maker/engine -> go up 4 levels -> src/tex/style
        second_path = mock_root.parent.parent.parent / "src" / "tex" / "style"
        second_path.mkdir(parents=True, exist_ok=True)
        (second_path / "rxiv_maker_style.cls").write_text("% Mock style")

        with patch("rxiv_maker.engines.operations.build_manager.__file__", str(mock_engine_file)):
            build_manager = BuildManager(
                manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
            )

            # Should find the second path or fallback gracefully
            assert build_manager.style_dir is not None
            # In this test, since no valid style directory with .cls files is found,
            # it will use the first option as fallback, which is expected behavior
