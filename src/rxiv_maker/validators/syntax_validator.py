"""Special syntax validator for custom markers and formatting elements."""

import os
import re
from typing import Any

from .base_validator import BaseValidator, ValidationLevel, ValidationResult


class SyntaxValidator(BaseValidator):
    """Validates special syntax elements and custom formatting."""

    # Special page control markers
    PAGE_MARKERS = {
        "newpage": re.compile(r"<newpage>"),
        "clearpage": re.compile(r"<clearpage>"),
        "float_barrier": re.compile(r"<float-barrier>"),
    }

    # Text formatting patterns
    TEXT_FORMATTING = {
        "bold": re.compile(r"\*\*(.+?)\*\*"),
        "italic": re.compile(r"\*(.+?)\*"),
        "subscript": re.compile(r"~([^~\s]+)~"),
        "superscript": re.compile(r"\^([^\^\s]+)\^"),
        "inline_code": re.compile(r"`([^`]+)`"),
        "double_backtick_code": re.compile(r"``([^`]+)``"),
    }

    # List patterns
    LIST_PATTERNS = {
        "unordered_dash": re.compile(r"^\s*-\s+(.+)$"),
        "unordered_asterisk": re.compile(r"^\s*\*\s+(.+)$"),
        "ordered_number": re.compile(r"^\s*\d+\.\s+(.+)$"),
        "ordered_paren": re.compile(r"^\s*\d+\)\s+(.+)$"),
    }

    # Code block patterns
    CODE_PATTERNS = {
        "fenced_code": re.compile(r"^```(\w+)?\s*$.*?^```\s*$", re.MULTILINE | re.DOTALL),
        "fenced_code_start": re.compile(r"^```(\w+)?\s*$", re.MULTILINE),
        "indented_code": re.compile(r"^(    .+)$", re.MULTILINE),
        "html_code": re.compile(r"<code>(.*?)</code>", re.DOTALL),
    }

    # HTML patterns
    HTML_PATTERNS = {
        "html_comment": re.compile(r"<!--(.*?)-->", re.DOTALL),
        "html_bold": re.compile(r"<b>(.*?)</b>"),
        "html_italic": re.compile(r"<i>(.*?)</i>"),
        "html_code": re.compile(r"<code>(.*?)</code>"),
        "html_br": re.compile(r"<br\s*/?>"),
        "html_entities": re.compile(r"&(amp|lt|gt|copy|reg|mdash|ndash|nbsp|hellip);"),
    }

    # URL and link patterns
    LINK_PATTERNS = {
        "markdown_link": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
        "markdown_image": re.compile(r"!\[([^\]]*)\]\(([^)]+)\)"),
        "bare_url": re.compile(r'https?://[^\s<>"]+'),
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    }

    # Table patterns
    TABLE_PATTERNS = {
        "table_row": re.compile(r"^\|.*\|$"),
        "table_separator": re.compile(r"^\|[-:\s]*(?:\|[-:\s]*)+$"),
    }

    # Special arrow patterns
    ARROW_PATTERNS = {
        "right_arrow": re.compile(r"→"),
        "left_arrow": re.compile(r"←"),
        "up_arrow": re.compile(r"↑"),
        "down_arrow": re.compile(r"↓"),
    }

    # Standard manuscript sections that should be level 2 headings (##)
    STANDARD_SECTIONS = {
        "Abstract",
        "Introduction",
        "Methods",
        "Materials and Methods",
        "Results",
        "Discussion",
        "Conclusion",
        "Conclusions",
        "Acknowledgements",
        "Acknowledgments",
        "References",
        "Supplementary Information",
        "Supplementary Material",
        "Appendix",
        "Abbreviations",
        "Declarations",
        "Ethics Statement",
        "Data Availability",
        "Code Availability",
        "Author Contributions",
        "Competing Interests",
        "Funding",
    }

    def __init__(self, manuscript_path: str):
        """Initialize syntax validator.

        Args:
            manuscript_path: Path to the manuscript directory
        """
        super().__init__(manuscript_path)
        self.found_elements: dict[str, list[dict]] = {
            "page_markers": [],
            "formatting": [],
            "lists": [],
            "code_blocks": [],
            "html_elements": [],
            "links": [],
            "images": [],
            "tables": [],
            "special_chars": [],
            "headings": [],
        }
        # Cache for protected content to avoid recomputing
        self._protected_content_cache: dict[str, str] = {}

    def validate(self) -> ValidationResult:
        """Validate special syntax elements in manuscript files."""
        errors = []
        metadata = {}

        # Validate title synchronization first
        title_errors = self._validate_title_sync()
        errors.extend(title_errors)

        # Process manuscript files
        files_to_check = [
            ("01_MAIN.md", "main"),
            ("02_SUPPLEMENTARY_INFO.md", "supplementary"),
        ]

        for filename, file_type in files_to_check:
            file_path = os.path.join(self.manuscript_path, filename)
            if os.path.exists(file_path):
                file_errors = self._validate_file_syntax(file_path, file_type)
                errors.extend(file_errors)

        # Add statistics to metadata
        metadata.update(self._generate_syntax_statistics())

        return ValidationResult("SyntaxValidator", errors, metadata)

    def _validate_title_sync(self) -> list:
        """Validate title synchronization between config and main file.

        Returns:
            List of validation errors if titles are mismatched
        """
        errors = []

        try:
            from pathlib import Path

            from ..utils.title_sync import extract_title_from_config, extract_title_from_main

            manuscript_dir = Path(self.manuscript_path)

            # Find config file (check in order of preference)
            config_path = manuscript_dir / "00_CONFIG.yml"
            if not config_path.exists():
                # Fallback to alternative config file names
                alt_paths = [
                    manuscript_dir / "rxiv.yml",
                    manuscript_dir / "rxiv.yaml",
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        config_path = alt_path
                        break

            main_path = manuscript_dir / "01_MAIN.md"

            # Extract titles
            config_title = extract_title_from_config(config_path)
            main_title, is_auto_generated, line_num = extract_title_from_main(main_path)

            # Check for mismatch (only if both exist and manual title in main)
            if config_title and main_title and not is_auto_generated:
                # Normalize for comparison
                config_normalized = config_title.strip().lower()
                main_normalized = main_title.strip().lower()

                if config_normalized != main_normalized:
                    # Get config file name for error message
                    config_name = config_path.name if config_path.exists() else "00_CONFIG.yml"

                    errors.append(
                        self._create_error(
                            ValidationLevel.ERROR,
                            "Title mismatch between config and main manuscript",
                            file_path=str(main_path),
                            line_number=line_num,
                            context=f"Config: '{config_title}' | Main: '{main_title}'",
                            suggestion=(
                                f"Update either the title in {config_name} or the # heading in 01_MAIN.md to match.\n"
                                f"   Or remove the # heading from 01_MAIN.md (line {line_num}) to use only the config title."
                            ),
                            error_code="title_mismatch",
                        )
                    )

        except ImportError:
            # Title sync module not available, skip validation
            pass
        except Exception as e:
            # Don't fail validation if title sync check fails
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Could not validate title synchronization: {e}",
                    error_code="title_sync_check_failed",
                )
            )

        return errors

    def _validate_file_syntax(self, file_path: str, file_type: str) -> list:
        """Validate special syntax in a specific file."""
        errors = []
        content = self._read_file_safely(file_path)

        if not content:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Could not read file: {os.path.basename(file_path)}",
                    file_path=file_path,
                )
            )
            return errors

        lines = content.split("\n")

        # Cache protected content for this file (avoids recomputing multiple times)
        protected_content = self._protect_validation_sensitive_content(content)
        self._protected_content_cache[file_path] = protected_content

        # Validate page markers
        marker_errors = self._validate_page_markers(protected_content, file_path)
        errors.extend(marker_errors)

        # Validate text formatting
        format_errors = self._validate_text_formatting(content, file_path)
        errors.extend(format_errors)

        # Validate unbalanced formatting
        unbalanced_errors = self._validate_unbalanced_formatting(content, file_path)
        errors.extend(unbalanced_errors)

        # Validate lists
        list_errors = self._validate_lists(lines, file_path)
        errors.extend(list_errors)

        # Validate code blocks
        code_errors = self._validate_code_blocks(content, file_path)
        errors.extend(code_errors)

        # Validate HTML elements
        html_errors = self._validate_html_elements(content, file_path)
        errors.extend(html_errors)

        # Validate links, images, and URLs
        link_errors = self._validate_links(protected_content, file_path)
        errors.extend(link_errors)

        # Validate images
        image_errors = self._validate_images(content, file_path)
        errors.extend(image_errors)

        # Validate tables
        table_errors = self._validate_tables(lines, file_path)
        errors.extend(table_errors)

        # Validate special characters
        char_errors = self._validate_special_characters(content, file_path)
        errors.extend(char_errors)

        # Validate heading levels
        heading_errors = self._validate_headings(lines, file_path, file_type)
        errors.extend(heading_errors)

        return errors

    def _validate_page_markers(self, protected_content: str, file_path: str) -> list:
        """Validate page control markers.

        Args:
            protected_content: Content with code blocks/comments protected
            file_path: Path to the file being validated
        """
        errors = []

        for marker_type, pattern in self.PAGE_MARKERS.items():
            for match in pattern.finditer(protected_content):
                if "XXPROTECTEDCODEXX" in match.group(0):
                    # Skip protected code - page markers in code blocks are docs
                    continue

                line_num = protected_content[: match.start()].count("\n") + 1

                # Store found marker
                self.found_elements["page_markers"].append(
                    {
                        "type": marker_type,
                        "line": line_num,
                        "file": os.path.basename(file_path),
                    }
                )

                # Check if marker is on its own line (recommended)
                lines = protected_content.split("\n")
                if line_num <= len(lines):
                    line_content = lines[line_num - 1].strip()
                    if line_content != match.group(0):
                        errors.append(
                            self._create_error(
                                ValidationLevel.INFO,
                                f"Page marker {match.group(0)} not on separate line",
                                file_path=file_path,
                                line_number=line_num,
                                context=line_content,
                                suggestion=("Place page markers on their own lines for clarity"),
                                error_code="inline_page_marker",
                            )
                        )

        return errors

    def _validate_text_formatting(self, content: str, file_path: str) -> list:
        """Validate text formatting elements."""
        errors = []

        for format_type, pattern in self.TEXT_FORMATTING.items():
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                formatted_text = match.group(1) if match.groups() else match.group(0)

                # Store found formatting
                self.found_elements["formatting"].append(
                    {
                        "type": format_type,
                        "content": formatted_text,
                        "line": line_num,
                        "file": os.path.basename(file_path),
                    }
                )

                # Check for common formatting issues
                format_errors = self._check_formatting_issues(
                    format_type, formatted_text, match.group(0), file_path, line_num
                )
                errors.extend(format_errors)

        return errors

    def _check_formatting_issues(
        self,
        format_type: str,
        content: str,
        full_match: str,
        file_path: str,
        line_num: int,
    ) -> list:
        """Check for common formatting issues."""
        errors = []

        # Check for empty formatting
        if not content.strip():
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Empty {format_type} formatting: {full_match}",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="Remove empty formatting or add content",
                    error_code="empty_formatting",
                )
            )

        # Check for nested formatting of the same type
        if format_type == "bold" and "**" in content:
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "Nested bold formatting detected",
                    file_path=file_path,
                    line_number=line_num,
                    context=full_match,
                    suggestion="Avoid nesting the same formatting type",
                    error_code="nested_formatting",
                )
            )

        # Check for very long inline code
        if format_type in ["inline_code", "double_backtick_code"] and len(content) > 100:
            errors.append(
                self._create_error(
                    ValidationLevel.INFO,
                    f"Very long inline code ({len(content)} characters)",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="Consider using a code block for long code snippets",
                    error_code="long_inline_code",
                )
            )

        return errors

    def _validate_unbalanced_formatting(self, content: str, file_path: str) -> list:
        """Validate for unbalanced formatting markers."""
        errors = []

        # Protect all code blocks, HTML comments, and Python expressions from formatting validation
        protected_content = self._protect_validation_sensitive_content(content)

        # Check for unbalanced bold formatting (**)
        lines = protected_content.split("\n")
        for line_idx, line in enumerate(lines):
            line_num = line_idx + 1

            # Skip lines that are entirely protected code
            if "XXPROTECTEDCODEXX" in line and line.strip().startswith("XXPROTECTEDCODEXX"):
                continue

            # Remove any remaining protected code segments from the line
            clean_line = re.sub(r"XXPROTECTEDCODEXX\d+XXPROTECTEDCODEXX", "", line)

            # Count unescaped double asterisks
            double_star_count = len(re.findall(r"(?<!\\)\*\*", clean_line))

            # If odd number, we have unbalanced bold formatting
            if double_star_count % 2 != 0:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        "Unbalanced bold formatting (**) detected",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="Ensure all ** markers are properly paired",
                        error_code="unbalanced_bold",
                    )
                )

            # Count single asterisks (excluding those that are part of **)
            # Remove ** first, then count remaining *
            no_double_stars = re.sub(r"(?<!\\)\*\*", "", clean_line)
            single_star_count = len(re.findall(r"(?<!\\)\*", no_double_stars))

            # If odd number, we have unbalanced italic formatting
            if single_star_count % 2 != 0:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        "Unbalanced italic formatting (*) detected",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="Ensure all * markers are properly paired",
                        error_code="unbalanced_italic",
                    )
                )

        return errors

    def _validate_lists(self, lines: list[str], file_path: str) -> list:
        """Validate list formatting."""
        errors = []

        for line_num, line in enumerate(lines, 1):
            for list_type, pattern in self.LIST_PATTERNS.items():
                match = pattern.match(line)
                if match:
                    list_content = match.group(1)

                    # Store found list item
                    self.found_elements["lists"].append(
                        {
                            "type": list_type,
                            "content": list_content,
                            "line": line_num,
                            "file": os.path.basename(file_path),
                        }
                    )

                    # Check for empty list items
                    if not list_content.strip():
                        errors.append(
                            self._create_error(
                                ValidationLevel.WARNING,
                                "Empty list item",
                                file_path=file_path,
                                line_number=line_num,
                                context=line,
                                suggestion="Add content to list item or remove it",
                                error_code="empty_list_item",
                            )
                        )

        return errors

    def _validate_code_blocks(self, content: str, file_path: str) -> list:
        """Validate code block formatting."""
        errors = []

        # Check for unclosed fenced code blocks
        lines = content.split("\n")
        in_code_block = False
        code_block_start_line = None

        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                if in_code_block:
                    # Found closing marker
                    in_code_block = False
                    code_block_start_line = None
                else:
                    # Found opening marker
                    in_code_block = True
                    code_block_start_line = line_num

        # If still in code block at end of file, it's unclosed
        if in_code_block and code_block_start_line:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Unclosed code block starting at line {code_block_start_line}",
                    file_path=file_path,
                    line_number=code_block_start_line,
                    suggestion="Add closing ``` to end the code block",
                    error_code="unclosed_code_block",
                )
            )

        # Check fenced code blocks
        for match in self.CODE_PATTERNS["fenced_code"].finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            language = match.group(1) if match.groups() else None

            # Store found code block
            self.found_elements["code_blocks"].append(
                {
                    "type": "fenced",
                    "language": language,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                }
            )

            # Check for missing language specification
            if not language:
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        "Code block without language specification",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=("Specify language for syntax highlighting (e.g., ```python)"),
                        error_code="no_code_language",
                    )
                )

        # Check indented code blocks
        lines = content.split("\n")
        in_code_block = False
        code_block_start = None

        for line_num, line in enumerate(lines, 1):
            if self.CODE_PATTERNS["indented_code"].match(line):
                if not in_code_block:
                    in_code_block = True
                    code_block_start = line_num

                    # Store found indented code block
                    self.found_elements["code_blocks"].append(
                        {
                            "type": "indented",
                            "line": line_num,
                            "file": os.path.basename(file_path),
                        }
                    )
            elif in_code_block and line.strip() == "":
                # Empty line in code block is ok
                continue
            elif in_code_block:
                # End of code block
                in_code_block = False

                # Suggest using fenced code blocks
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        (f"Indented code block (lines {code_block_start}-{line_num - 1})"),
                        file_path=file_path,
                        line_number=code_block_start,
                        suggestion=("Consider using fenced code blocks (```) for better syntax highlighting"),
                        error_code="indented_code_block",
                    )
                )

        return errors

    def _validate_html_elements(self, content: str, file_path: str) -> list:
        """Validate HTML elements."""
        errors = []

        for html_type, pattern in self.HTML_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1

                # Store found HTML element
                self.found_elements["html_elements"].append(
                    {
                        "type": html_type,
                        "content": match.group(0),
                        "line": line_num,
                        "file": os.path.basename(file_path),
                    }
                )

                # Check for discouraged HTML usage
                if html_type in ["html_bold", "html_italic", "html_code"]:
                    markdown_equivalent = {
                        "html_bold": "**text**",
                        "html_italic": "*text*",
                        "html_code": "`text`",
                    }

                    errors.append(
                        self._create_error(
                            ValidationLevel.INFO,
                            f"HTML {html_type.replace('html_', '')} tag used",
                            file_path=file_path,
                            line_number=line_num,
                            context=match.group(0),
                            suggestion=(f"Consider using Markdown syntax: {markdown_equivalent[html_type]}"),
                            error_code="html_instead_of_markdown",
                        )
                    )

        return errors

    def _validate_links(self, protected_content: str, file_path: str) -> list:
        """Validate links and URLs.

        Args:
            protected_content: Content with code blocks/comments protected
            file_path: Path to the file being validated
        """
        errors = []

        # Check markdown links
        for match in self.LINK_PATTERNS["markdown_link"].finditer(protected_content):
            if "XXPROTECTEDCODEXX" in match.group(0):
                continue  # Skip protected code

            line_num = protected_content[: match.start()].count("\n") + 1
            link_text = match.group(1)
            link_url = match.group(2)

            # Store found link
            self.found_elements["links"].append(
                {
                    "type": "markdown_link",
                    "text": link_text,
                    "url": link_url,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                }
            )

            # Check for empty link text
            if not link_text.strip():
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        "Link with empty text",
                        file_path=file_path,
                        line_number=line_num,
                        context=match.group(0),
                        suggestion="Provide descriptive link text",
                        error_code="empty_link_text",
                    )
                )

            # Check for suspicious URLs
            if link_url.startswith("http://"):
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        "HTTP URL used (consider HTTPS)",
                        file_path=file_path,
                        line_number=line_num,
                        context=match.group(0),
                        suggestion="Use HTTPS URLs when possible for security",
                        error_code="http_url",
                    )
                )

        # Check bare URLs (but skip those in code blocks or within markdown links)
        for match in self.LINK_PATTERNS["bare_url"].finditer(protected_content):
            if "XXPROTECTEDCODEXX" in match.group(0):
                continue  # Skip protected code - URLs in code blocks are intentional

            # Check if this URL is part of a markdown link
            url_start = match.start()

            # Look for markdown link patterns that might contain this URL
            is_part_of_markdown_link = False
            for link_match in self.LINK_PATTERNS["markdown_link"].finditer(protected_content):
                link_start = link_match.start()
                link_end = link_match.end()

                # Check if the URL is within the bounds of a markdown link
                if link_start <= url_start < link_end:
                    is_part_of_markdown_link = True
                    break

            if is_part_of_markdown_link:
                continue  # Skip URLs that are part of markdown links

            line_num = protected_content[: match.start()].count("\n") + 1

            # Store found bare URL
            self.found_elements["links"].append(
                {
                    "type": "bare_url",
                    "url": match.group(0),
                    "line": line_num,
                    "file": os.path.basename(file_path),
                }
            )

            # Suggest using markdown link format
            errors.append(
                self._create_error(
                    ValidationLevel.INFO,
                    "Bare URL found",
                    file_path=file_path,
                    line_number=line_num,
                    context=match.group(0),
                    suggestion=("Consider using markdown link format: [description](URL)"),
                    error_code="bare_url",
                )
            )

        return errors

    def _validate_tables(self, lines: list[str], file_path: str) -> list:
        """Validate table formatting."""
        errors = []

        in_table = False
        table_start = None
        header_found = False
        separator_found = False

        for line_num, line in enumerate(lines, 1):
            is_table_row = bool(self.TABLE_PATTERNS["table_row"].match(line))
            is_separator = bool(self.TABLE_PATTERNS["table_separator"].match(line))

            if is_table_row or is_separator:
                if not in_table:
                    in_table = True
                    table_start = line_num
                    header_found = is_table_row
                    separator_found = is_separator

                    # Store found table
                    self.found_elements["tables"].append({"line": line_num, "file": os.path.basename(file_path)})
                elif is_separator:
                    separator_found = True

            elif in_table:
                # End of table
                in_table = False

                # Check table structure
                if header_found and not separator_found:
                    errors.append(
                        self._create_error(
                            ValidationLevel.ERROR,
                            f"Table missing separator row (line {table_start})",
                            file_path=file_path,
                            line_number=table_start,
                            suggestion=("Add separator row with | --- | after table header"),
                            error_code="missing_table_separator",
                        )
                    )

                # Reset for next table
                header_found = False
                separator_found = False

        return errors

    def _validate_special_characters(self, content: str, file_path: str) -> list:
        """Validate special characters and arrows."""
        errors = []

        for arrow_type, pattern in self.ARROW_PATTERNS.items():
            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1

                # Store found special character
                self.found_elements["special_chars"].append(
                    {
                        "type": arrow_type,
                        "char": match.group(0),
                        "line": line_num,
                        "file": os.path.basename(file_path),
                    }
                )

                # Info about arrow usage (valid but might need LaTeX math mode)
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        f"Unicode arrow character used: {match.group(0)}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=("Consider using LaTeX math arrows (\\rightarrow, \\leftarrow) for consistency"),
                        error_code="unicode_arrow",
                    )
                )

        return errors

    def _validate_headings(self, lines: list[str], file_path: str, file_type: str) -> list:
        """Validate heading levels and structure.

        Checks for:
        - Standard sections using level 1 (#) instead of level 2 (##) in main manuscript
        - Multiple level 1 headings (only one should be the document title)
        - Heading hierarchy (skipped levels)
        - Duplicate heading text

        Args:
            lines: Lines of content to validate
            file_path: Path to the file being validated
            file_type: Type of file ("main" or "supplementary")
        """
        errors = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)(?:\s*\{#.*?\})?\s*$")
        level_1_headings = []
        all_headings = []
        heading_texts = {}
        previous_level = 0

        for line_num, line in enumerate(lines, 1):
            match = heading_pattern.match(line)
            if match:
                hashes = match.group(1)
                heading_text = match.group(2).strip()
                level = len(hashes)

                # Store found heading
                heading_info = {
                    "level": level,
                    "text": heading_text,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                }
                self.found_elements["headings"].append(heading_info)
                all_headings.append((line_num, level, heading_text))

                # Track level 1 headings
                if level == 1:
                    level_1_headings.append((line_num, heading_text))

                # Check for duplicate headings
                normalized_text = heading_text.lower().strip()
                if normalized_text in heading_texts:
                    first_line = heading_texts[normalized_text]
                    errors.append(
                        self._create_error(
                            ValidationLevel.WARNING,
                            f"Duplicate heading text: '{heading_text}'",
                            file_path=file_path,
                            line_number=line_num,
                            context=f"Also found at line {first_line}",
                            suggestion=(
                                "Consider using unique heading text or adding clarifying words.\n"
                                "   Duplicate headings can confuse cross-references."
                            ),
                            error_code="duplicate_heading",
                        )
                    )
                else:
                    heading_texts[normalized_text] = line_num

                # Check heading hierarchy (skip level check for first heading)
                if previous_level > 0 and level > previous_level + 1:
                    errors.append(
                        self._create_error(
                            ValidationLevel.WARNING,
                            f"Heading hierarchy skips levels: {previous_level} → {level}",
                            file_path=file_path,
                            line_number=line_num,
                            context=line.strip(),
                            suggestion=(
                                f"Consider using {'#' * (previous_level + 1)} instead of {'#' * level}.\n"
                                f"   Skipping heading levels (e.g., ## to ####) makes document structure unclear."
                            ),
                            error_code="skipped_heading_level",
                        )
                    )

                previous_level = level

                # Check if standard sections are using wrong heading level (only in main manuscript)
                # Supplementary files are separate documents and can have their own level 1 title
                if file_type == "main":
                    # Normalize for case-insensitive comparison and strip common punctuation
                    normalized_heading = heading_text.strip().rstrip(":").title()
                    if level == 1 and normalized_heading in self.STANDARD_SECTIONS:
                        errors.append(
                            self._create_error(
                                ValidationLevel.ERROR,
                                f"Standard section '{heading_text}' using level 1 heading (#)",
                                file_path=file_path,
                                line_number=line_num,
                                context=line.strip(),
                                suggestion=(
                                    f"Change to level 2 heading: ## {heading_text}\n"
                                    f"   Level 1 (#) should only be used for the document title.\n"
                                    f"   Standard sections (Abstract, Introduction, Methods, etc.) should use ## (level 2)."
                                ),
                                error_code="incorrect_heading_level",
                            )
                        )

        # Warn if there are multiple level 1 headings
        if len(level_1_headings) > 1:
            heading_list = ", ".join([f"'{text}' (line {num})" for num, text in level_1_headings])
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Multiple level 1 headings found: {len(level_1_headings)}",
                    file_path=file_path,
                    line_number=level_1_headings[0][0],
                    context=f"Found at: {heading_list}",
                    suggestion=(
                        "Typically, only the document title should use level 1 heading (#).\n"
                        "   Consider using ## for major sections."
                    ),
                    error_code="multiple_level1_headings",
                )
            )

        return errors

    def _validate_images(self, content: str, file_path: str) -> list:
        """Validate image syntax and check for common issues.

        Args:
            content: File content to validate
            file_path: Path to the file being validated
        """
        errors = []

        for match in self.LINK_PATTERNS["markdown_image"].finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            alt_text = match.group(1)
            image_path = match.group(2)

            # Store found image
            self.found_elements["images"].append(
                {
                    "alt_text": alt_text,
                    "path": image_path,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                }
            )

            # Check for missing alt text
            if not alt_text.strip():
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        "Image without alt text",
                        file_path=file_path,
                        line_number=line_num,
                        context=match.group(0),
                        suggestion="Add descriptive alt text for accessibility: ![description](path)",
                        error_code="missing_image_alt_text",
                    )
                )

            # Check for suspicious image paths (absolute paths, external URLs might be intentional)
            if image_path.startswith("/") and not image_path.startswith("http"):
                errors.append(
                    self._create_error(
                        ValidationLevel.INFO,
                        f"Image uses absolute path: {image_path}",
                        file_path=file_path,
                        line_number=line_num,
                        context=match.group(0),
                        suggestion="Consider using relative paths for better portability",
                        error_code="absolute_image_path",
                    )
                )

        return errors

    def _generate_syntax_statistics(self) -> dict[str, Any]:
        """Generate statistics about syntax elements."""
        stats: dict[str, Any] = {
            "total_elements": sum(len(elements) for elements in self.found_elements.values()),
            "elements_by_type": {k: len(v) for k, v in self.found_elements.items()},
            "formatting_breakdown": {},
            "code_block_languages": {},
            "html_element_types": {},
            "link_types": {},
        }

        # Detailed breakdown of formatting types
        formatting_breakdown: dict[str, int] = stats["formatting_breakdown"]
        for element in self.found_elements["formatting"]:
            fmt_type = element["type"]
            formatting_breakdown[fmt_type] = formatting_breakdown.get(fmt_type, 0) + 1

        # Code block language statistics
        code_langs: dict[str, int] = stats["code_block_languages"]
        for element in self.found_elements["code_blocks"]:
            if element.get("language"):
                lang = element["language"]
                code_langs[lang] = code_langs.get(lang, 0) + 1

        # HTML element type statistics
        html_types: dict[str, int] = stats["html_element_types"]
        for element in self.found_elements["html_elements"]:
            html_type = element["type"]
            html_types[html_type] = html_types.get(html_type, 0) + 1

        # Link type statistics
        link_types: dict[str, int] = stats["link_types"]
        for element in self.found_elements["links"]:
            link_type = element["type"]
            link_types[link_type] = link_types.get(link_type, 0) + 1

        return stats

    def _protect_validation_sensitive_content(self, content: str) -> str:
        """Protect code blocks, inline code, and HTML comments from validation."""
        # Protect HTML comments first (they can contain any other syntax)
        protected = re.sub(
            r"<!--.*?-->",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            content,
            flags=re.DOTALL,
        )

        # Protect fenced code blocks
        protected = re.sub(
            r"```.*?```",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
            flags=re.DOTALL,
        )

        # Protect inline code (backticks)
        protected = re.sub(
            r"`[^`]+`",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
        )

        # Protect indented code blocks
        protected = re.sub(
            r"^(    .+)$",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
            flags=re.MULTILINE,
        )

        # Protect Python code blocks {{py: ...}}
        protected = re.sub(
            r"\{\{py:.*?\}\}",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
            flags=re.DOTALL,
        )

        # Protect inline Python expressions {py: ...}
        protected = re.sub(
            r"\{py:[^}]+\}",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            protected,
        )

        return protected
