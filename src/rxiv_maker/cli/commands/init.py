"""Init command for rxiv-maker CLI."""

import datetime
import sys
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.prompt import Prompt

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("manuscript_path", type=click.Path(), required=False)
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing files")
@click.option("--no-interactive", is_flag=True, help="Skip interactive prompts and use defaults")
@click.pass_context
def init(
    ctx: click.Context,
    manuscript_path: str | None,
    force: bool,
    no_interactive: bool,
) -> None:
    """Initialize a new manuscript directory with template files and structure.

    **MANUSCRIPT_PATH**: Directory to create for your manuscript.
    Defaults to MANUSCRIPT/

    Creates all required files including configuration, main content, supplementary
    information, bibliography, and figure directory with example scripts.

    ## Examples

    **Initialize default manuscript:**

        $ rxiv init

    **Initialize custom manuscript directory:**

        $ rxiv init MY_PAPER/

    **Force overwrite existing directory:**

        $ rxiv init --force
    """
    verbose = ctx.obj.get("verbose", False)

    # Default to MANUSCRIPT if not specified
    if manuscript_path is None:
        manuscript_path = "MANUSCRIPT"

    manuscript_dir = Path(manuscript_path)

    # Check if directory exists
    if manuscript_dir.exists() and not force:
        console.print(f"❌ Error: Directory '{manuscript_path}' already exists", style="red")
        console.print("💡 Use --force to overwrite existing files", style="yellow")
        sys.exit(1)

    try:
        # Create directory structure
        manuscript_dir.mkdir(parents=True, exist_ok=True)
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir(exist_ok=True)

        console.print(f"📁 Created manuscript directory: {manuscript_path}", style="green")

        # Get metadata (interactive or defaults)
        if no_interactive:
            title = "My Research Paper"
            subtitle = ""
            author_name = "Your Name"
            author_email = "your.email@example.com"
            author_affiliation = "Your Institution"
        else:
            console.print("\n📝 Please provide manuscript information:", style="blue")

            title = Prompt.ask("Title", default="My Research Paper")
            subtitle = Prompt.ask("Subtitle (optional)", default="")

            # Author information
            author_name = Prompt.ask("Author name", default="Your Name")
            author_email = Prompt.ask("Author email", default="your.email@example.com")
            author_affiliation = Prompt.ask("Author affiliation", default="Your Institution")

        # Create 00_CONFIG.yml
        today = datetime.date.today().strftime("%Y-%m-%d")
        config_content = f'''# Manuscript Configuration
title: "{title}"
{f'subtitle: "{subtitle}"' if subtitle else '# subtitle: "Optional subtitle"'}
authors:
  - name: "{author_name}"
    email: "{author_email}"
    affiliations: [1]
    orcid: ""  # Optional ORCID ID

affiliations:
  - id: 1
    name: "{author_affiliation}"
    department: ""
    city: ""
    country: ""

# Publication metadata
date: "{today}"                      # Publication date (YYYY-MM-DD format)
status: "draft"                         # Status: draft, submitted, accepted, published
use_line_numbers: true                  # Enable line numbers for manuscript review
license: "CC BY 4.0"                    # Creative Commons license (CC BY 4.0, CC BY-SA 4.0, etc.)
acknowledge_rxiv_maker: true            # Include Rxiv-Maker acknowledgement and citation
enable_doi_validation: true             # Enable DOI validation against CrossRef/DataCite APIs

# Keywords and abstract
keywords: ["keyword1", "keyword2", "keyword3"]
abstract: |
  This is the abstract of your manuscript. Replace this text with your actual abstract.

  You can use multiple paragraphs here. The abstract should be concise and informative.

# Bibliography settings
bibliography_style: "rxiv_maker_style"  # or "nature", "science", "ieee", etc.
citation_style: "nature"  # or "apa", "mla", etc.

# Figure settings
figure_format: "png"  # or "pdf", "svg"
figure_dpi: 300

# Build settings
latex_engine: "pdflatex"  # or "xelatex", "lualatex"
'''

        with open(manuscript_dir / "00_CONFIG.yml", "w", encoding="utf-8") as f:
            f.write(config_content)

        # Create 01_MAIN.md
        main_content = f"""# {title}

## Introduction

Your introduction goes here. You can use all the features of **rxiv-markdown**:

- Citations: @your_reference_2024
- Figure references: @fig:example

## Methods

Describe your methods here.

### Subsection

You can use subsections to organize your content.

## Results

Present your results here. For example, see @fig:example for an example visualization.

![](FIGURES/Figure__example/Figure__example.png)
{{#fig:example}} **Example Figure.** This is an example figure showing a sine wave generated by the Python script in FIGURES/Figure__example.py. This demonstrates the basic workflow of rxiv-maker figure generation.

## Discussion

Discuss your findings here.

## Conclusion

Conclude your manuscript here.

## Acknowledgements

Acknowledge contributions here.
"""

        with open(manuscript_dir / "01_MAIN.md", "w", encoding="utf-8") as f:
            f.write(main_content)

        # Create 02_SUPPLEMENTARY_INFO.md
        supp_content = """# Supplementary Information

## Supplementary Methods

Additional methodological details.

## Supplementary Results

Additional results and figures.

## Supplementary Tables

Additional tables.

## Supplementary References

Additional references if needed.
"""

        with open(manuscript_dir / "02_SUPPLEMENTARY_INFO.md", "w", encoding="utf-8") as f:
            f.write(supp_content)

        # Create 03_REFERENCES.bib
        bib_content = """@article{your_reference_2024,
  title={Example Reference Title},
  author={Author, First and Author, Second},
  journal={Journal Name},
  volume={1},
  number={1},
  pages={1--10},
  year={2024},
  publisher={Publisher},
  doi={10.1000/example.doi}
}
"""

        with open(manuscript_dir / "03_REFERENCES.bib", "w", encoding="utf-8") as f:
            f.write(bib_content)

        # Create example figure script
        figure_script = '''#!/usr/bin/env python3
"""Example figure script for rxiv-maker."""

import matplotlib.pyplot as plt
import numpy as np

# Generate example data
x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)

# Create the plot
plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Example Figure')
plt.legend()
plt.grid(True, alpha=0.3)

# Save the figure directly (rxiv-maker handles the directory)
plt.tight_layout()
plt.savefig('Figure__example.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Example figure generated successfully!")
'''

        with open(figures_dir / "Figure__example.py", "w", encoding="utf-8") as f:
            f.write(figure_script)

        # Create .gitignore
        gitignore_content = """# Rxiv-Maker generated files
output/
*.aux
*.log
*.out
*.toc
*.fls
*.fdb_latexmk
*.synctex.gz
*.bak
*.backup

# Generated figures
FIGURES/*.png
FIGURES/*.pdf
FIGURES/*.svg
FIGURES/*.eps

# Cache files
.cache/
__pycache__/
*.pyc

# OS files
.DS_Store
Thumbs.db
"""

        with open(manuscript_dir / ".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)

        console.print("✅ Manuscript initialized successfully!", style="green")
        console.print(f"📁 Created in: {manuscript_dir.absolute()}", style="blue")

        # Show next steps
        console.print("\n🚀 Next steps:", style="blue")
        console.print(f"1. Edit {manuscript_path}/00_CONFIG.yml with your details", style="white")
        console.print(f"2. Write your content in {manuscript_path}/01_MAIN.md", style="white")
        console.print(f"3. Add references to {manuscript_path}/03_REFERENCES.bib", style="white")
        console.print(f"4. Run 'rxiv pdf {manuscript_path}' to generate PDF", style="white")

    except Exception as e:
        console.print(f"❌ Error initializing manuscript: {e}", style="red")
        if verbose:
            console.print_exception()
        sys.exit(1)
