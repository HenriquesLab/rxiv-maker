"""Unit tests for separate main/SI bibliographies in --split-si builds.

These cover the template-processing layer (no LaTeX toolchain needed): with
``split_si=True`` the document is wrapped in two ``bibunits`` units so the main body
and the SI each get their own reference list numbered from 1. The non-split path must
stay byte-for-byte the same single-bibliography document.
"""

from rxiv_maker.processors.template_processor import (
    get_template_path,
    process_template_replacements,
)

META = {"title": "T", "bibliography": "03_REFERENCES", "citation_style": "numbered"}


def _render(split_si):
    template = get_template_path().read_text(encoding="utf-8")
    return process_template_replacements(template, META, "/dev/null", output_dir=None, split_si=split_si)


def test_split_si_wraps_main_and_supplement_in_bibunits():
    out = _render(split_si=True)
    assert "\\usepackage{bibunits}" in out
    assert out.count("\\begin{bibunit}") == 2  # main + SI
    assert out.count("\\end{bibunit}") == 2
    assert out.count("\\putbib") == 2  # one reference list each
    assert "\\section*{Supplementary References}" in out
    # the single shared \bibliography command is gone, no placeholders leak
    assert "\\bibliography{03_REFERENCES}" not in out
    assert "<PY-RPL:BIBUNIT" not in out and "<PY-RPL:BIBUNITS" not in out


def test_combined_build_keeps_single_bibliography():
    out = _render(split_si=False)
    assert "\\bibliography{03_REFERENCES}" in out
    # no bibunits machinery in a normal build
    assert "\\usepackage{bibunits}" not in out
    assert "\\begin{bibunit}" not in out
    assert "\\putbib" not in out
    assert "<PY-RPL:BIBUNIT" not in out and "<PY-RPL:BIBUNITS" not in out
