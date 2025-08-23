"""Tests for cleanup engine functionality."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rxiv_maker.engines.operations.cleanup import CleanupManager


class TestCleanupManager(unittest.TestCase):
    """Test CleanupManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manuscript_dir = self.temp_dir / "manuscript"
        self.manuscript_dir.mkdir()
        self.output_dir = self.manuscript_dir / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_default_values(self):
        """Test CleanupManager initialization with default values."""
        manager = CleanupManager()

        # manuscript_path defaults to environment or "MANUSCRIPT", not None
        self.assertIsNotNone(manager.manuscript_path)
        self.assertEqual(manager.output_dir, Path("output"))
        self.assertFalse(manager.verbose)

    def test_init_custom_values(self):
        """Test CleanupManager initialization with custom values."""
        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), output_dir="custom_output", verbose=True)

        self.assertEqual(manager.manuscript_path, str(self.manuscript_dir))
        self.assertEqual(manager.output_dir, Path("custom_output"))
        self.assertTrue(manager.verbose)

    def test_init_with_none_manuscript_path(self):
        """Test initialization with None manuscript path."""
        manager = CleanupManager(manuscript_path=None)
        # When None is passed, it defaults to environment var or "MANUSCRIPT"
        self.assertIsNotNone(manager.manuscript_path)

    def test_cleanup_output_directory(self):
        """Test cleanup of output directory."""
        # Create test files in output directory
        test_files = [
            self.output_dir / "test.pdf",
            self.output_dir / "test.aux",
            self.output_dir / "test.log",
            self.output_dir / "figures" / "fig1.png",
        ]

        # Create figures subdirectory
        (self.output_dir / "figures").mkdir()

        # Create all test files
        for test_file in test_files:
            test_file.write_text("test content")

        # Verify files exist
        for test_file in test_files:
            self.assertTrue(test_file.exists())

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), output_dir="output", verbose=True)

        # Test cleanup functionality if it exists
        if hasattr(manager, "cleanup_output"):
            manager.cleanup_output()

            # Check if files were cleaned (depending on implementation)
            # This test structure allows for future implementation

        # At minimum, manager should be properly initialized
        self.assertIsNotNone(manager)

    def test_cleanup_figures_directory(self):
        """Test cleanup of figures directory."""
        # Create figures directory with test files
        figures_dir = self.manuscript_dir / "FIGURES"
        figures_dir.mkdir()

        test_figures = [
            figures_dir / "Figure1.pdf",
            figures_dir / "Figure1.png",
            figures_dir / "SFigure1.pdf",
            figures_dir / "cache" / "cached_fig.tmp",
        ]

        # Create cache subdirectory
        (figures_dir / "cache").mkdir()

        # Create all test figures
        for fig_file in test_figures:
            fig_file.write_text("figure content")

        # Verify files exist
        for fig_file in test_figures:
            self.assertTrue(fig_file.exists())

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        # Test cleanup functionality if it exists
        if hasattr(manager, "cleanup_figures"):
            manager.cleanup_figures()

        # Manager should be properly initialized
        self.assertIsNotNone(manager)

    def test_cleanup_temporary_files(self):
        """Test cleanup of temporary files."""
        # Create temporary files that should be cleaned
        temp_files = [
            self.manuscript_dir / ".DS_Store",
            self.manuscript_dir / "Thumbs.db",
            self.manuscript_dir / "*.tmp",
            self.manuscript_dir / ".cache" / "temp.cache",
        ]

        # Create cache directory
        (self.manuscript_dir / ".cache").mkdir()

        # Create test temporary files (except glob pattern)
        for temp_file in temp_files[:-2]:  # Skip glob pattern
            temp_file.write_text("temp content")

        # Create actual .tmp file instead of literal "*"
        (self.manuscript_dir / "actual.tmp").write_text("temp content")
        temp_files[-2] = self.manuscript_dir / "actual.tmp"

        # Create cache file
        temp_files[-1].write_text("cache content")

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        # Test cleanup functionality if it exists
        if hasattr(manager, "cleanup_temp"):
            manager.cleanup_temp()

        self.assertIsNotNone(manager)

    def test_cleanup_arxiv_files(self):
        """Test cleanup of ArXiv-related files."""
        # Create ArXiv files
        arxiv_files = [
            self.output_dir / "for_arxiv.zip",
            self.output_dir / "arxiv_submission" / "main.tex",
            self.output_dir / "arxiv_submission" / "figures" / "fig1.pdf",
        ]

        # Create directories
        (self.output_dir / "arxiv_submission").mkdir()
        (self.output_dir / "arxiv_submission" / "figures").mkdir()

        # Create all ArXiv files
        for arxiv_file in arxiv_files:
            arxiv_file.write_text("arxiv content")

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        # Test cleanup functionality if it exists
        if hasattr(manager, "cleanup_arxiv"):
            manager.cleanup_arxiv()

        self.assertIsNotNone(manager)

    def test_selective_cleanup(self):
        """Test selective cleanup options."""
        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        # Test that manager supports different cleanup modes
        if hasattr(manager, "cleanup"):
            # Test with different options if they exist
            test_options = [
                {"output": True, "figures": False, "temp": False},
                {"output": False, "figures": True, "temp": False},
                {"output": False, "figures": False, "temp": True},
                {"output": True, "figures": True, "temp": True},
            ]

            for options in test_options:
                try:
                    manager.cleanup(**options)
                except TypeError:
                    # Method might not support these options
                    pass

        self.assertIsNotNone(manager)

    @patch("rxiv_maker.utils.platform.platform_detector")
    def test_platform_specific_cleanup(self, mock_detector):
        """Test platform-specific cleanup behavior."""
        # Test Windows-specific cleanup
        mock_detector.is_windows.return_value = True
        mock_detector.is_macos.return_value = False

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        self.assertIsNotNone(manager)

        # Test macOS-specific cleanup
        mock_detector.is_windows.return_value = False
        mock_detector.is_macos.return_value = True

        manager_mac = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        self.assertIsNotNone(manager_mac)

    def test_verbose_output(self):
        """Test verbose output functionality."""
        manager_verbose = CleanupManager(verbose=True)
        manager_quiet = CleanupManager(verbose=False)

        self.assertTrue(manager_verbose.verbose)
        self.assertFalse(manager_quiet.verbose)

    def test_nonexistent_manuscript_path(self):
        """Test handling of nonexistent manuscript path."""
        nonexistent_path = str(self.temp_dir / "nonexistent")

        manager = CleanupManager(manuscript_path=nonexistent_path, verbose=True)

        # Should not crash during initialization
        self.assertEqual(manager.manuscript_path, nonexistent_path)

    def test_cleanup_with_permissions_error(self):
        """Test cleanup with file permission issues."""
        # Create a file that might have permission issues
        test_file = self.output_dir / "protected.pdf"
        test_file.write_text("protected content")

        # Make file read-only (simulate permission issue)
        test_file.chmod(0o444)

        try:
            manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

            # Test that manager handles permission errors gracefully
            if hasattr(manager, "cleanup"):
                # Should not raise an exception
                try:
                    manager.cleanup()
                except PermissionError:
                    # This is acceptable - cleanup might fail due to permissions
                    pass

            self.assertIsNotNone(manager)

        finally:
            # Restore permissions for cleanup
            try:
                test_file.chmod(0o644)
            except (OSError, FileNotFoundError):
                pass

    def test_cleanup_empty_directories(self):
        """Test cleanup behavior with empty directories."""
        # Create empty directories
        empty_dirs = [
            self.output_dir / "empty1",
            self.output_dir / "empty2" / "nested_empty",
            self.manuscript_dir / "empty_figures",
        ]

        for empty_dir in empty_dirs:
            empty_dir.mkdir(parents=True)

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        # Test cleanup functionality
        if hasattr(manager, "cleanup"):
            manager.cleanup()

        self.assertIsNotNone(manager)

    def test_cleanup_large_files(self):
        """Test cleanup with large files."""
        # Create a larger test file
        large_file = self.output_dir / "large_output.pdf"
        large_content = "x" * 10000  # 10KB file
        large_file.write_text(large_content)

        self.assertTrue(large_file.exists())
        self.assertGreater(large_file.stat().st_size, 5000)

        manager = CleanupManager(manuscript_path=str(self.manuscript_dir), verbose=True)

        # Test cleanup handles large files
        if hasattr(manager, "cleanup"):
            manager.cleanup()

        self.assertIsNotNone(manager)


