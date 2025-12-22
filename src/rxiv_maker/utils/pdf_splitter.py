"""PDF splitting utilities for separating main and SI sections."""

import logging
from pathlib import Path
from typing import Optional, Tuple

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


def find_si_start_page(pdf_path: Path) -> Optional[int]:
    """Find the page number where Supplementary Information starts.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Page number (0-indexed) where SI starts, or None if not found
    """
    try:
        reader = PdfReader(pdf_path)

        # Search for common SI markers
        si_markers = [
            "Supplementary Information",
            "Supplementary Material",
            "Supplementary Data",
            "Supporting Information",
            "SI APPENDIX",
            "SUPPLEMENTARY FIGURES",
            "Supplementary Methods",
        ]

        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()

                # Check for SI markers (case-insensitive)
                text_upper = text.upper()
                for marker in si_markers:
                    if marker.upper() in text_upper:
                        logger.info(f"Found SI marker '{marker}' on page {page_num + 1}")
                        return page_num

            except Exception as e:
                logger.debug(f"Could not extract text from page {page_num}: {e}")
                continue

        logger.warning("Could not find SI start marker in PDF")
        return None

    except Exception as e:
        logger.error(f"Error finding SI start: {e}")
        return None


def split_pdf(
    pdf_path: Path,
    si_start_page: Optional[int] = None,
) -> Tuple[Optional[Path], Optional[Path]]:
    """Split PDF into main and SI sections.

    Args:
        pdf_path: Path to the PDF file to split
        si_start_page: Page number (0-indexed) where SI starts. If None, will auto-detect.

    Returns:
        Tuple of (main_pdf_path, si_pdf_path). Either may be None if splitting fails.
    """
    try:
        # Auto-detect SI start if not provided
        if si_start_page is None:
            si_start_page = find_si_start_page(pdf_path)

        if si_start_page is None:
            logger.warning("Cannot split PDF: SI start page not found")
            return None, None

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        if si_start_page >= total_pages:
            logger.error(f"SI start page {si_start_page} exceeds total pages {total_pages}")
            return None, None

        # Generate output paths
        stem = pdf_path.stem
        parent = pdf_path.parent

        main_path = parent / f"{stem}__main.pdf"
        si_path = parent / f"{stem}__si.pdf"

        # Create main PDF (pages before SI)
        main_writer = PdfWriter()
        for page_num in range(si_start_page):
            main_writer.add_page(reader.pages[page_num])

        with open(main_path, "wb") as f:
            main_writer.write(f)
        logger.info(f"Created main PDF: {main_path} ({si_start_page} pages)")

        # Create SI PDF (pages from SI onwards)
        si_writer = PdfWriter()
        for page_num in range(si_start_page, total_pages):
            si_writer.add_page(reader.pages[page_num])

        with open(si_path, "wb") as f:
            si_writer.write(f)
        logger.info(f"Created SI PDF: {si_path} ({total_pages - si_start_page} pages)")

        return main_path, si_path

    except Exception as e:
        logger.error(f"Error splitting PDF: {e}")
        return None, None
