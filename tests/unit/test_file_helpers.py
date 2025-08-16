"""Comprehensive test coverage for file_helpers.py utilities."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rxiv_maker.utils.file_helpers import (
    create_output_dir,
    find_manuscript_md,
    write_manuscript_output,
)


class TestCreateOutputDir(unittest.TestCase):
    """Test create_output_dir functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("builtins.print")
    def test_create_output_dir_new_directory(self, mock_print):
        """Test creating a new output directory."""
        new_dir = os.path.join(self.test_dir, "new_output")

        create_output_dir(new_dir)

        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
        mock_print.assert_called_once_with(f"Created output directory: {new_dir}")

    @patch("builtins.print")
    def test_create_output_dir_existing_directory(self, mock_print):
        """Test with existing output directory."""
        existing_dir = os.path.join(self.test_dir, "existing")
        os.makedirs(existing_dir)

        create_output_dir(existing_dir)

        self.assertTrue(os.path.exists(existing_dir))
        mock_print.assert_called_once_with(f"Output directory already exists: {existing_dir}")

    @patch("builtins.print")
    def test_create_output_dir_nested_path(self, mock_print):
        """Test creating nested directory structure."""
        nested_dir = os.path.join(self.test_dir, "level1", "level2", "output")

        create_output_dir(nested_dir)

        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.isdir(nested_dir))
        mock_print.assert_called_once_with(f"Created output directory: {nested_dir}")

    @patch("builtins.print")
    def test_create_output_dir_with_permissions(self, mock_print):
        """Test directory creation preserves default permissions."""
        perm_dir = os.path.join(self.test_dir, "perm_test")

        create_output_dir(perm_dir)

        self.assertTrue(os.path.exists(perm_dir))
        # Check that directory has reasonable permissions
        dir_stat = os.stat(perm_dir)
        self.assertTrue(dir_stat.st_mode & 0o700)  # Owner has read/write/execute


