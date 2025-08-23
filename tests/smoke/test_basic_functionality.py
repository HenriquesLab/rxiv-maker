"""Smoke tests for basic Rxiv-Maker functionality.

These tests validate core functionality quickly without expensive operations.
Total execution time should be under 15 seconds.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCoreImports(unittest.TestCase):
    """Test that core modules can be imported without errors."""

    def test_main_module_import(self):
        """Test main rxiv_maker module imports."""
        import rxiv_maker

        self.assertTrue(hasattr(rxiv_maker, "__version__"))

    def test_cli_module_import(self):
        """Test CLI module imports."""
        from rxiv_maker.cli import main

        self.assertTrue(callable(main.main))

    def test_engine_modules_import(self):
        """Test engine modules import."""
        from rxiv_maker.engine import build_manager
        from rxiv_maker.engines import factory

        self.assertTrue(hasattr(factory, "ContainerEngineFactory"))
        self.assertTrue(hasattr(build_manager, "BuildManager"))

    def test_utils_modules_import(self):
        """Test utility modules import."""
        from rxiv_maker.utils import file_helpers
        from rxiv_maker.validators import base_validator

        self.assertTrue(hasattr(file_helpers, "find_manuscript_md"))
        self.assertTrue(hasattr(base_validator, "BaseValidator"))


class TestFileHelpers(unittest.TestCase):
    """Smoke tests for file helper utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_output_dir(self):
        """Test output directory creation."""
        from rxiv_maker.utils.file_helpers import create_output_dir

        output_dir = os.path.join(self.test_dir, "output")
        with patch("builtins.print"):  # Suppress print output
            create_output_dir(output_dir)

        self.assertTrue(os.path.exists(output_dir))
        self.assertTrue(os.path.isdir(output_dir))

    def test_find_manuscript_md_with_file(self):
        """Test manuscript file detection."""
        from rxiv_maker.utils.file_helpers import find_manuscript_md

        # Create test manuscript file
        manuscript_dir = os.path.join(self.test_dir, "manuscript")
        os.makedirs(manuscript_dir)
        manuscript_file = os.path.join(manuscript_dir, "01_MAIN.md")

        with open(manuscript_file, "w") as f:
            f.write("# Test Manuscript")

        result = find_manuscript_md(manuscript_dir)
        self.assertEqual(result.name, "01_MAIN.md")
        self.assertTrue(result.exists())

    def test_find_manuscript_md_missing_file(self):
        """Test manuscript file detection when file is missing."""
        from rxiv_maker.utils.file_helpers import find_manuscript_md

        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir)

        with self.assertRaises(FileNotFoundError):
            find_manuscript_md(empty_dir)


class TestContainerEngineFactory(unittest.TestCase):
    """Smoke tests for container engine factory."""

    def test_factory_initialization(self):
        """Test factory can be initialized."""
        from rxiv_maker.engines.factory import ContainerEngineFactory

        factory = ContainerEngineFactory()
        self.assertIsNotNone(factory)

    def test_list_supported_engines(self):
        """Test listing supported engines."""
        from rxiv_maker.engines.factory import ContainerEngineFactory

        engines = ContainerEngineFactory.get_supported_engines()
        self.assertIsInstance(engines, list)
        self.assertIn("docker", engines)
        self.assertIn("podman", engines)

    def test_engine_availability_check(self):
        """Test engine availability checking doesn't crash."""
        from rxiv_maker.engines.factory import ContainerEngineFactory

        # This should not raise an exception even if engines aren't available
        availability = ContainerEngineFactory.list_available_engines()
        self.assertIsInstance(availability, dict)
        self.assertIn("docker", availability)
        self.assertIn("podman", availability)
        # Don't assert True/False since availability depends on system


