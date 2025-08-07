"""Template processing utilities for Rxiv-Maker.

This module handles template content generation and replacement operations.
"""

import os
import re
from pathlib import Path

try:
    from ..converters.md2tex import extract_content_sections
    from .author_processor import (
        generate_authors_and_affiliations,
        generate_corresponding_authors,
        generate_extended_author_info,
    )
except ImportError:
    # Fallback for when run as script
    from ..converters.md2tex import extract_content_sections
    from .author_processor import (
        generate_authors_and_affiliations,
        generate_corresponding_authors,
        generate_extended_author_info,
    )


def get_template_path():
    """Get the path to the template file."""
    # Try pkg_resources first for installed packages (most reliable)
    try:
        import pkg_resources

        template_path = Path(pkg_resources.resource_filename("rxiv_maker", "tex/template.tex"))
        if template_path.exists():
            return template_path
    except Exception:
        # Catch all exceptions from pkg_resources
        pass

    # Fallback to relative path for development/source installations
    template_path = Path(__file__).parent.parent / "tex" / "template.tex"
    if template_path.exists():
        return template_path

    # Final fallback - try parent.parent.parent for old structure
    fallback_path = Path(__file__).parent.parent.parent / "tex" / "template.tex"
    if fallback_path.exists():
        return fallback_path

    # If all else fails, raise a descriptive error
    raise FileNotFoundError(
        f"Could not find template.tex file. Searched locations:\n"
        f"  - Package resource: rxiv_maker/tex/template.tex\n"
        f"  - Relative path: {Path(__file__).parent.parent / 'tex' / 'template.tex'}\n"
        f"  - Fallback path: {Path(__file__).parent.parent.parent / 'tex' / 'template.tex'}"
    )


def find_supplementary_md():
    """Find supplementary information file in the manuscript directory."""
    current_dir = Path.cwd()
    manuscript_path = os.getenv("MANUSCRIPT_PATH", "MANUSCRIPT")

    # Look for supplementary file: 02_SUPPLEMENTARY_INFO.md
    supplementary_md = current_dir / manuscript_path / "02_SUPPLEMENTARY_INFO.md"
    if supplementary_md.exists():
        return supplementary_md

    return None


def generate_supplementary_cover_page(yaml_metadata):
    """Generate LaTeX code for the supplementary information cover page."""
    # Extract title information
    title_info = yaml_metadata.get("title", {})
    long_title = "Supplementary Information"

    if isinstance(title_info, list):
        # Handle list format
        for item in title_info:
            if isinstance(item, dict) and "long" in item:
                long_title = item["long"]
    elif isinstance(title_info, dict):
        long_title = title_info.get("long", "Supplementary Information")
    else:
        long_title = str(title_info) if title_info else "Supplementary Information"

    # Create the cover page LaTeX
    cover_latex = f"""
% Supplementary Information Cover Page
\\newpage
\\thispagestyle{{empty}}
\\begin{{center}}

\\vspace*{{3cm}}

% Document type
\\textbf{{\\Large Supplementary Information}}

\\vspace{{3cm}}

% Main title section
{{\\Huge\\textbf{{{long_title}}}}}

\\vspace{{\\fill}}

% Footer information
\\begin{{minipage}}{{\\textwidth}}
\\centering
% Generated text removed
\\end{{minipage}}

\\end{{center}}
\\newpage
"""

    return cover_latex


