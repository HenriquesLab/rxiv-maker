"""Unit tests for rendering {{tex}} tables as images in DOCX export.

Covers the three pure layers of the feature:
  * the preprocessor emitting a recoverable sentinel (not a placeholder) for tables,
  * the content processor turning that sentinel into a ``tex_table`` section with
    its ``\\cite`` commands resolved to the DOCX citation numbers, and
  * the LaTeX-preparation helper that normalises a float/longtable down to a
    standalone-renderable ``tabular``.

The actual pdflatex -> png render is exercised in the integration suite (it needs
a LaTeX toolchain) and against the real manuscripts.
"""

from rxiv_maker.exporters.docx_content_processor import (
    DocxContentProcessor,
    resolve_latex_citations,
)
from rxiv_maker.exporters.docx_writer import prepare_table_latex
from rxiv_maker.processors.markdown_preprocessor import MarkdownPreprocessor
from rxiv_maker.utils.label_extractor import LabelExtractor

STABLE_BLOCK = """Intro paragraph.

{{tex:
\\begin{stable}[h!]
\\small
\\begin{tabular}{|l|l|}
\\hline
\\textbf{Feature} & \\textbf{Tool} \\\\
\\hline
Input & PDB~\\cite{smith2020} \\\\
\\hline
\\end{tabular}
\\caption{\\textbf{A comparison.}}
\\label{stable:comparison}
\\end{stable}
}}

Outro paragraph.
"""

LONGTABLE_BLOCK = """{{tex:
\\small
\\begin{longtable}{|p{0.3\\textwidth}|p{0.3\\textwidth}|}
\\hline
\\textbf{A} & \\textbf{B} \\\\
\\hline
\\endfirsthead
\\hline
\\textbf{A} & \\textbf{B} \\\\
\\hline
\\endhead
one & two \\\\
\\hline
\\end{longtable}
}}
"""

INLINE_TEX = "See `{{tex:\\alpha}}` inline.\n\nText with {{tex:\\alpha}} mention.\n"


class TestStripTexBlocksEmitsSentinel:
    def test_table_block_becomes_sentinel_not_placeholder(self):
        out = MarkdownPreprocessor().process(STABLE_BLOCK, target_format="docx")
        assert "<<TEX_TABLE_START>>" in out
        assert "<<TEX_TABLE_END>>" in out
        # the raw tabular survives for later rendering
        assert "\\begin{tabular}" in out
        # the old placeholder is gone
        assert "refer to the PDF version" not in out

    def test_longtable_block_becomes_sentinel(self):
        out = MarkdownPreprocessor().process(LONGTABLE_BLOCK, target_format="docx")
        assert "<<TEX_TABLE_START>>" in out
        assert "\\begin{longtable}" in out

    def test_inline_block_unchanged(self):
        # An inline mention must not be treated as a table.
        out = MarkdownPreprocessor().process(INLINE_TEX, target_format="docx")
        assert "<<TEX_TABLE_START>>" not in out


class TestResolveLatexCitations:
    def test_single_cite_to_number(self):
        assert resolve_latex_citations("PDB~\\cite{smith2020}", {"smith2020": 7}) == "PDB~[7]"

    def test_multi_key_cite_to_numbers(self):
        out = resolve_latex_citations("\\cite{a,b}", {"a": 3, "b": 9})
        assert out == "[3, 9]"

    def test_unknown_key_kept_verbatim(self):
        out = resolve_latex_citations("\\cite{ghost}", {"smith2020": 7})
        assert "ghost" in out and "\\cite" not in out

    def test_escaped_cite_is_not_touched(self):
        # The syntax-reference table shows "\textbackslash cite\{x\}" literally.
        text = "\\textbackslash cite\\{mycitation\\}"
        assert resolve_latex_citations(text, {"mycitation": 1}) == text


