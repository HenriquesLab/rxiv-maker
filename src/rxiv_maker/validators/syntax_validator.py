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
            "tables": [],
            "special_chars": [],
        }

    def validate(self) -> ValidationResult:
        """Validate special syntax elements in manuscript files."""
        errors = []
        metadata = {}

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

        # Validate page markers
        marker_errors = self._validate_page_markers(content, file_path)
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

        # Validate links and URLs
        link_errors = self._validate_links(content, file_path)
        errors.extend(link_errors)

        # Validate tables
        table_errors = self._validate_tables(lines, file_path)
        errors.extend(table_errors)

        # Validate special characters
        char_errors = self._validate_special_characters(content, file_path)
        errors.extend(char_errors)

        return errors

    def _validate_page_markers(self, content: str, file_path: str) -> list:
        """Validate page control markers."""
        errors = []

        # Protect code blocks and inline code from page marker validation
        protected_content = self._protect_code_blocks(content)

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

        # Protect all code blocks and Python expressions from formatting validation
        protected_content = self._protect_code_blocks(content)

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

    def _validate_links(self, content: str, file_path: str) -> list:
        """Validate links and URLs."""
        errors = []

        # Protect code blocks and inline code from URL validation
        protected_content = self._protect_code_blocks(content)

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
            match.end()

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

    def _protect_code_blocks(self, content: str) -> str:
        """Protect code blocks and inline code from URL validation."""
        # Protect fenced code blocks
        protected = re.sub(
            r"```.*?```",
            lambda m: f"XXPROTECTEDCODEXX{len(m.group(0))}XXPROTECTEDCODEXX",
            content,
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
