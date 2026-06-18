"""Unit tests for separate main/SI bibliographies in --split-si builds.

These cover the template-processing layer (no LaTeX toolchain needed): with
``split_si=True`` the document is wrapped in two ``bibunits`` units so the main body
and the SI each get their own reference list numbered from 1. The SI list is only
printed when the SI actually cites something, and the non-split path stays a single
combined-bibliography document.
"""

from rxiv_maker.processors.template_processor import (
    _supplementary_has_citations,
    get_template_path,
    process_template_replacements,
)

META = {"title": "T", "bibliography": "03_REFERENCES", "citation_style": "numbered"}


def _render(split_si, tmp_path, si_text="Supplementary text with no citations.\n"):
    (tmp_path / "01_MAIN.md").write_text("# Main\n", encoding="utf-8")
    (tmp_path / "02_SUPPLEMENTARY_INFO.md").write_text(si_text, encoding="utf-8")
    template = get_template_path().read_text(encoding="utf-8")
    return process_template_replacements(
        template, META, str(tmp_path / "01_MAIN.md"), output_dir=None, split_si=split_si
    )


def test_split_si_with_cited_supplement(tmp_path):
    out = _render(True, tmp_path, si_text="See [@smith2020] for details.\n")
    assert "\\usepackage{bibunits}" in out
    assert out.count("\\begin{bibunit}") == 2  # main + SI
    assert out.count("\\end{bibunit}") == 2
    assert out.count("\\putbib") == 2  # one reference list each
    assert "\\section*{Supplementary References}" in out
    # the single shared \bibliography command is gone, no placeholders leak
    assert "\\bibliography{03_REFERENCES}" not in out
    assert "<PY-RPL:BIBUNIT" not in out and "<PY-RPL:BIBUNITS" not in out


def test_split_si_no_cites_omits_supplementary_refs(tmp_path):
    out = _render(True, tmp_path, si_text="Methods only, no citations here.\n")
    assert out.count("\\begin{bibunit}") == 2  # SI is still wrapped in a unit
    assert out.count("\\putbib") == 1  # only the main bibliography prints
    assert "\\section*{Supplementary References}" not in out  # no empty heading
    assert "<PY-RPL:BIBUNIT" not in out


def test_split_si_detects_raw_cite_commands(tmp_path):
    # An SI whose only citations are raw \cite{} inside a {{tex}} block still gets refs.
    out = _render(True, tmp_path, si_text="{{tex:\n\\begin{table}A~\\cite{x}\\end{table}\n}}\n")
    assert "\\section*{Supplementary References}" in out


def test_split_si_ignores_escaped_cite_display(tmp_path):
    # The escaped display form in syntax-reference tables must not count as a citation.
    out = _render(True, tmp_path, si_text="syntax example: \\textbackslash cite\\{x\\}\n")
    assert "\\section*{Supplementary References}" not in out


def test_combined_build_keeps_single_bibliography(tmp_path):
    out = _render(False, tmp_path)
    assert "\\bibliography{03_REFERENCES}" in out
    # no bibunits machinery in a normal build
    assert "\\usepackage{bibunits}" not in out
    assert "\\begin{bibunit}" not in out
    assert "\\putbib" not in out
    assert "<PY-RPL:BIBUNIT" not in out and "<PY-RPL:BIBUNITS" not in out


def test_si_citation_detection(tmp_path):
    main = str(tmp_path / "01_MAIN.md")
    (tmp_path / "02_SUPPLEMENTARY_INFO.md").write_text("uses [@key2024] here", encoding="utf-8")
    assert _supplementary_has_citations(main) is True
    (tmp_path / "02_SUPPLEMENTARY_INFO.md").write_text("no citations at all", encoding="utf-8")
    assert _supplementary_has_citations(main) is False
    # no SI file -> no SI references
    assert _supplementary_has_citations(str(tmp_path / "nonexistent" / "01_MAIN.md")) is False
