"""Enhanced centralized content processing for rxiv-maker.

This module provides a centralized ContentProcessor that manages the complete
markdown→LaTeX conversion pipeline with better error handling, state management,
and extensibility compared to the scattered logic in md2tex.py.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..converters.types import LatexContent, MarkdownContent, ProtectedContent
from .error_recovery import RecoveryEnhancedMixin
from .logging_config import get_logger
from .resource_manager import get_resource_manager, managed_resources

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
            convert_figures_to_latex,
        )
        from ..converters.html_processor import convert_html_comments_to_latex, convert_html_tags_to_latex
        from ..converters.list_processor import convert_lists_to_latex
        from ..converters.math_processor import (
            process_enhanced_math_blocks,
            protect_math_expressions,
            restore_math_expressions,
        )
        from ..converters.md2tex import _convert_headers
        from ..converters.text_formatters import (
            convert_subscript_superscript_to_latex,
            escape_special_characters,
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
        self.register_processor(
            "html_comments",
            convert_html_comments_to_latex,
            ProcessorConfig(name="html_comments", priority=ProcessorPriority.NORMAL, stage=ProcessingStage.CONVERSION),
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

        self.register_processor(
            "headers",
            lambda content, **kwargs: _convert_headers(content, kwargs.get("is_supplementary", False)),
            ProcessorConfig(
                name="headers",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["figures"],
            ),
        )

        self.register_processor(
            "citations",
            lambda content, **kwargs: self._process_citations_enhanced(content, **kwargs),
            ProcessorConfig(
                name="citations",
                priority=ProcessorPriority.NORMAL,
                stage=ProcessingStage.CONVERSION,
                dependencies=["headers"],
            ),
        )

        self.register_processor(
            "urls",
            convert_links_to_latex,
            ProcessorConfig(name="urls", priority=ProcessorPriority.LOW, stage=ProcessingStage.CONVERSION),
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

    def _process_tables_enhanced(self, content: MarkdownContent, **kwargs) -> LatexContent:
        """Enhanced table processing with protection integration."""
        from ..converters.table_processor import convert_tables_to_latex

        # Use existing table processing logic
        is_supplementary = kwargs.get("is_supplementary", False)
        return convert_tables_to_latex(content, is_supplementary)

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
