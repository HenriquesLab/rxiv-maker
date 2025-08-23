"""Comprehensive tests for generate_preprint.py module.

Tests the preprint generation functionality including template processing,
YAML metadata handling, CLI integration, and error scenarios.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

from rxiv_maker.engines.operations.generate_preprint import generate_preprint, main


class TestGeneratePreprintCore(unittest.TestCase):
    """Test core generate_preprint functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"
        self.yaml_metadata = {
            "title": "Test Paper",
            "author": "Test Author",
            "email": "test@example.com",
            "affiliation": "Test University",
        }

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    @patch("rxiv_maker.engines.operations.generate_preprint.process_template_replacements")
    @patch("rxiv_maker.engines.operations.generate_preprint.write_manuscript_output")
    @patch("rxiv_maker.engines.operations.generate_preprint.generate_supplementary_tex")
    def test_generate_preprint_basic_workflow(
        self,
        mock_generate_supp,
        mock_write_output,
        mock_process_template,
        mock_find_md,
        mock_get_template,
        mock_create_dir,
    ):
        """Test basic preprint generation workflow."""
        # Mock setup
        mock_get_template.return_value = "/fake/template.tex"
        mock_find_md.return_value = Path("/fake/manuscript.md")
        mock_process_template.return_value = "processed template content"
        mock_write_output.return_value = "/output/manuscript.tex"

        # Mock file reading
        with patch("builtins.open", mock_open(read_data="template content")):
            result = generate_preprint(self.output_dir, self.yaml_metadata)

        # Verify function calls
        mock_create_dir.assert_called_once_with(self.output_dir)
        mock_get_template.assert_called_once()
        mock_find_md.assert_called_once_with(None)
        mock_process_template.assert_called_once_with("template content", self.yaml_metadata, "/fake/manuscript.md")
        mock_write_output.assert_called_once_with(self.output_dir, "processed template content", manuscript_name=None)
        mock_generate_supp.assert_called_once_with(self.output_dir, self.yaml_metadata)

        # Verify result
        self.assertEqual(result, "/output/manuscript.tex")

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    @patch("rxiv_maker.engines.operations.generate_preprint.process_template_replacements")
    @patch("rxiv_maker.engines.operations.generate_preprint.write_manuscript_output")
    @patch("rxiv_maker.engines.operations.generate_preprint.generate_supplementary_tex")
    def test_generate_preprint_with_manuscript_path(
        self,
        mock_generate_supp,
        mock_write_output,
        mock_process_template,
        mock_find_md,
        mock_get_template,
        mock_create_dir,
    ):
        """Test preprint generation with custom manuscript path."""
        custom_path = "/custom/manuscript.md"
        mock_get_template.return_value = "/fake/template.tex"
        mock_find_md.return_value = Path(custom_path)
        mock_process_template.return_value = "processed content"
        mock_write_output.return_value = "/output/manuscript.tex"

        with patch("builtins.open", mock_open(read_data="template")):
            result = generate_preprint(self.output_dir, self.yaml_metadata, custom_path)

        mock_find_md.assert_called_once_with(custom_path)
        self.assertEqual(result, "/output/manuscript.tex")

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    def test_generate_preprint_template_file_error(self, mock_get_template, mock_create_dir):
        """Test error handling when template file cannot be read."""
        mock_get_template.return_value = "/nonexistent/template.tex"

        with patch("builtins.open", side_effect=FileNotFoundError("Template not found")):
            with self.assertRaises(FileNotFoundError):
                generate_preprint(self.output_dir, self.yaml_metadata)

        mock_create_dir.assert_called_once_with(self.output_dir)

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    def test_generate_preprint_find_manuscript_error(self, mock_find_md, mock_get_template, mock_create_dir):
        """Test error handling when manuscript markdown cannot be found."""
        mock_get_template.return_value = "/fake/template.tex"
        mock_find_md.side_effect = FileNotFoundError("Manuscript not found")

        with patch("builtins.open", mock_open(read_data="template")):
            with self.assertRaises(FileNotFoundError):
                generate_preprint(self.output_dir, self.yaml_metadata)

        mock_find_md.assert_called_once_with(None)

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    @patch("rxiv_maker.engines.operations.generate_preprint.process_template_replacements")
    def test_generate_preprint_process_template_error(
        self, mock_process_template, mock_find_md, mock_get_template, mock_create_dir
    ):
        """Test error handling when template processing fails."""
        mock_get_template.return_value = "/fake/template.tex"
        mock_find_md.return_value = Path("/fake/manuscript.md")
        mock_process_template.side_effect = ValueError("Template processing failed")

        with patch("builtins.open", mock_open(read_data="template")):
            with self.assertRaises(ValueError):
                generate_preprint(self.output_dir, self.yaml_metadata)

    def test_generate_preprint_empty_metadata(self):
        """Test preprint generation with empty metadata."""
        with (
            patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir"),
            patch(
                "rxiv_maker.engines.operations.generate_preprint.get_template_path", return_value="/fake/template.tex"
            ),
            patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md", return_value=Path("/fake/md")),
            patch(
                "rxiv_maker.engines.operations.generate_preprint.process_template_replacements", return_value="content"
            ),
            patch(
                "rxiv_maker.engines.operations.generate_preprint.write_manuscript_output",
                return_value="/output/file.tex",
            ),
            patch("rxiv_maker.engines.operations.generate_preprint.generate_supplementary_tex"),
            patch("builtins.open", mock_open(read_data="template")),
        ):
            result = generate_preprint(self.output_dir, {})
            self.assertEqual(result, "/output/file.tex")