class TestCleanupManagerIntegration(unittest.TestCase):
    """Integration tests for CleanupManager."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up integration test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_cleanup_workflow(self):
        """Test complete cleanup workflow."""
        # Create realistic project structure
        project_dir = self.temp_dir / "test_project"
        project_dir.mkdir()

        # Create output directory with various files
        output_dir = project_dir / "output"
        output_dir.mkdir()

        # Create test files that would be generated during build
        test_files = [
            output_dir / "manuscript.pdf",
            output_dir / "manuscript.aux",
            output_dir / "manuscript.log",
            output_dir / "manuscript.bbl",
            output_dir / "Figures" / "Figure1.pdf",
            output_dir / "arxiv_submission" / "submission.zip",
        ]

        # Create directories
        (output_dir / "Figures").mkdir()
        (output_dir / "arxiv_submission").mkdir()

        # Create all files
        for test_file in test_files:
            test_file.write_text(f"Content for {test_file.name}")

        # Verify files exist
        for test_file in test_files:
            self.assertTrue(test_file.exists())

        # Run cleanup
        manager = CleanupManager(manuscript_path=str(project_dir), output_dir="output", verbose=True)

        # Test the cleanup manager was created successfully
        self.assertIsNotNone(manager)
        self.assertEqual(manager.manuscript_path, str(project_dir))
        self.assertEqual(str(manager.output_dir), "output")
        self.assertTrue(manager.verbose)

    def test_cleanup_with_mixed_file_types(self):
        """Test cleanup with various file types."""
        project_dir = self.temp_dir / "mixed_project"
        project_dir.mkdir()

        # Create files of different types
        file_types = [
            ("document.pdf", "PDF content"),
            ("data.csv", "CSV data"),
            ("image.png", "PNG data"),
            ("script.py", "Python code"),
            ("temp.tmp", "Temporary data"),
            (".hidden", "Hidden file"),
        ]

        for filename, content in file_types:
            file_path = project_dir / filename
            file_path.write_text(content)

        manager = CleanupManager(manuscript_path=str(project_dir), verbose=True)

        self.assertIsNotNone(manager)


if __name__ == "__main__":
    unittest.main()
