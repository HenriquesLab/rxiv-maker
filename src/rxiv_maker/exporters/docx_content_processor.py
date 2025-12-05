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

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            # Skip HTML/markdown comments
            if line.strip().startswith("<!--"):
                i += 1
                continue

            # Check for heading
            heading_match = re.match(r"^(#{1,6})\s+(.+?)(?:\s*\{#.*?\})?\s*$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
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

    def _parse_list(self, lines: List[str], start_idx: int, list_type: str) -> tuple[List[str], int]:
        """Parse a list (bullet or numbered).

        Args:
            lines: All lines of content
            start_idx: Starting line index
            list_type: 'bullet' or 'number'

        Returns:
            Tuple of (list items, next line index)
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
                items.append(match.group(1).strip())
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
        """Parse inline formatting (bold, italic, code, citations).

        This is complex as we need to handle:
        - **bold**
        - *italic*
        - `code`
        - [1] citations

        Args:
            text: Text to parse
            citation_map: Citation mapping (already replaced in text)

        Returns:
            List of run dictionaries with formatting
        """
        runs = []

        # Find all formatting markers and citations
        # For simplicity in MVP, we'll do a basic pass
        # More sophisticated parsing would use a state machine

        # Pattern to match: **bold**, *italic*, `code`, [number]
        pattern = re.compile(
            r"(\*\*([^*]+)\*\*)"  # Bold
            r"|(\*([^*]+)\*)"  # Italic
            r"|(`([^`]+)`)"  # Code
            r"|(\[(\d+(?:,\s*\d+)*)\])"  # Citation numbers
        )

        last_end = 0

        for match in pattern.finditer(text):
            # Add text before this match
            if match.start() > last_end:
                before_text = text[last_end : match.start()]
                if before_text:
                    runs.append({"type": "text", "text": before_text, "bold": False, "italic": False, "code": False})

            # Determine what was matched
            if match.group(1):  # Bold
                runs.append({"type": "text", "text": match.group(2), "bold": True, "italic": False, "code": False})
            elif match.group(3):  # Italic
                runs.append({"type": "text", "text": match.group(4), "bold": False, "italic": True, "code": False})
            elif match.group(5):  # Code
                runs.append({"type": "text", "text": match.group(6), "bold": False, "italic": False, "code": True})
            elif match.group(7):  # Citation
                # Parse citation numbers (may be multiple: [1, 2, 3])
                numbers_str = match.group(8)
                numbers = [int(n.strip()) for n in numbers_str.split(",")]
                for num in numbers:
                    runs.append({"type": "citation", "number": num})

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:]
            if remaining:
                runs.append({"type": "text", "text": remaining, "bold": False, "italic": False, "code": False})

        return runs if runs else [{"type": "text", "text": text, "bold": False, "italic": False, "code": False}]

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

        if next_i < len(lines):
            next_line = lines[next_i].strip()

            # Check for {#fig:label ...} **Caption**
            if next_line and next_line.startswith("{#fig:"):
                # Extract label if present
                label_match = re.match(r"\{#fig:(\w+)[^}]*\}", next_line)
                if label_match:
                    label = label_match.group(1)
                    # Remove the {#fig:...} part
                    next_line = re.sub(r"\{#fig:[^}]*\}\s*", "", next_line)

                # Extract caption (remove ** markdown)
                caption = re.sub(r"\*\*([^*]+)\*\*", r"\1", next_line)
                caption = caption.strip()
                next_i += 1

        return {
            "type": "figure",
            "path": image_path,
            "alt": alt_text,
            "caption": caption,
            "label": label,
        }, next_i
