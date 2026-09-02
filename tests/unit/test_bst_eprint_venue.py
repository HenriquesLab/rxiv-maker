"""Regression test: the bibliography style must render the arXiv venue.

Google Scholar clusters a reference to a target record using the venue token
and identifier. A reference printed as bare title/author/year is the weakest
form to match, so dropping `eprint` silently costs citations.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

BST = Path(__file__).parents[2] / "src" / "tex" / "style" / "rxiv_maker_style.bst"

BIB = """\
@misc{with_eprint,
      title={A preprint with an eprint field},
      author={Bruno M. Saraiva and Ricardo Henriques},
      year={2025},
      eprint={2508.00836},
      archivePrefix={arXiv},
      doi={10.48550/arXiv.2508.00836},
}

@misc{without_eprint,
      title={A misc entry with no eprint field},
      author={Jane Doe},
      year={2024},
}
"""

AUX = """\
\\relax
\\citation{with_eprint}
\\citation{without_eprint}
\\bibstyle{rxiv_maker_style}
\\bibdata{refs}
"""


def test_bst_declares_eprint_fields():
    """ENTRY must declare eprint and archiveprefix, else BibTeX ignores them."""
    text = BST.read_text(encoding="utf-8")
    assert "eprint" in text, "bst lost its eprint field declaration"
    assert "archiveprefix" in text
    assert "format.eprint output" in text, "misc entry no longer emits the venue"


@pytest.mark.skipif(shutil.which("bibtex") is None, reason="bibtex not installed")
def test_bst_eprint_venue(tmp_path):
    """A cited @misc with eprint must print an arXiv venue token."""
    shutil.copy(BST, tmp_path / BST.name)
    (tmp_path / "refs.bib").write_text(BIB, encoding="utf-8")
    (tmp_path / "test.aux").write_text(AUX, encoding="utf-8")

    subprocess.run(["bibtex", "test"], cwd=tmp_path, check=True, capture_output=True)
    bbl = (tmp_path / "test.bbl").read_text(encoding="utf-8")

    assert "arXiv:2508.00836" in bbl
    # An entry without eprint must stay clean, with no stray separator.
    assert "arXiv:" not in bbl.split("without_eprint")[-1]
