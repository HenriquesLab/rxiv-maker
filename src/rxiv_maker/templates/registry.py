"""Template registry for manuscript templates.

This module provides a registry of all available manuscript templates,
organized by template type (default, minimal, journal, preprint).
"""

from enum import Enum
from typing import Dict, Optional


class TemplateFile(Enum):
    """Manuscript template files."""

    CONFIG = "00_CONFIG.yml"
    MAIN = "01_MAIN.md"
    SUPPLEMENTARY = "02_SUPPLEMENTARY_INFO.md"
    BIBLIOGRAPHY = "03_REFERENCES.bib"
    FIGURE_EXAMPLE = "FIGURES/Figure__example.mmd"
    GITIGNORE = ".gitignore"


class TemplateRegistry:
    """Registry of all manuscript templates."""

    def __init__(self):
        """Initialize template registry."""
        self._templates: Dict[str, Dict[TemplateFile, str]] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        """Register all default templates."""
        # Register default template
        self._templates["default"] = {
            TemplateFile.CONFIG: self._get_default_config_template(),
            TemplateFile.MAIN: self._get_default_main_template(),
            TemplateFile.SUPPLEMENTARY: self._get_default_supplementary_template(),
            TemplateFile.BIBLIOGRAPHY: self._get_default_bibliography_template(),
            TemplateFile.FIGURE_EXAMPLE: self._get_default_figure_template(),
            TemplateFile.GITIGNORE: self._get_default_gitignore_template(),
        }

        # Register minimal template
        self._templates["minimal"] = {
            TemplateFile.CONFIG: self._get_minimal_config_template(),
            TemplateFile.MAIN: self._get_minimal_main_template(),
            TemplateFile.SUPPLEMENTARY: self._get_minimal_supplementary_template(),
            TemplateFile.BIBLIOGRAPHY: self._get_minimal_bibliography_template(),
            TemplateFile.FIGURE_EXAMPLE: self._get_default_figure_template(),  # Same as default
            TemplateFile.GITIGNORE: self._get_default_gitignore_template(),  # Same as default
        }

        # Register journal template (for traditional journal submission)
        self._templates["journal"] = {
            TemplateFile.CONFIG: self._get_journal_config_template(),
            TemplateFile.MAIN: self._get_journal_main_template(),
            TemplateFile.SUPPLEMENTARY: self._get_default_supplementary_template(),
            TemplateFile.BIBLIOGRAPHY: self._get_default_bibliography_template(),
            TemplateFile.FIGURE_EXAMPLE: self._get_default_figure_template(),
            TemplateFile.GITIGNORE: self._get_default_gitignore_template(),
        }

        # Register preprint template (for bioRxiv, arXiv, etc.)
        self._templates["preprint"] = {
            TemplateFile.CONFIG: self._get_preprint_config_template(),
            TemplateFile.MAIN: self._get_preprint_main_template(),
            TemplateFile.SUPPLEMENTARY: self._get_default_supplementary_template(),
            TemplateFile.BIBLIOGRAPHY: self._get_default_bibliography_template(),
            TemplateFile.FIGURE_EXAMPLE: self._get_default_figure_template(),
            TemplateFile.GITIGNORE: self._get_default_gitignore_template(),
        }

    def get_template(self, template_type: str, file_type: TemplateFile, **kwargs) -> str:
        """Get a template with optional variable substitution.

        Args:
            template_type: Type of template (default, minimal, journal, preprint)
            file_type: Type of file template to retrieve
            **kwargs: Variables for template substitution

        Returns:
            Template content with variables substituted
        """
        if template_type not in self._templates:
            raise ValueError(f"Unknown template type: {template_type}")

        template = self._templates[template_type].get(file_type)
        if template is None:
            raise ValueError(f"Template file not found: {file_type}")

        # Perform variable substitution if kwargs provided
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                # If key missing, return template as-is
                raise ValueError(
                    f"Template variable missing in {file_type.value}: {e}. Available: {list(kwargs.keys())}"
                ) from e
            except (ValueError, IndexError) as e:
                # Format string syntax error
                raise ValueError(
                    f"Template formatting error in {file_type.value}: {e}. Check for unescaped {{}} braces or malformed format fields."
                ) from e

        return template

    def list_template_types(self) -> list[str]:
        """List all available template types.

        Returns:
            List of template type names
        """
        return list(self._templates.keys())

    # Default template content methods
    def _get_default_config_template(self) -> str:
        """Get default configuration template."""
        return """# Manuscript Configuration
# See https://github.com/HenriquesLab/rxiv-maker for full documentation

title: "{title}"

authors:
  - name: "{author_name}"
    email: "{author_email}"
    orcid: "{author_orcid}"
    affiliation: "{author_affiliation}"

keywords:
  - keyword1
  - keyword2
  - keyword3

# Citation style: "numbered" for [1] or "author-date" for (Author, Year)
citation_style: "numbered"

# Note: Abstract is auto-extracted from ## Abstract section in 01_MAIN.md
# Note: All other settings (figures, validation, cache, methods_placement) use sensible defaults
# Uncomment below to override defaults:
#
# figures:
#   directory: "FIGURES"
#   generate: true
#   formats: ["png", "svg"]
#
# validation:
#   enabled: true
#   strict: false
#   skip_doi_check: false
#
# cache:
#   enabled: true
#   ttl_hours: 24
#
# methods_placement: "after_bibliography"  # Options: "inline", "after_results", "after_bibliography"
# acknowledge_rxiv_maker: true
#
# # Bibliography author name format (applies to both PDF and DOCX):
# bibliography_author_format: "lastname_firstname"  # Options: "lastname_initials" (Smith, J.A.), "lastname_firstname" (Smith, John A.), "firstname_lastname" (John A. Smith)
"""

    def _get_default_main_template(self) -> str:
        """Get default main manuscript template."""
        return """## Abstract

Your manuscript abstract goes here. Provide a comprehensive summary of your work, including the main problem you are addressing, your approach, key findings, and the significance of your results to the field. The abstract should be self-contained and provide readers with a clear understanding of your contribution. Aim for 150-300 words that capture the essence of your research.

## Introduction

Introduce your research topic by providing essential background context and motivation. Start with the broader significance of your field, then narrow down to the specific problem your work addresses. Clearly state your research objectives and how your approach differs from or builds upon existing work in the literature [@smith2023]. Explain why this research is important and what gap in knowledge it fills.

## Methods

Describe your experimental design, data collection procedures, and analytical techniques in sufficient detail to allow replication of your work. For computational studies, specify software versions, parameters, and algorithms used. For experimental work, detail protocols, sample preparation, and measurement procedures [@johnson2022]. Include information about statistical methods and data validation approaches. If you are writing a review article, you may remove this section or describe your literature search and selection strategy.

## Results

Present your findings in a logical sequence, using figures and tables to support your narrative. Start with an overview of the key results, then provide detailed analyses.

![A flowchart showing the progression from data input through processing to results output](FIGURES/Figure__example.mmd)
{{#fig:example}} **Example workflow diagram.** This Mermaid diagram illustrates a typical data processing pipeline, automatically converted to PDF during manuscript compilation. The diagram shows three stages: data input (gray), processing and analysis (red), and results output (green).

Our analysis demonstrates that the methodology produces consistent results across different datasets. The workflow presented in @fig:example provides a schematic overview of the processing pipeline. These findings build upon previous work [@smith2023; @johnson2022] while introducing novel approaches to data analysis.

## Discussion

Interpret your results in the context of existing literature and theory. Discuss how your findings support or challenge current understanding in the field. Address the implications of your work for theory, practice, or policy. Acknowledge limitations of your study, such as sample size constraints, methodological limitations, or scope boundaries. Suggest directions for future research that build upon your findings.

## Conclusions

Summarize your key findings and their significance. Reinforce the main contributions of your work and their broader impact on the field. Keep this section concise but impactful, leaving readers with a clear understanding of what your research has accomplished and why it matters.

## References

Citations are automatically formatted from 03_REFERENCES.bib. Reference works using citation keys like [@smith2023] for single citations or [@smith2023; @johnson2022] for multiple citations.
"""

    def _get_default_supplementary_template(self) -> str:
        """Get default supplementary information template."""
        return """# Supplementary Information

## Supplementary Methods

Additional methodological details that support the main manuscript.

## Supplementary Results

Additional results, extended data, and supporting analyses.

## Supplementary Figures

Additional figures that support the main findings.

## Supplementary Tables

Additional tables with extended data.

## Code and Data Availability

Information about code repositories, data availability, and reproducibility resources.
"""

    def _get_default_bibliography_template(self) -> str:
        """Get default bibliography template."""
        return """@article{{smith2023,
    title = {{Advances in computational biology: methods and applications}},
    author = {{Smith, John A. and Doe, Jane M. and Williams, Robert L.}},
    journal = {{Nature Methods}},
    volume = {{20}},
    number = {{8}},
    pages = {{1234--1245}},
    year = {{2023}},
    publisher = {{Springer Nature}},
    doi = {{10.1038/s41592-023-01234-5}}
}}

@article{{johnson2022,
    title = {{Machine learning approaches for biological data analysis}},
    author = {{Johnson, Alice B. and Brown, Robert C. and Davis, Sarah K.}},
    journal = {{Cell}},
    volume = {{185}},
    number = {{12}},
    pages = {{2156--2170}},
    year = {{2022}},
    publisher = {{Elsevier}},
    doi = {{10.1016/j.cell.2022.05.015}}
}}

@article{{wilson2024,
    title = {{Reproducible research practices in modern science}},
    author = {{Wilson, Greg and Jones, Emily R.}},
    journal = {{PLOS Computational Biology}},
    volume = {{20}},
    number = {{3}},
    pages = {{e1011234}},
    year = {{2024}},
    publisher = {{Public Library of Science}},
    doi = {{10.1371/journal.pcbi.1011234}}
}}
"""

    def _get_default_figure_template(self) -> str:
        """Get default figure template (Mermaid diagram)."""
        return """---
config:
  look: neo
  theme: neo
---
flowchart LR
    A["<b>DATA</b><br/>Input"] --> B["<b>PROCESSING</b><br/>Analysis"]
    B --> C["<b>RESULTS</b><br/>Output"]

    classDef inputStyle fill:#1f2937,stroke:#374151,stroke-width:3px,color:#ffffff
    classDef processStyle fill:#dc2626,stroke:#991b1b,stroke-width:3px,color:#ffffff
    classDef outputStyle fill:#059669,stroke:#047857,stroke-width:3px,color:#ffffff

    class A inputStyle
    class B processStyle
    class C outputStyle
"""

    def _get_default_gitignore_template(self) -> str:
        """Get default .gitignore template."""
        return """# rxiv-maker outputs
output/
.rxiv_cache/
*.pdf
*.docx
*.log
*.aux
*.fdb_latexmk
*.fls
*.out
*.toc
*.bbl
*.blg

# OS files
.DS_Store
Thumbs.db

# Editor files
*.swp
*.swo
*~
.vscode/
.idea/

# Python
__pycache__/
*.pyc
*.pyo
.env

# Temporary files
tmp/
temp/
.tmp/
"""

    # Minimal template methods
    def _get_minimal_config_template(self) -> str:
        """Get minimal configuration template."""
        return """title: "{title}"

authors:
  - name: "{author_name}"
    email: "{author_email}"

keywords:
  - keyword1
  - keyword2
  - keyword3

citation_style: "numbered"
"""

    def _get_minimal_main_template(self) -> str:
        """Get minimal main manuscript template."""
        return """## Abstract

Write your abstract here.

## Introduction

Introduce your topic.

## Main Content

Organize your content with additional sections as needed.

## Conclusions

Summarize your conclusions.

## References

Add citations using [@ref_key].
"""

    def _get_minimal_supplementary_template(self) -> str:
        """Get minimal supplementary template."""
        return """# Supplementary Information

Add supplementary materials here.
"""

    def _get_minimal_bibliography_template(self) -> str:
        """Get minimal bibliography template."""
        return """@article{{example2023,
    title = {{Example Article}},
    author = {{Author, First}},
    journal = {{Journal Name}},
    year = {{2023}}
}}
"""

    # Journal template methods
    def _get_journal_config_template(self) -> str:
        """Get journal-specific configuration template."""
        # Use the same config as default for journal submissions
        return self._get_default_config_template()

    def _get_journal_main_template(self) -> str:
        """Get detailed manuscript template (for comprehensive research papers)."""
        return """## Abstract

Comprehensive abstract summarizing your research.

## Introduction

Detailed introduction with literature review and clear objectives.

## Methods

Detailed methods with subsections for clarity.

### Experimental Design

Describe your study design.

### Data Analysis

Explain your analysis approach.

## Results

Present your findings organized by research question.

### Finding 1

First key result.

### Finding 2

Second key result.

## Discussion

In-depth discussion relating findings to existing literature.

### Implications

Discuss the implications of your work.

### Limitations

Acknowledge limitations.

### Future Directions

Suggest future research directions.

## Conclusions

Summarize key conclusions.

## References

[@ref]
"""

    # Preprint template methods
    def _get_preprint_config_template(self) -> str:
        """Get preprint-specific configuration template."""
        # Use the same config as default for preprints
        return self._get_default_config_template()

    def _get_preprint_main_template(self) -> str:
        """Get preprint template with open science focus."""
        return """## Abstract

Clear, accessible abstract for broad readership.

## Introduction

Introduction with clear motivation and objectives.

## Results

Present your key findings.

### Key Finding 1

### Key Finding 2

## Discussion

Discussion of implications and significance.

## Methods

Detailed methods (you can move this before Results if preferred).

### Experimental Design

### Data Analysis

## Data and Code Availability

Links to data repositories, code, and protocols for reproducibility.

## Author Contributions

Detailed author contribution statements.

## Competing Interests

Declaration of competing interests.

## References

[@ref]
"""


# Singleton instance
_template_registry: Optional[TemplateRegistry] = None


def get_template_registry() -> TemplateRegistry:
    """Get singleton instance of template registry.

    Returns:
        TemplateRegistry instance
    """
    global _template_registry
    if _template_registry is None:
        _template_registry = TemplateRegistry()
    return _template_registry


__all__ = ["TemplateFile", "TemplateRegistry", "get_template_registry"]
