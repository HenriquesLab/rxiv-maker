"""Unit tests for the md2tex module."""

import re

from rxiv_maker.converters.citation_processor import convert_citations_to_latex
from rxiv_maker.converters.code_processor import convert_code_blocks_to_latex
from rxiv_maker.converters.figure_processor import (
    convert_figure_references_to_latex,
    convert_figures_to_latex,
)
from rxiv_maker.converters.html_processor import convert_html_comments_to_latex
from rxiv_maker.converters.list_processor import convert_lists_to_latex
from rxiv_maker.converters.md2tex import (
    convert_markdown_to_latex,
    extract_content_sections,
    map_section_title_to_key,
)
from rxiv_maker.converters.table_processor import (
    convert_table_references_to_latex,
    convert_tables_to_latex,
)
from rxiv_maker.converters.url_processor import escape_url_for_latex


class TestMarkdownToLatexConversion:
    """Test basic markdown to LaTeX conversion."""

    def test_convert_bold_text(self):
        """Test conversion of bold text."""
        markdown = "This is **bold** text."
        expected = r"This is \textbf{bold} text."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)
        assert expected in result

    def test_convert_italic_text(self):
        """Test conversion of italic text."""
        markdown = "This is *italic* text."
        expected = r"This is \textit{italic} text."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)
        assert expected in result

    def test_convert_headers(self):
        """Test conversion of markdown headers."""
        markdown = "# Section\n## Subsection\n### Subsubsection\n#### Paragraph"
        result = convert_markdown_to_latex(markdown, is_supplementary=False)
        assert r"\section{Section}" in result
        assert r"\subsection{Subsection}" in result
        assert r"\subsubsection{Subsubsection}" in result
        assert r"\paragraph{Paragraph}" in result

    def test_convert_code_blocks(self):
        """Test conversion of inline code."""
        markdown = "Use `code_here` for testing."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)
        assert r"\texttt{code\_here}" in result

    def test_markdown_inside_backticks_preserved(self):
        """Test that markdown syntax inside backticks is preserved literally."""
        # Test various markdown syntaxes inside backticks
        test_cases = [
            ("This is `*italic*` text.", r"\texttt{*italic*}"),
            ("This is `**bold**` text.", r"\texttt{**bold**}"),
            (
                "Code: `*emphasis* and **strong**` here.",
                r"\texttt{\seqsplit{\textit{emphasis} and \textbf{strong}}}",
            ),
            ("Inline: `_underscore_` formatting.", r"\texttt{\_underscore\_}"),
            (
                "Complex: `**bold** and *italic* together`.",
                r"\texttt{\seqsplit{\textbf{bold} and \textit{italic} together}}",
            ),
        ]

        for markdown, expected in test_cases:
            result = convert_markdown_to_latex(markdown, is_supplementary=False)
            assert expected in result, f"Failed for: {markdown}\nExpected: {expected}\nGot: {result}"

    def test_list_items_with_formatting(self):
        """Test list items that contain formatting (bold and italic)."""
        markdown = "- *Citation Processing* function\n- **Bold Processing** function"
        result = convert_markdown_to_latex(markdown, is_supplementary=False)
        assert r"\item \textit{Citation Processing} function" in result
        assert r"\item \textbf{Bold Processing} function" in result


class TestCitationConversion:
    """Test citation conversion functionality."""

    def test_single_citation(self):
        """Test conversion of single citations."""
        text = "According to @smith2023, this is true."
        expected = r"According to \cite{smith2023}, this is true."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_multiple_citations_bracketed(self):
        """Test conversion of multiple bracketed citations."""
        text = "This is supported [@smith2023;@jones2022]."
        expected = r"This is supported \cite{smith2023,jones2022}."
        result = convert_citations_to_latex(text)
        assert result == expected

    def test_citation_with_underscores(self):
        """Test citations with underscores in keys."""
        text = "See @author_name_2023 for details."
        expected = r"See \cite{author_name_2023} for details."
        result = convert_citations_to_latex(text)
        assert result == expected


