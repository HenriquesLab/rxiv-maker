"""Unit tests for build manager improvements."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Define mock pytest.mark for when pytest is not available
    class MockPytest:
        class mark:
            @staticmethod
            def build_manager(cls):
                return cls

    pytest = MockPytest()

try:
    from rxiv_maker.engines.operations.build_manager import BuildManager

    BUILD_MANAGER_AVAILABLE = True
except ImportError:
    BUILD_MANAGER_AVAILABLE = False


@pytest.mark.build_manager
@unittest.skipUnless(BUILD_MANAGER_AVAILABLE, "Build manager not available")
class TestBuildManagerLogging(unittest.TestCase):
    """Test build manager logging functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.manuscript_dir)
        os.makedirs(self.output_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up logging handlers before removing files (Windows compatibility)
        from rxiv_maker.core.logging_config import cleanup

        cleanup()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_manager_initialization_creates_log_paths(self):
        """Test that BuildManager creates log file paths on initialization."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Check that log file paths are set
        self.assertTrue(hasattr(build_manager, "warnings_log"))
        self.assertTrue(hasattr(build_manager, "bibtex_log"))
        self.assertEqual(build_manager.warnings_log.name, "build_warnings.log")
        self.assertEqual(build_manager.bibtex_log.name, "bibtex_warnings.log")

    def test_log_to_file_creates_warning_log(self):
        """Test that warnings are logged to file."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Log a warning
        build_manager._log_to_file("Test warning message", "WARNING")

        # Check that log file was created
        self.assertTrue(build_manager.warnings_log.exists())

        # Check log content
        with open(build_manager.warnings_log) as f:
            content = f.read()

        self.assertIn("WARNING: Test warning message", content)
        self.assertIn("2025-", content)  # Should have timestamp

    def test_log_to_file_creates_error_log(self):
        """Test that errors are logged to file."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Log an error
        build_manager._log_to_file("Test error message", "ERROR")

        # Check that log file was created
        self.assertTrue(build_manager.warnings_log.exists())

        # Check log content
        with open(build_manager.warnings_log) as f:
            content = f.read()

        self.assertIn("ERROR: Test error message", content)

    def test_log_method_calls_file_logging_for_warnings(self):
        """Test that the log method calls file logging for warnings."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        with patch.object(build_manager, "_log_to_file") as mock_log_to_file:
            build_manager.log("Test warning", "WARNING")

            # Should have called _log_to_file
            mock_log_to_file.assert_called_once_with("Test warning", "WARNING")

    def test_log_method_calls_file_logging_for_errors(self):
        """Test that the log method calls file logging for errors."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        with patch.object(build_manager, "_log_to_file") as mock_log_to_file:
            build_manager.log("Test error", "ERROR")

            # Should have called _log_to_file
            mock_log_to_file.assert_called_once_with("Test error", "ERROR")

    def test_log_method_does_not_call_file_logging_for_info(self):
        """Test that the log method does not call file logging for info messages."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        with patch.object(build_manager, "_log_to_file") as mock_log_to_file:
            build_manager.log("Test info", "INFO")

            # Should NOT have called _log_to_file
            mock_log_to_file.assert_not_called()

    def test_log_bibtex_warnings_extracts_from_blg_file(self):
        """Test that BibTeX warnings are extracted from .blg file."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create a mock .blg file with warnings
        blg_content = """This is BibTeX, Version 0.99d
Warning--empty journal in test_reference
Warning--missing year in another_reference
You've used 2 entries,
(There were 2 warnings)
"""

        blg_file = Path(self.output_dir) / f"{Path(self.manuscript_dir).name}.blg"
        with open(blg_file, "w") as f:
            f.write(blg_content)

        with patch.object(build_manager, "log") as mock_log:
            build_manager._log_bibtex_warnings()

            # Should have logged success message
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            self.assertIn("BibTeX warnings logged", args[0])
            self.assertEqual(args[1], "INFO")

        # Check that BibTeX warning log was created
        self.assertTrue(build_manager.bibtex_log.exists())

        # Check log content
        with open(build_manager.bibtex_log) as f:
            content = f.read()

        self.assertIn("BibTeX Warnings Report", content)
        self.assertIn("1. empty journal in test_reference", content)
        self.assertIn("2. missing year in another_reference", content)

    def test_log_bibtex_warnings_handles_no_warnings(self):
        """Test that BibTeX warning logging handles case with no warnings."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create a mock .blg file without warnings
        blg_content = """This is BibTeX, Version 0.99d
You've used 2 entries,
(There were 0 warnings)
"""

        blg_file = Path(self.output_dir) / f"{Path(self.manuscript_dir).name}.blg"
        with open(blg_file, "w") as f:
            f.write(blg_content)

        with patch.object(build_manager, "log") as mock_log:
            build_manager._log_bibtex_warnings()

            # Should not have logged anything
            mock_log.assert_not_called()

        # Should not have created warning log
        self.assertFalse(build_manager.bibtex_log.exists())

    def test_log_bibtex_warnings_handles_missing_blg_file(self):
        """Test that BibTeX warning logging handles missing .blg file."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Don't create .blg file

        with patch.object(build_manager, "log") as mock_log:
            build_manager._log_bibtex_warnings()

            # Should not have logged anything
            mock_log.assert_not_called()

        # Should not have created warning log
        self.assertFalse(build_manager.bibtex_log.exists())

    def test_log_to_file_handles_exceptions_gracefully(self):
        """Test that file logging handles exceptions gracefully and logs them properly."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Mock the module-level logger to verify it's called when file writing fails
        with patch("rxiv_maker.engines.operations.build_manager.logger") as mock_logger:
            # Mock file operations to raise exception
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                # Should not raise exception but should log the error
                try:
                    build_manager._log_to_file("Test message", "WARNING")
                except Exception:
                    self.fail("_log_to_file should handle exceptions gracefully")

                # Verify that the exception was properly logged
                mock_logger.debug.assert_called_once()
                call_args = mock_logger.debug.call_args[0][0]
                self.assertIn("Failed to write to warnings log file", call_args)
                self.assertIn("Permission denied", call_args)

    def test_log_bibtex_warnings_handles_exceptions_gracefully(self):
        """Test that BibTeX warning extraction handles exceptions gracefully and logs them properly."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create a .blg file to trigger the method
        blg_file = Path(self.output_dir) / f"{Path(self.manuscript_dir).name}.blg"
        blg_file.write_text("This is BibTeX, Version 0.99d\nWarning--test warning\n")

        # Mock the module-level logger to verify it's called when BibTeX logging fails
        with patch("rxiv_maker.engines.operations.build_manager.logger") as mock_logger:
            # Mock open to raise exception when writing BibTeX log
            original_open = open

            def failing_open(path, mode="r", **kwargs):
                if str(path).endswith("bibtex_warnings.log") and "w" in mode:
                    raise PermissionError("Permission denied for BibTeX log")
                return original_open(path, mode, **kwargs)

            with patch("builtins.open", side_effect=failing_open):
                # Should not raise exception but should log the error
                try:
                    build_manager._log_bibtex_warnings()
                except Exception:
                    self.fail("_log_bibtex_warnings should handle exceptions gracefully")

                # Verify that the exception was properly logged
                mock_logger.debug.assert_called_once()
                call_args = mock_logger.debug.call_args[0][0]
                self.assertIn("Failed to extract BibTeX warnings from", call_args)
                self.assertIn("Permission denied for BibTeX log", call_args)

    def test_build_completion_reports_warning_log_existence(self):
        """Test that build completion reports warning log existence."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create a warning log file
        build_manager.warnings_log.touch()

        # Mock the full build process
        with patch.object(build_manager, "check_manuscript_structure", return_value=True):
            with patch.object(build_manager, "setup_output_directory", return_value=True):
                with patch.object(build_manager, "generate_figures", return_value=True):
                    with patch.object(build_manager, "validate_manuscript", return_value=True):
                        with patch.object(build_manager, "copy_style_files", return_value=True):
                            with patch.object(build_manager, "copy_references", return_value=True):
                                with patch.object(build_manager, "copy_figures", return_value=True):
                                    with patch.object(
                                        build_manager,
                                        "generate_tex_files",
                                        return_value=True,
                                    ):
                                        with patch.object(
                                            build_manager,
                                            "compile_pdf",
                                            return_value=True,
                                        ):
                                            with patch.object(
                                                build_manager,
                                                "copy_pdf_to_manuscript",
                                                return_value=True,
                                            ):
                                                with patch.object(
                                                    build_manager,
                                                    "run_pdf_validation",
                                                    return_value=True,
                                                ):
                                                    with patch.object(
                                                        build_manager,
                                                        "run_word_count_analysis",
                                                        return_value=True,
                                                    ):
                                                        with patch.object(build_manager, "log") as mock_log:
                                                            result = build_manager.run_full_build()

                                                            # Should have logged about warning log
                                                            log_calls = [
                                                                call
                                                                for call in mock_log.call_args_list
                                                                if "warnings logged" in str(call)
                                                            ]
                                                            self.assertTrue(len(log_calls) > 0)

                                                            # Should return success
                                                            self.assertTrue(result)


@pytest.mark.build_manager
@unittest.skipUnless(BUILD_MANAGER_AVAILABLE, "Build manager not available")
class TestBuildProcessOrder(unittest.TestCase):
    """Test build process order changes."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.manuscript_dir)
        os.makedirs(self.output_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up logging handlers before removing files (Windows compatibility)
        from rxiv_maker.core.logging_config import cleanup

        cleanup()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pdf_validation_runs_before_word_count(self):
        """Test that PDF validation runs before word count analysis."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Track the order of method calls
        call_order = []

        def track_pdf_validation():
            call_order.append("pdf_validation")
            return True

        def track_word_count():
            call_order.append("word_count")
            return True

        # Mock all prerequisites to return True
        with patch.object(build_manager, "check_manuscript_structure", return_value=True):
            with patch.object(build_manager, "setup_output_directory", return_value=True):
                with patch.object(build_manager, "generate_figures", return_value=True):
                    with patch.object(build_manager, "validate_manuscript", return_value=True):
                        with patch.object(build_manager, "copy_style_files", return_value=True):
                            with patch.object(build_manager, "copy_references", return_value=True):
                                with patch.object(build_manager, "copy_figures", return_value=True):
                                    with patch.object(
                                        build_manager,
                                        "generate_tex_files",
                                        return_value=True,
                                    ):
                                        with patch.object(
                                            build_manager,
                                            "compile_pdf",
                                            return_value=True,
                                        ):
                                            with patch.object(
                                                build_manager,
                                                "copy_pdf_to_manuscript",
                                                return_value=True,
                                            ):
                                                with patch.object(
                                                    build_manager,
                                                    "run_pdf_validation",
                                                    side_effect=track_pdf_validation,
                                                ):
                                                    with patch.object(
                                                        build_manager,
                                                        "run_word_count_analysis",
                                                        side_effect=track_word_count,
                                                    ):
                                                        with patch.object(build_manager, "log"):
                                                            result = build_manager.run_full_build()

                                                            # Should have run successfully
                                                            self.assertTrue(result)

                                                            # Should have called both methods
                                                            self.assertEqual(len(call_order), 2)

                                                            # PDF validation should come first
                                                            self.assertEqual(
                                                                call_order[0],
                                                                "pdf_validation",
                                                            )
                                                            self.assertEqual(
                                                                call_order[1],
                                                                "word_count",
                                                            )


@pytest.mark.build_manager
@unittest.skipUnless(BUILD_MANAGER_AVAILABLE, "Build manager not available")
class TestBibTeXWarningExtraction(unittest.TestCase):
    """Test BibTeX warning extraction functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.manuscript_dir)
        os.makedirs(self.output_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up logging handlers before removing files (Windows compatibility)
        from rxiv_maker.core.logging_config import cleanup

        cleanup()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bibtex_warning_extraction_multiple_warnings(self):
        """Test extraction of multiple BibTeX warnings."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create a realistic .blg file with multiple warnings
        blg_content = """This is BibTeX, Version 0.99d (TeX Live 2025)
Capacity: max_strings=200000, hash_size=200000, hash_prime=170003
The top-level auxiliary file: test.aux
The style file: rxiv_maker_style.bst
Database file #1: 03_REFERENCES.bib
Warning--empty journal in Xie2016_bookdown
Warning--missing year in smith2023
Warning--empty title in jones2022
You've used 25 entries,
            2450 wiz_defined-function locations,
            742 strings with 10894 characters,
and the built_in function-call counts, 10098 in all, are:
= -- 760
> -- 706
< -- 16
+ -- 270
- -- 220
warning$ -- 3
(There were 3 warnings)
"""

        blg_file = Path(self.output_dir) / f"{Path(self.manuscript_dir).name}.blg"
        with open(blg_file, "w") as f:
            f.write(blg_content)

        build_manager._log_bibtex_warnings()

        # Check that BibTeX warning log was created
        self.assertTrue(build_manager.bibtex_log.exists())

        # Check log content
        with open(build_manager.bibtex_log) as f:
            content = f.read()

        self.assertIn("BibTeX Warnings Report", content)
        self.assertIn("1. empty journal in Xie2016_bookdown", content)
        self.assertIn("2. missing year in smith2023", content)
        self.assertIn("3. empty title in jones2022", content)
        self.assertIn("2025-", content)  # Should have timestamp

    def test_bibtex_warning_log_overwrites_previous(self):
        """Test that BibTeX warning log overwrites previous logs."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create initial warning log
        with open(build_manager.bibtex_log, "w") as f:
            f.write("Old log content")

        # Create new .blg file
        blg_content = """This is BibTeX, Version 0.99d
Warning--new warning in test_ref
(There was 1 warning)
"""

        blg_file = Path(self.output_dir) / f"{Path(self.manuscript_dir).name}.blg"
        with open(blg_file, "w") as f:
            f.write(blg_content)

        build_manager._log_bibtex_warnings()

        # Check that log was overwritten
        with open(build_manager.bibtex_log) as f:
            content = f.read()

        self.assertNotIn("Old log content", content)
        self.assertIn("new warning in test_ref", content)


@pytest.mark.build_manager
@unittest.skipUnless(BUILD_MANAGER_AVAILABLE, "Build manager not available")
class TestBuildManagerIntegration(unittest.TestCase):
    """Integration tests for build manager improvements."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = os.path.join(self.temp_dir, "manuscript")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.manuscript_dir)
        os.makedirs(self.output_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up logging handlers before removing files (Windows compatibility)
        from rxiv_maker.core.logging_config import cleanup

        cleanup()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_manager_with_bibtex_warnings_integration(self):
        """Test integration of BibTeX warning logging in build process."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Create a .blg file that would be generated during build
        blg_content = """This is BibTeX, Version 0.99d
Warning--empty journal in test_reference
(There was 1 warning)
"""

        blg_file = Path(self.output_dir) / f"{Path(self.manuscript_dir).name}.blg"
        with open(blg_file, "w") as f:
            f.write(blg_content)

        # Mock the compile_pdf method to simulate successful BibTeX completion
        with patch.object(build_manager, "compile_pdf") as mock_compile:

            def mock_compile_pdf():
                # Create the .blg file as would happen during real compilation
                build_manager._log_bibtex_warnings()
                return True

            mock_compile.side_effect = mock_compile_pdf

            # Mock other methods to focus on our specific functionality
            with patch.object(build_manager, "check_manuscript_structure", return_value=True):
                with patch.object(build_manager, "setup_output_directory", return_value=True):
                    with patch.object(build_manager, "generate_figures", return_value=True):
                        with patch.object(build_manager, "validate_manuscript", return_value=True):
                            with patch.object(build_manager, "copy_style_files", return_value=True):
                                with patch.object(build_manager, "copy_references", return_value=True):
                                    with patch.object(build_manager, "copy_figures", return_value=True):
                                        with patch.object(
                                            build_manager,
                                            "generate_tex_files",
                                            return_value=True,
                                        ):
                                            with patch.object(
                                                build_manager,
                                                "copy_pdf_to_manuscript",
                                                return_value=True,
                                            ):
                                                with patch.object(
                                                    build_manager,
                                                    "run_pdf_validation",
                                                    return_value=True,
                                                ):
                                                    with patch.object(
                                                        build_manager,
                                                        "run_word_count_analysis",
                                                        return_value=True,
                                                    ):
                                                        # Run the build
                                                        result = build_manager.run_full_build()

                                                        # Should succeed
                                                        self.assertTrue(result)

                                                        # Should have created BibTeX warning log
                                                        self.assertTrue(build_manager.bibtex_log.exists())

                                                        # Check log content
                                                        with open(build_manager.bibtex_log) as f:
                                                            content = f.read()

                                                        self.assertIn(
                                                            "empty journal in test_reference",
                                                            content,
                                                        )


class TestLaTeXErrorHandling(unittest.TestCase):
    """Test LaTeX error handling and recovery strategies."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manuscript_dir = Path(self.temp_dir) / "manuscript"
        self.manuscript_dir.mkdir(parents=True)
        self.output_dir = Path(self.temp_dir) / "output"

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up logging handlers before removing files (Windows compatibility)
        from rxiv_maker.core.logging_config import cleanup

        cleanup()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_latex_undefined_control_sequence(self):
        """Test handling of undefined control sequence errors."""
        # Create a TeX file with undefined command
        tex_content = r"""
\documentclass{article}
\begin{document}
\undefined{This command does not exist}
\end{document}
"""
        tex_file = Path(self.output_dir) / "test.tex"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        tex_file.write_text(tex_content)

        # Test that error is properly parsed
        from rxiv_maker.validators.latex_error_parser import LaTeXErrorParser

        parser = LaTeXErrorParser(manuscript_path=self.manuscript_dir)

        error_output = r"""
! Undefined control sequence.
l.4 \undefined
              {This command does not exist}
"""
        # Use the private method for testing purposes
        errors = parser._parse_log_file(error_output)
        assert any(e.error_type == "undefined_command" for e in errors)

    def test_latex_missing_package_error(self):
        """Test handling of missing package errors."""
        # Test error detection for missing packages
        error_output = r"""
! LaTeX Error: File `nonexistentpackage.sty' not found.
"""
        from rxiv_maker.validators.latex_error_parser import LaTeXErrorParser

        parser = LaTeXErrorParser(manuscript_path=self.manuscript_dir)
        errors = parser._parse_log_file(error_output)
        assert any(e.error_type == "missing_file" for e in errors)
        assert any(e.error_type == "missing_file" for e in errors)

    def test_latex_compilation_timeout(self):
        """Test handling of LaTeX compilation timeout."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # Mock subprocess to simulate timeout
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("pdflatex", 30)

            result = build_manager.compile_pdf()
            self.assertFalse(result)

    def test_latex_error_recovery_with_fallback(self):
        """Test LaTeX compilation with error recovery fallback."""
        build_manager = BuildManager(manuscript_path=self.manuscript_dir, output_dir=self.output_dir)

        # First compilation fails, second succeeds (simulating recovery)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1, stdout="", stderr="Error in first run"),
                Mock(returncode=0, stdout="Success", stderr=""),
            ]

            # Should attempt recovery by calling compile_pdf multiple times if first fails  # noqa: E501
            build_manager.compile_pdf()
            # Check that subprocess was called at least once
            self.assertTrue(mock_run.call_count >= 1)


if __name__ == "__main__":
    unittest.main()