class TestPrepareTableLatex:
    def test_strips_float_and_caption(self):
        raw = STABLE_BLOCK.split("{{tex:")[1].split("}}")[0].strip()
        out = prepare_table_latex(raw)
        assert out is not None
        assert "\\begin{tabular}" in out and "\\end{tabular}" in out
        assert "\\begin{stable}" not in out
        assert "\\caption" not in out and "\\label" not in out
        # size command preserved
        assert "\\small" in out

    def test_longtable_converted_to_tabular(self):
        raw = LONGTABLE_BLOCK.split("{{tex:")[1].split("}}")[0].strip()
        out = prepare_table_latex(raw)
        assert out is not None
        assert "\\begin{tabular}" in out
        assert "longtable" not in out
        # repeated-header machinery removed
        assert "\\endhead" not in out and "\\endfirsthead" not in out
        # exactly one header row kept
        assert out.count("\\textbf{A}") == 1

    def test_plain_prose_yields_none(self):
        assert prepare_table_latex("\\textbf{just text, no table}") is None


class TestStandaloneTableCaption:
    def test_percent_caption_becomes_section(self):
        # %{#stable:label} caption (the % hides it from LaTeX) must not leak.
        parsed = DocxContentProcessor().parse("%{#stable:comparison} **Comparison of tools.**\n", {})
        caps = [s for s in parsed["sections"] if s["type"] == "table_caption"]
        assert len(caps) == 1
        assert caps[0]["label"] == "stable:comparison"
        assert "Comparison of tools" in caps[0]["caption"]

    def test_plain_caption_becomes_section(self):
        parsed = DocxContentProcessor().parse("{#stable:vm_params} **Optical parameters.**\n", {})
        caps = [s for s in parsed["sections"] if s["type"] == "table_caption"]
        assert len(caps) == 1 and caps[0]["label"] == "stable:vm_params"

    def test_caption_above_table_attaches_below(self):
        # A %{#stable:x} caption authored above a {{tex}} block is attached to the
        # tex_table (rendered below the image), not left as a standalone section.
        md = (
            "%{#stable:comparison} **Comparison of tools.**\n\n"
            "{{tex:\n\\begin{stable}[h!]\n\\begin{tabular}{|l|l|}\n\\hline\n"
            "A & B \\\\\n\\hline\n\\end{tabular}\n\\end{stable}\n}}\n"
        )
        pre = MarkdownPreprocessor().process(md, target_format="docx")
        parsed = DocxContentProcessor().parse(pre, {})
        tex = [s for s in parsed["sections"] if s["type"] == "tex_table"]
        caps = [s for s in parsed["sections"] if s["type"] == "table_caption"]
        assert len(tex) == 1
        assert tex[0]["caption_label"] == "stable:comparison"
        assert "Comparison of tools" in tex[0]["caption_text"]
        assert len(caps) == 0  # attached, not left standalone

    def test_caption_below_md_table_not_double_emitted(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n\n{#stable:t} Caption text.\n"
        parsed = DocxContentProcessor().parse(md, {})
        tables = [s for s in parsed["sections"] if s["type"] == "table"]
        caps = [s for s in parsed["sections"] if s["type"] == "table_caption"]
        # The caption is consumed by the table, not emitted as a standalone section.
        assert len(tables) == 1 and tables[0]["caption"] == "Caption text."
        assert len(caps) == 0


class TestTableLabelMerge:
    def test_mixed_label_forms_numbered_in_order(self):
        content = "{#stable:a} x\n{#stable:b} y\n\\label{stable:c}\n"
        assert LabelExtractor().extract_supplementary_table_labels(content) == {"a": 1, "b": 2, "c": 3}

    def test_same_label_in_both_forms_deduped(self):
        content = "{#stable:comp} x\n\\label{stable:comp}\n"
        assert LabelExtractor().extract_supplementary_table_labels(content) == {"comp": 1}


class TestContentProcessorTexTableSection:
    def test_sentinel_becomes_table_section_with_numbers(self):
        preprocessed = MarkdownPreprocessor().process(STABLE_BLOCK, target_format="docx")
        parsed = DocxContentProcessor().parse(preprocessed, {"smith2020": 7})
        tex_tables = [s for s in parsed["sections"] if s["type"] == "tex_table"]
        assert len(tex_tables) == 1
        latex = tex_tables[0]["latex"]
        assert "[7]" in latex
        assert "\\cite" not in latex
        # surrounding paragraphs still present, table sits between them
        types = [s["type"] for s in parsed["sections"]]
        ti = types.index("tex_table")
        assert "paragraph" in types[:ti]  # intro before
        assert "paragraph" in types[ti + 1 :]  # outro after
