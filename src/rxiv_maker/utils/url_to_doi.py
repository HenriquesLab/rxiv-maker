"""Utility functions for extracting DOIs from URLs."""

import re
from typing import Optional
from urllib.parse import urlparse


def extract_doi_from_url(url: str) -> Optional[str]:
    """Extract DOI from a URL.

    This function handles various URL formats from different publishers and
    converts them to standard DOI format.

    Args:
        url: URL string that may contain a DOI

    Returns:
        DOI string if found, None otherwise

    Examples:
        >>> extract_doi_from_url("https://www.nature.com/articles/d41586-022-00563-z")
        "10.1038/d41586-022-00563-z"

        >>> extract_doi_from_url("https://doi.org/10.1038/nature12373")
        "10.1038/nature12373"

        >>> extract_doi_from_url("https://dx.doi.org/10.1126/science.1234567")
        "10.1126/science.1234567"

        >>> extract_doi_from_url("https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0123456")
        "10.1371/journal.pone.0123456"
    """
    if not url:
        return None

    # If it's already a DOI (starts with 10.), return as-is
    if url.startswith("10."):
        return url

    # Parse the URL
    try:
        parsed = urlparse(url)
    except Exception:
        return None

    # Common DOI URL patterns
    doi_patterns = [
        # Direct DOI URLs: https://doi.org/10.1038/nature12373
        r"/(?:doi/)?(?:abs/)?(?:full/)?(?:pdf/)?(10\.\d{4,}[^\s]*)",
        # Nature articles: https://www.nature.com/articles/d41586-022-00563-z
        r"/articles/([^/?#&]+)",
        # Science articles: https://science.sciencemag.org/content/123/456/789
        r"/content/\d+/\d+/\d+(?:/([^/?#&]+))?",
        # PLoS articles: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0123456
        r"[?&]id=(10\.\d{4,}[^\s&]*)",
        # arXiv: https://arxiv.org/abs/1234.5678
        r"/abs/(\d{4}\.\d{4,}(?:v\d+)?)",
        # bioRxiv/medRxiv: https://www.biorxiv.org/content/10.1101/2023.01.01.522473v1
        r"/content/(?:early/\d{4}/\d{2}/\d{2}/)?(10\.1101/[^/?#&]+)",
    ]

    # Try each pattern
    for pattern in doi_patterns:
        matches = re.findall(pattern, url, re.IGNORECASE)
        if matches:
            potential_doi = matches[0]

            # Handle special cases
            if parsed.netloc and "nature.com" in parsed.netloc:
                # Nature articles need prefix
                if not potential_doi.startswith("10."):
                    potential_doi = f"10.1038/{potential_doi}"
            elif parsed.netloc and "sciencemag.org" in parsed.netloc:
                # Science articles need prefix
                if not potential_doi.startswith("10."):
                    potential_doi = f"10.1126/science.{potential_doi}"
            elif parsed.netloc and "arxiv.org" in parsed.netloc:
                # arXiv papers - these don't have DOIs, but we can construct a DOI
                if not potential_doi.startswith("10."):
                    potential_doi = f"10.48550/arXiv.{potential_doi}"

            # Validate the extracted DOI format
            if _is_valid_doi_format(potential_doi):
                return potential_doi

    # Try to extract any DOI-like pattern from the entire URL
    doi_in_url = re.search(r"(10\.\d{4,}/[^\s/?#&]+)", url, re.IGNORECASE)
    if doi_in_url:
        potential_doi = doi_in_url.group(1)
        if _is_valid_doi_format(potential_doi):
            return potential_doi

    return None


def _is_valid_doi_format(doi: str) -> bool:
    """Check if a string matches valid DOI format.

    Args:
        doi: Potential DOI string

    Returns:
        True if valid DOI format, False otherwise
    """
    if not doi:
        return False

    # DOI format regex from CrossRef documentation
    doi_pattern = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
    return bool(doi_pattern.match(doi))


def normalize_doi_input(input_str: str) -> str:
    """Normalize input that could be either a DOI or URL containing a DOI.

    Args:
        input_str: Input string (DOI or URL)

    Returns:
        Normalized DOI string

    Raises:
        ValueError: If no valid DOI can be extracted
    """
    if not input_str:
        raise ValueError("Empty input provided")

    # Try to extract DOI from the input
    doi = extract_doi_from_url(input_str)
    if doi:
        return doi

    # If we couldn't extract a DOI, raise an error with helpful message
    if input_str.startswith("http"):
        raise ValueError(f"Could not extract a valid DOI from URL: {input_str}")
    else:
        raise ValueError(
            f"Invalid DOI format: {input_str}. DOIs should start with '10.' or be a valid URL containing a DOI"
        )