def generate_supplementary_tex(output_dir, yaml_metadata=None):
    """Generate Supplementary.tex file from supplementary markdown."""
    from ..converters.md2tex import convert_markdown_to_latex

    supplementary_md = find_supplementary_md()
    if not supplementary_md:
        # Create empty supplementary file
        supplementary_tex_path = Path(output_dir) / "Supplementary.tex"
        with open(supplementary_tex_path, "w", encoding="utf-8") as f:
            f.write("% No supplementary information provided\n")
        return

    # Read and parse supplementary markdown content
    with open(supplementary_md, encoding="utf-8") as f:
        supplementary_content = f.read()

    # Parse and separate content into sections
    sections = parse_supplementary_sections(supplementary_content)

    # Convert each section to LaTeX separately
    tables_latex = ""
    notes_latex = ""
    figures_latex = ""

    if sections["tables"]:
        # Process tables section with special handling for section headers
        tables_content = sections["tables"]

        # Convert section headers to regular LaTeX sections
        tables_content = re.sub(r"^## (.+)$", r"\\section*{\1}", tables_content, flags=re.MULTILINE)

        tables_latex = "% Supplementary Tables\n\n" + convert_markdown_to_latex(tables_content, is_supplementary=True)

    if sections["notes"]:
        # Process notes section with special handling for section headers
        notes_content = sections["notes"]

        # Convert section headers to regular LaTeX sections (not supplementary notes)
        # This prevents "## Supplementary Notes" from becoming
        # "Supp. Note 1: Supplementary Notes"
        notes_content = re.sub(r"^## (.+)$", r"\\section*{\1}", notes_content, flags=re.MULTILINE)

        # Set up supplementary note numbering before the content
        note_setup = """
% Setup subsection numbering for supplementary notes
\\renewcommand{\\thesubsection}{Supp. Note \\arabic{subsection}}
\\setcounter{subsection}{0}

"""
        notes_latex = (
            "% Supplementary Notes\n" + note_setup + convert_markdown_to_latex(notes_content, is_supplementary=True)
        )

    if sections["figures"]:
        # Process figures section with special handling for section headers
        figures_content = sections["figures"]

        # Convert section headers to regular LaTeX sections
        figures_content = re.sub(r"^## (.+)$", r"\\section*{\1}", figures_content, flags=re.MULTILINE)

        figures_latex = "% Supplementary Figures\n\n" + convert_markdown_to_latex(
            figures_content, is_supplementary=True
        )

    # Combine sections in proper order
    supplementary_latex = tables_latex + "\n" + notes_latex + "\n" + figures_latex

    # Set up supplementary figure and table environment and numbering
    supplementary_setup = """% Setup for supplementary figures and tables
% Note: All supplementary counters and environments are already defined
% in the class file
\\renewcommand{\\figurename}{Sup. Fig.}
\\renewcommand{\\tablename}{Sup. Table}

"""

    # Process the LaTeX to convert figure environments to sfigure environments
    # Replace \begin{figure} with \begin{sfigure} and \end{figure} with \end{sfigure}
    # Also preserve \newpage commands that come after figures
    # (with or without line breaks)
    supplementary_latex = supplementary_latex.replace("\\begin{figure}", "\\begin{sfigure}")
    # Handle newpage with line breaks (using escaped backslashes)
    supplementary_latex = supplementary_latex.replace("\\end{figure}\n\\newpage", "\\end{sfigure}\n\\newpage")
    # Handle newpage without line breaks
    supplementary_latex = supplementary_latex.replace("\\end{figure}\\newpage", "\\end{sfigure}\\newpage")
    # Handle remaining figure endings
    supplementary_latex = supplementary_latex.replace("\\end{figure}", "\\end{sfigure}")

    # Process the LaTeX to convert table environments to stable environments
    # Replace \begin{table} with \begin{stable} and \end{table} with \end{stable}
    # Also preserve \newpage commands that come after tables
    # (with or without line breaks)
    supplementary_latex = supplementary_latex.replace("\\begin{table}", "\\begin{stable}")
    # Handle newpage with line breaks (using escaped backslashes)
    supplementary_latex = supplementary_latex.replace("\\end{table}\n\\newpage", "\\end{stable}\n\\newpage")
    # Handle newpage without line breaks
    supplementary_latex = supplementary_latex.replace("\\end{table}\\newpage", "\\end{stable}\\newpage")
    # Handle remaining table endings
    supplementary_latex = supplementary_latex.replace("\\end{table}", "\\end{stable}")

    # Also handle two-column tables
    supplementary_latex = supplementary_latex.replace("\\begin{table*}", "\\begin{stable*}")
    # Handle newpage with line breaks (using escaped backslashes)
    supplementary_latex = supplementary_latex.replace("\\end{table*}\n\\newpage", "\\end{stable*}\n\\newpage")
    # Handle newpage without line breaks
    supplementary_latex = supplementary_latex.replace("\\end{table*}\\newpage", "\\end{stable*}\\newpage")
    # Handle remaining table* endings
    supplementary_latex = supplementary_latex.replace("\\end{table*}", "\\end{stable*}")

    # Generate cover page if yaml_metadata is provided
    cover_page_latex = ""
    if yaml_metadata:
        cover_page_latex = generate_supplementary_cover_page(yaml_metadata)

    # Combine setup, cover page, and content
    final_latex = supplementary_setup + cover_page_latex + supplementary_latex

    # Write Supplementary.tex file
    supplementary_tex_path = Path(output_dir) / "Supplementary.tex"
    with open(supplementary_tex_path, "w", encoding="utf-8") as f:
        f.write(final_latex)

    print(f"Generated supplementary information: {supplementary_tex_path}")


