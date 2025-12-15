"""Main DOCX exporter orchestrator.

This module coordinates the DOCX export process, bringing together:
- Citation mapping
- Content processing
- Bibliography building
- DOCX writing
"""

from pathlib import Path
from typing import Any, Dict

from ..core.logging_config import get_logger
from ..core.managers.config_manager import ConfigManager
from ..core.path_manager import PathManager
from ..processors.yaml_processor import extract_yaml_metadata
from ..utils.bibliography_parser import parse_bib_file
from ..utils.docx_helpers import format_bibliography_entry, remove_yaml_header
from ..utils.file_helpers import find_manuscript_md
from ..utils.pdf_utils import get_custom_pdf_filename
from .docx_citation_mapper import CitationMapper
from .docx_content_processor import DocxContentProcessor
from .docx_writer import DocxWriter

logger = get_logger()


class DocxExporter:
    """Main orchestrator for DOCX export."""

    def __init__(
        self,
        manuscript_path: str,
        resolve_dois: bool = False,
        include_footnotes: bool = True,
    ):
        """Initialize DOCX exporter.

        Args:
            manuscript_path: Path to manuscript directory
            resolve_dois: Whether to attempt DOI resolution for missing entries
            include_footnotes: Whether to include DOI footnotes
        """
        self.path_manager = PathManager(manuscript_path=manuscript_path)
        self.resolve_dois = resolve_dois
        self.include_footnotes = include_footnotes

        # Load config to get author name format preference
        config_manager = ConfigManager(base_dir=Path(manuscript_path))
        config = config_manager.load_config()
        self.author_format = config.get("bibliography_author_format", "lastname_firstname")

        # Components
        self.citation_mapper = CitationMapper()
        self.content_processor = DocxContentProcessor()
        self.writer = DocxWriter()

        logger.debug(f"DocxExporter initialized: {self.path_manager.manuscript_path}")

    def _get_output_path(self) -> Path:
        """Get output path in manuscript directory with custom filename.

        Returns:
            Path to output DOCX file (in manuscript directory)
        """
        # Get metadata for custom filename
        try:
            manuscript_md = find_manuscript_md(str(self.path_manager.manuscript_path))
            yaml_metadata = extract_yaml_metadata(str(manuscript_md))

            # Generate DOCX name using same pattern as PDF: YEAR__lastname_et_al__rxiv.docx
            pdf_filename = get_custom_pdf_filename(yaml_metadata)
            docx_filename = pdf_filename.replace(".pdf", ".docx")

            return self.path_manager.manuscript_path / docx_filename
        except Exception as e:
            # Fallback to simple name if metadata extraction fails
            logger.warning(f"Could not extract metadata for custom filename: {e}")
            manuscript_name = self.path_manager.manuscript_name
            return self.path_manager.manuscript_path / f"{manuscript_name}.docx"

    def export(self) -> Path:
        """Execute complete DOCX export process.

        Returns:
            Path to generated DOCX file

        Raises:
            FileNotFoundError: If required files are missing
            ValueError: If content cannot be processed
        """
        logger.info("Starting DOCX export...")

        # Step 1: Validate manuscript
        self._validate_manuscript()

        # Step 2: Load markdown content
        markdown_content = self._load_markdown()
        logger.debug(f"Loaded {len(markdown_content)} characters of markdown")

        # Step 3: Extract and map citations
        citations = self.citation_mapper.extract_citations_from_markdown(markdown_content)
        citation_map = self.citation_mapper.create_mapping(citations)
        logger.info(f"Found {len(citation_map)} unique citations")

        # Step 4: Build bibliography
        bibliography = self._build_bibliography(citation_map)
        logger.info(f"Built bibliography with {len(bibliography)} entries")

        # Step 5: Replace citations in text
        markdown_with_numbers = self.citation_mapper.replace_citations_in_text(markdown_content, citation_map)

        # Step 5.5: Replace figure and equation references with numbers
        import re

        # Find all figures and create mapping
        # Allow hyphens and underscores in label names
        figure_labels = re.findall(r"!\[[^\]]*\]\([^)]+\)\s*\n\s*\{#fig:([\w-]+)", markdown_with_numbers)
        figure_map = {label: i + 1 for i, label in enumerate(figure_labels)}

        # Replace @fig:label with "Fig. X" in text, handling optional panel letters
        # Pattern matches: @fig:label optionally followed by space and panel letter(s)
        # Use special markers <<XREF>> to enable yellow highlighting in DOCX
        for label, num in figure_map.items():
            # Match @fig:label with optional panel letters like " a", " a,b", " a-c"
            # Use negative lookahead (?![a-z]) to prevent matching start of words like " is", " and"
            # Panel letters must be followed by non-letter (space, punctuation, end of string)
            markdown_with_numbers = re.sub(
                rf"@fig:{label}\b(\s+[a-z](?:[,\-][a-z])*(?![a-z]))?",
                lambda m, num=num: f"<<XREF>>Fig. {num}{m.group(1) if m.group(1) else ''}<</XREF>>",
                markdown_with_numbers,
            )

        logger.debug(f"Mapped {len(figure_map)} figure labels to numbers")

        # Find all supplementary figures and create mapping
        # Allow hyphens and underscores in label names
        sfig_labels = re.findall(r"!\[[^\]]*\]\([^)]+\)\s*\n\s*\{#sfig:([\w-]+)", markdown_with_numbers)
        sfig_map = {label: i + 1 for i, label in enumerate(sfig_labels)}

        # Replace @sfig:label with "Supp. Fig. X" in text, handling optional panel letters
        for label, num in sfig_map.items():
            # Match panel letters like " a", " b,c" but not words like " is"
            # Negative lookahead prevents matching start of words
            markdown_with_numbers = re.sub(
                rf"@sfig:{label}\b(\s+[a-z](?:[,\-][a-z])*(?![a-z]))?",
                lambda m, num=num: f"<<XREF>>Supp. Fig. {num}{m.group(1) if m.group(1) else ''}<</XREF>>",
                markdown_with_numbers,
            )

        logger.debug(f"Mapped {len(sfig_map)} supplementary figure labels to numbers")

        # Find all tables and create mapping (looking for {#stable:label} tags)
        # Allow hyphens and underscores in label names
        table_labels = re.findall(r"\{#stable:([\w-]+)\}", markdown_with_numbers)
        table_map = {label: i + 1 for i, label in enumerate(table_labels)}

        # Replace @stable:label with "Supp. Table X" in text
        for label, num in table_map.items():
            markdown_with_numbers = re.sub(
                rf"@stable:{label}\b", f"<<XREF>>Supp. Table {num}<</XREF>>", markdown_with_numbers
            )

        logger.debug(f"Mapped {len(table_map)} supplementary table labels to numbers")

        # Find all supplementary notes and create mapping (looking for {#snote:label} tags)
        # Allow hyphens and underscores in label names
        snote_labels = re.findall(r"\{#snote:([\w-]+)\}", markdown_with_numbers)
        snote_map = {label: i + 1 for i, label in enumerate(snote_labels)}

        # Replace @snote:label with "Supp. Note X" in text
        for label, num in snote_map.items():
            markdown_with_numbers = re.sub(
                rf"@snote:{label}\b", f"<<XREF>>Supp. Note {num}<</XREF>>", markdown_with_numbers
            )

        logger.debug(f"Mapped {len(snote_map)} supplementary note labels to numbers")

        # Find all equations and create mapping (looking for {#eq:label} tags)
        # Allow hyphens and underscores in label names
        equation_labels = re.findall(r"\{#eq:([\w-]+)\}", markdown_with_numbers)
        equation_map = {label: i + 1 for i, label in enumerate(equation_labels)}

        # Replace @eq:label with "Eq. X"
        # Handle both @eq:label and (@eq:label) formats
        for label, num in equation_map.items():
            # Replace (@eq:label) with (Eq. X)
            markdown_with_numbers = re.sub(
                rf"\(@eq:{label}\b\)", f"(<<XREF>>Eq. {num}<</XREF>>)", markdown_with_numbers
            )
            # Replace @eq:label with Eq. X
            markdown_with_numbers = re.sub(rf"@eq:{label}\b", f"<<XREF>>Eq. {num}<</XREF>>", markdown_with_numbers)

        logger.debug(f"Mapped {len(equation_map)} equation labels to numbers")

        # Step 5.6: Remove label markers now that mapping is complete
        # These metadata markers should not appear in the final output
        markdown_with_numbers = re.sub(
            r"^\{#(?:fig|sfig|snote|stable|table|eq):[^}]+\}\s*", "", markdown_with_numbers, flags=re.MULTILINE
        )

        # Step 6: Convert content to DOCX structure
        doc_structure = self.content_processor.parse(markdown_with_numbers, citation_map)
        logger.debug(f"Parsed {len(doc_structure['sections'])} sections")

        # Step 6.5: Get metadata for title page
        metadata = self._get_metadata()

        # Step 7: Write DOCX file
        output_path = self._get_output_path()
        docx_path = self.writer.write(
            doc_structure,
            bibliography,
            output_path,
            include_footnotes=self.include_footnotes,
            base_path=self.path_manager.manuscript_path,
            metadata=metadata,
        )
        logger.info(f"DOCX exported successfully: {docx_path}")

        # Step 8: Report results
        self._report_results(citation_map, bibliography)

        return docx_path

    def _validate_manuscript(self):
        """Validate that required manuscript files exist.

        Raises:
            FileNotFoundError: If required files are missing
        """
        main_md = self.path_manager.manuscript_path / "01_MAIN.md"
        if not main_md.exists():
            raise FileNotFoundError(f"01_MAIN.md not found in {self.path_manager.manuscript_path}")

        bib_file = self.path_manager.manuscript_path / "03_REFERENCES.bib"
        if not bib_file.exists():
            raise FileNotFoundError("03_REFERENCES.bib not found (required for citations)")

    def _load_markdown(self) -> str:
        """Load and combine markdown files.

        Returns:
            Combined markdown content with rxiv-maker syntax processed

        Raises:
            FileNotFoundError: If 01_MAIN.md doesn't exist
        """
        from ..processors.markdown_preprocessor import get_markdown_preprocessor

        content = []

        # Get markdown preprocessor for this manuscript
        preprocessor = get_markdown_preprocessor(manuscript_path=str(self.path_manager.manuscript_path))

        # Load 01_MAIN.md
        main_md = self.path_manager.manuscript_path / "01_MAIN.md"
        main_content = main_md.read_text(encoding="utf-8")

        # Remove YAML header
        main_content = remove_yaml_header(main_content)

        # Process rxiv-maker syntax ({{py:exec}}, {{py:get}}, {{tex:...}})
        main_content = preprocessor.process(main_content, target_format="docx", file_path="01_MAIN.md")

        content.append(main_content)

        # Load 02_SUPPLEMENTARY_INFO.md if exists
        supp_md = self.path_manager.manuscript_path / "02_SUPPLEMENTARY_INFO.md"
        if supp_md.exists():
            logger.info("Including supplementary information")
            supp_content = supp_md.read_text(encoding="utf-8")
            supp_content = remove_yaml_header(supp_content)

            # Process rxiv-maker syntax
            supp_content = preprocessor.process(
                supp_content, target_format="docx", file_path="02_SUPPLEMENTARY_INFO.md"
            )

            # Add page break and SI title before supplementary content
            content.append("<!-- PAGE_BREAK -->")
            content.append("# Supplementary Information")
            content.append(supp_content)
        else:
            logger.debug("No supplementary information file found")

        return "\n\n".join(content)

    def _build_bibliography(self, citation_map: Dict[str, int]) -> Dict[int, Dict]:
        """Build bibliography with optional DOI resolution.

        Args:
            citation_map: Mapping from citation keys to numbers

        Returns:
            Bibliography dict mapping numbers to entry info

        Raises:
            FileNotFoundError: If bibliography file doesn't exist
        """
        bib_file = self.path_manager.manuscript_path / "03_REFERENCES.bib"
        entries = parse_bib_file(bib_file)

        # Create lookup dictionary
        entries_by_key = {entry.key: entry for entry in entries}

        bibliography = {}
        missing_keys = []

        for key, number in citation_map.items():
            entry = entries_by_key.get(key)

            if not entry:
                logger.warning(f"Citation key '{key}' not found in bibliography")
                missing_keys.append(key)
                continue

            # Get DOI from entry
            doi = entry.fields.get("doi")

            # TODO: Implement DOI resolution if requested and DOI missing
            # if self.resolve_dois and not doi:
            #     doi = self._resolve_doi_from_metadata(entry)

            # Format entry (full format for DOCX bibliography)
            formatted = format_bibliography_entry(entry, doi, slim=False, author_format=self.author_format)

            bibliography[number] = {"key": key, "entry": entry, "doi": doi, "formatted": formatted}

        if missing_keys:
            logger.warning(f"{len(missing_keys)} citation(s) not found in bibliography: {', '.join(missing_keys)}")

        return bibliography

    def _get_metadata(self) -> Dict[str, Any]:
        """Extract metadata for title page.

        Returns:
            Metadata dictionary with title, authors, affiliations, etc.
        """
        try:
            manuscript_md = find_manuscript_md(str(self.path_manager.manuscript_path))
            metadata = extract_yaml_metadata(str(manuscript_md))
            return metadata
        except Exception as e:
            logger.warning(f"Could not extract metadata: {e}")
            return {}

    def _report_results(self, citation_map: Dict[str, int], bibliography: Dict[int, Dict]):
        """Report export statistics.

        Args:
            citation_map: Citation mapping
            bibliography: Bibliography entries
        """
        total_citations = len(citation_map)
        resolved_dois = sum(1 for b in bibliography.values() if b["doi"])
        missing_dois = len(bibliography) - resolved_dois

        logger.info("Export complete:")
        logger.info(f"  - {total_citations} unique citations")
        logger.info(f"  - {resolved_dois} DOIs found")

        if missing_dois > 0:
            logger.warning(
                f"  - {missing_dois} citation(s) missing DOIs (run with --resolve-dois to attempt resolution)"
            )
