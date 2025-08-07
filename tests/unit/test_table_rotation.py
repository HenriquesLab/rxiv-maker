"""Tests for table rotation functionality in markdown to LaTeX conversion."""

import unittest

from rxiv_maker.converters.table_processor import (
    convert_tables_to_latex,
    generate_latex_table,
)


class TestTableRotation(unittest.TestCase):
    """Test table rotation features."""

    def test_table_with_rotation_attribute(self):
        """Test that tables with rotate attribute get wrapped in rotatebox."""
        markdown_input = """| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

{#stable:test rotate=90} **Test Table.** A rotated table for testing.
"""

        result = convert_tables_to_latex(markdown_input)

        # Should contain rotatebox
        self.assertIn("\\rotatebox{90}{%", result)
        self.assertIn("}%", result)

        # Should contain proper table structure
        self.assertIn("\\begin{table}[ht]", result)
        self.assertIn("\\begin{tabular}", result)
        self.assertIn("Column 1 & Column 2", result)
        self.assertIn("Data 1 & Data 2", result)

        # Should have correct label
        self.assertIn("\\label{stable:test}", result)

    def test_table_without_rotation_attribute(self):
        """Test that tables without rotate attribute don't get wrapped in rotatebox."""
        markdown_input = """| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

{#stable:test} **Test Table.** A normal table without rotation.
"""

        result = convert_tables_to_latex(markdown_input)

        # Should NOT contain rotatebox
        self.assertNotIn("\\rotatebox", result)

        # Should still contain proper table structure
        self.assertIn("\\begin{table}[ht]", result)
        self.assertIn("\\begin{tabular}", result)

    def test_different_rotation_angles(self):
        """Test that different rotation angles are parsed correctly."""
        test_cases = [
            ("rotate=90", "\\rotatebox{90}{%"),
            ("rotate=180", "\\rotatebox{180}{%"),
            ("rotate=270", "\\rotatebox{270}{%"),
            ("rotate=45", "\\rotatebox{45}{%"),
        ]

        for attribute, expected in test_cases:
            with self.subTest(attribute=attribute):
                markdown_input = f"""| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

{{#stable:test {attribute}}} **Test Table.** A rotated table.
"""

                result = convert_tables_to_latex(markdown_input)
                self.assertIn(expected, result)

    def test_rotation_with_other_attributes(self):
        """Test that rotation works with other attributes in the caption."""
        markdown_input = """| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

{#stable:test rotate=90 width=double} **Test Table.** A rotated table with width.
"""

        result = convert_tables_to_latex(markdown_input)

        # Should contain rotatebox
        self.assertIn("\\rotatebox{90}{%", result)
        self.assertIn("}%", result)

    def test_generate_latex_table_with_rotation(self):
        """Test the generate_latex_table function directly with rotation."""
        headers = ["Header 1", "Header 2"]
        data_rows = [["Data 1", "Data 2"], ["Data 3", "Data 4"]]
        caption = "Test caption"

        # Test with rotation
        result = generate_latex_table(headers, data_rows, caption, "single", "test:table", None, 90)

        self.assertIn("\\rotatebox{90}{%", result)
        self.assertIn("}%", result)
        self.assertIn("\\begin{tabular}", result)
        self.assertIn("\\end{tabular}", result)

        # Test without rotation
        result_no_rotation = generate_latex_table(headers, data_rows, caption, "single", "test:table", None, None)

        self.assertNotIn("\\rotatebox", result_no_rotation)

    def test_rotation_in_double_column_table(self):
        """Test that rotation works with double column tables."""
        headers = ["Header 1", "Header 2"]
        data_rows = [["Data 1", "Data 2"]]

        result = generate_latex_table(headers, data_rows, "Test caption", "double", "test:table", None, 90)

        # Should have table* environment for double column
        self.assertIn("\\begin{table*}[!ht]", result)
        # Should still have rotation
        self.assertIn("\\rotatebox{90}{%", result)


if __name__ == "__main__":
    unittest.main()
