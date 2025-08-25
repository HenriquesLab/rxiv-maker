"""Enhanced centralized content processing for rxiv-maker.

This module provides a centralized ContentProcessor that manages the complete
markdown→LaTeX conversion pipeline with better error handling, state management,
and extensibility compared to the scattered logic in md2tex.py.
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..converters.types import LatexContent, MarkdownContent, ProtectedContent
from .error_recovery import RecoveryEnhancedMixin
from .logging_config import get_logger
from .managers.resource_manager import get_resource_manager, managed_resources

logger = get_logger()


class ProcessingStage(Enum):
    """Content processing stages."""

    PREPARATION = "preparation"
    PROTECTION = "protection"
    CONVERSION = "conversion"
    RESTORATION = "restoration"
    FINALIZATION = "finalization"


class ProcessorPriority(Enum):
    """Processor execution priority."""

    CRITICAL = 1  # Must run first (e.g., code block protection)
    HIGH = 2  # Important early processing (e.g., math protection)
    NORMAL = 3  # Standard conversion (e.g., lists, tables)
    LOW = 4  # Final formatting (e.g., text formatting)
    CLEANUP = 5  # Restoration and cleanup


@dataclass
class ProcessorConfig:
    """Configuration for content processors."""

    name: str
    enabled: bool = True
    priority: ProcessorPriority = ProcessorPriority.NORMAL
    stage: ProcessingStage = ProcessingStage.CONVERSION
    dependencies: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result from content processing."""

    success: bool
    content: LatexContent
    duration: float
    stage: ProcessingStage
    processor_results: Dict[str, Any] = field(default_factory=dict)
    protected_content: Dict[str, ProtectedContent] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ContentProcessor(RecoveryEnhancedMixin):
    """Enhanced centralized content processing pipeline.

    Features:
    - Structured processing pipeline with clear stages
    - Dependency-aware processor execution
    - State management for protected content
    - Error recovery and rollback capabilities
    - Progress tracking and performance monitoring
    - Extensible processor registration system
    """

    def __init__(self, progress_callback: Optional[Callable[[str, int, int], None]] = None):
        """Initialize content processor.

        Args:
            progress_callback: Optional progress reporting callback
        """
        super().__init__()
        self.progress_callback = progress_callback
        self.resource_manager = get_resource_manager()

        # Processor registry
        self.processors: Dict[str, ProcessorConfig] = {}
        self.processor_functions: Dict[str, Callable] = {}

        # Processing state
        self.protected_content: Dict[str, ProtectedContent] = {}
        self.processing_metadata: Dict[str, Any] = {}

        # Register built-in processors
        self._register_builtin_processors()

        logger.debug("ContentProcessor initialized")

    def _register_builtin_processors(self) -> None:
        """Register built-in content processors."""
        # Import processor functions
        from ..converters.code_processor import (
            convert_code_blocks_to_latex,
            protect_code_content,
            restore_protected_code,
        )
        from ..converters.figure_processor import (
            convert_equation_references_to_latex,
            convert_figure_references_to_latex,
            convert_figures_to_latex,
        )
        from ..converters.html_processor import convert_html_comments_to_latex, convert_html_tags_to_latex
        from ..converters.list_processor import convert_lists_to_latex
        from ..converters.math_processor import (
            process_enhanced_math_blocks,
            protect_math_expressions,
            restore_math_expressions,
        )
        from ..converters.supplementary_note_processor import (
            process_supplementary_note_references,
            process_supplementary_notes,
            restore_supplementary_note_placeholders,
        )
        from ..converters.table_processor import convert_table_references_to_latex
        from ..converters.text_formatters import (
            convert_subscript_superscript_to_latex,
            escape_special_characters,
            process_code_spans,
            protect_bold_outside_texttt,
            protect_italic_outside_texttt,
            restore_protected_seqsplit,
        )
        from ..converters.url_processor import convert_links_to_latex

        # Stage 1: Preparation - Critical early processing
        self.register_processor(
            "code_blocks",
            convert_code_blocks_to_latex,
            ProcessorConfig(name="code_blocks", priority=ProcessorPriority.CRITICAL, stage=ProcessingStage.PREPARATION),
        )

        self.register_processor(
            "enhanced_math_blocks",
            process_enhanced_math_blocks,
            ProcessorConfig(
                name="enhanced_math_blocks", priority=ProcessorPriority.CRITICAL, stage=ProcessingStage.PREPARATION
            ),
        )

        # Stage 2: Protection - Protect content from further processing
        self.register_processor(
            "protect_code",
            self._create_protection_wrapper("code", protect_code_content),
            ProcessorConfig(
                name="protect_code",
                priority=ProcessorPriority.HIGH,
                stage=ProcessingStage.PROTECTION,
                dependencies=["code_blocks"],
            ),
        )

        self.register_processor(
            "protect_math",
            self._create_protection_wrapper("math", protect_math_expressions),
            ProcessorConfig(
                name="protect_math",
                priority=ProcessorPriority.HIGH,
                stage=ProcessingStage.PROTECTION,
                dependencies=["enhanced_math_blocks"],
            ),
        )

        self.register_processor(
            "protect_markdown_tables",
            self._create_protection_wrapper("markdown_tables", self._import_protect_markdown_tables),
            ProcessorConfig(
                name="protect_markdown_tables", priority=ProcessorPriority.HIGH, stage=ProcessingStage.PROTECTION
            ),
        )

        # Stage 3: Conversion - Main content conversion
        # Early conversion of page break markers
        self.register_processor(
            "newpage_markers",
            self._process_newpage_markers,
            ProcessorConfig(name="newpage_markers", priority=ProcessorPriority.HIGH, stage=ProcessingStage.CONVERSION),
        )

        self.register_processor(
            "float_barrier_markers",
            self._process_float_barrier_markers,
            ProcessorConfig(
                name="float_barrier_markers",
                priority=ProcessorPriority.HIGH,
                stage=ProcessingStage.CONVERSION,
                dependencies=["newpage_markers"],
            ),
        )

        self.register_processor(
            "html_comments",
            convert_html_comments_to_latex,
            ProcessorConfig(
                name="html_comments",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["float_barrier_markers"],
            ),
        )

        self.register_processor(
            "html_tags",
            convert_html_tags_to_latex,
            ProcessorConfig(
                name="html_tags",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["html_comments"],
            ),
        )

        self.register_processor(
            "lists",
            convert_lists_to_latex,
            ProcessorConfig(name="lists", priority=ProcessorPriority.NORMAL, stage=ProcessingStage.CONVERSION),
        )

        self.register_processor(
            "tables",
            lambda content, **kwargs: self._process_tables_enhanced(content, **kwargs),
            ProcessorConfig(
                name="tables",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["lists"],
            ),
        )

        self.register_processor(
            "figures",
            lambda content, **kwargs: convert_figures_to_latex(content, kwargs.get("is_supplementary", False)),
            ProcessorConfig(
                name="figures",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["tables"],
            ),
        )

        # Supplementary note headers must be processed early (before general headers)
        self.register_processor(
            "supplementary_notes",
            lambda content, **kwargs: process_supplementary_notes(content)
            if kwargs.get("is_supplementary", False)
            else content,
            ProcessorConfig(
                name="supplementary_notes",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["figures"],
            ),
        )

        # Headers processor runs after supplementary notes
        self.register_processor(
            "headers",
            lambda content, **kwargs: self._convert_headers_enhanced(content, kwargs.get("is_supplementary", False)),
            ProcessorConfig(
                name="headers",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["supplementary_notes"],
            ),
        )

        self.register_processor(
            "figure_references",
            convert_figure_references_to_latex,
            ProcessorConfig(
                name="figure_references",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["headers"],
            ),
        )

        self.register_processor(
            "equation_references",
            convert_equation_references_to_latex,
            ProcessorConfig(
                name="equation_references",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["figure_references"],
            ),
        )

        self.register_processor(
            "table_references",
            convert_table_references_to_latex,
            ProcessorConfig(
                name="table_references",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["equation_references"],
            ),
        )

        self.register_processor(
            "citations",
            lambda content, **kwargs: self._process_citations_enhanced(content, **kwargs),
            ProcessorConfig(
                name="citations",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["supplementary_note_references"],
            ),
        )

        # Text formatting processors (LOW priority)
        self.register_processor(
            "code_spans",
            process_code_spans,
            ProcessorConfig(
                name="code_spans",
                priority=ProcessorPriority.LOW,
                stage=ProcessingStage.CONVERSION,
                dependencies=["citations"],
            ),
        )

        self.register_processor(
            "bold_formatting",
            protect_bold_outside_texttt,
            ProcessorConfig(
                name="bold_formatting",
                priority=ProcessorPriority.LOW,
                stage=ProcessingStage.CONVERSION,
                dependencies=["code_spans"],
            ),
        )

        self.register_processor(
            "italic_formatting",
            protect_italic_outside_texttt,
            ProcessorConfig(
                name="italic_formatting",
                priority=ProcessorPriority.LOW,
                stage=ProcessingStage.CONVERSION,
                dependencies=["bold_formatting"],
            ),
        )

        # Special handling for italic text in list items (must come after italic_formatting)
        self.register_processor(
            "italic_in_lists",
            lambda content, **kwargs: re.sub(r"(\\item\s+)\*([^*]+?)\*", r"\1\\textit{\2}", content),
            ProcessorConfig(
                name="italic_in_lists",
                priority=ProcessorPriority.LOW,
                stage=ProcessingStage.CONVERSION,
                dependencies=["italic_formatting"],
            ),
        )

        self.register_processor(
            "urls",
            convert_links_to_latex,
            ProcessorConfig(
                name="urls",
                priority=ProcessorPriority.LOW,
                stage=ProcessingStage.CONVERSION,
                dependencies=["italic_in_lists"],
            ),
        )

        # Supplementary note references (moved up in processing order)

        self.register_processor(
            "supplementary_note_references",
            process_supplementary_note_references,
            ProcessorConfig(
                name="supplementary_note_references",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["table_references"],
            ),
        )

        # Stage 4: Restoration - Restore protected content
        self.register_processor(
            "restore_math",
            self._create_restoration_wrapper("math", restore_math_expressions),
            ProcessorConfig(name="restore_math", priority=ProcessorPriority.HIGH, stage=ProcessingStage.RESTORATION),
        )

        self.register_processor(
            "restore_code",
            self._create_restoration_wrapper("code", restore_protected_code),
            ProcessorConfig(name="restore_code", priority=ProcessorPriority.HIGH, stage=ProcessingStage.RESTORATION),
        )

        self.register_processor(
            "restore_supplementary_placeholders",
            lambda content, **kwargs: restore_supplementary_note_placeholders(content)
            if kwargs.get("is_supplementary", False)
            else content,
            ProcessorConfig(
                name="restore_supplementary_placeholders",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.RESTORATION,
            ),
        )

        self.register_processor(
            "restore_tables",
            self._restore_protected_tables,
            ProcessorConfig(
                name="restore_tables",
                priority=ProcessorPriority.HIGH,
                stage=ProcessingStage.RESTORATION,
                dependencies=["restore_code"],
            ),
        )

        # Stage 5: Finalization - Final text formatting
        self.register_processor(
            "subscript_superscript",
            convert_subscript_superscript_to_latex,
            ProcessorConfig(
                name="subscript_superscript", priority=ProcessorPriority.LOW, stage=ProcessingStage.FINALIZATION
            ),
        )

        self.register_processor(
            "escape_special",
            escape_special_characters,
            ProcessorConfig(
                name="escape_special", priority=ProcessorPriority.CLEANUP, stage=ProcessingStage.FINALIZATION
            ),
        )

        self.register_processor(
            "restore_seqsplit",
            restore_protected_seqsplit,
            ProcessorConfig(
                name="restore_seqsplit",
                priority=ProcessorPriority.CLEANUP,
                stage=ProcessingStage.FINALIZATION,
                dependencies=["escape_special"],
            ),
        )

        self.register_processor(
            "restore_underscores",
            lambda content, **kwargs: content.replace("XUNDERSCOREX", "\\_"),
            ProcessorConfig(
                name="restore_underscores",
                priority=ProcessorPriority.CLEANUP,
                stage=ProcessingStage.FINALIZATION,
                dependencies=["restore_seqsplit"],
            ),
        )

    def register_processor(self, name: str, function: Callable, config: ProcessorConfig) -> None:
        """Register a content processor.

        Args:
            name: Processor name
            function: Processing function
            config: Processor configuration
        """
        self.processors[name] = config
        self.processor_functions[name] = function

        logger.debug(f"Registered processor: {name} ({config.stage.value})")

    def _create_protection_wrapper(self, protection_type: str, protect_function: Callable) -> Callable:
        """Create wrapper for protection functions.

        Args:
            protection_type: Type of protection (e.g., "math", "code")
            protect_function: Function that protects content

        Returns:
            Wrapped function that stores protected content
        """

        def wrapper(content: MarkdownContent, **kwargs) -> MarkdownContent:
            protected_content, protected_dict = protect_function(content)
            self.protected_content[protection_type] = protected_dict
            return protected_content

        return wrapper

    def _create_restoration_wrapper(self, protection_type: str, restore_function: Callable) -> Callable:
        """Create wrapper for restoration functions.

        Args:
            protection_type: Type of protection to restore
            restore_function: Function that restores content

        Returns:
            Wrapped function that uses stored protected content
        """

        def wrapper(content: LatexContent, **kwargs) -> LatexContent:
            protected_dict = self.protected_content.get(protection_type, {})
            return restore_function(content, protected_dict)

        return wrapper

    def _import_protect_markdown_tables(self, content: str):
        """Import and call the markdown table protection function."""
        from ..converters.md2tex import _protect_markdown_tables

        return _protect_markdown_tables(content)

    def _process_newpage_markers(self, content: MarkdownContent) -> LatexContent:
        """Convert <newpage> and <clearpage> markers to LaTeX commands."""
        # Replace <clearpage> with \\clearpage
        content = re.sub(r"^\s*<clearpage>\s*$", r"\\clearpage", content, flags=re.MULTILINE)
        content = re.sub(r"<clearpage>", r"\\clearpage", content)

        # Replace <newpage> with \\newpage
        content = re.sub(r"^\s*<newpage>\s*$", r"\\newpage", content, flags=re.MULTILINE)
        content = re.sub(r"<newpage>", r"\\newpage", content)

        return content

    def _process_float_barrier_markers(self, content: MarkdownContent) -> LatexContent:
        r"""Convert <float-barrier> markers to LaTeX \\FloatBarrier commands."""
        # Replace <float-barrier> with \\FloatBarrier
        content = re.sub(r"^\s*<float-barrier>\s*$", r"\\FloatBarrier", content, flags=re.MULTILINE)
        content = re.sub(r"<float-barrier>", r"\\FloatBarrier", content)

        return content

    def _convert_headers_enhanced(self, content: LatexContent, is_supplementary: bool = False) -> LatexContent:
        """Enhanced header conversion that properly handles supplementary content."""
        # Use the legacy header conversion logic but ensure ALL ### headers get converted
        # even in supplementary content, since supplementary note processing should have
        # already handled the ones that needed special treatment
        if is_supplementary:
            # For supplementary content, use \section* for the first header
            content = re.sub(r"^# (.+)$", r"\\section*{\1}", content, flags=re.MULTILINE, count=1)
            # Then replace any remaining # headers with regular \section
            content = re.sub(r"^# (.+)$", r"\\section{\1}", content, flags=re.MULTILINE)
        else:
            content = re.sub(r"^# (.+)$", r"\\section{\1}", content, flags=re.MULTILINE)

        content = re.sub(r"^## (.+)$", r"\\subsection{\1}", content, flags=re.MULTILINE)

        # Convert ALL remaining ### headers to \subsubsection{}, even in supplementary content
        # This runs after supplementary note processing, so any ### headers that remain
        # are standalone headers that should be converted normally
        content = re.sub(r"^### (.+)$", r"\\subsubsection{\1}", content, flags=re.MULTILINE)

        content = re.sub(r"^#### (.+)$", r"\\paragraph{\1}", content, flags=re.MULTILINE)
        return content

    def _process_tables_enhanced(self, content: MarkdownContent, **kwargs) -> LatexContent:
        """Enhanced table processing with protection integration."""
        from ..converters.table_processor import convert_tables_to_latex

        is_supplementary = kwargs.get("is_supplementary", False)

        # Get protected content from processing state
        protected_markdown_tables = self.protected_content.get("markdown_tables", {})
        protected_backtick_content = self.protected_content.get("code", {})  # From code protection

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
        protected_tables = self.protected_content.setdefault("tables", {})

        def protect_latex_table(match):
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

    def _restore_protected_tables(self, content: LatexContent, **kwargs) -> LatexContent:
        """Restore protected table content."""
        protected_tables = self.protected_content.get("tables", {})

        # Restore protected tables at the very end (after all other conversions)
        for placeholder, table_content in protected_tables.items():
            content = content.replace(placeholder, table_content)

        return content

    def _process_citations_enhanced(self, content: MarkdownContent, **kwargs) -> LatexContent:
        """Enhanced citation processing with table protection integration."""
        from ..converters.citation_processor import process_citations_outside_tables

        # Get protected tables from the processing state
        protected_markdown_tables = self.protected_content.get("markdown_tables", {})

        # Process citations with table protection
        return process_citations_outside_tables(content, protected_markdown_tables)

    def _get_execution_order(self) -> List[str]:
        """Get processors in execution order based on stage and priority.

        Returns:
            List of processor names in execution order
        """
        # Sort by stage, then by priority, then by dependencies
        all_processors = list(self.processors.keys())

        # Group by stage
        stages = {stage: [] for stage in ProcessingStage}
        for name in all_processors:
            config = self.processors[name]
            if config.enabled:
                stages[config.stage].append(name)

        # Sort within each stage by priority and dependencies
        ordered_processors = []
        for stage in ProcessingStage:
            stage_processors = stages[stage]

            # Sort by priority
            stage_processors.sort(key=lambda name: self.processors[name].priority.value)

            # Resolve dependencies within stage
            stage_ordered = self._resolve_dependencies(stage_processors)
            ordered_processors.extend(stage_ordered)

        return ordered_processors

    def _resolve_dependencies(self, processor_names: List[str]) -> List[str]:
        """Resolve processor dependencies within a stage.

        Args:
            processor_names: List of processor names to order

        Returns:
            Dependency-resolved list
        """
        ordered = []
        remaining = processor_names.copy()

        while remaining:
            ready = []
            for name in remaining:
                config = self.processors[name]
                # Check if all dependencies are satisfied
                if all(dep in ordered or dep not in processor_names for dep in config.dependencies):
                    ready.append(name)

            if not ready:
                # Circular dependency or missing dependency
                logger.warning(f"Cannot resolve dependencies for: {remaining}")
                ordered.extend(remaining)
                break

            for name in ready:
                ordered.append(name)
                remaining.remove(name)

        return ordered

    def process(self, content: MarkdownContent, is_supplementary: bool = False, **kwargs) -> ProcessingResult:
        """Process markdown content through the complete pipeline.

        Args:
            content: Markdown content to process
            is_supplementary: Whether processing supplementary content
            **kwargs: Additional processing arguments

        Returns:
            Processing result with converted content
        """
        start_time = time.time()

        logger.info("Starting content processing pipeline")

        with managed_resources():
            # Clear previous state
            self.protected_content.clear()
            self.processing_metadata.clear()

            # Get execution order
            ordered_processors = self._get_execution_order()

            if not ordered_processors:
                logger.warning("No processors enabled")
                return ProcessingResult(
                    success=False,
                    content=content,
                    duration=0.0,
                    stage=ProcessingStage.PREPARATION,
                    errors=["No processors enabled"],
                )

            # Process content through pipeline
            current_content = content
            processor_results = {}
            warnings = []
            errors = []
            current_stage = ProcessingStage.PREPARATION

            for i, processor_name in enumerate(ordered_processors):
                config = self.processors[processor_name]
                function = self.processor_functions[processor_name]

                # Report progress
                if self.progress_callback:
                    self.progress_callback(f"Processing {processor_name}", i + 1, len(ordered_processors))

                # Update current stage
                current_stage = config.stage

                try:
                    processor_start = time.time()

                    # Execute processor
                    logger.debug(f"Running processor: {processor_name} ({config.stage.value})")

                    # Pass context to processor, handling different function signatures
                    processor_kwargs = {"is_supplementary": is_supplementary, **kwargs}

                    if config.timeout:
                        # TODO: Implement timeout handling
                        pass

                    # Try calling with kwargs first, fallback to content-only
                    try:
                        processed_content = function(current_content, **processor_kwargs)
                    except TypeError as e:
                        if "unexpected keyword argument" in str(e):
                            # Function doesn't accept the additional arguments, call with content only
                            logger.debug(f"Processor {processor_name} doesn't accept kwargs, calling with content only")
                            processed_content = function(current_content)
                        else:
                            raise

                    processor_duration = time.time() - processor_start

                    # Store result
                    processor_results[processor_name] = {
                        "success": True,
                        "duration": processor_duration,
                        "stage": config.stage.value,
                    }

                    current_content = processed_content

                    logger.debug(f"Processor {processor_name} completed ({processor_duration:.3f}s)")

                except Exception as e:
                    error_msg = f"Processor {processor_name} failed: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

                    processor_results[processor_name] = {"success": False, "error": str(e), "stage": config.stage.value}

                    # Continue processing unless critical
                    if config.priority == ProcessorPriority.CRITICAL:
                        logger.error(f"Critical processor {processor_name} failed, stopping pipeline")
                        break

            # Calculate final result
            total_duration = time.time() - start_time
            success = len(errors) == 0

            result = ProcessingResult(
                success=success,
                content=current_content,
                duration=total_duration,
                stage=current_stage,
                processor_results=processor_results,
                protected_content=self.protected_content.copy(),
                metadata=self.processing_metadata.copy(),
                warnings=warnings,
                errors=errors,
            )

            logger.info(
                f"Content processing completed: {len(ordered_processors)} processors, "
                f"{len(errors)} errors, {len(warnings)} warnings ({total_duration:.1f}s)"
            )

            return result

    def get_processor_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered processors.

        Returns:
            Dictionary with processor status information
        """
        return {
            name: {
                "enabled": config.enabled,
                "priority": config.priority.value,
                "stage": config.stage.value,
                "dependencies": config.dependencies,
            }
            for name, config in self.processors.items()
        }


# Global content processor instance
_content_processor: Optional[ContentProcessor] = None


def get_content_processor() -> ContentProcessor:
    """Get the global content processor instance.

    Returns:
        Global content processor
    """
    global _content_processor
    if _content_processor is None:
        _content_processor = ContentProcessor()
    return _content_processor


# Convenience function for backward compatibility
def convert_markdown_to_latex(content: MarkdownContent, is_supplementary: bool = False, **kwargs) -> LatexContent:
    """Convert markdown to LaTeX using centralized processor.

    Args:
        content: Markdown content to convert
        is_supplementary: Whether processing supplementary content
        **kwargs: Additional processing arguments

    Returns:
        Converted LaTeX content
    """
    processor = get_content_processor()
    result = processor.process(content, is_supplementary=is_supplementary, **kwargs)

    if not result.success:
        logger.warning(f"Content processing completed with errors: {result.errors}")

    return result.content
