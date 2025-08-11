"""Practical integration tests for manuscript directory setup and build validation.

These tests simulate realistic user scenarios for setting up and building
manuscripts with custom directory names and PDF naming.
"""

from pathlib import Path

import pytest


@pytest.mark.xdist_group(name="practical_workflows")
class TestPracticalManuscriptWorkflow:
    """Test realistic manuscript setup and build workflows."""

    def test_new_user_manuscript_setup_workflow(self, temp_dir, monkeypatch):
        """Test complete workflow a new user would follow to set up a manuscript."""
        monkeypatch.chdir(temp_dir)

        # Scenario: A researcher wants to create a new manuscript called "ML_STUDY_2025"
        manuscript_name = "ML_STUDY_2025"

        # Step 1: User sets up environment variable
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_name)

        # Step 2: User creates the manuscript directory structure
        manuscript_dir = temp_dir / manuscript_name
        manuscript_dir.mkdir()

        # Step 3: User creates required subdirectories
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir()

        # Step 4: User creates configuration file with their metadata
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_content = """---
title:
  main: "Machine Learning Study 2025"
  lead_author: "Rodriguez"
date: "2025-06-25"
authors:
  - name: "Dr. Maria Rodriguez"
    affiliation: "University of Data Science"
    email: "m.rodriguez@uds.edu"
    orcid: "0000-0001-2345-6789"
affiliations:
  - name: "University of Data Science"
    address: "123 Data Ave, Science City, SC 12345"
keywords: ["machine learning", "data science", "algorithms"]
"""
        config_file.write_text(config_content)

        # Step 5: User creates main manuscript file
        main_file = manuscript_dir / "01_MAIN.md"
        main_content = """---
title: "Machine Learning Study 2025"
authors:
  - name: "Dr. Maria Rodriguez"
    affiliation: "University of Data Science"
---

# Introduction

This study investigates machine learning algorithms for data analysis.

## Background

Recent advances in ML have shown promise for various applications.

# Methods

We implemented several ML algorithms and compared their performance.

# Results

Our results show significant improvements in accuracy and efficiency.

# Discussion

The findings have important implications for the field.

# Conclusion

This work demonstrates the effectiveness of our approach.
"""
        main_file.write_text(main_content)

        # Step 6: User creates bibliography
        bib_file = manuscript_dir / "03_REFERENCES.bib"
        bib_content = """@article{ml2024,
  title={Machine Learning Advances},
  author={Smith, John and Jones, Jane},
  journal={ML Journal},
  volume={15},
  pages={100-120},
  year={2024}
}

@book{datascience2023,
  title={Data Science Handbook},
  author={Davis, Bob},
  publisher={Tech Press},
  year={2023}
}
"""
        bib_file.write_text(bib_content)

        # Step 7: Test that the build system can find and process the manuscript
        from rxiv_maker.utils import (
            create_output_dir,
            find_manuscript_md,
            write_manuscript_output,
        )

        # Verify manuscript is found correctly
        found_manuscript = find_manuscript_md()
        assert Path(found_manuscript).name == "01_MAIN.md"
        assert manuscript_name in str(found_manuscript)

        # Step 8: Test output directory creation (as build system would do)
        output_dir = temp_dir / "output"
        create_output_dir(str(output_dir))
        assert output_dir.exists()

        # Step 9: Test LaTeX generation with correct file naming
        # Simulate what the build system would generate
        latex_content = r"""
\documentclass[letterpaper,10pt]{article}
\usepackage[utf8]{inputenc}
\title{Machine Learning Study 2025}
\author{Dr. Maria Rodriguez}
\date{2025-06-25}

\begin{document}
\maketitle

\section{Introduction}
This study investigates machine learning algorithms.

\section{Methods}
We implemented several ML algorithms.

\section{Results}
Our results show improvements.

\section{Conclusion}
This work demonstrates effectiveness.

\bibliographystyle{plain}
\bibliography{03_REFERENCES}

\end{document}
"""

        # Test manuscript output writing
        result_tex = write_manuscript_output(str(output_dir), latex_content)

        # Verify correct naming: should be ML_STUDY_2025.tex
        expected_tex_name = f"{manuscript_name}.tex"
        assert Path(result_tex).name == expected_tex_name
        assert Path(result_tex).exists()

        # Verify content is correct
        written_content = Path(result_tex).read_text()
        assert "Machine Learning Study 2025" in written_content
        assert r"\documentclass" in written_content

        # Step 10: Test PDF naming and placement (simulate successful LaTeX compilation)
        from rxiv_maker.utils import copy_pdf_to_manuscript_folder

        # Create mock PDF (as if LaTeX compiled successfully)
        mock_pdf = output_dir / f"{manuscript_name}.pdf"
        mock_pdf.write_text("Mock PDF content - compiled LaTeX output")

        # Test custom PDF naming based on metadata
        yaml_metadata = {"date": "2025-06-25", "title": {"lead_author": "Rodriguez"}}

        copied_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Verify PDF is placed in manuscript directory with custom name
        expected_pdf_name = "2025__rodriguez_et_al__rxiv.pdf"
        expected_pdf_path = manuscript_dir / expected_pdf_name

        assert copied_pdf.resolve() == expected_pdf_path.resolve()
        assert expected_pdf_path.exists()
        assert expected_pdf_path.read_text() == "Mock PDF content - compiled LaTeX output"

        print(f"✅ Complete user workflow validated for manuscript: {manuscript_name}")
        print(f"   - LaTeX output: {result_tex}")
        print(f"   - PDF output: {expected_pdf_path}")

    def test_multiple_manuscripts_in_same_workspace(self, temp_dir, monkeypatch):
        """Test managing multiple manuscripts in the same workspace."""
        monkeypatch.chdir(temp_dir)

        # Scenario: Researcher has multiple ongoing projects
        manuscripts = [
            ("PROJECT_ALPHA", "Smith", "AI Research Project Alpha"),
            ("PROJECT_BETA", "Johnson", "Machine Learning Study Beta"),
            ("PROJECT_GAMMA", "Chen", "Data Analysis Project Gamma"),
        ]

        created_files = {}

        # Set up each manuscript
        for manuscript_path, lead_author, title in manuscripts:
            # Create directory structure
            manuscript_dir = temp_dir / manuscript_path
            manuscript_dir.mkdir()

            # Create main file
            main_file = manuscript_dir / "01_MAIN.md"
            main_content = f"""---
title: "{title}"
authors:
  - name: "Dr. {lead_author}"
---

# {title}

This is the manuscript for {manuscript_path}.
"""
            main_file.write_text(main_content)

            # Create config for PDF naming
            config_file = manuscript_dir / "00_CONFIG.yml"
            config_content = f"""---
title:
  main: "{title}"
  lead_author: "{lead_author}"
date: "2025-06-25"
"""
            config_file.write_text(config_content)

            created_files[manuscript_path] = (manuscript_dir, lead_author.lower())

        # Test building each manuscript independently
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        for manuscript_path, (
            manuscript_dir,
            lead_author_clean,
        ) in created_files.items():
            # Switch to this manuscript
            monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_path)

            # Test manuscript finding
            from rxiv_maker.utils import (
                copy_pdf_to_manuscript_folder,
                find_manuscript_md,
                write_manuscript_output,
            )

            found = find_manuscript_md()
            assert manuscript_path in str(found)

            # Test LaTeX output
            latex_content = f"\\title{{{manuscript_path}}}"
            tex_result = write_manuscript_output(str(output_dir), latex_content)

            expected_tex = output_dir / f"{manuscript_path}.tex"
            assert Path(tex_result) == expected_tex
            assert expected_tex.exists()

            # Test PDF copying
            mock_pdf = output_dir / f"{manuscript_path}.pdf"
            mock_pdf.write_text(f"PDF content for {manuscript_path}")

            yaml_metadata = {
                "date": "2025-06-25",
                "title": {"lead_author": created_files[manuscript_path][1].title()},
            }

            copied_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

            expected_pdf_name = f"2025__{lead_author_clean}_et_al__rxiv.pdf"
            expected_pdf_path = manuscript_dir / expected_pdf_name

            assert copied_pdf.resolve() == expected_pdf_path.resolve()
            assert expected_pdf_path.exists()

        # Verify all manuscripts coexist without interference
        all_tex_files = list(output_dir.glob("*.tex"))
        all_pdf_files = []

        for _, (manuscript_dir, _) in created_files.items():
            pdf_files = list(manuscript_dir.glob("*_et_al__rxiv.pdf"))
            all_pdf_files.extend(pdf_files)

        assert len(all_tex_files) == len(manuscripts)
        assert len(all_pdf_files) == len(manuscripts)

        print("✅ Multiple manuscript workflow validated:")
        for manuscript_path in created_files:
            print(f"   - {manuscript_path}: LaTeX and PDF generated successfully")

    def test_build_validation_with_makefile_integration(self, temp_dir, monkeypatch):
        """Test that the build integrates properly with Makefile workflows."""
        monkeypatch.chdir(temp_dir)

        # Set up manuscript similar to how Makefile would be used
        manuscript_path = "PAPER_SUBMISSION_2025"
        monkeypatch.setenv("MANUSCRIPT_PATH", manuscript_path)

        # Create manuscript structure
        manuscript_dir = temp_dir / manuscript_path
        manuscript_dir.mkdir()

        # Create figures directory (as Makefile expects)
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir()

        # Create sample figure subdirectory
        fig1_dir = figures_dir / "Figure__example"
        fig1_dir.mkdir()

        # Create main manuscript with figure references
        main_file = manuscript_dir / "01_MAIN.md"
        main_content = """---
title: "Research Paper for Submission 2025"
authors:
  - name: "Dr. Lead Author"
    affiliation: "Research University"
---

# Introduction

This paper presents our research findings.

## Methodology

Our approach is illustrated in @fig:methodology.

![Methodology Overview](FIGURES/Figure__example/methodology.png){#fig:methodology width="0.8"}

# Results

The results demonstrate the effectiveness of our approach.

# Conclusion

This work contributes to the field significantly.
"""
        main_file.write_text(main_content)

        # Create config for realistic metadata
        config_file = manuscript_dir / "00_CONFIG.yml"
        config_content = """---
title:
  main: "Research Paper for Submission 2025"
  lead_author: "LeadAuthor"
date: "2025-06-25"
authors:
  - name: "Dr. Lead Author"
    affiliation: "Research University"
    email: "lead.author@research-uni.edu"
affiliations:
  - name: "Research University"
    address: "123 Research Blvd, Academic City, AC 12345"
"""
        config_file.write_text(config_content)

        # Create bibliography
        bib_file = manuscript_dir / "03_REFERENCES.bib"
        bib_content = """@article{reference2024,
  title={Important Previous Work},
  author={Previous, Author and Other, Researcher},
  journal={Journal of Research},
  volume={10},
  pages={1-20},
  year={2024}
}
"""
        bib_file.write_text(bib_content)

        # Test the build process components
        from rxiv_maker.utils import (
            copy_pdf_to_manuscript_folder,
            create_output_dir,
            find_manuscript_md,
            write_manuscript_output,
        )

        # Step 1: Manuscript discovery (as Makefile would do)
        found_manuscript = find_manuscript_md()
        assert Path(found_manuscript).name == "01_MAIN.md"
        assert manuscript_path in str(found_manuscript)

        # Step 2: Output directory setup (as Makefile would do)
        output_dir = temp_dir / "output"
        create_output_dir(str(output_dir))

        # Step 3: LaTeX generation (simulate what generate_preprint.py would do)
        latex_content = r"""
\documentclass[letterpaper,10pt]{article}
\usepackage{graphicx}
\usepackage{cite}

\title{Research Paper for Submission 2025}
\author{Dr. Lead Author}
\date{2025-06-25}

\begin{document}
\maketitle

\section{Introduction}
This paper presents our research findings.

\subsection{Methodology}
Our approach is illustrated in Figure \ref{fig:methodology}.

\begin{figure}[ht]
\centering
\includegraphics[width=0.8\linewidth]{Figures/Figure__example/methodology.png}
\caption{Methodology Overview}
\label{fig:methodology}
\end{figure}

\section{Results}
The results demonstrate effectiveness.

\section{Conclusion}
This work contributes significantly.

\bibliographystyle{plain}
\bibliography{03_REFERENCES}

\end{document}
"""

        tex_result = write_manuscript_output(str(output_dir), latex_content)

        # Verify LaTeX file naming matches manuscript path
        expected_tex_name = f"{manuscript_path}.tex"
        assert Path(tex_result).name == expected_tex_name
        assert Path(tex_result).exists()

        # Verify LaTeX content includes figure references
        tex_content = Path(tex_result).read_text()
        assert "Research Paper for Submission 2025" in tex_content
        assert r"\includegraphics" in tex_content
        assert "methodology.png" in tex_content

        # Step 4: PDF generation and placement (simulate LaTeX compilation + copy)
        # Create mock compiled PDF
        compiled_pdf = output_dir / f"{manuscript_path}.pdf"
        compiled_pdf.write_text("Compiled PDF content with figures and references")

        # Test PDF copying with custom naming
        yaml_metadata = {"date": "2025-06-25", "title": {"lead_author": "LeadAuthor"}}

        final_pdf = copy_pdf_to_manuscript_folder(str(output_dir), yaml_metadata)

        # Verify PDF placement and naming
        expected_pdf_name = "2025__leadauthor_et_al__rxiv.pdf"
        expected_pdf_path = manuscript_dir / expected_pdf_name

        assert final_pdf.resolve() == expected_pdf_path.resolve()
        assert expected_pdf_path.exists()
        assert expected_pdf_path.read_text() == "Compiled PDF content with figures and references"

        # Verify directory structure is maintained
        assert manuscript_dir.is_dir()
        assert figures_dir.is_dir()
        assert fig1_dir.is_dir()
        assert config_file.exists()
        assert main_file.exists()
        assert bib_file.exists()

        print(f"✅ Makefile integration validated for: {manuscript_path}")
        print(f"   - Source files in: {manuscript_dir}")
        print(f"   - LaTeX output: {tex_result}")
        print(f"   - Final PDF: {expected_pdf_path}")
