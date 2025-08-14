"""YAML processing utilities for Rxiv-Maker.

This module handles the extraction and parsing of YAML metadata from markdown files.
"""

import re
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# Import email processing utilities
def _get_email_processor():
    """Get the email processing function with fallback."""
    try:
        from ..utils.email_encoder import process_author_emails

        return process_author_emails
    except ImportError:
        # Fallback if utils package is not available
        def fallback_processor(authors):
            """Fallback function if email_encoder is not available."""
            return authors

        return fallback_processor


process_author_emails = _get_email_processor()


def find_config_file(md_file):
    """Find the configuration file for the manuscript."""
    from pathlib import Path

    md_path = Path(md_file)
    manuscript_dir = md_path.parent

    # Look for config file: 00_CONFIG.yml
    config_file = manuscript_dir / "00_CONFIG.yml"
    if config_file.exists():
        return config_file

    # Fall back to looking for YAML in the markdown file itself
    return None


def extract_yaml_metadata(md_file):
    """Extract yaml metadata from separate config file or from the markdown file."""
    # First try to find separate config file
    config_file = find_config_file(md_file)
    if config_file:
        print(f"Loading metadata from separate config file: {config_file}")
        with open(config_file, encoding="utf-8") as file:
            yaml_content = file.read()

        if yaml:
            try:
                metadata = yaml.safe_load(yaml_content)
                # Process email64 fields if present
                if metadata and "authors" in metadata:
                    metadata["authors"] = process_author_emails(metadata["authors"])
                return metadata
            except yaml.YAMLError as e:
                print(f"Error parsing YAML config file: {e}")
                return {}
        else:
            metadata = parse_yaml_simple(yaml_content)
            # Process email64 fields if present
            if metadata and "authors" in metadata:
                metadata["authors"] = process_author_emails(metadata["authors"])
            return metadata

    # Fall back to extracting from markdown file
    print(f"Looking for YAML metadata in markdown file: {md_file}")
    with open(md_file, encoding="utf-8") as file:
        content = file.read()

    # Use regex to find YAML metadata block
    match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        yaml_content = match.group(1)
        if yaml:
            try:
                metadata = yaml.safe_load(yaml_content)
                # Process email64 fields if present
                if metadata and "authors" in metadata:
                    metadata["authors"] = process_author_emails(metadata["authors"])
                return metadata
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}")
                return {}
        else:
            # Fallback to simple parsing if yaml is not available
            metadata = parse_yaml_simple(yaml_content)
            # Process email64 fields if present
            if metadata and "authors" in metadata:
                metadata["authors"] = process_author_emails(metadata["authors"])
            return metadata
    else:
        return {}


def get_doi_validation_setting(metadata: dict) -> bool:
    """Extract DOI validation setting from metadata with default fallback.

    Args:
        metadata: Parsed YAML metadata dictionary

    Returns:
        bool: True if DOI validation should be enabled, False otherwise
    """
    if not metadata:
        return True  # Default to enabled

    doi_setting = metadata.get("enable_doi_validation")

    if doi_setting is None:
        return True  # Default to enabled if not specified

    # Handle string representations of booleans
    if isinstance(doi_setting, str):
        return doi_setting.lower() in ("true", "yes", "1", "on")

    # Handle boolean values
    return bool(doi_setting)


def parse_yaml_simple(yaml_content):
    """Simple YAML parser for basic key-value pairs."""
    metadata: dict[str, Any] = {}
    lines = yaml_content.strip().split("\n")
    current_key = None
    current_value = []
    current_indent = 0
    in_list = False

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped_line = line.strip()

        if not stripped_line:
            i += 1
            continue

        # Get indentation level
        indent = len(line) - len(line.lstrip())

        # Handle key-value pairs
        if ":" in stripped_line and not stripped_line.startswith("-"):
            # Save previous key if exists
            if current_key:
                _save_current_value(metadata, current_key, current_value, in_list)

            key, value = stripped_line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            current_indent = indent
            in_list = False

            # Handle inline values
            if value:
                if value.startswith("[") and value.endswith("]"):
                    # Handle inline array like ["item1", "item2"]
                    current_value = _parse_inline_array(value)
                    in_list = True
                else:
                    # Regular string value
                    current_value = value.strip("\"'")
                    in_list = False
            else:
                # Value will be on next lines
                current_value = []
                in_list = True

        # Handle list items
        elif stripped_line.startswith("-") and current_key and indent > current_indent:
            if not in_list:
                current_value = []
                in_list = True

            item_text = stripped_line[1:].strip()

            # Check if this is a complex item (has nested structure)
            if ":" in item_text:
                # This is a nested object
                item_obj = {}
                obj_key, obj_value = item_text.split(":", 1)
                obj_key = obj_key.strip()
                obj_value = obj_value.strip().strip("\"'")
                item_obj[obj_key] = obj_value

                # Look ahead for more nested properties
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].rstrip()
                    next_stripped = next_line.strip()
                    next_indent = len(next_line) - len(next_line.lstrip())

                    if not next_stripped:
                        j += 1
                        continue

                    if next_indent > indent and ":" in next_stripped and not next_stripped.startswith("-"):
                        prop_key, prop_value = next_stripped.split(":", 1)
                        prop_key = prop_key.strip()
                        prop_value = prop_value.strip().strip("\"'")
                        item_obj[prop_key] = prop_value
                        j += 1
                    else:
                        break

                current_value.append(item_obj)
                i = j - 1  # Adjust loop counter
            else:
                # Simple list item
                current_value.append(item_text.strip("\"'"))

        i += 1

    # Save the last key
    if current_key:
        _save_current_value(metadata, current_key, current_value, in_list)

    return metadata


def _save_current_value(metadata, key, value, is_list):
    """Helper function to save the current value to metadata."""
    if is_list and isinstance(value, list):
        metadata[key] = value
    elif is_list and not isinstance(value, list):
        metadata[key] = [value] if value else []
    else:
        metadata[key] = value


def _parse_inline_array(array_str):
    """Parse inline array like ["item1", "item2"]."""
    # Remove brackets
    content = array_str[1:-1].strip()
    if not content:
        return []

    # Split by comma and clean up
    items = []
    for item in content.split(","):
        item = item.strip().strip('"')
        if item:
            items.append(item)

    return items
