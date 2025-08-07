"""Add bibliography entries from DOI to the bibliography file."""

import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from crossref_commons.retrieval import get_publication_as_json

from rxiv_maker.utils.doi_cache import DOICache

logger = logging.getLogger(__name__)


class BibliographyAdder:
    """Add bibliography entries from DOI to bibliography file."""

    # DOI format regex from CrossRef documentation
    DOI_REGEX = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)

    def __init__(self, manuscript_path: str):
        """Initialize bibliography adder.

        Args:
            manuscript_path: Path to manuscript directory
        """
        self.manuscript_path = Path(manuscript_path)
        self.bib_file = self.manuscript_path / "03_REFERENCES.bib"
        self.cache = DOICache()

    def add_entries(self, doi_inputs: list[str], overwrite: bool = False) -> bool:
        """Add bibliography entries for the given DOIs or URLs.

        Args:
            doi_inputs: List of DOI strings or URLs containing DOIs to add
            overwrite: Whether to overwrite existing entries

        Returns:
            True if all entries were added successfully, False otherwise
        """
        success = True

        # Ensure bibliography file exists
        if not self.bib_file.exists():
            print(f"Creating new bibliography file: {self.bib_file}")
            self.bib_file.touch()

        # Read existing bibliography
        existing_entries = self._get_existing_entries()

        # Process each DOI input (could be DOI or URL)
        for doi_input in doi_inputs:
            try:
                # Normalize input to proper DOI format
                try:
                    from ..utils.url_to_doi import normalize_doi_input

                    doi = normalize_doi_input(doi_input)
                    if doi_input != doi:
                        print(f"INFO: Converted URL to DOI: {doi_input} → {doi}")
                except ValueError as e:
                    print(f"ERROR: {e}")
                    success = False
                    continue

                # Validate DOI format (should be valid after normalization)
                if not self._validate_doi_format(doi):
                    print(f"ERROR: Invalid DOI format after normalization: {doi}")
                    success = False
                    continue

                # Check if entry already exists
                if self._doi_exists(doi, existing_entries) and not overwrite:
                    print(f"SKIP: DOI {doi} already exists in bibliography")
                    continue

                # Fetch metadata
                metadata = self._fetch_metadata(doi)
                if not metadata:
                    print(f"ERROR: Could not fetch metadata for DOI: {doi}")
                    success = False
                    continue

                # Generate bibliography entry
                entry = self._generate_bib_entry(doi, metadata)
                if not entry:
                    print(f"ERROR: Could not generate bibliography entry for DOI: {doi}")
                    success = False
                    continue

                # Add to bibliography
                self._add_to_bibliography(entry, overwrite)
                print(f"SUCCESS: Added entry for DOI: {doi}")

            except Exception as e:
                print(f"ERROR: Failed to process input {doi_input}: {e}")
                success = False

        return success

    def _validate_doi_format(self, doi: str) -> bool:
        """Validate DOI format.

        Args:
            doi: DOI string to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(self.DOI_REGEX.match(doi))

    def _get_existing_entries(self) -> dict[str, str]:
        """Get existing bibliography entries.

        Returns:
            Dictionary mapping DOIs to entry keys
        """
        entries: dict[str, str] = {}

        if not self.bib_file.exists():
            return entries

        try:
            content = self.bib_file.read_text(encoding="utf-8")

            # Extract DOIs from existing entries
            doi_pattern = re.compile(r"doi\s*=\s*\{([^}]+)\}", re.IGNORECASE)
            entry_pattern = re.compile(r"@\w+\s*\{\s*([^,\s}]+)", re.IGNORECASE)

            for match in entry_pattern.finditer(content):
                entry_start = match.start()
                entry_key = match.group(1)

                # Find the end of this entry
                brace_count = 0
                entry_end = entry_start
                for i, char in enumerate(content[entry_start:], entry_start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            entry_end = i + 1
                            break

                entry_content = content[entry_start:entry_end]
                doi_match = doi_pattern.search(entry_content)
                if doi_match:
                    entries[doi_match.group(1)] = entry_key

        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Could not access bibliography file: {e}")
        except UnicodeDecodeError as e:
            logger.warning(f"Bibliography file encoding error: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error reading bibliography file: {e}")

        return entries

    def _doi_exists(self, doi: str, existing_entries: dict[str, str]) -> bool:
        """Check if DOI already exists in bibliography.

        Args:
            doi: DOI to check
            existing_entries: Dictionary of existing DOIs

        Returns:
            True if DOI exists, False otherwise
        """
        return doi in existing_entries

    def _fetch_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata for DOI from CrossRef or DataCite.

        Args:
            doi: DOI to fetch metadata for

        Returns:
            Metadata dictionary or None if not found
        """
        # Try cache first
        cached_metadata = self.cache.get(doi)
        if cached_metadata:
            return cached_metadata

        # Try CrossRef API first
        try:
            result = get_publication_as_json(doi)
            if result:
                # CrossRef API returns data directly, not wrapped in 'message'
                metadata = result
                metadata["_source"] = "CrossRef"
                self.cache.set(doi, metadata)
                logger.debug(f"Found DOI in CrossRef: {doi}")
                return metadata
        except requests.exceptions.Timeout:
            logger.debug(f"CrossRef API timeout for {doi}")
        except requests.exceptions.ConnectionError:
            logger.debug(f"CrossRef API connection error for {doi}")
        except requests.exceptions.HTTPError as e:
            logger.debug(f"CrossRef API HTTP error for {doi}: {e}")
        except Exception as e:
            logger.debug(f"CrossRef API unexpected error for {doi}: {e}")

        # If CrossRef failed, try DataCite
        try:
            metadata = self._fetch_datacite_metadata(doi)
            if metadata:
                metadata["_source"] = "DataCite"
                self.cache.set(doi, metadata)
                logger.debug(f"Found DOI in DataCite: {doi}")
                return metadata
        except requests.exceptions.Timeout:
            logger.debug(f"DataCite API timeout for {doi}")
        except requests.exceptions.ConnectionError:
            logger.debug(f"DataCite API connection error for {doi}")
        except requests.exceptions.HTTPError as e:
            logger.debug(f"DataCite API HTTP error for {doi}: {e}")
        except Exception as e:
            logger.debug(f"DataCite API unexpected error for {doi}: {e}")

        return None

    def _fetch_datacite_metadata(self, doi: str) -> dict[str, Any] | None:
        """Fetch metadata from DataCite API.

        Args:
            doi: DOI to fetch metadata for

        Returns:
            Metadata dictionary or None if not found
        """
        # Add small delay to respect rate limits
        time.sleep(0.1)

        # DataCite REST API endpoint
        url = f"https://api.datacite.org/dois/{doi}"
        headers = {"Accept": "application/json"}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "data" in data and "attributes" in data["data"]:
                return data["data"]["attributes"]
        elif response.status_code == 404:
            return None
        else:
            response.raise_for_status()

        return None

    def _generate_bib_entry(self, doi: str, metadata: dict[str, Any]) -> str | None:
        """Generate bibliography entry from metadata.

        Args:
            doi: DOI string
            metadata: CrossRef or DataCite metadata

        Returns:
            BibTeX entry string or None if generation fails
        """
        try:
            source = metadata.get("_source", "CrossRef")

            # Generate entry key from first author and year
            entry_key = self._generate_entry_key(metadata, source)

            # Determine entry type
            entry_type = self._get_entry_type(metadata, source)

            # Extract fields
            fields = self._extract_fields(metadata, doi, source)

            # Format entry
            entry_lines = [f"@{entry_type}{{{entry_key},"]

            # Add fields with proper formatting
            for field, value in fields.items():
                if value:
                    entry_lines.append(f"  {field:<12} = {{{value}}},")

            entry_lines.append("}")

            return "\n".join(entry_lines)

        except Exception as e:
            logger.error(f"Error generating bibliography entry: {e}")
            return None

    def _generate_entry_key(self, metadata: dict[str, Any], source: str = "CrossRef") -> str:
        """Generate entry key from metadata.

        Args:
            metadata: CrossRef or DataCite metadata
            source: Source of metadata ('CrossRef' or 'DataCite')

        Returns:
            Entry key string
        """
        # Get first author family name
        first_author = "unknown"

        if source == "DataCite":
            if "creators" in metadata and metadata["creators"]:
                first_creator = metadata["creators"][0]
                first_author = first_creator.get("familyName", "unknown")
        else:  # CrossRef
            if "author" in metadata and metadata["author"]:
                first_author = metadata["author"][0].get("family", "unknown")

        # Get year
        year = "unknown"

        if source == "DataCite":
            if "publicationYear" in metadata:
                year = str(metadata["publicationYear"])
        else:  # CrossRef
            if "published-print" in metadata:
                date_parts = metadata["published-print"].get("date-parts", [[]])[0]
                if date_parts:
                    year = str(date_parts[0])
            elif "published-online" in metadata:
                date_parts = metadata["published-online"].get("date-parts", [[]])[0]
                if date_parts:
                    year = str(date_parts[0])

        # Clean and format
        first_author = re.sub(r"[^\w]", "", first_author.lower())

        return f"{first_author}{year}"

    def _get_entry_type(self, metadata: dict[str, Any], source: str = "CrossRef") -> str:
        """Get BibTeX entry type from metadata.

        Args:
            metadata: CrossRef or DataCite metadata
            source: Source of metadata ('CrossRef' or 'DataCite')

        Returns:
            Entry type string
        """
        if source == "DataCite":
            # DataCite resource types
            resource_type = metadata.get("types", {}).get("resourceTypeGeneral", "Text")

            # Map DataCite types to BibTeX types
            datacite_mapping = {
                "JournalArticle": "article",
                "ConferencePaper": "inproceedings",
                "Book": "book",
                "BookChapter": "inbook",
                "Report": "techreport",
                "Dissertation": "phdthesis",
                "Dataset": "misc",
                "Software": "misc",
                "Text": "article",
            }

            return datacite_mapping.get(resource_type, "misc")
        else:
            # CrossRef types
            entry_type = metadata.get("type", "article")

            # Map CrossRef types to BibTeX types
            crossref_mapping = {
                "journal-article": "article",
                "conference-paper": "inproceedings",
                "book": "book",
                "book-chapter": "inbook",
                "report": "techreport",
                "dissertation": "phdthesis",
                "posted-content": "misc",
            }

            return crossref_mapping.get(entry_type, "article")

    def _extract_fields(self, metadata: dict[str, Any], doi: str, source: str = "CrossRef") -> dict[str, str]:
        """Extract fields from metadata.

        Args:
            metadata: CrossRef or DataCite metadata
            doi: DOI string
            source: Source of metadata ('CrossRef' or 'DataCite')

        Returns:
            Dictionary of field names to values
        """
        fields = {}

        if source == "DataCite":
            # Title
            if "titles" in metadata and metadata["titles"]:
                title = metadata["titles"][0].get("title", "")
                fields["title"] = self._clean_text(title)

            # Authors/Creators
            if "creators" in metadata and metadata["creators"]:
                authors = []
                for creator in metadata["creators"]:
                    if "familyName" in creator and "givenName" in creator:
                        authors.append(f"{creator['familyName']}, {creator['givenName']}")
                    elif "familyName" in creator:
                        authors.append(creator["familyName"])
                    elif "name" in creator:
                        authors.append(creator["name"])
                if authors:
                    fields["author"] = " and ".join(authors)

            # Year
            if "publicationYear" in metadata:
                fields["year"] = str(metadata["publicationYear"])

            # Publisher
            if "publisher" in metadata:
                fields["publisher"] = self._clean_text(metadata["publisher"])

            # URL (if available)
            if "url" in metadata:
                fields["url"] = metadata["url"]

        else:  # CrossRef
            # Title
            if "title" in metadata and metadata["title"]:
                title = metadata["title"][0] if isinstance(metadata["title"], list) else metadata["title"]
                fields["title"] = self._clean_text(title)

            # Authors
            if "author" in metadata and metadata["author"]:
                authors = []
                for author in metadata["author"]:
                    if "family" in author and "given" in author:
                        authors.append(f"{author['family']}, {author['given']}")
                    elif "family" in author:
                        authors.append(author["family"])
                if authors:
                    fields["author"] = " and ".join(authors)

            # Journal
            if "container-title" in metadata and metadata["container-title"]:
                journal = (
                    metadata["container-title"][0]
                    if isinstance(metadata["container-title"], list)
                    else metadata["container-title"]
                )
                fields["journal"] = self._clean_text(journal)

            # Volume
            if "volume" in metadata:
                fields["volume"] = str(metadata["volume"])

            # Issue/Number
            if "issue" in metadata:
                fields["number"] = str(metadata["issue"])

            # Pages
            if "page" in metadata:
                fields["pages"] = str(metadata["page"])

            # Year
            if "published-print" in metadata:
                date_parts = metadata["published-print"].get("date-parts", [[]])[0]
                if date_parts:
                    fields["year"] = str(date_parts[0])
            elif "published-online" in metadata:
                date_parts = metadata["published-online"].get("date-parts", [[]])[0]
                if date_parts:
                    fields["year"] = str(date_parts[0])

            # Publisher
            if "publisher" in metadata:
                fields["publisher"] = self._clean_text(metadata["publisher"])

        # DOI (common to both)
        fields["doi"] = doi

        return fields

    def _clean_text(self, text: str) -> str:
        """Clean text for BibTeX entry.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Handle special characters
        text = text.replace("&amp;", "\\&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _add_to_bibliography(self, entry: str, overwrite: bool = False):
        """Add entry to bibliography file.

        Args:
            entry: BibTeX entry string
            overwrite: Whether to overwrite existing entry
        """
        # Read existing content
        existing_content = ""
        if self.bib_file.exists():
            existing_content = self.bib_file.read_text(encoding="utf-8")

        # Add new entry
        if existing_content and not existing_content.endswith("\n"):
            existing_content += "\n"

        new_content = existing_content + entry + "\n"

        # Write back to file
        self.bib_file.write_text(new_content, encoding="utf-8")


# CLI integration
def main():
    """Main function for CLI integration."""
    import argparse

    parser = argparse.ArgumentParser(description="Add bibliography entries from DOIs or URLs")
    parser.add_argument("manuscript_path", help="Path to manuscript directory")
    parser.add_argument("dois", nargs="+", help="DOI strings or URLs containing DOIs to add")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing entries")

    args = parser.parse_args()

    adder = BibliographyAdder(args.manuscript_path)
    success = adder.add_entries(args.dois, overwrite=args.overwrite)

    if success:
        print("Bibliography entries added successfully!")
    else:
        print("Some entries could not be added.")
        exit(1)


if __name__ == "__main__":
    main()