class TestGeneratePreprintCLI(unittest.TestCase):
    """Test CLI functionality of generate_preprint."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    @patch("rxiv_maker.engines.operations.generate_preprint.generate_preprint")
    @patch("pathlib.Path.exists")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_default_args(self, mock_parse_args, mock_path_exists, mock_generate):
        """Test main function with default arguments."""
        # Mock arguments
        mock_args = Mock()
        mock_args.output_dir = None
        mock_args.config = None
        mock_parse_args.return_value = mock_args

        # Mock config file existence
        mock_path_exists.return_value = True
        mock_generate.return_value = "/output/manuscript.tex"

        mock_yaml_data = {"title": "Test"}
        with (
            patch("builtins.open", mock_open(read_data="title: Test")),
            patch("yaml.safe_load", return_value=mock_yaml_data),
        ):
            result = main()

        # Verify calls
        mock_generate.assert_called_once_with(".", mock_yaml_data)
        self.assertEqual(result, 0)

    @patch("rxiv_maker.engines.operations.generate_preprint.generate_preprint")
    @patch("pathlib.Path.exists")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_custom_args(self, mock_parse_args, mock_path_exists, mock_generate):
        """Test main function with custom arguments."""
        # Mock arguments
        mock_args = Mock()
        mock_args.output_dir = "/custom/output"
        mock_args.config = "/custom/config.yml"
        mock_parse_args.return_value = mock_args

        mock_path_exists.return_value = True
        mock_generate.return_value = "/custom/output/manuscript.tex"

        mock_yaml_data = {"title": "Custom Test", "author": "Test Author"}
        with (
            patch("builtins.open", mock_open(read_data="title: Custom Test")),
            patch("yaml.safe_load", return_value=mock_yaml_data),
        ):
            result = main()

        mock_generate.assert_called_once_with("/custom/output", mock_yaml_data)
        self.assertEqual(result, 0)

    @patch("rxiv_maker.engines.operations.generate_preprint.generate_preprint")
    @patch("pathlib.Path.exists")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_config_file_not_exists(self, mock_parse_args, mock_path_exists, mock_generate):
        """Test main function when config file doesn't exist."""
        mock_args = Mock()
        mock_args.output_dir = None
        mock_args.config = None
        mock_parse_args.return_value = mock_args

        mock_path_exists.return_value = False
        mock_generate.return_value = "/output/manuscript.tex"

        result = main()

        # Should call generate_preprint with empty metadata
        mock_generate.assert_called_once_with(".", {})
        self.assertEqual(result, 0)

    @patch("rxiv_maker.engines.operations.generate_preprint.generate_preprint")
    @patch("pathlib.Path.exists")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_yaml_loading_error(self, mock_parse_args, mock_path_exists, mock_generate):
        """Test main function with YAML loading error."""
        mock_args = Mock()
        mock_args.output_dir = None
        mock_args.config = None
        mock_parse_args.return_value = mock_args

        mock_path_exists.return_value = True

        # Mock YAML loading error - this will cause an unhandled exception
        # since the main function doesn't have try/catch around yaml.safe_load
        with (
            patch("builtins.open", mock_open(read_data="invalid: yaml: content")),
            patch("yaml.safe_load", side_effect=ValueError("Invalid YAML")),
        ):
            with self.assertRaises(ValueError):
                main()

    @patch("rxiv_maker.engines.operations.generate_preprint.generate_preprint")
    @patch("pathlib.Path.exists")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_generate_preprint_error(self, mock_parse_args, mock_path_exists, mock_generate):
        """Test main function when generate_preprint raises an error."""
        mock_args = Mock()
        mock_args.output_dir = None
        mock_args.config = None
        mock_parse_args.return_value = mock_args

        mock_path_exists.return_value = False
        mock_generate.side_effect = Exception("Generation failed")

        result = main()

        self.assertEqual(result, 1)

    @patch("argparse.ArgumentParser.parse_args")
    def test_main_argument_parsing(self, mock_parse_args):
        """Test that main function sets up argument parser correctly."""
        mock_args = Mock()
        mock_args.output_dir = "/test/output"
        mock_args.config = "/test/config.yml"
        mock_parse_args.return_value = mock_args

        with (
            patch("pathlib.Path.exists", return_value=False),
            patch("rxiv_maker.engines.operations.generate_preprint.generate_preprint", return_value="/output/file.tex"),
        ):
            main()

        # Verify argument parser was called
        mock_parse_args.assert_called_once()


