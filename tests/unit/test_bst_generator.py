"""Unit tests for BST generator functionality."""

import re
import tempfile
from pathlib import Path

import pytest

from rxiv_maker.utils.bst_generator import generate_bst_file


@pytest.mark.unit
class TestBSTGenerator:
    """Test BST file generation and format string replacement."""

    def extract_function_section(self, content: str, function_name: str) -> str:
        """Extract a specific FUNCTION block from BST content.

        Args:
            content: BST file content
            function_name: Name of the function to extract

        Returns:
            The function block content
        """
        pattern = rf"FUNCTION\s+\{{{function_name}\}}.*?(?=FUNCTION|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(0) if match else ""

    def test_bst_generator_only_modifies_format_names(self):
        """Ensure format.full.names is not modified (regression test for #XXX)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate BST with lastname_initials format
            output_path = generate_bst_file("lastname_initials", temp_dir)

            # Read generated file
            content = output_path.read_text()

            # Verify format.names was modified (should have new format)
            format_names_section = self.extract_function_section(content, "format.names")
            assert "{vv~}{ll}{, f.}" in format_names_section, "format.names should have lastname_initials format"

            # Verify format.full.names was NOT modified (should have original format)
            format_full_names_section = self.extract_function_section(content, "format.full.names")
            assert "{vv~}{ll}" in format_full_names_section, "format.full.names should keep original format"
            assert "{vv~}{ll}{, f.}" not in format_full_names_section, (
                "format.full.names should NOT have our modified format"
            )

    def test_bst_generator_lastname_initials_format(self):
        """Test BST generation with lastname_initials format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_bst_file("lastname_initials", temp_dir)

            assert output_path.exists()
            content = output_path.read_text()

            # Should contain the lastname_initials format: {vv~}{ll}{, f.}
            format_names_section = self.extract_function_section(content, "format.names")
            assert "{vv~}{ll}{, f.}" in format_names_section

    def test_bst_generator_lastname_firstname_format(self):
        """Test BST generation with lastname_firstname format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_bst_file("lastname_firstname", temp_dir)

            assert output_path.exists()
            content = output_path.read_text()

            # Should contain the lastname_firstname format: {vv~}{ll}{, ff}
            format_names_section = self.extract_function_section(content, "format.names")
            assert "{vv~}{ll}{, ff}" in format_names_section

    def test_bst_generator_firstname_lastname_format(self):
        """Test BST generation with firstname_lastname format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_bst_file("firstname_lastname", temp_dir)

            assert output_path.exists()
            content = output_path.read_text()

            # Should contain the firstname_lastname format: {ff~}{vv~}{ll}
            format_names_section = self.extract_function_section(content, "format.names")
            assert "{ff~}{vv~}{ll}" in format_names_section

    def test_bst_generator_creates_output_directory(self):
        """Test that BST generator creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = Path(temp_dir) / "nested" / "output"
            output_path = generate_bst_file("lastname_initials", str(nested_dir))

            assert nested_dir.exists()
            assert output_path.exists()

    def test_bst_generator_file_name(self):
        """Test that generated BST file has correct name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_bst_file("lastname_initials", temp_dir)

            assert output_path.name == "rxiv_maker_style.bst"

    def test_bst_generator_invalid_format_type(self):
        """Test that invalid format type raises appropriate error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError, match="Invalid bibliography author format"):
                generate_bst_file("invalid_format", temp_dir)

    def test_bst_both_functions_exist_in_template(self):
        """Verify the BST template contains both format.names and format.full.names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_bst_file("lastname_initials", temp_dir)
            content = output_path.read_text()

            # Both functions should exist
            assert "FUNCTION {format.names}" in content
            assert "FUNCTION {format.full.names}" in content

    def test_bst_regex_matches_exactly_once(self):
        """Verify that the regex pattern matches exactly once (not multiple times)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = generate_bst_file("lastname_initials", temp_dir)
            content = output_path.read_text()

            # Count occurrences of our modified format
            format_names_section = self.extract_function_section(content, "format.names")
            format_full_names_section = self.extract_function_section(content, "format.full.names")

            # Should appear once in format.names
            assert format_names_section.count("{vv~}{ll}{, f.}") == 1

            # Should NOT appear in format.full.names
            assert format_full_names_section.count("{vv~}{ll}{, f.}") == 0
