"""Prepare bioRxiv author submission template (TSV format).

This module generates a tab-separated values (TSV) file containing author information
formatted for bioRxiv submission system upload.
"""

import csv
import html.entities
import logging
import shutil
import zipfile
from pathlib import Path

from ...core.managers.config_manager import ConfigManager
from ...utils.author_name_formatter import parse_author_name
from ...utils.email_encoder import decode_email

logger = logging.getLogger(__name__)


def encode_html_entities(text: str) -> str:
    """Convert Unicode characters to HTML entities for bioRxiv submission.

    bioRxiv's TSV upload requires special characters to be encoded as HTML entities.
    For example, "António" becomes "Ant&oacute;nio", "Åbo" becomes "&Aring;bo".

    Args:
        text: Text that may contain Unicode characters

    Returns:
        Text with Unicode characters converted to HTML entities
        (e.g., "António" -> "Ant&oacute;nio", "Åbo" -> "&Aring;bo")

    Examples:
        >>> encode_html_entities("António")
        'Ant&oacute;nio'
        >>> encode_html_entities("Åbo")
        '&Aring;bo'
        >>> encode_html_entities("José García")
        'Jos&eacute; Garc&iacute;a'
    """
    if not text:
        return text

    # Build reverse mapping: Unicode character -> HTML entity name
    char_to_entity = {}
    for entity_name, codepoint in html.entities.name2codepoint.items():
        char = chr(codepoint)
        # Skip basic ASCII characters and use named entities for special chars
        if ord(char) > 127:
            char_to_entity[char] = f"&{entity_name};"

    # Convert each character to HTML entity if it has one
    result = []
    for char in text:
        if char in char_to_entity:
            result.append(char_to_entity[char])
        else:
            result.append(char)

    return "".join(result)


class BioRxivAuthorError(Exception):
    """Exception raised for bioRxiv author template generation errors."""

    pass


def validate_author_data(authors: list[dict]) -> None:
    """Validate author data for bioRxiv submission requirements.

    Args:
        authors: List of author dictionaries from config

    Raises:
        BioRxivAuthorError: If validation fails
    """
    if not authors:
        raise BioRxivAuthorError("No authors found in configuration")

    # Count corresponding authors
    corresponding_count = sum(1 for author in authors if author.get("corresponding_author", False))

    if corresponding_count == 0:
        raise BioRxivAuthorError(
            "No corresponding author found. "
            "Exactly one author must be marked with 'corresponding_author: true' in 00_CONFIG.yml"
        )

    if corresponding_count > 1:
        corresponding_names = [
            author.get("name", "Unknown") for author in authors if author.get("corresponding_author", False)
        ]
        raise BioRxivAuthorError(
            f"Multiple corresponding authors found: {', '.join(corresponding_names)}. "
            "Only one author should be marked with 'corresponding_author: true' in 00_CONFIG.yml"
        )

    # Validate each author has a name
    for i, author in enumerate(authors):
        if not author.get("name"):
            raise BioRxivAuthorError(f"Author at index {i} is missing the 'name' field")


def format_author_row(author_data: dict, affiliation_map: dict) -> list[str]:
    """Format a single author's data as a bioRxiv TSV row.

    Args:
        author_data: Author dictionary with processed data
        affiliation_map: Dictionary mapping affiliation shortnames to full data

    Returns:
        List of column values in bioRxiv order:
        Email, Institution, First Name, Middle Name(s)/Initial(s), Last Name, Suffix,
        Corresponding Author, Home Page URL, Collaborative Group/Consortium, ORCiD
    """
    # Email (decoded from email64)
    email = author_data.get("email", "")

    # Institution (first affiliation's full_name) - encode HTML entities for bioRxiv
    institution = ""
    affiliations = author_data.get("affiliations", [])
    if affiliations and affiliations[0] in affiliation_map:
        institution = encode_html_entities(affiliation_map[affiliations[0]].get("full_name", ""))

    # Parse name into components and encode HTML entities for bioRxiv
    name_str = author_data.get("name", "")
    name_parts = parse_author_name(name_str)

    first_name = encode_html_entities(name_parts.get("first", ""))
    middle_name = encode_html_entities(name_parts.get("middle", ""))
    last_name = encode_html_entities(name_parts.get("last", ""))
    suffix = encode_html_entities(name_parts.get("suffix", ""))

    # Corresponding author (any text for Yes, empty string for No)
    corresponding = "Yes" if author_data.get("corresponding_author", False) else ""

    # Home Page URL (empty - user preference)
    home_page_url = ""

    # Collaborative Group/Consortium (empty)
    collaborative_group = ""

    # ORCiD (if present)
    orcid = author_data.get("orcid", "")

    return [
        email,
        institution,
        first_name,
        middle_name,
        last_name,
        suffix,
        corresponding,
        home_page_url,
        collaborative_group,
        orcid,
    ]


