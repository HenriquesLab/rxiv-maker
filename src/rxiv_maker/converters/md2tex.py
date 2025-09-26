"""Main markdown to LaTeX conversion orchestrator.

This module provides the main entry point for converting markdown content
to LaTeX format, coordinating all the specialized processors.
"""

import re

from .citation_processor import process_citations_outside_tables
from .code_processor import (
    convert_code_blocks_to_latex,
    protect_code_content,
    restore_protected_code,
)
from .comment_processor import preprocess_comments
from .custom_command_processor import process_custom_commands
from .figure_processor import (
    convert_equation_references_to_latex,
    convert_figure_references_to_latex,
    convert_figures_to_latex,
)
from .html_processor import convert_html_comments_to_latex, convert_html_tags_to_latex
from .list_processor import convert_lists_to_latex
from .math_processor import (
    process_enhanced_math_blocks,
    protect_math_expressions,
    restore_math_expressions,
)
from .section_processor import extract_content_sections, map_section_title_to_key
from .supplementary_note_processor import (
    process_supplementary_note_references,
    process_supplementary_notes,
    restore_supplementary_note_placeholders,
)
from .table_processor import convert_table_references_to_latex, convert_tables_to_latex
from .text_formatters import (
    convert_subscript_superscript_to_latex,
    escape_special_characters,
    find_and_replace_python_color,
    process_code_spans,
    protect_bold_outside_texttt,
    protect_italic_outside_texttt,
    protect_underline_outside_texttt,
    restore_protected_seqsplit,
)
from .types import LatexContent, MarkdownContent, ProtectedContent
from .url_processor import convert_links_to_latex


