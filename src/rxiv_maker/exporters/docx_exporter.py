"""Main DOCX exporter orchestrator.

This module coordinates the DOCX export process, bringing together:
- Citation mapping
- Content processing
- Bibliography building
- DOCX writing
"""

from pathlib import Path
from typing import Dict

from ..core.logging_config import get_logger
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

        # Step 6: Convert content to DOCX structure
        doc_structure = self.content_processor.parse(markdown_with_numbers, citation_map)
        logger.debug(f"Parsed {len(doc_structure['sections'])} sections")

        # Step 7: Write DOCX file
        output_path = self._get_output_path()
        docx_path = self.writer.write(
            doc_structure,
            bibliography,
            output_path,
            include_footnotes=self.include_footnotes,
            base_path=self.path_manager.manuscript_path,
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
            Combined markdown content

        Raises:
            FileNotFoundError: If 01_MAIN.md doesn't exist
        """
        content = []

        # Load 01_MAIN.md
        main_md = self.path_manager.manuscript_path / "01_MAIN.md"
        main_content = main_md.read_text(encoding="utf-8")

        # Remove YAML header
        main_content = remove_yaml_header(main_content)
        content.append(main_content)

        # Load 02_SUPPLEMENTARY_INFO.md if exists
        supp_md = self.path_manager.manuscript_path / "02_SUPPLEMENTARY_INFO.md"
        if supp_md.exists():
            logger.info("Including supplementary information")
            supp_content = supp_md.read_text(encoding="utf-8")
            supp_content = remove_yaml_header(supp_content)
            content.append("\n\n# Supplementary Information\n\n" + supp_content)
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

            # Format entry
            formatted = format_bibliography_entry(entry, doi)

            bibliography[number] = {"key": key, "entry": entry, "doi": doi, "formatted": formatted}

        if missing_keys:
            logger.warning(f"{len(missing_keys)} citation(s) not found in bibliography: {', '.join(missing_keys)}")

        return bibliography

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
