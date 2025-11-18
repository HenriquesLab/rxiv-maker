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
            except KeyError:
                # If key missing, return template as-is
                return template

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

abstract: |
  Your manuscript abstract goes here. Provide a comprehensive summary of your research work,
  methodology, key findings, and conclusions. This should give readers a clear understanding
  of your research contribution and its significance to the field.

keywords:
  - keyword1
  - keyword2
  - keyword3

# Style configuration
style:
  format: "nature"           # Journal style: nature, cell, science, pnas, etc.
  font_size: "11pt"          # Font size for the manuscript
  line_spacing: "single"     # Line spacing: single, onehalf, double

# Output configuration
output:
  format: "pdf"              # Output format
  directory: "output"        # Output directory name
  filename: "manuscript"     # Base filename for outputs

# Figures configuration
figures:
  directory: "FIGURES"       # Directory containing figure scripts
  generate: true            # Whether to generate figures automatically
  formats: ["png", "svg"]   # Figure output formats

# Bibliography configuration
bibliography:
  file: "03_REFERENCES.bib"  # Bibliography file name
  style: "nature"           # Citation style

# Validation configuration
validation:
  enabled: true             # Enable manuscript validation
  strict: false            # Strict validation mode
  skip_doi_check: false    # Skip DOI validation (useful for drafts)

# Cache configuration (improves build speed)
cache:
  enabled: true            # Enable caching
  ttl_hours: 24           # Cache time-to-live in hours

# Acknowledgment
acknowledge_rxiv_maker: true  # Include rxiv-maker acknowledgment

# Section ordering
methods_after_bibliography: false  # If true, Methods appears after Bibliography (Nature Methods style); if false, Methods before Bibliography (traditional)

version: "1.0"
"""

    def _get_default_main_template(self) -> str:
        """Get default main manuscript template."""
        return """# Introduction

Your manuscript introduction goes here. This should provide background information,
context for your research, and clearly state the objectives and significance of your work.

# Methods

Describe your experimental methods, computational approaches, data collection procedures,
and analysis techniques. Provide sufficient detail for reproducibility.

## Data Collection

Detail your data collection methodology.

## Analysis

Explain your analysis approach and statistical methods.

# Results

Present your key findings with supporting figures and tables. Use clear section
headers to organize your results logically.

## Primary Findings

Describe your main results.

## Additional Analysis

Present supporting analysis and secondary findings.

# Discussion

Interpret your results in the context of existing literature. Discuss the implications
of your findings, acknowledge limitations, and suggest future research directions.

# Conclusions

Summarize the key conclusions of your study and their broader impact.

# Figures

Figure references will be automatically generated. Place your figure scripts in the
FIGURES/ directory and reference them using standard markdown syntax:

![Figure 1: Example figure caption](FIGURES/Figure__example.mmd)

# Tables

Create tables using standard markdown syntax:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

# References

Citations will be automatically formatted. Add entries to 03_REFERENCES.bib and
reference them in your text.

This is an important finding [@smith2023; @johnson2022].
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
        return """@article{smith2023,
    title = {Example Research Article},
    author = {Smith, John and Doe, Jane},
    journal = {Nature},
    volume = {123},
    pages = {456-789},
    year = {2023},
    doi = {10.1038/nature12345}
}

@article{johnson2022,
    title = {Another Important Study},
    author = {Johnson, Alice and Brown, Bob},
    journal = {Cell},
    volume = {185},
    pages = {1234-1245},
    year = {2022},
    doi = {10.1016/j.cell.2022.01.001}
}
"""

    def _get_default_figure_template(self) -> str:
        """Get default figure template (Mermaid diagram)."""
        return """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Process 1]
    B -->|No| D[Process 2]
    C --> E[End]
    D --> E
"""

    def _get_default_gitignore_template(self) -> str:
        """Get default .gitignore template."""
        return """# rxiv-maker outputs
output/
*.pdf
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

output:
  format: "pdf"

bibliography:
  file: "03_REFERENCES.bib"

version: "1.0"
"""

    def _get_minimal_main_template(self) -> str:
        """Get minimal main manuscript template."""
        return """# Introduction

Write your introduction here.

# Methods

Describe your methods.

# Results

Present your results.

# Discussion

Discuss your findings.

# References

Add citations using [@ref_key].
"""

    def _get_minimal_supplementary_template(self) -> str:
        """Get minimal supplementary template."""
        return """# Supplementary Information

Add supplementary materials here.
"""

    def _get_minimal_bibliography_template(self) -> str:
        """Get minimal bibliography template."""
        return """@article{example2023,
    title = {Example Article},
    author = {Author, First},
    journal = {Journal Name},
    year = {2023}
}
"""

    # Journal template methods
    def _get_journal_config_template(self) -> str:
        """Get journal-specific configuration template."""
        config = self._get_default_config_template()
        # Modify for journal submission
        config = config.replace('format: "nature"', 'format: "nature"  # Change to target journal')
        config = config.replace(
            'line_spacing: "single"', 'line_spacing: "double"  # Most journals require double-spacing'
        )
        return config

    def _get_journal_main_template(self) -> str:
        """Get journal-specific main template."""
        return """# Abstract

Structured abstract as required by the target journal.

# Introduction

Comprehensive introduction with literature review.

# Materials and Methods

Detailed methods section with subsections.

## Study Design

## Experimental Procedures

## Statistical Analysis

# Results

Results organized by research question.

## Result 1

## Result 2

# Discussion

In-depth discussion relating findings to existing literature.

## Implications

## Limitations

## Future Directions

# Conclusions

Brief conclusions summarizing key findings.

# Acknowledgments

Funding sources, contributions, and acknowledgments.

# References

Citations formatted per journal guidelines [@ref].
"""

    # Preprint template methods
    def _get_preprint_config_template(self) -> str:
        """Get preprint-specific configuration template."""
        config = self._get_default_config_template()
        # Modify for preprint
        config = config.replace(
            "acknowledge_rxiv_maker: true", "acknowledge_rxiv_maker: true  # Include software citation"
        )
        return config

    def _get_preprint_main_template(self) -> str:
        """Get preprint-specific main template."""
        return """# Abstract

Clear, accessible abstract for broad readership.

# Introduction

Introduction with clear motivation and objectives.

# Results

Results-first organization common in preprints.

## Key Finding 1

## Key Finding 2

## Additional Results

# Discussion

Discussion of implications and significance.

# Methods

Detailed methods at the end (common for preprints).

## Experimental Design

## Data Analysis

# Data and Code Availability

Links to data repositories and code (required for preprints).

# Author Contributions

Detailed author contribution statements.

# Competing Interests

Declaration of competing interests.

# References

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
