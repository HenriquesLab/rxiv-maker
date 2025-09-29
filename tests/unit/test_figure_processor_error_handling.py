"""Tests for improved error handling in figure processor."""

from unittest.mock import Mock, patch

from src.rxiv_maker.converters.figure_processor import (
    _process_figure_without_attributes,
    _process_new_figure_format,
    parse_figure_attributes,
    validate_figure_path,
)


class TestFigureAttributesParsing:
    """Test figure attributes parsing with error handling."""

    def test_valid_attributes_parsing(self):
        """Test parsing valid attributes."""
        attr_string = '#fig:test width="0.8" tex_position="!ht"'
        result = parse_figure_attributes(attr_string)

        assert result["id"] == "fig:test"
        assert result["width"] == "0.8"
        assert result["tex_position"] == "!ht"

    def test_malformed_attributes_handling(self):
        """Test handling of malformed attributes."""
        # This should not raise an exception but return what it can parse
        attr_string = '#fig:test width="unclosed tex_position="!ht"'
        result = parse_figure_attributes(attr_string)

        # Should at least get the ID and handle malformed attributes gracefully
        assert result["id"] == "fig:test"
        # The malformed quote causes tex_position to be included in width value
        assert "width" in result
        assert "tex_position=" in result["width"]


class TestFigurePathValidation:
    """Test figure path validation with error handling."""

    def test_valid_paths(self):
        """Test validation of valid paths."""
        valid_paths = [
            "FIGURES/test.pdf",
            "images/photo.jpg",
            "diagram.png",
            "https://raw.githubusercontent.com/test/repo/image.png",
            "extensionless_file",  # Should be valid
        ]

        for path in valid_paths:
            assert validate_figure_path(path) is True

    def test_invalid_paths(self):
        """Test validation of invalid paths."""
        invalid_paths = [
            "",  # Empty path
            None,  # None path
            123,  # Non-string path
            "file.txt",  # Invalid extension
        ]

        for path in invalid_paths:
            assert validate_figure_path(path) is False

    def test_edge_case_paths(self):
        """Test edge cases in path validation."""
        edge_cases = [
            '"quoted_path.pdf"',  # Should handle quotes
            "'single_quoted.png'",  # Should handle single quotes
            "  spaced_path.jpg  ",  # Should handle whitespace
        ]

        for path in edge_cases:
            # These should not raise exceptions
            result = validate_figure_path(path)
            assert isinstance(result, bool)


class TestNewFigureFormatErrorHandling:
    """Test error handling in new figure format processing."""

    @patch("src.rxiv_maker.converters.figure_processor.parse_figure_attributes")
    @patch("src.rxiv_maker.core.logging_config.get_logger")
    def test_attribute_parsing_error_logging(self, mock_logger, mock_parse):
        """Test that attribute parsing errors are logged."""
        mock_parse.side_effect = ValueError("Invalid attributes")
        mock_log = Mock()
        mock_logger.return_value = mock_log

        # Use properly formatted text that will match the regex pattern
        text = """![](test.png)
{#fig:test width="0.8"} Test caption

"""

        result = _process_new_figure_format(text)

        # Should keep original text when parsing fails
        assert "![](test.png)" in result
        mock_log.warning.assert_called_once()

    @patch("src.rxiv_maker.converters.figure_processor.create_latex_figure_environment")
    @patch("src.rxiv_maker.core.logging_config.get_logger")
    def test_latex_generation_error_logging(self, mock_logger, mock_create):
        """Test that LaTeX generation errors are logged."""
        mock_create.side_effect = TypeError("Invalid parameters")
        mock_log = Mock()
        mock_logger.return_value = mock_log

        text = """![](test.png)
{#fig:test width="0.8"} Test caption

"""

        result = _process_new_figure_format(text)

        # Should keep original text when LaTeX generation fails
        assert "![](test.png)" in result
        mock_log.warning.assert_called_once()


