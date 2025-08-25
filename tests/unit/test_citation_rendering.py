"""Unit tests for citation rendering in PDF output."""

import re
import subprocess
from pathlib import Path

import pytest


def has_latex():
    """Check if LaTeX is available."""
    try:
        result = subprocess.run(["pdflatex", "--version"], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


requires_latex = pytest.mark.skipif(not has_latex(), reason="LaTeX not installed")


class TestCitationRendering:
    """Test that citations are properly rendered in the final PDF."""

    @pytest.mark.medium
    @requires_latex
    def test_bibtex_processing(self, tmp_path):
        """Test that BibTeX processing works correctly."""
        # Create a minimal manuscript with citations
        manuscript_dir = tmp_path / "test_manuscript"
        manuscript_dir.mkdir()

        # Create config file
        config_content = """
title: "Test Citation Rendering"
short_title: "Test Citations"
authors:
  - name: "Test Author"
    email: "test@example.com"
    affiliations: [1]
affiliations:
  1: "Test University"
abstract: "Testing citation rendering."
"""
        (manuscript_dir / "00_CONFIG.yml").write_text(config_content)

        # Create main document with various citation formats
        main_content = """# Introduction

This is a test of citation rendering. Single citation: @test2023.
Multiple citations: [@test2023;@another2023].
Citation in parentheses: [@test2023].
Multiple authors citation: [@smith2023;@jones2023;@brown2023].

# Methods

More text with citations @test2023 and @another2023.
"""
        (manuscript_dir / "01_MAIN.md").write_text(main_content)

        # Create bibliography
        bib_content = """@article{test2023,
    title = {Test Article},
    author = {Test Author},
    journal = {Test Journal},
    year = {2023},
    volume = {1},
    pages = {1--10}
}

@article{another2023,
    title = {Another Test Article},
    author = {Another Author},
    journal = {Another Journal},
    year = {2023},
    volume = {2},
    pages = {20--30}
}

@article{smith2023,
    title = {Smith Article},
    author = {Smith, John},
    journal = {Smith Journal},
    year = {2023}
}

@article{jones2023,
    title = {Jones Article},
    author = {Jones, Mary},
    journal = {Jones Journal},
    year = {2023}
}

@article{brown2023,
    title = {Brown Article},
    author = {Brown, David},
    journal = {Brown Journal},
    year = {2023}
}
"""
        (manuscript_dir / "03_REFERENCES.bib").write_text(bib_content)

        # Generate LaTeX using the actual system
        from rxiv_maker.engines.operations.build_manager import BuildManager

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Run the build
        build_manager = BuildManager(manuscript_path=str(manuscript_dir), output_dir=str(output_dir))

        # Run partial build to generate LaTeX
        assert build_manager.copy_style_files()
        assert build_manager.copy_references()
        assert build_manager.generate_tex_files()

        # Check that LaTeX file contains proper bibliography commands
        tex_path = output_dir / "test_manuscript.tex"
        assert tex_path.exists(), "LaTeX file was not generated"

        tex_content = tex_path.read_text()

        # Check for bibliography command
        assert r"\bibliography{03_REFERENCES}" in tex_content, "Bibliography command not found in LaTeX"

        # Check that citations were converted properly
        assert r"\cite{test2023}" in tex_content, "Single citation not converted properly"
        assert r"\cite{test2023,another2023}" in tex_content, "Multiple citations not converted properly"
        assert r"\cite{smith2023,jones2023,brown2023}" in tex_content, (
            "Multiple author citations not converted properly"
        )

        # Run compilation to test bibtex processing
        assert build_manager.compile_pdf()

        # Check that .bbl file was created
        bbl_path = output_dir / "test_manuscript.bbl"
        assert bbl_path.exists(), "BibTeX did not generate .bbl file"

        # Check that .bbl contains the citations
        bbl_content = bbl_path.read_text()
        assert "test2023" in bbl_content, "Citation test2023 not in bibliography"
        assert "another2023" in bbl_content, "Citation another2023 not in bibliography"

        # Check aux file for proper citations
        aux_path = output_dir / "test_manuscript.aux"
        assert aux_path.exists(), "Auxiliary file not generated"

        aux_content = aux_path.read_text()
        assert r"\citation{test2023}" in aux_content, "Citation not found in aux file"
        assert r"\bibdata{03_REFERENCES}" in aux_content, "Bibliography data not set in aux file"

    def test_citation_in_generated_tex(self, tmp_path):
        """Test that citations are properly converted in the LaTeX file."""
        from rxiv_maker.converters.citation_processor import convert_citations_to_latex

        # Test various citation formats
        test_cases = [
            ("Single citation: @test2023.", r"Single citation: \cite{test2023}."),
            (
                "Multiple: [@test2023;@another2023].",
                r"Multiple: \cite{test2023,another2023}.",
            ),
            ("In text @citation_key here.", r"In text \cite{citation_key} here."),
        ]

        for input_text, expected in test_cases:
            result = convert_citations_to_latex(input_text)
            assert result == expected, f"Expected '{expected}', got '{result}'"


class TestCitationProcessingIntegration:
    """Integration tests for the full citation processing pipeline."""

    def test_example_manuscript_citations_resolved(self):
        """Test that EXAMPLE_MANUSCRIPT citations are properly resolved."""
        # This test checks that the build process properly resolves citations
        example_manuscript_path = Path("EXAMPLE_MANUSCRIPT")
        if not example_manuscript_path.exists():
            pytest.skip("EXAMPLE_MANUSCRIPT not found")

        # Check that the bibliography file has all needed entries
        bib_path = example_manuscript_path / "03_REFERENCES.bib"
        assert bib_path.exists()

        bib_content = bib_path.read_text()

        # Check for specific citations that were showing as ?
        important_citations = [
            "beck2020",
            "levchenk2024",
            "Fraser2020_preprint_growth",
            "Mermaid2023_documentation",
        ]

        for citation in important_citations:
            assert "@" in bib_content and citation in bib_content, f"Citation {citation} not found in bibliography"
            # Also check it's a complete entry (has closing brace)
            pattern = rf"@\w+\{{{citation},[^@]+\}}"
            assert re.search(pattern, bib_content, re.DOTALL), f"Citation {citation} appears incomplete in bibliography"

    @pytest.mark.medium
    @requires_latex
    def test_build_process_resolves_citations(self, tmp_path):
        """Test that the full build process properly resolves citations."""
        # Create a test manuscript
        manuscript_dir = tmp_path / "test_manuscript"
        manuscript_dir.mkdir()

        # Create config file
        config_content = """
title: "Citation Resolution Test"
short_title: "Citation Test"
authors:
  - name: "Test Author"
    email: "test@example.com"
    affiliations: [1]
affiliations:
  1: "Test University"
abstract: "Testing citation resolution."
"""
        (manuscript_dir / "00_CONFIG.yml").write_text(config_content)

        # Create main document with problematic citations that were showing as ?
        main_content = """# Introduction

Modern scientific research relies on preprint servers such as arXiv, bioRxiv,
and medRxiv for rapid dissemination [@beck2020;@levchenk2024;@Fraser2020].
This system also integrates Mermaid.js [@Mermaid2023] for generating diagrams.
"""
        (manuscript_dir / "01_MAIN.md").write_text(main_content)

        # Create bibliography with the problematic citations
        bib_content = """@misc{beck2020,
    title = {Building trust in preprints: recommendations for servers},
    author = {Beck, Jeffrey and others},
    year = {2020}
}

@misc{levchenk2024,
    title = {Enabling preprint discovery, evaluation, and analysis with Europe PMC},
    author = {Levchenko, Mariia and others},
    year = {2024}
}

@article{Fraser2020,
    title = {The relationship between bioRxiv preprints, citations and altmetrics},
    author = {Fraser, Nicholas and others},
    year = {2020}
}

@misc{Mermaid2023,
    title = {Mermaid: Generation of diagrams and flowcharts},
    author = {{Mermaid Team}},
    year = {2023}
}
"""
        (manuscript_dir / "03_REFERENCES.bib").write_text(bib_content)

        # Run the full build process
        from rxiv_maker.engines.operations.build_manager import BuildManager

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        build_manager = BuildManager(manuscript_path=str(manuscript_dir), output_dir=str(output_dir))

        # Run full build
        assert build_manager.copy_style_files()
        assert build_manager.copy_references()
        assert build_manager.generate_tex_files()
        assert build_manager.compile_pdf()

        # Check that compilation was successful
        pdf_path = output_dir / "test_manuscript.pdf"
        assert pdf_path.exists(), "PDF was not generated"

        # Most importantly: check that the .aux file has \bibcite entries
        # This indicates that BibTeX ran and citations were resolved
        aux_path = output_dir / "test_manuscript.aux"
        assert aux_path.exists(), "Auxiliary file not generated"

        aux_content = aux_path.read_text()

        # Check for resolved citations (bibcite entries)
        assert r"\bibcite{beck2020}" in aux_content, (
            "Citation beck2020 not resolved - shows this would appear as ? in PDF"
        )
        assert r"\bibcite{levchenk2024}" in aux_content, (
            "Citation levchenk2024 not resolved - shows this would appear as ? in PDF"
        )
        assert r"\bibcite{Fraser2020}" in aux_content, (
            "Citation Fraser2020 not resolved - shows this would appear as ? in PDF"
        )
        assert r"\bibcite{Mermaid2023}" in aux_content, (
            "Citation Mermaid2023 not resolved - shows this would appear as ? in PDF"
        )

        # Check that .bbl file was created (proof that BibTeX ran)
        bbl_path = output_dir / "test_manuscript.bbl"
        assert bbl_path.exists(), "BibTeX did not run - this causes ? to appear instead of citations"

        # Check LaTeX log doesn't have "undefined citation" warnings
        log_path = output_dir / "test_manuscript.log"
        if log_path.exists():
            log_content = log_path.read_text()
            undefined_citations = re.findall(r"Citation.*undefined", log_content)
            assert len(undefined_citations) == 0, (
                f"Found undefined citations in log: {undefined_citations} - these appear as ? in PDF"
            )