class TestFigureConversion:
    """Test figure conversion functionality."""

    def test_figure_with_attributes(self):
        """Test conversion of figures with attributes."""
        markdown = '![Test Caption](FIGURES/test.png){#fig:test width="0.8" tex_position="!ht"}'
        result = convert_figures_to_latex(markdown)

        assert r"\begin{figure}[!ht]" in result
        assert r"\includegraphics[width=0.8\linewidth]{Figures/test/test.png}" in result
        assert r"\caption{Test Caption}" in result
        assert r"\label{fig:test}" in result
        assert r"\end{figure}" in result

    def test_figure_without_attributes(self):
        """Test conversion of figures without attributes."""
        markdown = "![Simple Caption](FIGURES/simple.png)"
        result = convert_figures_to_latex(markdown)

        assert r"\begin{figure}[ht]" in result
        assert r"\includegraphics[width=\linewidth]{Figures/simple/simple.png}" in result
        assert r"\caption{Simple Caption}" in result
        assert r"\end{figure}" in result

    def test_figure_reference_conversion(self):
        """Test conversion of figure references."""
        text = "As shown in @fig:test, the results are clear."
        expected = r"As shown in Fig. \ref{fig:test}, the results are clear."
        result = convert_figure_references_to_latex(text)
        assert result == expected


class TestTableReferenceConversion:
    """Test table reference conversion functionality."""

    def test_regular_table_reference_conversion(self):
        """Test conversion of regular table references."""
        text = "As shown in @table:results, the performance is excellent."
        expected = r"As shown in Table \ref{table:results}, the performance is excellent."
        result = convert_table_references_to_latex(text)
        assert result == expected

    def test_supplementary_table_reference_conversion(self):
        """Test conversion of supplementary table references."""
        text = "A detailed comparison is provided in @stable:tool-comparison."
        expected = r"A detailed comparison is provided in Table \ref{stable:tool-comparison}."
        result = convert_table_references_to_latex(text)
        assert result == expected

    def test_multiple_table_references(self):
        """Test conversion of multiple table references."""
        text = "See @table:results and @stable:comparison for details."
        expected = (
            r"See Table \ref{table:results} and "
            r"Table \ref{stable:comparison} for details."
        )
        result = convert_table_references_to_latex(text)
        assert result == expected

    def test_table_references_with_underscores_and_hyphens(self):
        """Test table references with underscores and hyphens in IDs."""
        text = "Compare @table:result_summary and @stable:tool-comparison-detailed."
        expected = (
            r"Compare Table \ref{table:result_summary} and "
            r"Table \ref{stable:tool-comparison-detailed}."
        )
        result = convert_table_references_to_latex(text)
        assert result == expected

    def test_table_references_integrated_in_markdown_to_latex(self):
        """Test table references work in the complete markdown to LaTeX pipeline."""
        markdown = """## Results

The performance metrics are shown in @table:metrics.

Additional details are available in @stable:extended-analysis."""
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Check that table references are converted
        assert r"Table \ref{table:metrics}" in result
        assert r"Table \ref{stable:extended-analysis}" in result

        # Check that other markdown is still converted
        assert r"\subsection{Results}" in result


class TestSectionExtraction:
    """Test section extraction from markdown."""

    def test_map_section_titles(self):
        """Test mapping of section titles to keys."""
        assert map_section_title_to_key("Abstract") == "abstract"
        assert map_section_title_to_key("Methods") == "methods"
        assert map_section_title_to_key("Results and Discussion") == "results_and_discussion"
        assert map_section_title_to_key("Acknowledgements") == "acknowledgements"

    def test_extract_sections_with_yaml(self, temp_dir, sample_markdown):
        """Test extraction of sections from markdown with YAML frontmatter."""
        markdown_file = temp_dir / "test.md"
        markdown_file.write_text(sample_markdown)

        sections = extract_content_sections(str(markdown_file))

        assert "main" in sections
        assert "methods" in sections
        assert "results" in sections
        # Check that YAML frontmatter is removed
        assert "---" not in sections["main"]


class TestHTMLCommentConversion:
    """Test HTML comment conversion."""

    def test_html_comment_to_latex(self):
        """Test conversion of HTML comments to LaTeX comments."""
        html = "<!-- This is a comment\nwith multiple lines -->"
        result = convert_html_comments_to_latex(html)
        expected = "% This is a comment\n% with multiple lines"
        assert result == expected


class TestURLEscaping:
    """Test URL escaping for LaTeX."""

    def test_escape_hash_in_url(self):
        """Test escaping of hash symbols in URLs."""
        url = "https://example.com/page#section"
        expected = "https://example.com/page\\#section"
        result = escape_url_for_latex(url)
        assert result == expected

    def test_escape_percent_in_url(self):
        """Test escaping of percent symbols in URLs."""
        url = "https://example.com/page%20with%20spaces"
        expected = "https://example.com/page\\%20with\\%20spaces"
        result = escape_url_for_latex(url)
        assert result == expected