def convert_markdown_to_latex(content: MarkdownContent, is_supplementary: bool = False) -> LatexContent:
    r"""Convert basic markdown formatting to LaTeX.

    This function now uses the centralized ContentProcessor for enhanced
    pipeline management, error handling, and extensibility. Falls back to
    legacy conversion logic if the ContentProcessor is unavailable or fails.

    Args:
        content: The markdown content to convert
        is_supplementary: If True, adds \newpage after figures and tables

    Returns:
        LaTeX formatted content
    """
    # Use the new centralized ContentProcessor for enhanced processing
    # ContentProcessor is now complete with all processors from legacy logic
    # TEMPORARY: Re-disable ContentProcessor due to hanging issues with Python execution
    # Two critical issues discovered:
    # 1. Python execution errors not being displayed and halting PDF generation
    # 2. Protected content placeholders not being restored in final output
    # TODO: Fix ContentProcessor execution flow and protected content restoration
    use_content_processor = False  # Disabled due to execution and restoration issues

    if use_content_processor:
        try:
            from ..core.content_processor import get_content_processor

            processor = get_content_processor()
            result = processor.process(content, is_supplementary=is_supplementary)

            if result.success:
                return result.content
            else:
                # Log warnings but continue with legacy logic for graceful degradation
                from ..core.logging_config import get_logger

                logger = get_logger()
                logger.warning(f"ContentProcessor completed with {len(result.errors)} errors: {result.errors}")
                logger.warning("Falling back to legacy conversion logic")

        except ImportError:
            # Fallback for environments where core modules aren't available
            pass
        except (AttributeError, ValueError, RuntimeError) as e:
            # Graceful degradation on content processor errors
            try:
                from ..core.logging_config import get_logger

                logger = get_logger()
                logger.warning(f"ContentProcessor failed: {e}, falling back to legacy conversion")
            except ImportError:
                pass  # Continue silently if logging is unavailable

    # Legacy conversion logic (original implementation)
    # CRITICAL FIRST STEP: Remove HTML comments to prevent any commented content
    # from being processed by subsequent steps (tables, citations, executable blocks, etc.)
    # This is essential for security - commented content should NEVER be processed
    content = preprocess_comments(content)

    # PROTECT TEX BLOCKS: Protect {{tex:...}} blocks from markdown processing
    # This must happen early to prevent markdown syntax inside tex blocks from being processed
    content, protected_tex_content = _protect_tex_blocks(content)

    # CRITICAL: Process custom commands (Python/R execution) BEFORE any code protection
    # This ensures Python code can be extracted properly before LaTeX processing interferes
    # NOTE: tex blocks are still protected at this point and will be handled specially
    content = process_custom_commands(content)

    # SECOND: Convert fenced code blocks AFTER Python execution
    content = convert_code_blocks_to_latex(content)

    # Process enhanced math blocks ($$...$$ {#eq:id})
    content = process_enhanced_math_blocks(content)

    # FIRST: Protect backtick content (including math inside backticks)
    # from further markdown processing
    protected_backtick_content: ProtectedContent = {}
    protected_tables: ProtectedContent = {}
    protected_markdown_tables: ProtectedContent = {}
    # Note: protected_tex_content is already populated above

    # Protect backtick content and markdown tables BEFORE math protection
    content, protected_backtick_content = _protect_backtick_content(content)
    content, protected_markdown_tables = _protect_markdown_tables(content)

    # THEN: Protect mathematical expressions from markdown processing
    # (but this will skip math expressions that are already protected inside backticks)
    content, protected_math = protect_math_expressions(content)

    # THEN: Protect verbatim blocks from further markdown processing
    content, protected_verbatim_content = protect_code_content(content)

    # Convert HTML elements early
    content = convert_html_comments_to_latex(content)
    content = convert_html_tags_to_latex(content)

    # Process <newpage> and <float-barrier> markers early in the pipeline
    content = _process_newpage_markers(content)
    content = _process_float_barrier_markers(content)

    # Convert lists BEFORE other processing to avoid conflicts
    content = convert_lists_to_latex(content)

    # Convert tables BEFORE figures to avoid conflicts
    content = _process_tables_with_protection(
        content,
        protected_backtick_content,
        protected_markdown_tables,
        protected_tables,
        is_supplementary,
    )

    # Convert figures BEFORE headers to avoid conflicts
    content = convert_figures_to_latex(content, is_supplementary)

    # Convert figure references BEFORE citations to avoid conflicts
    content = convert_figure_references_to_latex(content)

    # Convert equation references BEFORE citations to avoid conflicts
    content = convert_equation_references_to_latex(content)

    # Convert table references BEFORE citations to avoid conflicts
    content = convert_table_references_to_latex(content)

    # Process supplementary notes EARLY (only for supplementary content)
    # Must happen before text formatting to avoid conflicts with \subsection*
    if is_supplementary:
        content = process_supplementary_notes(content)

    # Convert headers
    content = _convert_headers(content, is_supplementary)

    # Post-processing: catch any remaining unconverted headers
    # This is a safety net in case some headers weren't converted properly
    content = re.sub(r"^### (.+)$", r"\\subsubsection{\1}", content, flags=re.MULTILINE)

    # Process supplementary note references BEFORE citations
    # (for both main and supplementary content)
    content = process_supplementary_note_references(content)

    # Convert citations with table protection
    content = process_citations_outside_tables(content, protected_markdown_tables)

    # Process text formatting
    content = _process_text_formatting(content, protected_backtick_content)

    # Restore supplementary note placeholders after text formatting
    if is_supplementary:
        content = restore_supplementary_note_placeholders(content)

    # Convert markdown links to LaTeX URLs
    content = convert_links_to_latex(content)

    # Handle special characters
    content = escape_special_characters(content)

    # Restore protected seqsplit commands after escaping
    content = restore_protected_seqsplit(content)

    # Final step: replace all placeholders with properly escaped underscores
    content = content.replace("XUNDERSCOREX", "\\_")

    # Restore protected content
    content = _restore_protected_content(content, protected_tables, protected_verbatim_content)

    # Finally restore mathematical expressions
    content = restore_math_expressions(content, protected_math)

    # FINAL STEP: Restore {{tex:...}} blocks after all markdown processing is complete
    # This ensures tex blocks are processed at the very end
    content = _restore_tex_blocks(content, protected_tex_content)

    # Process only tex commands now that all markdown processing is done
    from .custom_command_processor import _process_tex_commands

    content = _process_tex_commands(content)

    return content


def _process_newpage_markers(content: MarkdownContent) -> LatexContent:
    r"""Convert <newpage> and <clearpage> markers to LaTeX commands.

    Args:
        content: The markdown content with page break markers

    Returns:
        Content with page break markers converted to LaTeX commands
    """
    # Replace <clearpage> with \\clearpage, handling both with and without
    # surrounding whitespace
    content = re.sub(r"^\s*<clearpage>\s*$", r"\\clearpage", content, flags=re.MULTILINE)
    content = re.sub(r"<clearpage>", r"\\clearpage", content)

    # Replace <newpage> with \\newpage, handling both with and without
    # surrounding whitespace
    content = re.sub(r"^\s*<newpage>\s*$", r"\\newpage", content, flags=re.MULTILINE)
    content = re.sub(r"<newpage>", r"\\newpage", content)

    return content


def _process_float_barrier_markers(content: MarkdownContent) -> LatexContent:
    r"""Convert <float-barrier> markers to LaTeX \FloatBarrier commands.

    Args:
        content: The markdown content with float barrier markers

    Returns:
        Content with float barrier markers converted to LaTeX commands
    """
    # Replace <float-barrier> with \\FloatBarrier, handling both with and without
    # surrounding whitespace
    content = re.sub(r"^\s*<float-barrier>\s*$", r"\\FloatBarrier", content, flags=re.MULTILINE)
    content = re.sub(r"<float-barrier>", r"\\FloatBarrier", content)

    return content