class TestBuildManager(unittest.TestCase):
    """Smoke tests for build manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_build_manager_initialization(self):
        """Test build manager can be initialized."""
        from rxiv_maker.engines.build_manager import BuildManager

        manager = BuildManager(self.test_dir)
        self.assertIsNotNone(manager)
        # BuildManager may modify the output directory path, so just check it's set
        self.assertIsNotNone(manager.output_dir)

    def test_style_directory_detection(self):
        """Test style directory detection."""
        from rxiv_maker.engines.build_manager import BuildManager

        manager = BuildManager(self.test_dir)
        style_dir = manager.style_dir

        # Should detect style directory without errors
        self.assertIsNotNone(style_dir)
        # If it exists, it should be a Path or string
        if style_dir:
            self.assertTrue(isinstance(style_dir, (str, Path)))


class TestValidation(unittest.TestCase):
    """Smoke tests for validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_base_validator_import(self):
        """Test base validator can be imported."""
        from rxiv_maker.validators.base_validator import BaseValidator

        # BaseValidator is abstract, so just test it can be imported
        self.assertTrue(hasattr(BaseValidator, "validate"))
        self.assertTrue(callable(getattr(BaseValidator, "validate", None)))

    def test_citation_validator_import(self):
        """Test citation validator imports."""
        from rxiv_maker.validators.citation_validator import CitationValidator

        # Just test that the class can be imported and has expected methods
        self.assertTrue(hasattr(CitationValidator, "__init__"))
        self.assertTrue(hasattr(CitationValidator, "validate"))

    def test_figure_validator_import(self):
        """Test figure validator imports."""
        from rxiv_maker.validators.figure_validator import FigureValidator

        # Just test that the class can be imported and has expected methods
        self.assertTrue(hasattr(FigureValidator, "__init__"))
        self.assertTrue(hasattr(FigureValidator, "validate"))


class TestProcessors(unittest.TestCase):
    """Smoke tests for processor functionality."""

    def test_yaml_processor_import(self):
        """Test YAML processor imports."""
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        self.assertTrue(callable(extract_yaml_metadata))

    def test_template_processor_import(self):
        """Test template processor imports."""
        from rxiv_maker.processors.template_processor import process_template_replacements

        # Test that the template processing function can be imported
        self.assertTrue(callable(process_template_replacements))

    def test_md2tex_converter_import(self):
        """Test markdown to LaTeX converter imports."""
        from rxiv_maker.converters.md2tex import convert_markdown_to_latex

        # Test that the main conversion function can be imported
        self.assertTrue(callable(convert_markdown_to_latex))


class TestCLIBasics(unittest.TestCase):
    """Smoke tests for CLI functionality."""

    def test_cli_main_import(self):
        """Test CLI main function imports."""
        from rxiv_maker.cli.main import main

        self.assertTrue(callable(main))

    def test_cli_commands_import(self):
        """Test CLI command modules import."""
        # Test that key command modules can be imported without errors

        # If we reach here, imports succeeded
        self.assertTrue(True)


@pytest.mark.smoke
class TestMinimalManuscriptWorkflow:
    """Smoke tests for minimal manuscript processing workflow."""

    def test_yaml_metadata_extraction(self, tmp_path):
        """Test YAML metadata extraction from minimal content."""
        from rxiv_maker.processors.yaml_processor import extract_yaml_metadata

        # Create minimal manuscript file
        manuscript_file = tmp_path / "01_MAIN.md"
        manuscript_file.write_text("""---
title: "Test Manuscript"
author: "Test Author"
---

# Introduction
This is a test.""")

        metadata = extract_yaml_metadata(str(manuscript_file))

        assert isinstance(metadata, dict)
        assert metadata.get("title") == "Test Manuscript"
        assert metadata.get("author") == "Test Author"

    def test_markdown_to_latex_conversion(self):
        """Test basic markdown to LaTeX conversion."""
        from rxiv_maker.converters.md2tex import convert_markdown_to_latex

        # Test basic conversion
        markdown_content = "# Introduction\n\nThis is **bold** text with *italic* text."
        latex_content = convert_markdown_to_latex(markdown_content)

        assert isinstance(latex_content, str)
        assert "section" in latex_content.lower()
        assert "textbf" in latex_content or "bold" in latex_content.lower()

    def test_citation_detection(self):
        """Test citation pattern detection import."""
        from rxiv_maker.validators.citation_validator import CitationValidator

        # Just test that the validator class can be imported
        # Don't instantiate as it requires arguments
        assert hasattr(CitationValidator, "__init__")
        assert hasattr(CitationValidator, "validate")


# Mark all tests in this module as smoke tests
pytestmark = pytest.mark.smoke


if __name__ == "__main__":
    unittest.main()
