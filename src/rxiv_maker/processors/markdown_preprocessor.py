"""Centralized markdown preprocessor for rxiv-maker.

This module processes rxiv-maker-specific markdown syntax before conversion
to different output formats (PDF/DOCX). It handles:
- {{py:exec}} code execution
- {{py:get variable}} variable substitution
- {{tex:...}} LaTeX block handling (format-specific)

This preprocessor is used by both PDF and DOCX pipelines to ensure consistent
markdown processing across all output formats.
"""

import re
from pathlib import Path
from typing import Optional

from ..converters.python_executor import PythonExecutor, get_python_executor
from ..core.logging_config import get_logger

logger = get_logger()


class MarkdownPreprocessor:
    """Preprocesses rxiv-maker markdown for different output formats."""

    def __init__(self, manuscript_path: Optional[str] = None):
        """Initialize markdown preprocessor.

        Args:
            manuscript_path: Path to manuscript directory for Python execution context
        """
        self.manuscript_path = Path(manuscript_path) if manuscript_path else None
        self.python_executor: Optional[PythonExecutor] = None

    def _get_python_executor(self) -> PythonExecutor:
        """Get or create Python executor instance."""
        if self.python_executor is None:
            self.python_executor = get_python_executor()
            # Set manuscript directory if available
            if self.manuscript_path:
                self.python_executor.manuscript_dir = self.manuscript_path
        return self.python_executor

    def process(
        self,
        markdown: str,
        target_format: str = "latex",
        file_path: Optional[str] = None,
    ) -> str:
        """Process markdown content for specified output format.

        Args:
            markdown: Raw markdown content with rxiv-maker syntax
            target_format: Target format ("latex" for PDF, "docx" for DOCX)
            file_path: Optional source file path for error reporting

        Returns:
            Processed markdown with rxiv-maker syntax resolved
        """
        # Step 1: Execute all {{py:exec}} blocks (in order)
        markdown = self._process_python_exec_blocks(markdown, file_path)

        # Step 2: Replace all {{py:get variable}} with values
        markdown = self._process_python_get_blocks(markdown, file_path)

        # Step 3: Handle {{tex:...}} blocks based on target format
        if target_format == "docx":
            markdown = self._strip_tex_blocks_for_docx(markdown)
            # Also clean up inline LaTeX formatting for DOCX
            markdown = self._clean_latex_formatting_for_docx(markdown)
        # For latex target, {{tex:...}} blocks are preserved and handled later

        return markdown

    def _process_python_exec_blocks(self, markdown: str, file_path: Optional[str] = None) -> str:
        """Execute all {{py:exec}} blocks and remove them from markdown.

        Args:
            markdown: Markdown content
            file_path: Source file path for error reporting

        Returns:
            Markdown with {{py:exec}} blocks executed and removed
        """
        executor = self._get_python_executor()

        # Pattern to match {{py:exec ...}} blocks
        # Use DOTALL to match across newlines
        pattern = r"\{\{py:exec\s+(.*?)\}\}"

        def execute_block(match: re.Match) -> str:
            """Execute Python code block and return empty string."""
            code = match.group(1).strip()

            # Calculate line number for error reporting
            line_number = markdown[: match.start()].count("\n") + 1

            try:
                executor.execute_initialization_block(
                    code, manuscript_file=file_path or "manuscript", line_number=line_number
                )
                # Successfully executed, remove the block from output
                return ""
            except Exception as e:
                # Log error but don't halt processing
                logger.error(f"Python execution error in {file_path or 'manuscript'}:{line_number}: {e}")
                # Return placeholder to make error visible in output
                return f"[ERROR: Python execution failed at line {line_number}]"

        # Process all {{py:exec}} blocks
        result = re.sub(pattern, execute_block, markdown, flags=re.DOTALL)

        return result

    def _process_python_get_blocks(self, markdown: str, file_path: Optional[str] = None) -> str:
        """Replace all {{py:get variable}} with variable values.

        Args:
            markdown: Markdown content
            file_path: Source file path for error reporting

        Returns:
            Markdown with {{py:get}} blocks replaced with values
        """
        executor = self._get_python_executor()

        # Pattern to match {{py:get variable_name}}
        pattern = r"\{\{py:get\s+([^}]+)\}\}"

        def get_variable(match: re.Match) -> str:
            """Get variable value and return as string."""
            variable_name = match.group(1).strip()

            # Calculate line number for error reporting
            line_number = markdown[: match.start()].count("\n") + 1

            try:
                value = executor.get_variable_value(
                    variable_name, line_number=line_number, file_path=file_path or "manuscript"
                )
                return str(value)
            except Exception as e:
                # Log error and return placeholder
                logger.error(f"Variable '{variable_name}' not found in {file_path or 'manuscript'}:{line_number}: {e}")
                return f"[ERROR: {variable_name}]"

        # Process all {{py:get}} blocks
        result = re.sub(pattern, get_variable, markdown)

        return result

    def _strip_tex_blocks_for_docx(self, markdown: str) -> str:
        """Convert {{tex:...}} blocks for DOCX output with visible note.

        For DOCX, we can't execute raw LaTeX, so we keep the block visible
        with a note indicating it cannot be converted.

        Args:
            markdown: Markdown content

        Returns:
            Markdown with {{tex:...}} blocks replaced with formatted notes
        """
        # Pattern to match {{tex: ... }} blocks
        # Only match {{tex: at start of line to avoid matching inline mentions in backticks
        # Match until we find }} on its own line (after newline)
        # This prevents matching }} inside LaTeX code like {\textbf{...}}
        # Use MULTILINE for ^ to match line starts, DOTALL so . matches newlines
        pattern = r"^\{\{tex:(.*?)\n\s*\}\}"

        def handle_tex_block(match: re.Match) -> str:
            """Handle LaTeX block for DOCX export - keep visible with note."""
            tex_content = match.group(1).strip()

            # Only process multi-line blocks (those with newlines)
            # Single-line mentions are likely syntax examples in explanatory text
            if "\n" not in tex_content:
                # Convert inline mentions to code format
                return f"`{{{{tex:{tex_content}}}}}`"

            # Check if this is a large table/complex structure
            is_table = "\\begin{" in tex_content and ("table" in tex_content or "longtable" in tex_content)

            # For tables, provide a more informative message with yellow highlighting
            if is_table:
                note = (
                    "\n\n---\n\n"
                    "<<HIGHLIGHT_YELLOW>>**[LaTeX Table - Please refer to the PDF version for proper table formatting]**<</HIGHLIGHT_YELLOW>>\n\n"
                    "<<HIGHLIGHT_YELLOW>>_This section contains a complex LaTeX table that cannot be displayed in Word format. "
                    "The table shows the Markdown-to-LaTeX syntax reference with formatting examples._<</HIGHLIGHT_YELLOW>>\n\n"
                    "---\n\n"
                )
            else:
                # For other LaTeX blocks, show a compact version
                # Truncate very long content
                display_content = tex_content if len(tex_content) < 200 else tex_content[:200] + "\n..."
                note = (
                    f"\n\n**[LaTeX Content]** _(See PDF for proper rendering)_\n\n```latex\n{display_content}\n```\n\n"
                )

            return note

        # Process all {{tex:...}} blocks
        # MULTILINE: ^ matches line starts, DOTALL: . matches newlines
        result = re.sub(pattern, handle_tex_block, markdown, flags=re.MULTILINE | re.DOTALL)

        return result

    def _clean_latex_formatting_for_docx(self, markdown: str) -> str:
        r"""Clean inline LaTeX formatting that doesn't translate well to DOCX.

        This handles common LaTeX patterns like:
        - {\\color{red}R} → R (colored text)
        - $\\chi$ → χ (Greek letters)
        - Other LaTeX commands that should be simplified

        Args:
            markdown: Markdown content

        Returns:
            Markdown with LaTeX formatting cleaned for DOCX
        """
        # Replace colored text {\\color{...}text} with just text
        markdown = re.sub(r"\{\\color\{[^}]+\}([^}]+)\}", r"\1", markdown)

        # Replace common Greek letters in math mode
        greek_letters = {
            r"\$\\chi\$": "χ",
            r"\$\\alpha\$": "α",
            r"\$\\beta\$": "β",
            r"\$\\gamma\$": "γ",
            r"\$\\delta\$": "δ",
            r"\$\\epsilon\$": "ε",
            r"\$\\theta\$": "θ",
            r"\$\\lambda\$": "λ",
            r"\$\\mu\$": "μ",
            r"\$\\pi\$": "π",
            r"\$\\sigma\$": "σ",
            r"\$\\tau\$": "τ",
            r"\$\\phi\$": "φ",
            r"\$\\omega\$": "ω",
        }

        for latex_pattern, unicode_char in greek_letters.items():
            markdown = re.sub(latex_pattern, unicode_char, markdown)

        # NOTE: Label markers like {#fig:label} are NOT removed here because
        # docx_exporter needs them to create the cross-reference mapping.
        # They will be removed later in docx_exporter after the mapping is created.

        return markdown

    def reset_context(self) -> None:
        """Reset Python execution context."""
        if self.python_executor:
            self.python_executor.reset_context()
            self.python_executor = None


# Global preprocessor instance for reuse across processing
_global_preprocessor: Optional[MarkdownPreprocessor] = None


def get_markdown_preprocessor(manuscript_path: Optional[str] = None) -> MarkdownPreprocessor:
    """Get or create global markdown preprocessor instance.

    Args:
        manuscript_path: Path to manuscript directory

    Returns:
        MarkdownPreprocessor instance
    """
    global _global_preprocessor
    if _global_preprocessor is None or manuscript_path is not None:
        _global_preprocessor = MarkdownPreprocessor(manuscript_path=manuscript_path)
    return _global_preprocessor


def reset_markdown_preprocessor() -> None:
    """Reset global markdown preprocessor instance.

    Useful for testing to ensure clean state between tests.
    """
    global _global_preprocessor
    if _global_preprocessor:
        _global_preprocessor.reset_context()
    _global_preprocessor = None