def _protect_tex_blocks(
    content: MarkdownContent,
) -> tuple[LatexContent, ProtectedContent]:
    """Protect {{tex:...}} blocks from markdown processing, excluding those in backticks."""
    protected_tex_content: ProtectedContent = {}

    # First, identify all backtick spans to exclude from tex block protection
    backtick_spans = []
    i = 0
    while i < len(content):
        if content[i] == "`":
            # Count opening backticks
            start = i
            backtick_count = 0
            while i < len(content) and content[i] == "`":
                backtick_count += 1
                i += 1

            # Find matching closing backticks
            while i < len(content):
                if content[i] == "`":
                    # Count closing backticks
                    closing_count = 0
                    while i < len(content) and content[i] == "`":
                        closing_count += 1
                        i += 1

                    if closing_count == backtick_count:
                        # Found complete backtick span
                        backtick_spans.append((start, i))
                        break
                else:
                    i += 1
            else:
                # No matching closing backticks found
                i = start + backtick_count
        else:
            i += 1

    def is_inside_backticks(pos: int) -> bool:
        """Check if position is inside any backtick span."""
        for start, end in backtick_spans:
            if start <= pos < end:
                return True
        return False

    # Now scan for tex blocks, excluding those inside backtick spans
    result = []
    i = 0

    while i < len(content):
        if content[i : i + 6] == "{{tex:" and not is_inside_backticks(i):
            # Found tex block outside of backticks
            brace_count = 2  # Start with {{
            start = i + 6  # length of "{{tex:"
            j = start
            while j < len(content) and brace_count > 0:
                if content[j] == "{":
                    brace_count += 1
                elif content[j] == "}":
                    brace_count -= 1
                j += 1

            if brace_count == 0:
                # Found complete tex block
                full_block = content[i:j]
                placeholder = f"XXPROTECTEDTEXBLOCKXX{len(protected_tex_content)}XXPROTECTEDTEXBLOCKXX"
                protected_tex_content[placeholder] = full_block
                result.append(placeholder)
                i = j
            else:
                # Incomplete block, treat as regular text
                result.append(content[i])
                i += 1
        else:
            result.append(content[i])
            i += 1

    return "".join(result), protected_tex_content


def _restore_tex_blocks(content: LatexContent, protected_tex_content: ProtectedContent) -> LatexContent:
    """Restore {{tex:...}} blocks from placeholders."""
    for placeholder, original_content in protected_tex_content.items():
        content = content.replace(placeholder, original_content)
    return content


def _protect_backtick_content(
    content: MarkdownContent,
) -> tuple[LatexContent, ProtectedContent]:
    """Protect backtick content from markdown processing."""
    protected_backtick_content: ProtectedContent = {}

    def protect_backtick_content_func(match: re.Match[str]) -> str:
        original = match.group(0)
        placeholder = f"XXPROTECTEDBACKTICKXX{len(protected_backtick_content)}XXPROTECTEDBACKTICKXX"
        protected_backtick_content[placeholder] = original
        return placeholder

    # Protect all backtick content globally (excluding fenced blocks which are
    # already processed)
    # Handle both single backticks and double backticks for inline code
    content = re.sub(r"``[^`]+``", protect_backtick_content_func, content)  # Double backticks first
    content = re.sub(r"`[^`]+`", protect_backtick_content_func, content)  # Then single backticks

    return content, protected_backtick_content


def _protect_markdown_tables(
    content: MarkdownContent,
) -> tuple[LatexContent, ProtectedContent]:
    """Protect markdown tables from citation processing."""
    protected_markdown_tables: ProtectedContent = {}

    def protect_markdown_table(match: re.Match[str]) -> str:
        table_content = match.group(0)
        placeholder = f"XXPROTECTEDMARKDOWNTABLEXX{len(protected_markdown_tables)}XXPROTECTEDMARKDOWNTABLEXX"
        protected_markdown_tables[placeholder] = table_content
        return placeholder

    # Protect entire markdown table blocks (including headers, separators,
    # and data rows)
    # This regex matches multi-line markdown tables
    content = re.sub(
        r"(?:^[ \t]*\|.*\|[ \t]*$\s*)+",
        protect_markdown_table,
        content,
        flags=re.MULTILINE,
    )

    return content, protected_markdown_tables