class TestGeneratePreprintIntegration(unittest.TestCase):
    """Test integration scenarios for generate_preprint."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    @patch("rxiv_maker.engines.operations.generate_preprint.process_template_replacements")
    @patch("rxiv_maker.engines.operations.generate_preprint.write_manuscript_output")
    @patch("rxiv_maker.engines.operations.generate_preprint.generate_supplementary_tex")
    def test_full_workflow_integration(
        self,
        mock_generate_supp,
        mock_write_output,
        mock_process_template,
        mock_find_md,
        mock_get_template,
        mock_create_dir,
    ):
        """Test full workflow integration with realistic data."""
        # Setup realistic test data
        yaml_metadata = {
            "title": "Advanced Machine Learning Techniques",
            "subtitle": "A Comprehensive Study",
            "author": "Dr. Jane Smith",
            "email": "jane.smith@university.edu",
            "affiliation": "Department of Computer Science, University of Excellence",
            "abstract": "This paper presents novel approaches to machine learning...",
            "keywords": ["machine learning", "deep learning", "neural networks"],
        }

        mock_get_template.return_value = "/templates/paper.tex"
        mock_find_md.return_value = Path("/manuscripts/paper.md")
        mock_process_template.return_value = "\\documentclass{article}\\begin{document}..."
        mock_write_output.return_value = "/output/paper.tex"

        template_content = "\\documentclass{article}\n\\title{{{title}}}\n\\author{{{author}}}"

        with patch("builtins.open", mock_open(read_data=template_content)):
            result = generate_preprint(self.output_dir, yaml_metadata, "/custom/manuscript.md")

        # Verify all components called correctly
        mock_create_dir.assert_called_once_with(self.output_dir)
        mock_find_md.assert_called_once_with("/custom/manuscript.md")
        mock_process_template.assert_called_once_with(template_content, yaml_metadata, "/manuscripts/paper.md")
        mock_write_output.assert_called_once_with(
            self.output_dir, "\\documentclass{article}\\begin{document}...", manuscript_name=None
        )
        mock_generate_supp.assert_called_once_with(self.output_dir, yaml_metadata)

        self.assertEqual(result, "/output/paper.tex")

    def test_metadata_validation_types(self):
        """Test that function handles different metadata types correctly."""
        test_cases = [
            # String values
            {"title": "String Title", "author": "String Author"},
            # Mixed types
            {"title": "Title", "year": 2023, "pages": 42},
            # Lists
            {"keywords": ["word1", "word2"], "authors": ["Author 1", "Author 2"]},
            # Nested dictionaries
            {"contact": {"email": "test@example.com", "phone": "123-456-7890"}},
        ]

        for metadata in test_cases:
            with (
                patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir"),
                patch(
                    "rxiv_maker.engines.operations.generate_preprint.get_template_path",
                    return_value="/fake/template.tex",
                ),
                patch(
                    "rxiv_maker.engines.operations.generate_preprint.find_manuscript_md", return_value=Path("/fake/md")
                ),
                patch(
                    "rxiv_maker.engines.operations.generate_preprint.process_template_replacements",
                    return_value="content",
                ),
                patch(
                    "rxiv_maker.engines.operations.generate_preprint.write_manuscript_output",
                    return_value="/output/file.tex",
                ),
                patch("rxiv_maker.engines.operations.generate_preprint.generate_supplementary_tex"),
                patch("builtins.open", mock_open(read_data="template")),
            ):
                result = generate_preprint(self.output_dir, metadata)
                self.assertEqual(result, "/output/file.tex")


class TestGeneratePreprintErrorHandling(unittest.TestCase):
    """Test error handling scenarios for generate_preprint."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "output"

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    def test_create_output_dir_failure(self, mock_create_dir):
        """Test handling of output directory creation failure."""
        mock_create_dir.side_effect = PermissionError("Cannot create directory")

        with self.assertRaises(PermissionError):
            generate_preprint(self.output_dir, {})

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    def test_template_permission_error(self, mock_get_template, mock_create_dir):
        """Test handling of template file permission error."""
        mock_get_template.return_value = "/restricted/template.tex"

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                generate_preprint(self.output_dir, {})

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    @patch("rxiv_maker.engines.operations.generate_preprint.process_template_replacements")
    @patch("rxiv_maker.engines.operations.generate_preprint.write_manuscript_output")
    def test_write_output_failure(
        self, mock_write_output, mock_process_template, mock_find_md, mock_get_template, mock_create_dir
    ):
        """Test handling of manuscript output writing failure."""
        mock_get_template.return_value = "/fake/template.tex"
        mock_find_md.return_value = Path("/fake/manuscript.md")
        mock_process_template.return_value = "processed content"
        mock_write_output.side_effect = IOError("Cannot write to output file")

        with patch("builtins.open", mock_open(read_data="template")):
            with self.assertRaises(IOError):
                generate_preprint(self.output_dir, {})

    @patch("rxiv_maker.engines.operations.generate_preprint.create_output_dir")
    @patch("rxiv_maker.engines.operations.generate_preprint.get_template_path")
    @patch("rxiv_maker.engines.operations.generate_preprint.find_manuscript_md")
    @patch("rxiv_maker.engines.operations.generate_preprint.process_template_replacements")
    @patch("rxiv_maker.engines.operations.generate_preprint.write_manuscript_output")
    @patch("rxiv_maker.engines.operations.generate_preprint.generate_supplementary_tex")
    def test_supplementary_generation_failure(
        self,
        mock_generate_supp,
        mock_write_output,
        mock_process_template,
        mock_find_md,
        mock_get_template,
        mock_create_dir,
    ):
        """Test handling of supplementary file generation failure."""
        mock_get_template.return_value = "/fake/template.tex"
        mock_find_md.return_value = Path("/fake/manuscript.md")
        mock_process_template.return_value = "processed content"
        mock_write_output.return_value = "/output/manuscript.tex"
        mock_generate_supp.side_effect = RuntimeError("Supplementary generation failed")

        with patch("builtins.open", mock_open(read_data="template")):
            with self.assertRaises(RuntimeError):
                generate_preprint(self.output_dir, {})


if __name__ == "__main__":
    unittest.main()