class TestListConversion:
    """Test markdown list conversion to LaTeX."""

    def test_convert_unordered_list(self):
        """Test conversion of unordered lists with dash bullets."""
        markdown = "- First item\n- Second item\n- Third item"
        expected = "\\begin{itemize}\n  \\item First item\n  \\item Second item\n  \\item Third item\n\\end{itemize}"
        result = convert_lists_to_latex(markdown)
        assert expected in result

    def test_convert_unordered_list_asterisk(self):
        """Test conversion of unordered lists with asterisk bullets."""
        markdown = "* First item\n* Second item\n* Third item"
        expected = "\\begin{itemize}\n  \\item First item\n  \\item Second item\n  \\item Third item\n\\end{itemize}"
        result = convert_lists_to_latex(markdown)
        assert expected in result

    def test_convert_ordered_list(self):
        """Test conversion of ordered lists."""
        markdown = "1. First item\n2. Second item\n3. Third item"
        expected = (
            "\\begin{enumerate}\n  \\item First item\n  \\item Second item\n  \\item Third item\n\\end{enumerate}"
        )
        result = convert_lists_to_latex(markdown)
        assert expected in result

    def test_convert_ordered_list_parentheses(self):
        """Test conversion of ordered lists with parentheses."""
        markdown = "1) First item\n2) Second item\n3) Third item"
        expected = (
            "\\begin{enumerate}\n  \\item First item\n  \\item Second item\n  \\item Third item\n\\end{enumerate}"
        )
        result = convert_lists_to_latex(markdown)
        assert expected in result

    def test_mixed_list_content(self):
        """Test lists with mixed content including formatting."""
        markdown = "- **Bold item**\n- *Italic item*\n- `Code item`"
        result = convert_lists_to_latex(markdown)
        assert "\\begin{itemize}" in result
        assert "\\item **Bold item**" in result
        assert "\\item *Italic item*" in result
        assert "\\item `Code item`" in result
        assert "\\end{itemize}" in result


class TestCodeBlockConversion:
    """Test markdown code block conversion to LaTeX."""

    def test_convert_fenced_code_block(self):
        """Test conversion of fenced code blocks."""
        markdown = "```\nprint('Hello, world!')\nprint('Second line')\n```"
        expected = "\\begin{verbatim}\nprint('Hello, world!')\nprint('Second line')\n\\end{verbatim}"
        result = convert_code_blocks_to_latex(markdown)
        assert expected in result

    def test_convert_fenced_code_block_with_language(self):
        """Test conversion of fenced code blocks with language specification."""
        markdown = "```python\nprint('Hello, world!')\nprint('Second line')\n```"
        expected = (
            "\\begin{lstlisting}[style=arxivstyle,language=python]\n"
            "print('Hello, world!')\n"
            "print('Second line')\n\\end{lstlisting}"
        )
        result = convert_code_blocks_to_latex(markdown)
        assert expected in result

    def test_convert_indented_code_block(self):
        """Test conversion of indented code blocks."""
        markdown = "    print('Hello, world!')\n    print('Second line')"
        expected = "\\begin{verbatim}\nprint('Hello, world!')\nprint('Second line')\n\\end{verbatim}"
        result = convert_code_blocks_to_latex(markdown)
        assert expected in result

    def test_preserve_code_content(self):
        """Test that code block content is preserved exactly."""
        markdown = "```\nfunction test() {\n    return 'Hello & World';\n}\n```"
        result = convert_code_blocks_to_latex(markdown)
        assert "function test() {" in result
        assert "    return 'Hello & World';" in result
        assert "}" in result


class TestIntegratedConversion:
    """Test integrated markdown to LaTeX conversion with lists and code blocks."""

    def test_full_markdown_with_lists_and_code(self):
        """Test complete markdown conversion including lists and code blocks."""
        markdown = """# Title

Here are some features:

- **Bold feature**
- *Italic feature*
- Regular feature

And some code:

```python
def hello():
    print("Hello, world!")
```

Numbered steps:

1. First step
2. Second step
3. Third step
"""
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Check that all elements are converted
        assert "\\section{Title}" in result
        assert "\\begin{itemize}" in result
        assert "\\end{itemize}" in result
        assert "\\begin{enumerate}" in result
        assert "\\end{enumerate}" in result
        assert "\\begin{lstlisting}[style=arxivstyle,language=python]" in result
        assert "\\end{lstlisting}" in result
        assert "def hello():" in result


