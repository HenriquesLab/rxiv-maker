"""Content processor for DOCX export.

This module parses markdown content into a structured format suitable for
DOCX generation with python-docx.
"""

import re
from typing import Any, Dict, List, Optional


class DocxContentProcessor:
    """Parses markdown content into structured format for DOCX writing."""

    def parse(self, markdown: str, citation_map: Dict[str, int]) -> Dict[str, Any]:
        """Parse markdown into structured sections for DOCX.

        Args:
            markdown: Markdown content to parse
            citation_map: Mapping from citation keys to numbers

        Returns:
            Document structure with sections and formatting metadata

        Example structure:
            {
                'sections': [
                    {'type': 'heading', 'level': 1, 'text': 'Introduction'},
                    {'type': 'paragraph', 'runs': [
                        {'type': 'text', 'text': 'Some ', 'bold': False},
                        {'type': 'text', 'text': 'bold', 'bold': True},
                        {'type': 'citation', 'number': 1}
                    ]},
                    {'type': 'list', 'list_type': 'bullet', 'items': [...]}
                ]
            }
        """
        sections = []
        lines = markdown.split("\n")

        # Track if we've seen the first H1 heading (title) to skip it
        seen_first_h1 = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Check for page break BEFORE skipping comments
            if line.strip() == "<!-- PAGE_BREAK -->":
                sections.append({"type": "page_break"})
                i += 1
                continue

            # Skip HTML/markdown comments
            if line.strip().startswith("<!--"):
                i += 1
                continue

            # Skip LaTeX commands like <clearpage>
            if line.strip().startswith("<") and line.strip().endswith(">") and " " not in line.strip():
                i += 1
                continue

            # Check for supplementary note title: {#snote:label} Title
            snote_title_match = re.match(r"^\{#snote:(\w+)\}\s+(.+)$", line.strip())
            if snote_title_match:
                label = snote_title_match.group(1)
                title_text = snote_title_match.group(2).strip()
                # Remove bold markers if present
                title_text = re.sub(r"^\*\*(.+?)\*\*$", r"\1", title_text)
                # Treat as a heading with special formatting
                sections.append({"type": "snote_title", "label": label, "text": title_text})
                i += 1
                continue

            # Check for heading
            heading_match = re.match(r"^(#{1,6})\s+(.+?)(?:\s*\{#.*?\})?\s*$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()

                # Skip the first H1 heading (it's the title, added from metadata)
                if level == 1 and not seen_first_h1:
                    seen_first_h1 = True
                    i += 1
                    continue

                sections.append({"type": "heading", "level": level, "text": text})
                i += 1
                continue

            # Check for unordered list
            if re.match(r"^\s*[-*]\s+", line):
                list_items, next_i = self._parse_list(lines, i, "bullet")
                sections.append({"type": "list", "list_type": "bullet", "items": list_items})
                i = next_i
                continue

            # Check for ordered list
            if re.match(r"^\s*\d+\.\s+", line):
                list_items, next_i = self._parse_list(lines, i, "number")
                sections.append({"type": "list", "list_type": "number", "items": list_items})
                i = next_i
                continue

            # Check for display equation ($$...$$)
            if line.strip().startswith("$$"):
                equation_data, next_i = self._parse_equation(lines, i)
                if equation_data:
                    sections.append(equation_data)
                    i = next_i
                    continue

            # Check for code block
            if line.strip().startswith("```"):
                code_content, next_i = self._parse_code_block(lines, i)
                sections.append({"type": "code_block", "content": code_content})
                i = next_i
                continue

            # Check for figure (markdown image syntax)
            if line.strip().startswith("!["):
                figure_data, next_i = self._parse_figure(lines, i)
                if figure_data:
                    sections.append(figure_data)
                    i = next_i
                    continue

            # Check for table (starts with |)
            if line.strip().startswith("|"):
                table_data, next_i = self._parse_table(lines, i)
                if table_data:
                    sections.append(table_data)
                    i = next_i
                    continue

            # Otherwise, it's a paragraph - accumulate until empty line or special element
            paragraph_lines = []
            while i < len(lines):
                current_line = lines[i]

                # Stop at empty line
                if not current_line.strip():
                    break

                # Stop at heading
                if re.match(r"^#{1,6}\s+", current_line):
                    break

                # Stop at list
                if re.match(r"^\s*[-*]\s+", current_line) or re.match(r"^\s*\d+\.\s+", current_line):
                    break

                # Stop at code block
                if current_line.strip().startswith("```"):
                    break

                paragraph_lines.append(current_line)
                i += 1

            if paragraph_lines:
                paragraph_text = " ".join(paragraph_lines)
                runs = self._parse_inline_formatting(paragraph_text, citation_map)
                sections.append({"type": "paragraph", "runs": runs})

        return {"sections": sections}

    def _parse_list(self, lines: List[str], start_idx: int, list_type: str) -> tuple[List[List[Dict[str, Any]]], int]:
        """Parse a list (bullet or numbered) with inline formatting.

        Args:
            lines: All lines of content
            start_idx: Starting line index
            list_type: 'bullet' or 'number'

        Returns:
            Tuple of (list items with runs, next line index)
        """
        items = []
        i = start_idx

        # Determine the pattern based on list type
        if list_type == "bullet":
            pattern = re.compile(r"^\s*[-*]\s+(.+)$")
        else:  # number
            pattern = re.compile(r"^\s*\d+\.\s+(.+)$")

        while i < len(lines):
            line = lines[i]
            match = pattern.match(line)

            if match:
                # Parse inline formatting for list item text
                item_text = match.group(1).strip()
                item_runs = self._parse_inline_formatting(item_text, {})
                items.append(item_runs)
                i += 1
            else:
                # Stop if we hit a non-list line (unless it's empty and next line continues)
                if not line.strip():
                    # Peek ahead
                    if i + 1 < len(lines) and pattern.match(lines[i + 1]):
                        i += 1  # Skip empty line
                        continue
                break

        return items, i

    def _parse_equation(self, lines: List[str], start_idx: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a display equation block.

        Expected format:
            $$ equation content $$
            {#eq:label}

        Args:
            lines: All lines of content
            start_idx: Starting line index (at $$)

        Returns:
            Tuple of (equation dict or None, next line index)
        """
        equation_line = lines[start_idx].strip()

        # Check for single-line equation: $$ ... $$ or $$ ... $$ {#eq:label}
        if equation_line.startswith("$$"):
            # Check if label is on the same line
            label = None
            label_match = re.search(r"\{#eq:(\w+)\}\s*$", equation_line)
            if label_match:
                label = f"eq:{label_match.group(1)}"
                # Remove label from equation line
                equation_line = equation_line[: label_match.start()].strip()

            # Check if equation closes on the same line
            if "$$" in equation_line[2:]:  # Look for closing $$ after opening $$
                # Find the closing $$
                close_idx = equation_line.rfind("$$")
                if close_idx > 2:  # Make sure it's not the opening $$
                    # Extract equation content (between the two $$)
                    latex_content = equation_line[2:close_idx].strip()
                    next_i = start_idx + 1

                    # If no label on same line, check next line
                    if label is None and next_i < len(lines):
                        label_line = lines[next_i].strip()
                        label_match = re.match(r"^\{#eq:(\w+)\}$", label_line)
                        if label_match:
                            label = f"eq:{label_match.group(1)}"
                            next_i += 1

                    return {
                        "type": "equation",
                        "content": latex_content,
                        "label": label,
                    }, next_i

        # Multi-line equation (starts with $$, content on next lines, closes with $$)
        if equation_line == "$$":
            i = start_idx + 1
            equation_lines = []

            while i < len(lines):
                line = lines[i].strip()
                if line == "$$":
                    # Found closing marker
                    latex_content = " ".join(equation_lines).strip()
                    next_i = i + 1

                    # Check for label
                    label = None
                    if next_i < len(lines):
                        label_line = lines[next_i].strip()
                        label_match = re.match(r"^\{#eq:(\w+)\}$", label_line)
                        if label_match:
                            label = f"eq:{label_match.group(1)}"
                            next_i += 1

                    return {
                        "type": "equation",
                        "content": latex_content,
                        "label": label,
                    }, next_i

                equation_lines.append(line)
                i += 1

        return None, start_idx + 1

    def _parse_code_block(self, lines: List[str], start_idx: int) -> tuple[str, int]:
        """Parse a fenced code block.

        Args:
            lines: All lines of content
            start_idx: Starting line index (at opening ```)

        Returns:
            Tuple of (code content, next line index)
        """
        i = start_idx + 1  # Skip opening ```
        code_lines = []

        while i < len(lines):
            line = lines[i]
            if line.strip().startswith("```"):
                # Found closing marker
                return "\n".join(code_lines), i + 1
            code_lines.append(line)
            i += 1

        # Unclosed code block - return what we have
        return "\n".join(code_lines), i

    def _parse_inline_formatting(self, text: str, citation_map: Dict[str, int]) -> List[Dict[str, Any]]:
        """Parse inline formatting (bold, italic, code, citations, links).

        This is complex as we need to handle:
        - **bold**
        - *italic*
        - `code`
        - [text](url) links
        - [1] citations

        Args:
            text: Text to parse
            citation_map: Citation mapping (already replaced in text)

        Returns:
            List of run dictionaries with formatting
        """
        runs = []

        # Find all formatting markers, links, and citations
        # Pattern to match: <<HIGHLIGHT_YELLOW>>text<</HIGHLIGHT_YELLOW>>, <<XREF>>text<</XREF>>, [text](url), **bold**, __underlined__, *italic*, _italic_, `code`, $math$, [number]
        pattern = re.compile(
            r"(<<HIGHLIGHT_YELLOW>>([^<]+)<</HIGHLIGHT_YELLOW>>)"  # Yellow highlight (must be first)
            r"|(<<XREF>>([^<]+)<</XREF>>)"  # Cross-reference
            r"|(\[([^\]]+)\]\(([^)]+)\))"  # Markdown link [text](url) (before citations)
            r"|(\*\*([^*]+)\*\*)"  # Bold
            r"|(__([^_]+)__)"  # Underline with double underscores (must come before single underscore)
            r"|(\*([^*]+)\*)"  # Italic with asterisks
            r"|(_([^_]+)_)"  # Italic with underscores
            r"|(`([^`]+)`)"  # Code
            r"|(\$([^\$]+)\$)"  # Inline math
            r"|(\[(\d+(?:,\s*\d+)*)\])"  # Citation numbers
        )

        last_end = 0

        for match in pattern.finditer(text):
            # Add text before this match
            if match.start() > last_end:
                before_text = text[last_end : match.start()]
                if before_text:
                    runs.append(
                        {
                            "type": "text",
                            "text": before_text,
                            "bold": False,
                            "italic": False,
                            "underline": False,
                            "code": False,
                            "xref": False,
                        }
                    )

            # Determine what was matched
            if match.group(1):  # Yellow highlight
                # Recursively parse inner text for bold/italic/other formatting
                inner_text = match.group(2)
                inner_runs = self._parse_inline_formatting(inner_text, citation_map)
                # Add yellow highlight to all inner runs
                for run in inner_runs:
                    if run["type"] == "text":
                        run["highlight_yellow"] = True
                    runs.append(run)
            elif match.group(3):  # Cross-reference
                runs.append(
                    {
                        "type": "text",
                        "text": match.group(4),
                        "bold": False,
                        "italic": False,
                        "underline": False,
                        "code": False,
                        "xref": True,
                    }
                )
            elif match.group(5):  # Markdown link [text](url)
                runs.append(
                    {
                        "type": "hyperlink",
                        "text": match.group(6),
                        "url": match.group(7),
                    }
                )
            elif match.group(8):  # Bold
                # Recursively parse inner text for underline/italic/other formatting
                inner_text = match.group(9)
                inner_runs = self._parse_inline_formatting(inner_text, citation_map)
                # Add bold to all inner runs
                for run in inner_runs:
                    if run["type"] == "text":
                        run["bold"] = True
                    runs.append(run)
            elif match.group(10):  # Underline
                # Recursively parse inner text for bold/italic/other formatting
                inner_text = match.group(11)
                inner_runs = self._parse_inline_formatting(inner_text, citation_map)
                # Add underline to all inner runs
                for run in inner_runs:
                    if run["type"] == "text":
                        run["underline"] = True
                    runs.append(run)
            elif match.group(12):  # Italic with asterisks
                # Recursively parse inner text for bold/underline/other formatting
                inner_text = match.group(13)
                inner_runs = self._parse_inline_formatting(inner_text, citation_map)
                # Add italic to all inner runs
                for run in inner_runs:
                    if run["type"] == "text":
                        run["italic"] = True
                    runs.append(run)
            elif match.group(14):  # Italic with underscores
                # Recursively parse inner text for bold/underline/other formatting
                inner_text = match.group(15)
                inner_runs = self._parse_inline_formatting(inner_text, citation_map)
                # Add italic to all inner runs
                for run in inner_runs:
                    if run["type"] == "text":
                        run["italic"] = True
                    runs.append(run)
            elif match.group(16):  # Code
                runs.append(
                    {
                        "type": "text",
                        "text": match.group(17),
                        "bold": False,
                        "italic": False,
                        "underline": False,
                        "code": True,
                        "xref": False,
                    }
                )
            elif match.group(18):  # Inline math
                runs.append({"type": "inline_equation", "latex": match.group(19)})
            elif match.group(20):  # Citation
                # Parse citation numbers (may be multiple: [1, 2, 3])
                numbers_str = match.group(21)
                numbers = [int(n.strip()) for n in numbers_str.split(",")]
                for num in numbers:
                    runs.append({"type": "citation", "number": num})

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                runs.append(
                    {
                        "type": "text",
                        "text": remaining,
                        "bold": False,
                        "italic": False,
                        "underline": False,
                        "code": False,
                        "xref": False,
                    }
                )

        return (
            runs
            if runs
            else [
                {
                    "type": "text",
                    "text": text,
                    "bold": False,
                    "italic": False,
                    "underline": False,
                    "code": False,
                    "xref": False,
                }
            ]
        )

    def _parse_figure(self, lines: List[str], start_idx: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a figure with image path and caption.

        Expected format:
            ![alt text](path/to/image.pdf)
            {#fig:label width="100%"} **Caption text**

        Args:
            lines: All lines of content
            start_idx: Starting line index (at ![...])

        Returns:
            Tuple of (figure dict or None, next line index)
        """
        line = lines[start_idx]

        # Parse image markdown: ![alt](path)
        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if not img_match:
            return None, start_idx + 1

        alt_text = img_match.group(1)
        image_path = img_match.group(2)

        # Look ahead for caption line (skip empty lines)
        caption = ""
        label = ""
        next_i = start_idx + 1

        # Skip empty lines to find caption
        while next_i < len(lines) and not lines[next_i].strip():
            next_i += 1

        # Collect multi-line caption
        caption_lines = []
        if next_i < len(lines):
            next_line = lines[next_i].strip()

            # Check for {#fig:label ...} or {#sfig:label ...} **Caption**
            if next_line and (next_line.startswith("{#fig:") or next_line.startswith("{#sfig:")):
                # Extract label if present
                label_match = re.match(r"\{#s?fig:(\w+)[^}]*\}", next_line)
                if label_match:
                    label = label_match.group(1)
                    # Remove the {#fig:...} or {#sfig:...} part
                    next_line = re.sub(r"\{#s?fig:[^}]*\}\s*", "", next_line)

                # Add first line of caption
                caption_lines.append(next_line)
                next_i += 1

                # Continue reading caption lines until empty line or next section
                while next_i < len(lines):
                    line = lines[next_i].strip()

                    # Stop at empty line
                    if not line:
                        break

                    # Stop at next figure
                    if line.startswith("!["):
                        break

                    # Stop at heading
                    if re.match(r"^#{1,6}\s+", line):
                        break

                    # Stop at label (new figure/table/note)
                    if re.match(r"\{#(fig|sfig|stable|snote):", line):
                        break

                    caption_lines.append(line)
                    next_i += 1

                # Combine caption lines - keep markdown for inline formatting
                caption = " ".join(caption_lines)

        return {
            "type": "figure",
            "path": image_path,
            "alt": alt_text,
            "caption": caption,
            "label": label,
        }, next_i

    def _parse_table(self, lines: List[str], start_idx: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a markdown table.

        Expected format:
            | Header 1 | Header 2 |
            |----------|----------|
            | Cell 1   | Cell 2   |

        Args:
            lines: All lines of content
            start_idx: Starting line index (at first |)

        Returns:
            Tuple of (table dict or None, next line index)
        """
        table_lines = []
        i = start_idx

        # Collect all consecutive table lines
        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i].strip())
            i += 1

        if len(table_lines) < 2:
            return None, start_idx + 1

        # Parse header row
        header_row = table_lines[0]
        headers = [cell.strip() for cell in header_row.split("|")[1:-1]]

        # Skip separator row (line with dashes)
        data_start = 2 if len(table_lines) > 1 and re.match(r"^\|[\s\-:|]+\|$", table_lines[1]) else 1

        # Parse data rows
        rows = []
        for line in table_lines[data_start:]:
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if cells:  # Skip empty rows
                rows.append(cells)

        # Check for table caption after the table (format: {#stable:label} Caption text)
        caption = None
        label = None

        # Skip blank line if present
        if i < len(lines) and not lines[i].strip():
            i += 1

        # Check for caption line
        if i < len(lines):
            caption_line = lines[i].strip()
            # Match {#stable:label} Caption or {#table:label} Caption
            caption_match = re.match(r"^\{#(stable|table):(\w+)\}\s*(.+)$", caption_line)
            if caption_match:
                label = f"{caption_match.group(1)}:{caption_match.group(2)}"
                caption = caption_match.group(3).strip()
                i += 1  # Move past caption line

        return {
            "type": "table",
            "headers": headers,
            "rows": rows,
            "caption": caption,
            "label": label,
        }, i