def generate_keywords(yaml_metadata):
    """Generate LaTeX keywords section from YAML metadata."""
    keywords = yaml_metadata.get("keywords", [])

    if not keywords:
        return "% No keywords found\n"

    # Join keywords with ' | ' separator
    keywords_str = " | ".join(keywords)

    result = "\\begin{keywords}\n"
    result += keywords_str
    result += "\n\\end{keywords}"

    return result


def generate_bibliography(yaml_metadata):
    """Generate LaTeX bibliography section from YAML metadata."""
    bibliography = yaml_metadata.get("bibliography", "03_REFERENCES")

    # Remove .bib extension if present
    if bibliography.endswith(".bib"):
        bibliography = bibliography[:-4]

    return f"\\bibliography{{{bibliography}}}"


def process_template_replacements(template_content, yaml_metadata, article_md):
    """Process all template replacements with metadata and content."""
    # Process draft watermark based on status field
    is_draft = False
    if "status" in yaml_metadata:
        status = str(yaml_metadata["status"]).lower()
        is_draft = status == "draft"

    if is_draft:
        # Enable watermark option in document class
        template_content = template_content.replace(
            r"\documentclass[times, twoside]{rxiv_maker_style}",
            r"\documentclass[times, twoside, watermark]{rxiv_maker_style}",
        )

    # Process line numbers
    txt = ""
    if "use_line_numbers" in yaml_metadata:
        use_line_numbers = str(yaml_metadata["use_line_numbers"]).lower() == "true"
        if use_line_numbers:
            txt = "% Add number to the lines\n\\usepackage{lineno}\n\\linenumbers\n"
    template_content = template_content.replace("<PY-RPL:USE-LINE-NUMBERS>", txt)

    # Process date
    date_str = yaml_metadata.get("date", "")
    txt = f"\\renewcommand{{\\today}}{{{date_str}}}\n" if date_str else ""
    template_content = template_content.replace("<PY-RPL:DATE>", txt)

    # Process lead author
    lead_author = "Unknown"
    if "title" in yaml_metadata:
        title_data = yaml_metadata["title"]
        if isinstance(title_data, list):
            for item in title_data:
                if isinstance(item, dict) and "lead_author" in item:
                    lead_author = item["lead_author"]
                    break
        elif isinstance(title_data, dict) and "lead_author" in title_data:
            lead_author = title_data["lead_author"]

    if lead_author == "Unknown" and "authors" in yaml_metadata and yaml_metadata["authors"]:
        # get the last name of the first author
        first_author = yaml_metadata["authors"][0]
        if isinstance(first_author, dict) and "name" in first_author:
            lead_author = first_author["name"].split()[-1]
        elif isinstance(first_author, str):
            lead_author = first_author.split()[-1]
    txt = f"\\leadauthor{{{lead_author}}}\n"
    template_content = template_content.replace("<PY-RPL:LEAD-AUTHOR>", txt)

    # Process long title
    long_title = "Untitled Article"
    if "title" in yaml_metadata:
        if isinstance(yaml_metadata["title"], dict) and "long" in yaml_metadata["title"]:
            long_title = yaml_metadata["title"]["long"]
        elif isinstance(yaml_metadata["title"], list):
            for item in yaml_metadata["title"]:
                if isinstance(item, dict) and "long" in item:
                    long_title = item["long"]
                    break
        elif isinstance(yaml_metadata["title"], str):
            long_title = yaml_metadata["title"]
    txt = f"\\title{{{long_title}}}\n"
    template_content = template_content.replace("<PY-RPL:LONG-TITLE-STR>", txt)

    # Process short title
    short_title = "Untitled"
    if "title" in yaml_metadata:
        if isinstance(yaml_metadata["title"], dict) and "short" in yaml_metadata["title"]:
            short_title = yaml_metadata["title"]["short"]
        elif isinstance(yaml_metadata["title"], list):
            for item in yaml_metadata["title"]:
                if isinstance(item, dict) and "short" in item:
                    short_title = item["short"]
                    break
        elif isinstance(yaml_metadata["title"], str):
            short_title = (
                yaml_metadata["title"][:50] + "..." if len(yaml_metadata["title"]) > 50 else yaml_metadata["title"]
            )
    txt = f"\\shorttitle{{{short_title}}}\n"
    template_content = template_content.replace("<PY-RPL:SHORT-TITLE-STR>", txt)

    # Generate authors and affiliations dynamically
    authors_and_affiliations = generate_authors_and_affiliations(yaml_metadata)
    template_content = template_content.replace("<PY-RPL:AUTHORS-AND-AFFILIATIONS>", authors_and_affiliations)

    # Generate corresponding authors section
    corresponding_authors = generate_corresponding_authors(yaml_metadata)
    template_content = template_content.replace("<PY-RPL:CORRESPONDING-AUTHORS>", corresponding_authors)

    # Generate extended author information section
    extended_author_info = generate_extended_author_info(yaml_metadata)
    template_content = template_content.replace("<PY-RPL:EXTENDED-AUTHOR-INFO>", extended_author_info)

    # Generate keywords section
    keywords_section = generate_keywords(yaml_metadata)
    template_content = template_content.replace("<PY-RPL:KEYWORDS>", keywords_section)

    # Generate bibliography section
    bibliography_section = generate_bibliography(yaml_metadata)
    template_content = template_content.replace("<PY-RPL:BIBLIOGRAPHY>", bibliography_section)

    # Extract content sections from markdown
    content_sections = extract_content_sections(article_md)

    # Replace content placeholders with extracted sections
    template_content = template_content.replace("<PY-RPL:ABSTRACT>", content_sections.get("abstract", ""))
    template_content = template_content.replace("<PY-RPL:MAIN-CONTENT>", content_sections.get("main", ""))
    template_content = template_content.replace("<PY-RPL:METHODS>", content_sections.get("methods", ""))

    # Handle main content sections conditionally
    # Results section
    results_content = content_sections.get("results", "").strip()
    if results_content:
        results_section = f"\\section*{{Results}}\n{results_content}"
    else:
        results_section = ""
    template_content = template_content.replace("<PY-RPL:RESULTS-SECTION>", results_section)

    # Discussion section
    discussion_content = content_sections.get("discussion", "").strip()
    if discussion_content:
        discussion_section = f"\\section*{{Discussion}}\n{discussion_content}"
    else:
        discussion_section = ""
    template_content = template_content.replace("<PY-RPL:DISCUSSION-SECTION>", discussion_section)

    # Conclusions section
    conclusions_content = content_sections.get("conclusion", "").strip()
    if conclusions_content:
        conclusions_section = f"\\section*{{Conclusions}}\n{conclusions_content}"
    else:
        conclusions_section = ""
    template_content = template_content.replace("<PY-RPL:CONCLUSIONS-SECTION>", conclusions_section)

    # Handle optional sections conditionally
    # Data availability
    data_availability = content_sections.get("data_availability", "").strip()
    if data_availability:
        data_block = f"""\\begin{{data}}
{data_availability}
\\end{{data}}"""
    else:
        data_block = ""
    template_content = template_content.replace("<PY-RPL:DATA-AVAILABILITY-BLOCK>", data_block)

    # Code availability
    code_availability = content_sections.get("code_availability", "").strip()
    if code_availability:
        code_block = f"""\\begin{{code}}
{code_availability}
\\end{{code}}"""
    else:
        code_block = ""
    template_content = template_content.replace("<PY-RPL:CODE-AVAILABILITY-BLOCK>", code_block)

    # Author contributions
    author_contributions = content_sections.get("author_contributions", "").strip()
    if author_contributions:
        contributions_block = f"""\\begin{{contributions}}
{author_contributions}
\\end{{contributions}}"""
    else:
        contributions_block = ""
    template_content = template_content.replace("<PY-RPL:AUTHOR-CONTRIBUTIONS-BLOCK>", contributions_block)

    # Acknowledgements
    acknowledgements = content_sections.get("acknowledgements", "").strip()
    if acknowledgements:
        acknowledgements_block = f"""\\begin{{acknowledgements}}
{acknowledgements}
\\end{{acknowledgements}}"""
    else:
        acknowledgements_block = ""
    template_content = template_content.replace("<PY-RPL:ACKNOWLEDGEMENTS-BLOCK>", acknowledgements_block)

    template_content = template_content.replace("<PY-RPL:FUNDING>", content_sections.get("funding", ""))
    # Generate manuscript preparation content
    manuscript_prep_content = content_sections.get("manuscript_preparation", "")

    # Add RχIV-Maker acknowledgment if requested
    acknowledge_rxiv = yaml_metadata.get("acknowledge_rxiv_maker", False)
    if acknowledge_rxiv and not manuscript_prep_content.strip():
        manuscript_prep_content = (
            "This manuscript was prepared using {\\color{red}R}$\\chi$iv-Maker~\\cite{saraiva_2025_rxivmaker}."
        )

    # Add license information if specified
    license_info = yaml_metadata.get("license", "")
    if license_info:
        license_text = f"This work is licensed under {license_info}."
        if manuscript_prep_content.strip():
            manuscript_prep_content += f" {license_text}"
        else:
            manuscript_prep_content = license_text

    # Only include manuscript information block if there's content
    if manuscript_prep_content.strip():
        manuscript_prep_block = f"""\\begin{{manuscriptinfo}}
{manuscript_prep_content}
\\end{{manuscriptinfo}}"""
    else:
        manuscript_prep_block = ""

    template_content = template_content.replace(
        "<PY-RPL:MANUSCRIPT-PREPARATION-BLOCK>",
        manuscript_prep_block,
    )

    return template_content