class TestFigureWithoutAttributesErrorHandling:
    """Test error handling in figure processing without attributes."""

    @patch("src.rxiv_maker.converters.figure_processor.validate_figure_path")
    @patch("src.rxiv_maker.core.logging_config.get_logger")
    def test_path_validation_error_logging(self, mock_logger, mock_validate):
        """Test that path validation errors are logged."""
        mock_validate.side_effect = OSError("File not found")
        mock_log = Mock()
        mock_logger.return_value = mock_log

        text = "![Test caption](invalid_path.png)"

        result = _process_figure_without_attributes(text)

        # Should keep original text when validation fails
        assert "![Test caption](invalid_path.png)" in result
        mock_log.warning.assert_called_once()

    @patch("src.rxiv_maker.converters.figure_processor.validate_figure_path")
    @patch("src.rxiv_maker.converters.figure_processor.create_latex_figure_environment")
    @patch("src.rxiv_maker.core.logging_config.get_logger")
    def test_latex_creation_error_logging(self, mock_logger, mock_create, mock_validate):
        """Test that LaTeX creation errors are logged."""
        mock_validate.return_value = True
        mock_create.side_effect = ValueError("Invalid figure parameters")
        mock_log = Mock()
        mock_logger.return_value = mock_log

        text = "![Test caption](test.png)"

        result = _process_figure_without_attributes(text)

        # Should keep original text when LaTeX creation fails
        assert "![Test caption](test.png)" in result
        mock_log.warning.assert_called_once()


class TestSpecificErrorTypes:
    """Test handling of specific error types."""

    def test_key_error_handling(self):
        """Test that KeyError is handled properly."""
        # This tests the specific exception types we catch
        with patch("src.rxiv_maker.converters.figure_processor.parse_figure_attributes") as mock_parse:
            mock_parse.side_effect = KeyError("Missing required key")

            text = """![](test.png)
{#fig:test} Test caption

"""

            result = _process_new_figure_format(text)
            # Should not raise, should return original text
            assert "![](test.png)" in result

    def test_attribute_error_handling(self):
        """Test that AttributeError is handled properly."""
        with patch("src.rxiv_maker.converters.figure_processor.parse_figure_attributes") as mock_parse:
            mock_parse.side_effect = AttributeError("Object has no attribute")

            text = """![](test.png)
{#fig:test} Test caption

"""

            result = _process_new_figure_format(text)
            # Should not raise, should return original text
            assert "![](test.png)" in result

    def test_type_error_handling(self):
        """Test that TypeError is handled properly."""
        with patch("src.rxiv_maker.converters.figure_processor.create_latex_figure_environment") as mock_create:
            mock_create.side_effect = TypeError("Wrong argument type")

            text = """![](test.png)
{#fig:test width="0.8"} Test caption

"""

            result = _process_new_figure_format(text)
            # Should not raise, should return original text
            assert "![](test.png)" in result


class TestLoggingIntegration:
    """Test logging integration in error handling."""

    @patch("src.rxiv_maker.core.logging_config.get_logger")
    def test_logger_import_and_usage(self, mock_get_logger):
        """Test that logger is properly imported and used."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        with patch("src.rxiv_maker.converters.figure_processor.parse_figure_attributes") as mock_parse:
            mock_parse.side_effect = ValueError("Test error")

            text = """![](test.png)
{#fig:test} Test caption

"""

            _process_new_figure_format(text)

            # Verify logger was obtained and warning was called
            mock_get_logger.assert_called_once()
            mock_logger.warning.assert_called_once()

            # Check the warning message format
            call_args = mock_logger.warning.call_args[0][0]
            assert "Failed to parse figure attributes" in call_args
            assert "Test error" in call_args


class TestRegressionTests:
    """Regression tests for previously problematic cases."""

    def test_empty_attributes_dont_crash(self):
        """Test that empty attributes don't crash the parser."""
        text = """![](test.png)
{} Empty attributes"""

        # Should not raise an exception
        result = _process_new_figure_format(text)
        assert isinstance(result, str)

    def test_complex_nested_quotes(self):
        """Test handling of complex nested quotes in attributes."""
        text = """![](test.png)
{#fig:test caption="This has \\"nested\\" quotes"} Test caption"""

        # Should not raise an exception
        result = _process_new_figure_format(text)
        assert isinstance(result, str)

    def test_malformed_regex_patterns(self):
        """Test that malformed content doesn't break regex processing."""
        # Content with regex special characters that might break naive processing
        text = "![Caption with [brackets] and (parens) and {braces}](test.png)"

        result = _process_figure_without_attributes(text)
        assert isinstance(result, str)
