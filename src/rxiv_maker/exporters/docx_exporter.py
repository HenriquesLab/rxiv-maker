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

        # Load config to get author name format preference and DOCX options
        config_manager = ConfigManager(base_dir=Path(manuscript_path))
        config = config_manager.load_config()
        self.author_format = config.get("bibliography_author_format", "lastname_firstname")

        # DOCX export options
        docx_config = config.get("docx", {})
        self.hide_si = docx_config.get("hide_si", False)  # Default to False (don't hide SI) for backwards compatibility
        self.figures_at_end = docx_config.get("figures_at_end", False)  # Default to False (inline figures)
        self.hide_highlighting = docx_config.get("hide_highlighting", False)  # Default to False (show highlights)
        self.hide_comments = docx_config.get("hide_comments", False)  # Default to False (include comments)

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

        # Step 2.5: If SI is hidden from export, still load it for label mapping
        si_content_for_mapping = ""
        if self.hide_si:
            si_content_for_mapping = self._load_si_for_mapping()
            if si_content_for_mapping:
                logger.info("📋 Loaded SI content for label mapping (SI section hidden from export)")

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

        # Extract all labels using centralized utility
        from ..utils.label_extractor import LabelExtractor

        label_extractor = LabelExtractor()

        # Find all figures and create mapping
        figure_map = label_extractor.extract_figure_labels(markdown_with_numbers)

        # Replace @fig:label with "Fig. X" in text, handling optional panel letters
        # Pattern matches: @fig:label optionally followed by space and panel letter(s)
        # Use special markers <<XREF:type>> to enable color-coded highlighting in DOCX
        for label, num in figure_map.items():
            # Match @fig:label with optional panel letters like " a", " a,b", " a-c"
            # Use negative lookahead (?![a-z]) to prevent matching start of words like " is", " and"
            # Panel letters must be followed by non-letter (space, punctuation, end of string)
            markdown_with_numbers = re.sub(
                rf"@fig:{label}\b(\s+[a-z](?:[,\-][a-z])*(?![a-z]))?",
                lambda m, num=num: f"<<XREF:fig>>Fig. {num}{m.group(1).strip() if m.group(1) else ''}<</XREF>>",
                markdown_with_numbers,
            )

        logger.debug(f"Mapped {len(figure_map)} figure labels to numbers")

        # Find all supplementary figures and create mapping
        # IMPORTANT: When SI is excluded, extract from SI content (where figures are defined)
        content_to_scan_for_sfigs = si_content_for_mapping if si_content_for_mapping else markdown_with_numbers
        sfig_map = label_extractor.extract_supplementary_figure_labels(content_to_scan_for_sfigs)

        # Replace @sfig:label with "Supp. Fig. X" in text, handling optional panel letters
        for label, num in sfig_map.items():
            # Match panel letters like " a", " b,c" but not words like " is"
            # Negative lookahead prevents matching start of words
            markdown_with_numbers = re.sub(
                rf"@sfig:{label}\b(\s+[a-z](?:[,\-][a-z])*(?![a-z]))?",
                lambda m, num=num: f"<<XREF:sfig>>Supp. Fig. {num}{m.group(1).strip() if m.group(1) else ''}<</XREF>>",
                markdown_with_numbers,
            )

        logger.debug(f"Mapped {len(sfig_map)} supplementary figure labels to numbers")

        # Find all tables and create mapping (looking for {#stable:label} or \label{stable:label} tags)
        # IMPORTANT: PDF uses the order that tables are DEFINED in the document (order of \label{stable:X})
        # When SI is excluded from export, we still need to extract labels from SI
        content_to_scan_for_tables = si_content_for_mapping if si_content_for_mapping else markdown_with_numbers
        table_map = label_extractor.extract_supplementary_table_labels(content_to_scan_for_tables)
        logger.debug(f"Mapped {len(table_map)} supplementary tables: {table_map}")

        # Replace @stable:label with "Supp. Table X" in text
        for label, num in table_map.items():
            markdown_with_numbers = re.sub(
                rf"@stable:{label}\b", f"<<XREF:stable>>Supp. Table {num}<</XREF>>", markdown_with_numbers
            )

        # Find all supplementary notes and create mapping (looking for {#snote:label} tags)
        # IMPORTANT: When SI is excluded, extract from SI content (where notes are defined)
        content_to_scan_for_snotes = si_content_for_mapping if si_content_for_mapping else markdown_with_numbers
        snote_map = label_extractor.extract_supplementary_note_labels(content_to_scan_for_snotes)

        # Replace @snote:label with "Supp. Note X" in text
        for label, num in snote_map.items():
            markdown_with_numbers = re.sub(
                rf"@snote:{label}\b", f"<<XREF:snote>>Supp. Note {num}<</XREF>>", markdown_with_numbers
            )

        logger.debug(f"Mapped {len(snote_map)} supplementary note labels to numbers")

        # Find all equations and create mapping (looking for {#eq:label} tags)
        equation_map = label_extractor.extract_equation_labels(markdown_with_numbers)

        # Replace @eq:label with "Eq. X"
        # Handle both @eq:label and (@eq:label) formats
        for label, num in equation_map.items():
            # Replace (@eq:label) with (Eq. X)
            markdown_with_numbers = re.sub(
                rf"\(@eq:{label}\b\)", f"(<<XREF:eq>>Eq. {num}<</XREF>>)", markdown_with_numbers
            )
            # Replace @eq:label with Eq. X
            markdown_with_numbers = re.sub(rf"@eq:{label}\b", f"<<XREF:eq>>Eq. {num}<</XREF>>", markdown_with_numbers)

        logger.debug(f"Mapped {len(equation_map)} equation labels to numbers")

        # Step 5.6: Remove label markers now that mapping is complete
        # These metadata markers should not appear in the final output
        # NOTE: Keep fig/sfig/stable/table labels - they're needed by content processor and removed during caption parsing
        markdown_with_numbers = re.sub(r"^\{#(?:snote|eq):[^}]+\}\s*", "", markdown_with_numbers, flags=re.MULTILINE)

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
            table_map=table_map,
            equation_map=equation_map,
            figures_at_end=self.figures_at_end,
            hide_highlighting=self.hide_highlighting,
            hide_comments=self.hide_comments,
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

        # Load 02_SUPPLEMENTARY_INFO.md if exists and not configured to hide SI
        supp_md = self.path_manager.manuscript_path / "02_SUPPLEMENTARY_INFO.md"
        if supp_md.exists() and not self.hide_si:
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
        elif supp_md.exists() and self.hide_si:
            logger.info("Supplementary information exists but hidden per config (docx.hide_si: true)")
        else:
            logger.debug("No supplementary information file found")

        return "\n\n".join(content)

    def _load_si_for_mapping(self) -> str:
        r"""Load SI content for label mapping without including in export.

        This method is used when hide_si is True but we still need to extract
        SI labels (stable, sfig, snote) for cross-references in the main text.

        IMPORTANT: We return RAW content (before preprocessing) because we need to
        extract LaTeX labels (\label{stable:X}) which determine the PDF numbering order.
        The preprocessor strips out {{tex: blocks, losing this ordering information.

        Returns:
            SI content as string (raw, before preprocessing), or empty string if SI doesn't exist
        """
        supp_md = self.path_manager.manuscript_path / "02_SUPPLEMENTARY_INFO.md"
        if not supp_md.exists():
            return ""

        # Load RAW SI content (don't preprocess - we need LaTeX labels for ordering)
        supp_content = supp_md.read_text(encoding="utf-8")
        supp_content = remove_yaml_header(supp_content)

        return supp_content

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

            # Attempt DOI resolution if requested and DOI missing
            if self.resolve_dois and not doi:
                doi = self._resolve_doi_from_metadata(entry)
                if doi:
                    # Store in entry for this export
                    entry.fields["doi"] = doi
                    logger.info(f"Resolved DOI for {key}: {doi}")

            # Format entry (full format for DOCX bibliography)
            # Don't include DOI in formatted text - it will be added separately as a hyperlink by the writer
            formatted = format_bibliography_entry(entry, doi=None, slim=False, author_format=self.author_format)

            bibliography[number] = {"key": key, "entry": entry, "doi": doi, "formatted": formatted}

        if missing_keys:
            logger.warning(f"{len(missing_keys)} citation(s) not found in bibliography: {', '.join(missing_keys)}")

        return bibliography

    def _resolve_doi_from_metadata(self, entry) -> str | None:
        """Resolve DOI from entry metadata using CrossRef API.

        Args:
            entry: Bibliography entry to resolve DOI for

        Returns:
            Resolved DOI if found, None otherwise
        """
        import requests

        # Try to construct a search query from available fields
        title = entry.fields.get("title", "").strip()
        year = entry.fields.get("year", "").strip()

        if not title:
            logger.debug(f"Cannot resolve DOI for {entry.key}: no title")
            return None

        # Clean title for search (remove LaTeX commands, braces, etc.)
        search_title = self._clean_title_for_search(title)

        # Try CrossRef search API
        try:
            url = "https://api.crossref.org/works"
            params = {
                "query.title": search_title,
                "rows": 5,  # Get top 5 results
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get("message", {}).get("items", [])

                # Find best match
                for item in items:
                    item_title = item.get("title", [""])[0].lower()
                    search_title_lower = search_title.lower()

                    # Simple similarity check - titles should be very similar
                    if item_title and (search_title_lower in item_title or item_title in search_title_lower):
                        # Verify year matches if available
                        if year:
                            item_year = item.get("published", {}).get("date-parts", [[None]])[0][0]
                            if item_year and str(item_year) != year:
                                continue

                        doi = item.get("DOI")
                        if doi:
                            logger.info(f"Resolved DOI for {entry.key}: {doi}")
                            return doi

            logger.debug(f"Could not resolve DOI for {entry.key} via CrossRef")
            return None

        except requests.exceptions.Timeout:
            logger.debug(f"CrossRef API timeout resolving DOI for {entry.key}")
            return None
        except requests.exceptions.ConnectionError:
            logger.debug(f"CrossRef API connection error for {entry.key}")
            return None
        except Exception as e:
            logger.debug(f"Error resolving DOI for {entry.key}: {e}")
            return None

    def _clean_title_for_search(self, title: str) -> str:
        """Clean title for CrossRef search by removing LaTeX commands.

        Args:
            title: Raw title from BibTeX entry

        Returns:
            Cleaned title suitable for search
        """
        import re

        # Remove LaTeX commands
        title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", title)  # \textit{foo} -> foo
        title = re.sub(r"\\[a-zA-Z]+", "", title)  # \LaTeX -> LaTeX

        # Remove braces
        title = title.replace("{", "").replace("}", "")

        # Remove special characters
        title = re.sub(r"[^a-zA-Z0-9\s\-]", " ", title)

        # Normalize whitespace
        title = " ".join(title.split())

        return title.strip()

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