def generate_biorxiv_author_tsv(config_path: Path, output_path: Path) -> Path:
    """Generate bioRxiv author submission template (TSV format).

    Args:
        config_path: Path to the manuscript 00_CONFIG.yml file
        output_path: Path where the TSV file should be written

    Returns:
        Path to the generated TSV file

    Raises:
        BioRxivAuthorError: If author data is invalid or missing
        FileNotFoundError: If config file doesn't exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load manuscript configuration
    config_manager = ConfigManager(config_path.parent)
    config = config_manager.load_config(config_path)

    # Extract authors and affiliations
    authors = config.get("authors", [])
    affiliations = config.get("affiliations", [])

    # Handle multiple corresponding authors: keep only the last one
    corresponding_indices = [i for i, author in enumerate(authors) if author.get("corresponding_author", False)]
    if len(corresponding_indices) > 1:
        # Unmark all but the last corresponding author
        for idx in corresponding_indices[:-1]:
            authors[idx]["corresponding_author"] = False
        logger.warning(
            f"Multiple corresponding authors found. Only keeping the last one: "
            f"{authors[corresponding_indices[-1]].get('name', 'Unknown')}"
        )

    # Validate author data
    validate_author_data(authors)

    # Build affiliation map (shortname -> full data)
    affiliation_map = {}
    for affiliation in affiliations:
        shortname = affiliation.get("shortname", "")
        if shortname:
            affiliation_map[shortname] = affiliation

    # Process authors: decode emails
    processed_authors = []
    for author in authors:
        author_copy = author.copy()

        # Decode email64 if present
        if "email64" in author_copy:
            try:
                author_copy["email"] = decode_email(author_copy["email64"])
            except ValueError as e:
                logger.warning(f"Failed to decode email64 for {author_copy.get('name', 'Unknown')}: {e}")
                author_copy["email"] = ""
        elif "email" not in author_copy:
            author_copy["email"] = ""

        processed_authors.append(author_copy)

    # Generate TSV file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        # Write header row
        header = [
            "Email",
            "Institution",
            "First Name",
            "Middle Name(s)/Initial(s)",
            "Last Name",
            "Suffix",
            "Corresponding Author",
            "Home Page URL",
            "Collaborative Group/Consortium",
            "ORCiD",
        ]
        writer.writerow(header)

        # Write author rows
        for author in processed_authors:
            row = format_author_row(author, affiliation_map)
            writer.writerow(row)

    logger.info(f"Generated bioRxiv author template: {output_path}")
    return output_path


def prepare_biorxiv_package(
    manuscript_path: Path,
    output_dir: Path,
    biorxiv_dir: Path | None = None,
) -> Path:
    """Prepare bioRxiv submission package.

    Creates a directory containing:
    - biorxiv_authors.tsv (author template)
    - manuscript PDF
    - source files (TeX, figures, bibliography)

    Args:
        manuscript_path: Path to the manuscript directory
        output_dir: Path to the rxiv-maker output directory
        biorxiv_dir: Path where bioRxiv submission files will be created.
                     If None, defaults to {output_dir}/biorxiv_submission

    Returns:
        Path to the bioRxiv submission directory

    Raises:
        FileNotFoundError: If required files are missing
    """
    output_path = Path(output_dir)

    # Default bioRxiv directory to be inside the output directory
    if biorxiv_dir is None:
        biorxiv_dir = output_path / "biorxiv_submission"

    biorxiv_path = Path(biorxiv_dir)

    # Create clean bioRxiv directory
    if biorxiv_path.exists():
        shutil.rmtree(biorxiv_path)
    biorxiv_path.mkdir(parents=True)

    manuscript_name = manuscript_path.name if manuscript_path else "manuscript"
    logger.info(f"Preparing bioRxiv submission package for '{manuscript_name}' in {biorxiv_path}")

    # 1. Copy the bioRxiv authors TSV file (already generated)
    tsv_source = output_path / "biorxiv_authors.tsv"
    if not tsv_source.exists():
        raise FileNotFoundError(
            f"bioRxiv author template not found: {tsv_source}\n"
            "Please run TSV generation first or ensure output directory is correct."
        )
    shutil.copy2(tsv_source, biorxiv_path / "biorxiv_authors.tsv")
    logger.info("✓ Copied author template: biorxiv_authors.tsv")

    # 2. Find and copy the manuscript PDF
    pdf_files = list(output_path.glob("*.pdf"))
    main_pdf = None
    for pdf in pdf_files:
        # Skip supplementary PDFs
        if "supplementary" not in pdf.name.lower():
            main_pdf = pdf
            break

    if not main_pdf:
        logger.warning("⚠ No manuscript PDF found in output directory")
    else:
        shutil.copy2(main_pdf, biorxiv_path / main_pdf.name)
        logger.info(f"✓ Copied manuscript PDF: {main_pdf.name}")

    # 3. Copy source files for submission
    # Copy TeX files
    tex_files = list(output_path.glob("*.tex"))
    for tex_file in tex_files:
        shutil.copy2(tex_file, biorxiv_path / tex_file.name)
        logger.info(f"✓ Copied TeX file: {tex_file.name}")

    # Copy style file
    style_file = output_path / "rxiv_maker_style.cls"
    if style_file.exists():
        shutil.copy2(style_file, biorxiv_path / "rxiv_maker_style.cls")
        logger.info("✓ Copied style file: rxiv_maker_style.cls")

    # Copy bibliography
    bib_file = output_path / "03_REFERENCES.bib"
    if bib_file.exists():
        shutil.copy2(bib_file, biorxiv_path / "03_REFERENCES.bib")
        logger.info("✓ Copied bibliography: 03_REFERENCES.bib")

    # Copy FIGURES directory
    figures_source = output_path / "FIGURES"
    if figures_source.exists() and figures_source.is_dir():
        figures_dest = biorxiv_path / "FIGURES"
        shutil.copytree(figures_source, figures_dest)
        figure_count = len(list(figures_dest.rglob("*")))
        logger.info(f"✓ Copied FIGURES directory ({figure_count} files)")

    logger.info(f"\n📦 bioRxiv package prepared in {biorxiv_path}")
    return biorxiv_path


def create_biorxiv_zip(
    biorxiv_path: Path,
    zip_filename: str = "biorxiv_submission.zip",
    manuscript_path: Path | None = None,
) -> Path:
    """Create a ZIP file for bioRxiv submission.

    Args:
        biorxiv_path: Path to the bioRxiv submission directory
        zip_filename: Name of the ZIP file to create
        manuscript_path: Optional manuscript path for naming

    Returns:
        Path to the created ZIP file
    """
    # Use manuscript-aware naming if manuscript path is provided
    if manuscript_path and zip_filename == "biorxiv_submission.zip":
        manuscript_name = manuscript_path.name
        zip_filename = f"{manuscript_name}_biorxiv.zip"

    zip_path = Path(zip_filename).resolve()

    # Define auxiliary files that should be excluded
    auxiliary_extensions = {".aux", ".blg", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz"}

    logger.info(f"\n📁 Creating ZIP package: {zip_path}")

    excluded_files = []
    included_files = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in biorxiv_path.rglob("*"):
            if file_path.is_file():
                # Check if file should be excluded (auxiliary files)
                should_exclude = file_path.suffix.lower() in auxiliary_extensions

                if should_exclude:
                    excluded_files.append(file_path.name)
                    continue

                # Store files with relative paths
                arcname = file_path.relative_to(biorxiv_path)
                zipf.write(file_path, arcname)
                included_files.append(str(arcname))

    logger.info(f"✅ ZIP created: {zip_path}")
    logger.info(f"   Files included: {len(included_files)}")
    if excluded_files:
        logger.info(f"   Files excluded: {len(excluded_files)} (auxiliary files)")

    return zip_path
