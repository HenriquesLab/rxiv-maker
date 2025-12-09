"""Unit tests for citation style configuration and processing."""

import re
from pathlib import Path

import pytest


class TestCitationStyleConfig:
    """Test citation style configuration validation and processing."""

    def test_citation_style_schema_validation(self):
        """Test that citation_style config validates correctly."""
        from rxiv_maker.config.validator import ConfigValidator

        validator = ConfigValidator(cache_enabled=False)

        # Test valid config with numbered citation style
        config_data = {
            "title": "Test Manuscript",
            "authors": [{"name": "Test Author"}],
            "keywords": ["test", "citation", "style"],
            "citation_style": "numbered",
        }

        errors, warnings = validator._validate_against_schema(config_data, "manuscript_config")
        assert len(errors) == 0, f"Unexpected errors for numbered citation style: {errors}"

        # Test valid config with author-date citation style
        config_data["citation_style"] = "author-date"
        errors, warnings = validator._validate_against_schema(config_data, "manuscript_config")
        assert len(errors) == 0, f"Unexpected errors for author-date citation style: {errors}"

        # Test invalid citation style
        config_data["citation_style"] = "invalid-style"
        errors, warnings = validator._validate_against_schema(config_data, "manuscript_config")
        assert len(errors) > 0, "Should have validation error for invalid citation style"

    def test_default_citation_style(self):
        """Test that default citation style is 'numbered'."""
        from rxiv_maker.core.managers.config_manager import ConfigManager

        config_manager = ConfigManager()
        default_config = config_manager._get_default_config()

        assert "citation_style" in default_config
        assert default_config["citation_style"] == "numbered"


class TestCitationStyleTemplateProcessing:
    """Test citation style in template processing."""

    def test_numbered_citation_style_template(self):
        """Test that numbered citation style generates correct LaTeX."""
        from rxiv_maker.processors.template_processor import process_template_replacements

        template_content = "<PY-RPL:CITATION-STYLE>\n\\documentclass[times]{rxiv_maker_style}"
        yaml_metadata = {"citation_style": "numbered"}
        article_md = "# Introduction\n\nTest content."

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should not add any command for numbered (it's the default)
        assert "\\renewcommand{\\rxivcitationstyle}" not in result
        assert "<PY-RPL:CITATION-STYLE>" not in result

    def test_author_date_citation_style_template(self):
        """Test that author-date citation style generates correct LaTeX."""
        from rxiv_maker.processors.template_processor import process_template_replacements

        template_content = "<PY-RPL:CITATION-STYLE>\n\\documentclass[times]{rxiv_maker_style}"
        yaml_metadata = {"citation_style": "author-date"}
        article_md = "# Introduction\n\nTest content."

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should add command to set author-date style (using \def before documentclass)
        assert "\\def\\rxivcitationstyle{author-date}" in result
        assert "<PY-RPL:CITATION-STYLE>" not in result

    def test_missing_citation_style_defaults_to_numbered(self):
        """Test that missing citation_style config defaults to numbered."""
        from rxiv_maker.processors.template_processor import process_template_replacements

        template_content = "<PY-RPL:CITATION-STYLE>\n\\documentclass[times]{rxiv_maker_style}"
        yaml_metadata = {}  # No citation_style specified
        article_md = "# Introduction\n\nTest content."

        result = process_template_replacements(template_content, yaml_metadata, article_md)

        # Should not add any command (defaults to numbered)
        assert "\\renewcommand{\\rxivcitationstyle}" not in result


class TestCitationStyleLatexClass:
    """Test LaTeX class file citation style handling."""

    def test_latex_class_has_citation_style_logic(self):
        """Test that LaTeX class file contains citation style conditional logic."""
        # This test verifies the class file was modified correctly
        # Use direct path for development
        class_file_path = Path(__file__).parent.parent.parent / "src" / "tex" / "style" / "rxiv_maker_style.cls"

        if not class_file_path.exists():
            pytest.skip("LaTeX class file not found in test environment")

        content = class_file_path.read_text(encoding="utf-8")

        # Verify conditional loading logic exists (updated to use \edef expansion)
        assert "\\providecommand{\\rxivcitationstyle}" in content
        assert "\\edef\\expandedstyle{\\rxivcitationstyle}" in content
        assert "\\ifx\\expandedstyle\\tempauthoryear" in content
        assert "authoryear" in content
        assert "numbers" in content

    def test_latex_class_default_citation_style(self):
        """Test that LaTeX class defaults to numbered citations."""
        # Use direct path for development
        class_file_path = Path(__file__).parent.parent.parent / "src" / "tex" / "style" / "rxiv_maker_style.cls"

        if not class_file_path.exists():
            pytest.skip("LaTeX class file not found in test environment")

        content = class_file_path.read_text(encoding="utf-8")

        # Default should be "numbers"
        assert re.search(r"\\providecommand\{\\rxivcitationstyle\}\{numbers\}", content)