class TestTableRotation:
    """Test table rotation functionality."""

    def test_table_with_rotation_90_degrees(self):
        """Test table with 90-degree rotation."""
        markdown_input = """| Element | LaTeX | Description |
|---------|-------|-------------|
| **bold** | \\textbf{bold} | Bold text |
| *italic* | \\textit{italic} | Italic text |

{#stable:syntax rotate=90} **Syntax Table.** Rotated markdown syntax reference.
"""

        result = convert_tables_to_latex(markdown_input)

        # Should wrap table content in rotatebox
        assert "\\rotatebox{90}{%" in result
        assert "}%" in result

        # Should maintain table structure
        assert "\\begin{table}[ht]" in result
        assert "\\begin{tabular}" in result
        assert "Element & LaTeX & Description" in result

        # Should have correct label
        assert "\\label{stable:syntax}" in result

    def test_table_without_rotation(self):
        """Test table without rotation attribute."""
        markdown_input = """| Element | LaTeX |
|---------|-------|
| **bold** | \\textbf{bold} |

{#stable:normal} **Normal Table.** Standard table without rotation.
"""

        result = convert_tables_to_latex(markdown_input)

        # Should NOT contain rotatebox
        assert "\\rotatebox" not in result

        # Should still have proper table structure
        assert "\\begin{table}[ht]" in result
        assert "\\begin{tabular}" in result


class TestTableFormattingConversion:
    """Test table markdown formatting conversion."""

    def test_bold_table_headers(self):
        """Test that **bold** headers are converted to \\textbf{} in tables."""
        markdown_input = """| **Header 1** | **Header 2** | Normal Header |
|--------------|--------------|---------------|
| Regular text | **bold text** | *italic text* |

{#table:formatting} **Test Table.** Table with formatted headers and content.
"""

        result = convert_tables_to_latex(markdown_input)

        # Check that headers are bold
        assert "\\textbf{Header 1}" in result
        assert "\\textbf{Header 2}" in result
        assert "Normal Header" in result  # Should remain normal

        # Check that content formatting works
        assert "\\textbf{bold text}" in result
        assert "\\textit{italic text}" in result

        # Should have proper table structure
        assert "\\begin{table}[ht]" in result
        assert "\\begin{tabular}" in result

    def test_italic_table_content(self):
        """Test that *italic* content is converted to \\textit{} in tables."""
        markdown_input = """| Column 1 | Column 2 |
|----------|----------|
| *italic* | regular |

{#table:italic} **Italic Test.** Table with italic content.
"""

        result = convert_tables_to_latex(markdown_input)

        # Check that italic is converted
        assert "\\textit{italic}" in result
        assert "regular" in result


class TestNoAutomaticNewpage:
    """Test that automatic newpage insertion has been removed."""

    def test_supplementary_table_no_automatic_newpage(self) -> None:
        """Test that tables in supplementary content don't get automatic \\newpage."""
        markdown = """# Supplementary Information

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

{#stable:test} **Test supplementary table.**
"""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)
        assert "\\end{table}" in result
        # Should not contain automatic newpage
        assert "\\newpage" not in result

    def test_supplementary_figure_no_automatic_newpage(self) -> None:
        """Test that figures in supplementary content don't get automatic \\newpage."""
        markdown = """# Supplementary Information

![Test Figure](FIGURES/test.png)
{#sfig:test} **Test supplementary figure.**
"""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)
        assert "\\end{figure}" in result
        # Should not contain automatic newpage
        assert "\\newpage" not in result

    def test_explicit_newpage_still_works(self) -> None:
        """Test that explicit <newpage> markers still work."""
        markdown = """# Regular Section

Some content

<newpage>

More content after page break"""
        result = convert_markdown_to_latex(markdown, is_supplementary=False)
        # Should contain the explicit newpage
        assert "\\newpage" in result


