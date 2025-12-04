"""DOCX writer for rxiv-maker export.

This module handles the actual generation of DOCX files using python-docx,
writing structured content with formatting and footnotes.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from ..core.logging_config import get_logger
from ..utils.docx_helpers import convert_pdf_to_image

logger = get_logger()


class DocxWriter:
    """Writes structured content to DOCX files using python-docx."""

    def write(
        self,
        doc_structure: Dict[str, Any],
        bibliography: Dict[int, Dict],
        output_path: Path,
        include_footnotes: bool = True,
        base_path: Optional[Path] = None,
    ) -> Path:
        """Write DOCX file from structured content.

        Args:
            doc_structure: Structured document with sections
            bibliography: Bibliography entries mapped by number
            output_path: Path where DOCX file should be saved
            include_footnotes: Whether to add DOI footnotes
            base_path: Base path for resolving relative figure paths

        Returns:
            Path to created DOCX file
        """
        self.base_path = base_path or Path.cwd()
        doc = Document()

        # Collect figures to add at the end
        figures = []

        # Process each section (skip figures for now)
        for section in doc_structure["sections"]:
            if section["type"] == "figure":
                figures.append(section)
            else:
                self._add_section(doc, section, bibliography, include_footnotes)

        # Add figures at the end
        if figures:
            # Add page break before figures
            doc.add_page_break()

            # Add "Figures" heading
            doc.add_heading("Figures", level=1)

            # Add each figure
            for figure in figures:
                self._add_figure(doc, figure)

        # Save document
        doc.save(str(output_path))
        return output_path

    def _add_section(
        self,
        doc: Document,
        section: Dict[str, Any],
        bibliography: Dict[int, Dict],
        include_footnotes: bool,
    ):
        """Add a section to the document.

        Args:
            doc: Document object
            section: Section data
            bibliography: Bibliography entries
            include_footnotes: Whether to add footnotes
        """
        section_type = section["type"]

        if section_type == "heading":
            self._add_heading(doc, section)
        elif section_type == "paragraph":
            self._add_paragraph(doc, section, bibliography, include_footnotes)
        elif section_type == "list":
            self._add_list(doc, section)
        elif section_type == "code_block":
            self._add_code_block(doc, section)
        elif section_type == "figure":
            self._add_figure(doc, section)

    def _add_heading(self, doc: Document, section: Dict[str, Any]):
        """Add heading to document.

        Args:
            doc: Document object
            section: Heading section data with 'level' and 'text'
        """
        level = section["level"]
        text = section["text"]
        doc.add_heading(text, level=level)

    def _add_paragraph(
        self,
        doc: Document,
        section: Dict[str, Any],
        bibliography: Dict[int, Dict],
        include_footnotes: bool,
    ):
        """Add paragraph with formatted runs to document.

        Args:
            doc: Document object
            section: Paragraph section data with 'runs'
            bibliography: Bibliography entries
            include_footnotes: Whether to add footnotes
        """
        paragraph = doc.add_paragraph()

        # Set justified alignment for all paragraphs
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        runs_data = section["runs"]

        for run_data in runs_data:
            self._add_run(paragraph, run_data, bibliography, include_footnotes)

    def _add_run(self, paragraph, run_data: Dict[str, Any], bibliography: Dict[int, Dict], include_footnotes: bool):
        """Add a single run to a paragraph.

        Args:
            paragraph: Paragraph object
            run_data: Run data with type and formatting
            bibliography: Bibliography entries
            include_footnotes: Whether to add footnotes
        """
        if run_data["type"] == "text":
            text = run_data["text"]
            run = paragraph.add_run(text)

            # Apply formatting
            if run_data.get("bold"):
                run.bold = True
            if run_data.get("italic"):
                run.italic = True
            if run_data.get("code"):
                run.font.name = "Courier New"
                run.font.size = Pt(10)

        elif run_data["type"] == "citation":
            cite_num = run_data["number"]
            run = paragraph.add_run(f"[{cite_num}]")
            # Make citations bold and slightly smaller, but not superscript
            run.bold = True
            run.font.size = Pt(10)

            # Add footnote if requested and bibliography entry exists
            if include_footnotes and cite_num in bibliography:
                bib_entry = bibliography[cite_num]
                self._add_footnote(run, bib_entry)

    def _add_list(self, doc: Document, section: Dict[str, Any]):
        """Add list to document.

        Args:
            doc: Document object
            section: List section data with 'list_type' and 'items'
        """
        list_type = section["list_type"]
        items = section["items"]

        for item in items:
            doc.add_paragraph(item, style="List Bullet" if list_type == "bullet" else "List Number")

    def _add_code_block(self, doc: Document, section: Dict[str, Any]):
        """Add code block to document.

        Args:
            doc: Document object
            section: Code block section data with 'content'
        """
        code_content = section["content"]
        paragraph = doc.add_paragraph(code_content)

        # Style as code
        for run in paragraph.runs:
            run.font.name = "Courier New"
            run.font.size = Pt(9)

        # Set paragraph formatting
        paragraph_format = paragraph.paragraph_format
        paragraph_format.left_indent = Pt(36)  # Indent code blocks

    def _add_figure(self, doc: Document, section: Dict[str, Any]):
        """Add figure to document with caption.

        Args:
            doc: Document object
            section: Figure section data with 'path', 'caption', 'label'
        """
        figure_path = Path(section["path"])
        caption = section.get("caption", "")
        label = section.get("label", "")

        # Resolve relative path
        if not figure_path.is_absolute():
            figure_path = self.base_path / figure_path

        # Try to convert PDF to image if it's a PDF
        img_bytes = None
        if figure_path.exists() and figure_path.suffix.lower() == ".pdf":
            img_bytes = convert_pdf_to_image(figure_path)
        elif not figure_path.exists():
            logger.warning(f"Figure file not found: {figure_path}")

        if img_bytes:
            # Add image
            try:
                doc.add_picture(img_bytes, width=Inches(6))
                logger.debug(f"Embedded figure: {figure_path}")
            except Exception as e:
                logger.warning(f"Failed to embed figure {figure_path}: {e}")
                # Add placeholder text
                p = doc.add_paragraph()
                run = p.add_run(f"[Figure: {figure_path.name}]")
                run.italic = True
        else:
            # Add placeholder if conversion failed or not a PDF
            p = doc.add_paragraph()
            run = p.add_run(f"[Figure: {figure_path.name}]")
            run.italic = True
            logger.warning(f"Could not embed figure: {figure_path}")

        # Add caption
        if caption:
            caption_para = doc.add_paragraph()
            caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Format as "Figure label: caption"
            if label:
                run = caption_para.add_run(f"Figure {label}: ")
                run.bold = True
            else:
                run = caption_para.add_run("Figure: ")
                run.bold = True

            caption_para.add_run(caption)

            # Add spacing after figure
            caption_para.paragraph_format.space_after = Pt(12)

    def _add_footnote(self, run, bib_entry: Dict[str, Any]):
        """Add footnote with bibliography entry and DOI.

        Args:
            run: Run object to attach footnote to
            bib_entry: Bibliography entry with 'formatted' text and optional 'doi'
        """
        # Note: python-docx doesn't have built-in footnote support
        # We'll need to add it via OOXML
        # For MVP, we'll add a simplified version

        # TODO: Implement proper footnote support
        # For now, we'll add the citation in a comment or just the number
        # Full footnote implementation requires OOXML manipulation

        # Simplified approach: Add footnote-like paragraph at end
        # (This is a limitation of python-docx - proper footnotes need OOXML)
        pass

    def _add_hyperlink(self, paragraph, url: str, text: str):
        """Add hyperlink to paragraph.

        Args:
            paragraph: Paragraph object
            url: URL to link to
            text: Display text
        """
        # Add hyperlink using OOXML
        part = paragraph.part
        r_id = part.relate_to(
            url,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )

        # Create hyperlink element
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)

        # Create run element
        new_run = OxmlElement("w:r")

        # Create run properties
        r_pr = OxmlElement("w:rPr")

        # Add underline
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        r_pr.append(u)

        # Add color (blue)
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "0000FF")
        r_pr.append(color)

        new_run.append(r_pr)

        # Create text element
        text_element = OxmlElement("w:t")
        text_element.text = text
        new_run.append(text_element)

        hyperlink.append(new_run)
        paragraph._p.append(hyperlink)