def _process_tables_with_protection(
    content: LatexContent,
    protected_backtick_content: ProtectedContent,
    protected_markdown_tables: ProtectedContent,
    protected_tables: ProtectedContent,
    is_supplementary: bool,
) -> LatexContent:
    """Process tables with proper content protection."""
    # Restore protected markdown tables before table processing
    for placeholder, original in protected_markdown_tables.items():
        content = content.replace(placeholder, original)

    # Restore backticks only in table rows to avoid affecting verbatim blocks
    table_lines = content.split("\n")
    for i, line in enumerate(table_lines):
        if "|" in line and line.strip().startswith("|") and line.strip().endswith("|"):
            # Restore backticks in table rows only
            for placeholder, original in protected_backtick_content.items():
                line = line.replace(placeholder, original)
            table_lines[i] = line

    temp_content = "\n".join(table_lines)

    # Process tables with restored content
    table_processed_content = convert_tables_to_latex(
        temp_content,
        protected_backtick_content,
        is_supplementary,
    )

    # Protect LaTeX table blocks from further markdown processing
    def protect_latex_table(match: re.Match[str]) -> str:
        table_content = match.group(0)
        placeholder = f"XXPROTECTEDTABLEXX{len(protected_tables)}XXPROTECTEDTABLEXX"
        protected_tables[placeholder] = table_content
        return placeholder

    # Protect all LaTeX table environments
    for env in ["table", "sidewaystable", "stable"]:
        pattern = rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}"
        table_processed_content = re.sub(pattern, protect_latex_table, table_processed_content, flags=re.DOTALL)

    # Re-protect unconverted backtick content
    for original, placeholder in [(v, k) for k, v in protected_backtick_content.items()]:
        if original in table_processed_content:
            table_processed_content = table_processed_content.replace(original, placeholder)

    return table_processed_content


def _convert_headers(content: LatexContent, is_supplementary: bool = False) -> LatexContent:
    """Convert markdown headers to LaTeX sections."""
    if is_supplementary:
        # For supplementary content, use \\section* for the first header
        # to avoid "Note 1:" prefix
        # First, find the first # header and replace it with \section*
        content = re.sub(r"^# (.+)$", r"\\section*{\1}", content, flags=re.MULTILINE, count=1)
        # Then replace any remaining # headers with regular \section
        content = re.sub(r"^# (.+)$", r"\\section{\1}", content, flags=re.MULTILINE)
    else:
        content = re.sub(r"^# (.+)$", r"\\section{\1}", content, flags=re.MULTILINE)

    content = re.sub(r"^## (.+)$", r"\\subsection{\1}", content, flags=re.MULTILINE)

    # For supplementary content, ### headers are handled by the
    # supplementary note processor
    # For non-supplementary content, convert all ### headers normally
    if not is_supplementary:
        content = re.sub(r"^### (.+)$", r"\\subsubsection{\1}", content, flags=re.MULTILINE)

    content = re.sub(r"^#### (.+)$", r"\\paragraph{\1}", content, flags=re.MULTILINE)
    return content


def _process_text_formatting(content: LatexContent, protected_backtick_content: ProtectedContent) -> LatexContent:
    """Process text formatting (backticks, bold, italic, subscript, superscript)."""
    # IMPORTANT: Process backticks BEFORE bold/italic to ensure markdown inside
    # code spans is preserved as literal text

    # First restore protected backtick content so we can process it
    for placeholder, original in protected_backtick_content.items():
        content = content.replace(placeholder, original)

    # Then convert backticks to texttt with proper underscore handling
    content = process_code_spans(content)

    # Process protected Python color placeholders
    content = find_and_replace_python_color(content)

    # Convert bold, italic, and underline AFTER processing backticks
    content = protect_bold_outside_texttt(content)
    content = protect_italic_outside_texttt(content)
    content = protect_underline_outside_texttt(content)

    # Convert subscript and superscript formatting
    content = convert_subscript_superscript_to_latex(content)

    # Special handling for italic text in list items
    content = re.sub(r"(\\item\s+)\*([^*]+?)\*", r"\1\\textit{\2}", content)

    return content


def _restore_protected_content(
    content: LatexContent,
    protected_tables: ProtectedContent,
    protected_verbatim_content: ProtectedContent,
) -> LatexContent:
    """Restore all protected content."""
    # Restore protected tables at the very end (after all other conversions)
    for placeholder, table_content in protected_tables.items():
        content = content.replace(placeholder, table_content)

    # Restore protected verbatim blocks at the very end
    content = restore_protected_code(content, protected_verbatim_content)

    return content


# Export functions that are used by other modules to avoid circular imports
__all__ = [
    "convert_markdown_to_latex",
    "extract_content_sections",
    "map_section_title_to_key",
]