class TestCodeBlockProtection:
    """Test that content inside code blocks is not converted to LaTeX."""

    def test_fenced_code_block_protection(self) -> None:
        """Test that markdown inside fenced code blocks is not converted."""
        markdown = """Here is some regular text with **bold**.

```yaml
title: "Test Document"
authors:
  - name: "Test Author"
    email: "test@example.com"
keywords: ["test", "example"]
```

And some more text with @citation."""

        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Check that regular markdown outside code blocks is converted
        assert "\\textbf{bold}" in result
        assert "\\cite{citation}" in result

        # Check that content inside code blocks is NOT converted
        assert "\\begin{lstlisting}[style=arxivstyle,language=yaml]" in result
        assert "\\end{lstlisting}" in result
        # The YAML should be preserved exactly as-is within lstlisting
        assert 'title: "Test Document"' in result
        assert '  - name: "Test Author"' in result
        assert '    email: "test@example.com"' in result

        # Make sure no LaTeX conversion happened inside the code block
        lst_sections = re.findall(
            r"\\begin\{lstlisting\}\[style=arxivstyle,language=yaml\](.*?)\\end\{lstlisting\}",
            result,
            re.DOTALL,
        )
        assert len(lst_sections) == 1
        lst_content = lst_sections[0]

        # These should NOT be in the lstlisting content (no conversion should happen)
        assert "\\textbf{" not in lst_content
        assert "\\cite{" not in lst_content
        assert "\\begin{itemize}" not in lst_content

    def test_code_block_with_markdown_syntax(self) -> None:
        """Test that markdown syntax inside code blocks is preserved."""
        markdown = """
```markdown
## Header
**Bold text** and *italic text*
- List item 1
- List item 2
[@citation1;@citation2]
![Figure](image.png){#fig:test}
```
"""

        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should contain lstlisting environment for markdown
        assert "\\begin{lstlisting}[style=arxivstyle,language=markdown]" in result
        assert "\\end{lstlisting}" in result

        # Extract lstlisting content
        lst_sections = re.findall(
            r"\\begin\{lstlisting\}\[style=arxivstyle,language=markdown\](.*?)\\end\{lstlisting\}",
            result,
            re.DOTALL,
        )
        assert len(lst_sections) == 1
        lst_content = lst_sections[0].strip()

        # Markdown syntax should be preserved exactly
        assert "## Header" in lst_content
        assert "**Bold text**" in lst_content
        assert "*italic text*" in lst_content
        assert "- List item 1" in lst_content
        assert "[@citation1;@citation2]" in lst_content
        assert "![Figure](image.png){#fig:test}" in lst_content

        # Should NOT be converted to LaTeX
        assert "\\subsection{" not in lst_content
        assert "\\textbf{" not in lst_content
        assert "\\textit{" not in lst_content
        assert "\\begin{itemize}" not in lst_content
        assert "\\cite{" not in lst_content
        assert "\\begin{figure}" not in lst_content

    def test_code_block_with_bibtex_syntax(self) -> None:
        """Test that BibTeX syntax inside code blocks is preserved."""
        markdown = """
```bibtex
@article{test2023,
  title={Test Article},
  author={Test Author},
  journal={Test Journal},
  year={2023}
}
```
"""

        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should contain lstlisting environment for bibtex
        assert "\\begin{lstlisting}[style=arxivstyle,language=bibtex]" in result
        assert "\\end{lstlisting}" in result

        # Extract lstlisting content
        lst_sections = re.findall(
            r"\\begin\{lstlisting\}\[style=arxivstyle,language=bibtex\](.*?)\\end\{lstlisting\}",
            result,
            re.DOTALL,
        )
        assert len(lst_sections) == 1
        lst_content = lst_sections[0].strip()

        # BibTeX syntax should be preserved exactly
        assert "@article{test2023," in lst_content
        assert "title={Test Article}," in lst_content
        assert "author={Test Author}," in lst_content

        # Should NOT be converted (e.g., @ shouldn't become \cite{})
        assert "\\cite{" not in lst_content


