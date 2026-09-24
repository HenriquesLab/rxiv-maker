"""Unit tests for figure legend continuation functionality (Issue #324)."""

from rxiv_maker.converters.figure_processor import (
    convert_figures_to_latex,
    create_latex_figure_environment,
    extract_continued_caption,
)
from rxiv_maker.exporters.docx_content_processor import DocxContentProcessor


class TestExtractContinuedCaption:
    """Test extract_continued_caption helper."""

    def test_no_continuation(self):
        caption = "**Figure Title.** Caption text describing panels A and B."
        main, cont, hdr = extract_continued_caption(caption)
        assert main == caption
        assert cont is None
        assert hdr == "(Continued from previous page.)"

    def test_basic_continuation_separator(self):
        caption = (
            "**Figure Title.**\n\n(**A**) Panel A details.\n\n---continued---\n\n(**B**) Panel B details on next page."
        )
        main, cont, hdr = extract_continued_caption(caption)
        assert "**Figure Title.**" in main
        assert "(**A**) Panel A details." in main
        assert cont == "(**B**) Panel B details on next page."
        assert hdr == "(Continued from previous page.)"

    def test_custom_continuation_header(self):
        caption = "**Figure Title.** Panel A text.\n---continued: (Continued from page 1)---\nPanel B text on page 2."
        main, cont, hdr = extract_continued_caption(caption)
        assert main == "**Figure Title.** Panel A text."
        assert cont == "Panel B text on page 2."
        assert hdr == "(Continued from page 1)"


class TestCreateLatexFigureEnvironmentContinuation:
    """Test LaTeX generation with figure legend continuation."""

    def test_create_latex_environment_with_continuation(self):
        latex = create_latex_figure_environment(
            path="FIGURES/Fig1.png",
            caption="**Title.** Main caption text.",
            attributes={"id": "fig:test", "tex_position": "p"},
            continued_caption="(**E--H**) Continued legend text on next page.",
            continued_header="(Continued from previous page.)",
        )
        # Main figure environment checks
        assert r"\begin{figure*}[p!]" in latex
        assert r"\caption{\textbf{Title.} Main caption text.}" in latex
        assert r"\label{fig:test}" in latex
        assert r"\end{figure*}" in latex

        # Continuation figure environment checks
        assert r"\begin{figure*}[t!]" in latex
        assert r"\ContinuedFloat" in latex
        assert (
            r"\caption[]{\textbf{(Continued from previous page.)} (\textbf{E--H}) Continued legend text on next page.}"
            in latex
        )

    def test_convert_figures_to_latex_with_continued_separator(self):
        markdown = (
            "![](FIGURES/Figure1.png)\n"
            '{#fig:cell-migration width="0.70" tex_position="p"} **Cell migration is regulated by matrix organisation.**\n\n'
            "(**A**) Overview of the experimental workflow.\n\n"
            "---continued---\n\n"
            "(**E--H**) Time-lapse imaging and analysis of protrusion dynamics.\n\n"
            "## Next Section"
        )
        result = convert_figures_to_latex(markdown)

        assert r"\begin{figure*}" in result
        assert r"\label{fig:cell-migration}" in result
        assert r"\ContinuedFloat" in result
        assert (
            r"\caption[]{\textbf{(Continued from previous page.)} (\textbf{E--H}) Time-lapse imaging and analysis of protrusion dynamics.}"
            in result
        )


class TestAttributeContinuedCaption:
    """Test attribute block specifying continued_caption."""

    def test_attribute_continued_caption(self):
        markdown = (
            "![](FIGURES/Figure1.png)\n"
            '{#fig:attr-test width="0.8" continued_caption="(**C**) Extra details on next page."} **Main title.** Panel A details.'
        )
        result = convert_figures_to_latex(markdown)

        assert r"\begin{figure}" in result or r"\begin{figure*}" in result
        assert r"\ContinuedFloat" in result
        assert "Extra details on next page." in result


class TestDocxContentProcessorContinuation:
    """Test DOCX content processor parsing of continued captions."""

    def test_parse_figure_with_continued_caption(self):
        lines = [
            "![](FIGURES/Fig1.png)",
            '{#fig:cell-migration width="0.7"} **Cell migration.**',
            "",
            "(**A**) Overview.",
            "",
            "---continued---",
            "",
            "(**E**) Time-lapse.",
            "",
            "## Section Title",
        ]
        processor = DocxContentProcessor()
        doc_structure = processor.parse("\n".join(lines), {})

        fig_sections = [s for s in doc_structure["sections"] if s.get("type") == "figure"]
        assert len(fig_sections) == 1
        fig = fig_sections[0]

        assert "**Cell migration.**" in fig["caption"]
        assert "(**A**) Overview." in fig["caption"]
        assert fig["continued_caption"] == "(**E**) Time-lapse."
        assert fig["continued_header"] == "(Continued from previous page.)"