class TestFindManuscriptMd(unittest.TestCase):
    """Test find_manuscript_md functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_find_manuscript_md_with_explicit_path(self):
        """Test finding manuscript with explicit path."""
        manuscript_dir = os.path.join(self.test_dir, "my_manuscript")
        os.makedirs(manuscript_dir)
        manuscript_file = os.path.join(manuscript_dir, "01_MAIN.md")

        # Create the manuscript file
        with open(manuscript_file, "w") as f:
            f.write("# Test Manuscript")

        result = find_manuscript_md(manuscript_dir)

        self.assertEqual(result.resolve(), Path(manuscript_file).resolve())
        self.assertTrue(result.exists())

    def test_find_manuscript_md_explicit_path_not_found(self):
        """Test explicit path when manuscript file doesn't exist."""
        manuscript_dir = os.path.join(self.test_dir, "empty_manuscript")
        os.makedirs(manuscript_dir)

        with self.assertRaises(FileNotFoundError) as context:
            find_manuscript_md(manuscript_dir)

        self.assertIn("01_MAIN.md not found", str(context.exception))
        self.assertIn(manuscript_dir, str(context.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_find_manuscript_md_current_directory(self):
        """Test finding manuscript in current directory."""
        # Change to test directory and create manuscript
        os.chdir(self.test_dir)
        manuscript_file = os.path.join(self.test_dir, "01_MAIN.md")

        with open(manuscript_file, "w") as f:
            f.write("# Test Manuscript")

        result = find_manuscript_md()

        self.assertEqual(result.resolve(), Path(manuscript_file).resolve())

    @patch.dict(os.environ, {"MANUSCRIPT_PATH": "my_manuscript"})
    def test_find_manuscript_md_env_var_path(self):
        """Test finding manuscript using MANUSCRIPT_PATH environment variable."""
        os.chdir(self.test_dir)
        manuscript_dir = os.path.join(self.test_dir, "my_manuscript")
        os.makedirs(manuscript_dir)
        manuscript_file = os.path.join(manuscript_dir, "01_MAIN.md")

        with open(manuscript_file, "w") as f:
            f.write("# Test Manuscript")

        result = find_manuscript_md()

        self.assertEqual(result.resolve(), Path(manuscript_file).resolve())

    @patch.dict(os.environ, {}, clear=True)
    def test_find_manuscript_md_default_manuscript_path(self):
        """Test finding manuscript with default MANUSCRIPT path."""
        os.chdir(self.test_dir)
        manuscript_dir = os.path.join(self.test_dir, "MANUSCRIPT")
        os.makedirs(manuscript_dir)
        manuscript_file = os.path.join(manuscript_dir, "01_MAIN.md")

        with open(manuscript_file, "w") as f:
            f.write("# Test Manuscript")

        result = find_manuscript_md()

        self.assertEqual(result.resolve(), Path(manuscript_file).resolve())

    @patch.dict(os.environ, {"MANUSCRIPT_PATH": "nonexistent"})
    def test_find_manuscript_md_not_found_anywhere(self):
        """Test when manuscript file is not found in any location."""
        os.chdir(self.test_dir)

        with self.assertRaises(FileNotFoundError) as context:
            find_manuscript_md()

        error_message = str(context.exception)
        self.assertIn("01_MAIN.md not found", error_message)
        self.assertIn("nonexistent", error_message)

    def test_find_manuscript_md_with_pathlib_path(self):
        """Test with pathlib.Path as manuscript_path."""
        manuscript_dir = Path(self.test_dir) / "pathlib_manuscript"
        manuscript_dir.mkdir()
        manuscript_file = manuscript_dir / "01_MAIN.md"
        manuscript_file.write_text("# Test Manuscript")

        result = find_manuscript_md(str(manuscript_dir))

        self.assertEqual(result, manuscript_file)

    @patch.dict(os.environ, {}, clear=True)
    def test_find_manuscript_md_current_dir_priority(self):
        """Test that current directory has priority over env var."""
        os.chdir(self.test_dir)

        # Create manuscript in current directory
        current_manuscript = os.path.join(self.test_dir, "01_MAIN.md")
        with open(current_manuscript, "w") as f:
            f.write("# Current Dir Manuscript")

        # Create manuscript in MANUSCRIPT subdirectory
        manuscript_dir = os.path.join(self.test_dir, "MANUSCRIPT")
        os.makedirs(manuscript_dir)
        subdir_manuscript = os.path.join(manuscript_dir, "01_MAIN.md")
        with open(subdir_manuscript, "w") as f:
            f.write("# Subdir Manuscript")

        result = find_manuscript_md()

        # Should find the one in current directory first
        self.assertEqual(result.resolve(), Path(current_manuscript).resolve())


class TestWriteManuscriptOutput(unittest.TestCase):
    """Test write_manuscript_output functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("builtins.print")
    def test_write_manuscript_output_with_explicit_name(self, mock_print):
        """Test writing manuscript with explicit name."""
        template_content = "\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}"
        manuscript_name = "my_paper"

        result = write_manuscript_output(self.test_dir, template_content, manuscript_name)

        expected_file = os.path.join(self.test_dir, "my_paper.tex")
        self.assertEqual(result, expected_file)
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, template_content)

        mock_print.assert_called_once_with(f"Generated manuscript: {expected_file}")

    @patch("builtins.print")
    @patch.dict(os.environ, {"MANUSCRIPT_PATH": "env_manuscript"})
    def test_write_manuscript_output_with_env_var(self, mock_print):
        """Test writing manuscript using MANUSCRIPT_PATH environment variable."""
        template_content = "\\documentclass{article}\nContent"

        result = write_manuscript_output(self.test_dir, template_content)

        expected_file = os.path.join(self.test_dir, "env_manuscript.tex")
        self.assertEqual(result, expected_file)
        self.assertTrue(os.path.exists(expected_file))

    @patch("builtins.print")
    @patch.dict(os.environ, {}, clear=True)
    def test_write_manuscript_output_default_name(self, mock_print):
        """Test writing manuscript with default name."""
        template_content = "\\documentclass{article}\nDefault content"

        result = write_manuscript_output(self.test_dir, template_content)

        expected_file = os.path.join(self.test_dir, "MANUSCRIPT.tex")
        self.assertEqual(result, expected_file)
        self.assertTrue(os.path.exists(expected_file))

    @patch("builtins.print")
    @patch.dict(os.environ, {"MANUSCRIPT_PATH": "/path/to/my_project"})
    def test_write_manuscript_output_basename_from_path(self, mock_print):
        """Test extracting basename from MANUSCRIPT_PATH."""
        template_content = "\\documentclass{article}\nBasename test"

        result = write_manuscript_output(self.test_dir, template_content)

        expected_file = os.path.join(self.test_dir, "my_project.tex")
        self.assertEqual(result, expected_file)

    @patch("builtins.print")
    def test_write_manuscript_output_invalid_names(self, mock_print):
        """Test handling of invalid manuscript names."""
        template_content = "\\documentclass{article}\nInvalid name test"

        # Test with dot
        result = write_manuscript_output(self.test_dir, template_content, ".")
        expected_file = os.path.join(self.test_dir, "MANUSCRIPT.tex")
        self.assertEqual(result, expected_file)

        # Clean up for next test
        os.remove(expected_file)

        # Test with double dot
        result = write_manuscript_output(self.test_dir, template_content, "..")
        self.assertEqual(result, expected_file)

        # Clean up for next test
        os.remove(expected_file)

        # Test with empty string
        result = write_manuscript_output(self.test_dir, template_content, "")
        self.assertEqual(result, expected_file)

    @patch("builtins.print")
    def test_write_manuscript_output_unicode_content(self, mock_print):
        """Test writing manuscript with Unicode content."""
        template_content = (
            "\\documentclass{article}\n\\begin{document}\nTéxt with spëcial characTërs: αβγ\n\\end{document}"
        )
        manuscript_name = "unicode_test"

        write_manuscript_output(self.test_dir, template_content, manuscript_name)

        expected_file = os.path.join(self.test_dir, "unicode_test.tex")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, template_content)

    @patch("builtins.print")
    def test_write_manuscript_output_creates_directory_structure(self, mock_print):
        """Test that Path object properly creates the output file."""
        nested_output_dir = os.path.join(self.test_dir, "nested", "output")
        os.makedirs(nested_output_dir)

        template_content = "\\documentclass{article}\nNested test"
        manuscript_name = "nested_paper"

        result = write_manuscript_output(nested_output_dir, template_content, manuscript_name)

        expected_file = os.path.join(nested_output_dir, "nested_paper.tex")
        self.assertEqual(result, expected_file)
        self.assertTrue(os.path.exists(expected_file))

    @patch("builtins.print")
    def test_write_manuscript_output_file_encoding(self, mock_print):
        """Test that file is written with correct UTF-8 encoding."""
        template_content = "Content with émoji: 🚀 and mäth: ∫∂∆"
        manuscript_name = "encoding_test"

        write_manuscript_output(self.test_dir, template_content, manuscript_name)

        # Read file with explicit encoding
        expected_file = os.path.join(self.test_dir, "encoding_test.tex")
        with open(expected_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, template_content)

    @patch("builtins.print")
    @patch.dict(os.environ, {"MANUSCRIPT_PATH": "special/chars/path"})
    def test_write_manuscript_output_special_chars_in_env_path(self, mock_print):
        """Test handling of special characters in environment path."""
        template_content = "\\documentclass{article}\nSpecial chars test"

        result = write_manuscript_output(self.test_dir, template_content)

        expected_file = os.path.join(self.test_dir, "path.tex")
        self.assertEqual(result, expected_file)


class TestFileHelpersEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_find_manuscript_md_with_none_parameter(self):
        """Test find_manuscript_md with None parameter."""
        # Should behave the same as calling without parameters
        original_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            manuscript_file = os.path.join(self.test_dir, "01_MAIN.md")
            with open(manuscript_file, "w") as f:
                f.write("# Test")

            result = find_manuscript_md(None)
            self.assertEqual(result.resolve(), Path(manuscript_file).resolve())
        finally:
            os.chdir(original_cwd)

    def test_write_manuscript_output_with_none_name(self):
        """Test write_manuscript_output with None name parameter."""
        with patch.dict(os.environ, {"MANUSCRIPT_PATH": "test_manuscript"}):
            template_content = "Test content"

            result = write_manuscript_output(self.test_dir, template_content, None)

            expected_file = os.path.join(self.test_dir, "test_manuscript.tex")
            self.assertEqual(result, expected_file)

    @patch("builtins.print")
    def test_create_output_dir_permission_handling(self, mock_print):
        """Test create_output_dir with potential permission issues."""
        # This test focuses on the happy path since permission errors
        # would require special setup that might not work in all test environments
        test_output = os.path.join(self.test_dir, "permission_test")

        create_output_dir(test_output)

        self.assertTrue(os.path.exists(test_output))
        mock_print.assert_called_once()


class TestFileHelpersIntegration(unittest.TestCase):
    """Integration tests for file_helpers functions working together."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("builtins.print")
    def test_full_workflow_integration(self, mock_print):
        """Test complete workflow: create dir, find manuscript, write output."""
        # Set up manuscript structure
        manuscript_dir = os.path.join(self.test_dir, "integration_manuscript")
        output_dir = os.path.join(self.test_dir, "output")

        # Create output directory
        create_output_dir(output_dir)

        # Create manuscript directory and file
        os.makedirs(manuscript_dir)
        manuscript_file = os.path.join(manuscript_dir, "01_MAIN.md")
        with open(manuscript_file, "w") as f:
            f.write("# Integration Test Manuscript")

        # Find manuscript
        found_manuscript = find_manuscript_md(manuscript_dir)
        self.assertEqual(found_manuscript.resolve(), Path(manuscript_file).resolve())

        # Write output
        template_content = "\\documentclass{article}\n\\begin{document}\nIntegration test\n\\end{document}"
        output_file = write_manuscript_output(output_dir, template_content, "integration_test")

        # Verify output
        expected_output = os.path.join(output_dir, "integration_test.tex")
        self.assertEqual(output_file, expected_output)
        self.assertTrue(os.path.exists(expected_output))

        with open(expected_output, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, template_content)

    @patch("builtins.print")
    @patch.dict(os.environ, {"MANUSCRIPT_PATH": "integration_manuscript"})
    def test_env_var_integration(self, mock_print):
        """Test integration with environment variable workflow."""
        os.chdir(self.test_dir)

        # Create manuscript using env var path
        manuscript_dir = os.path.join(self.test_dir, "integration_manuscript")
        os.makedirs(manuscript_dir)
        manuscript_file = os.path.join(manuscript_dir, "01_MAIN.md")
        with open(manuscript_file, "w") as f:
            f.write("# Env Var Integration Test")

        # Create output directory
        output_dir = os.path.join(self.test_dir, "output")
        create_output_dir(output_dir)

        # Find manuscript (should use env var)
        found_manuscript = find_manuscript_md()
        self.assertEqual(found_manuscript.resolve(), Path(manuscript_file).resolve())

        # Write output (should use env var for naming)
        template_content = "\\documentclass{article}\nEnv var test"
        output_file = write_manuscript_output(output_dir, template_content)

        expected_output = os.path.join(output_dir, "integration_manuscript.tex")
        self.assertEqual(output_file, expected_output)


if __name__ == "__main__":
    unittest.main()