class TestSupplementaryNoteIntegration:
    """Test supplementary note integration with the main conversion pipeline."""

    def test_supplementary_note_conversion_basic(self):
        """Test basic supplementary note conversion."""
        markdown = "{#snote:test-id} **Test Supplementary Note.**"
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        assert "\\suppnotesection{Test Supplementary Note.}\\label{snote:test-id}" in result
        assert "\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}" in result

    def test_supplementary_note_with_reference(self):
        """Test supplementary note with reference."""
        markdown = """{#snote:method} **Detailed Methods.**

See @snote:method for implementation details."""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        assert "\\suppnotesection{Detailed Methods.}\\label{snote:method}" in result
        assert "\\ref{snote:method}" in result

    def test_multiple_supplementary_notes_in_pipeline(self):
        """Test multiple supplementary notes in the conversion pipeline."""
        markdown = """{#snote:first} **First Note.**

Content of first note.

{#snote:second} **Second Note.**

Content of second note with reference to @snote:first."""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        assert "\\suppnotesection{First Note.}\\label{snote:first}" in result
        assert "\\suppnotesection{Second Note.}\\label{snote:second}" in result
        assert "\\ref{snote:first}" in result
        # Should only have one renewcommand setup
        assert result.count("\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}") == 1

    def test_supplementary_note_with_text_formatting(self):
        """Test that supplementary notes work with text formatting."""
        markdown = """{#snote:format} **Note with simple formatting.**

This note has **bold text** and *italic text* in the content."""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        # The title should be in the subsection
        assert "\\suppnotesection{Note with simple formatting.}" in result
        # The content should have formatting converted
        assert "\\textbf{bold text}" in result
        assert "\\textit{italic text}" in result