def parse_supplementary_sections(content):
    """Parse supplementary markdown content into separate sections.

    Separates content based on level 2 headers:
    - ## Supplementary Tables
    - ## Supplementary Notes
    - ## Supplementary Figures

    Returns:
        dict: Dictionary with 'tables', 'notes', and 'figures' keys
    """
    sections = {"tables": "", "notes": "", "figures": ""}

    # Split content by lines
    lines = content.split("\n")
    current_section = None
    section_content = []

    for line in lines:
        stripped = line.strip()

        # Check for section markers (level 2 headers)
        if stripped.startswith("## Supplementary Tables"):
            # Save previous section if exists
            if current_section and section_content:
                sections[current_section] = "\n".join(section_content)
            current_section = "tables"
            section_content = []
        elif stripped.startswith("## Supplementary Notes"):
            # Save previous section if exists
            if current_section and section_content:
                sections[current_section] = "\n".join(section_content)
            current_section = "notes"
            section_content = []
        elif stripped.startswith("## Supplementary Figures"):
            # Save previous section if exists
            if current_section and section_content:
                sections[current_section] = "\n".join(section_content)
            current_section = "figures"
            section_content = []
        else:
            # Add line to current section
            if current_section:
                section_content.append(line)

    # Save the last section
    if current_section and section_content:
        sections[current_section] = "\n".join(section_content)

    return sections