class TestSubscriptSuperscriptFormatting:
    """Test subscript and superscript formatting conversion."""

    def test_subscript_conversion(self) -> None:
        """Test that subscript markdown is converted to LaTeX."""
        markdown = "Water is H~2~O and carbon dioxide is CO~2~."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should convert subscript syntax
        assert "H\\textsubscript{2}O" in result
        assert "CO\\textsubscript{2}" in result
        # Should not contain original markdown syntax
        assert "H~2~O" not in result
        assert "CO~2~" not in result

    def test_superscript_conversion(self) -> None:
        """Test that superscript markdown is converted to LaTeX."""
        markdown = "Einstein's famous equation is E=mc^2^ and x^n^ is a power."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should convert superscript syntax
        assert "E=mc\\textsuperscript{2}" in result
        assert "x\\textsuperscript{n}" in result
        # Should not contain original markdown syntax
        assert "mc^2^" not in result
        assert "x^n^" not in result

    def test_mixed_subscript_superscript(self) -> None:
        """Test that mixed subscript and superscript work together."""
        markdown = "The isotope U~235~ has a half-life of 7.04×10^8^ years."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should convert both subscript and superscript
        assert "U\\textsubscript{235}" in result
        assert "10\\textsuperscript{8}" in result
        # Should not contain original markdown syntax
        assert "U~235~" not in result
        assert "10^8^" not in result

    def test_subscript_superscript_with_bold_italic(self) -> None:
        """Test that subscript/superscript work with bold and italic."""
        markdown = "The **bold H~2~O** and *italic x^2^* formatting should work."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should convert all formatting
        assert "\\textbf{bold H\\textsubscript{2}O}" in result
        assert "\\textit{italic x\\textsuperscript{2}}" in result

    def test_subscript_superscript_in_code_spans_not_converted(self) -> None:
        """Test that subscript/superscript in code spans are not converted."""
        markdown = "The code `H~2~O` and `x^2^` should remain unchanged."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should contain code spans with original syntax
        assert "\\texttt{H~2~O}" in result
        assert "\\texttt{x^2^}" in result
        # Should not be converted to LaTeX formatting
        assert "\\textsubscript{2}" not in result
        assert "\\textsuperscript{2}" not in result

    def test_scientific_notation_formatting(self) -> None:
        """Test common scientific notation patterns."""
        markdown = "Avogadro's number is 6.022×10^23^ mol^-1^."
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Should convert scientific notation
        assert "10\\textsuperscript{23}" in result
        assert "mol\\textsuperscript{-1}" in result

    def test_supplementary_note_with_code_blocks(self):
        """Test supplementary notes with code blocks."""
        markdown = """{#snote:code} **Code Example.**

Here's a code example:

```python
def example():
    return "test"
```

End of note."""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        assert "\\suppnotesection{Code Example.}\\label{snote:code}" in result
        assert "\\begin{lstlisting}[style=arxivstyle,language=python]" in result
        assert "def example():" in result

    def test_supplementary_note_with_citations(self):
        """Test supplementary notes with citations."""
        markdown = """{#snote:refs} **References Discussion.**

This note discusses @author2023 and [@multiple2023;@refs2023]."""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        assert "\\suppnotesection{References Discussion.}\\label{snote:refs}" in result
        assert "\\cite{author2023}" in result
        assert "\\cite{multiple2023,refs2023}" in result

    def test_supplementary_note_with_figures(self):
        """Test supplementary notes with figure references."""
        markdown = """{#snote:figs} **Figure Discussion.**

This note discusses @fig:test and @sfig:supp-figure."""
        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        assert "\\suppnotesection{Figure Discussion.}\\label{snote:figs}" in result
        assert "Fig. \\ref{fig:test}" in result
        assert "Fig. \\ref{sfig:supp-figure}" in result

    def test_supplementary_note_in_regular_content(self):
        """Test that supplementary notes are only processed in supplementary content."""
        markdown = """{#snote:main} **Note in Main Text.**

This is a supplementary note in the main document."""
        result = convert_markdown_to_latex(markdown, is_supplementary=False)

        # Supplementary notes should NOT be processed in regular content
        assert "{#snote:main}" in result
        assert "\\subsection*{Note in Main Text.}" not in result
        # But text formatting should still work
        assert "\\textbf{Note in Main Text.}" in result

    def test_supplementary_note_edge_cases(self):
        """Test edge cases for supplementary notes."""
        # Test with minimal content
        markdown1 = "{#snote:minimal} **Min.**"
        result1 = convert_markdown_to_latex(markdown1, is_supplementary=True)
        assert "\\suppnotesection{Min.}\\label{snote:minimal}" in result1

        # Test with special characters in ID
        markdown2 = "{#snote:test-id_with.dots} **Special ID.**"
        result2 = convert_markdown_to_latex(markdown2, is_supplementary=True)
        assert "\\label{snote:test-id_with.dots}" in result2

        # Test with long title
        long_title = "Very Long Title That Spans Multiple Words And Tests Title Handling"
        markdown3 = f"{{#snote:long}} **{long_title}.**"
        result3 = convert_markdown_to_latex(markdown3, is_supplementary=True)
        assert f"\\suppnotesection{{{long_title}.}}" in result3

    def test_supplementary_note_complex_document(self):
        """Test supplementary notes in a complex document structure."""
        markdown = """# Main Document

This document has a reference to @snote:detailed.

## Methods

Standard methods here.

# Supplementary Information

{#snote:detailed} **Detailed Analysis Methods.**

This note provides detailed methods used in the analysis.

### Subsection in Note

This is a subsection within the supplementary note.

{#snote:implementation} **Implementation Details.**

Technical implementation details with code:

```bash
make build
```

And references to @snote:detailed and @fig:example."""

        result = convert_markdown_to_latex(markdown, is_supplementary=True)

        # Verify headers are converted (first header uses \section* in supplementary)
        assert "\\section*{Main Document}" in result
        assert "\\subsection{Methods}" in result
        assert "\\section{Supplementary Information}" in result
        # ### headers are not converted in supplementary content
        # (handled by supplementary note processor)
        assert "\\subsubsection{Subsection in Note}" in result

        # Verify supplementary notes are processed
        assert "\\suppnotesection{Detailed Analysis Methods.}\\label{snote:detailed}" in result
        assert "\\suppnotesection{Implementation Details.}\\label{snote:implementation}" in result

        # Verify references are processed
        assert "\\ref{snote:detailed}" in result
        assert "Fig. \\ref{fig:example}" in result

        # Verify code blocks are processed
        assert "\\begin{lstlisting}[style=arxivstyle,language=bash]" in result
        assert "make build" in result


class TestCompleteFormatter:
    """Test complete formatting through the whole pipeline."""

    def test_bold_and_italic_in_list_items(self):
        """Test that bold and italic formatting works correctly in list items."""
        markdown = "- **Bold Processing**: Test description\n- *Italic Processing*: Another test"
        result = convert_markdown_to_latex(markdown)

        assert "\\begin{itemize}" in result
        assert "\\item \\textbf{Bold Processing}: Test description" in result
        assert "\\item \\textit{Italic Processing}: Another test" in result
        assert "\\end{itemize}" in result

    def test_italic_in_list_items(self):
        """Test that italic formatting works correctly in list items."""
        markdown = "- *Citation Processing*: Test description\n- *Figure Processing*: Another test"
        result = convert_markdown_to_latex(markdown)

        assert "\\begin{itemize}" in result
        assert "\\item \\textit{Citation Processing}: Test description" in result
        assert "\\item \\textit{Figure Processing}: Another test" in result
        assert "\\end{itemize}" in result
