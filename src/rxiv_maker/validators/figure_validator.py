"""Figure validator for checking figure syntax, attributes, and file existence."""

import os
import re
from typing import Any

from ..core.error_codes import ErrorCode, create_validation_error
from .base_validator import (
    BaseValidator,
    ValidationError,
    ValidationLevel,
    ValidationResult,
)


class FigureValidator(BaseValidator):
    """Validates figure syntax, attributes, and file references."""

    # Figure patterns based on codebase analysis
    FIGURE_PATTERNS = {
        "traditional": re.compile(r"!\[([^\]]*)\]\(([^)]+)\)(\{[^}]*\})?"),  # ![caption](path){attrs}
        "new_format": re.compile(
            r"!\[\]\(([^)]+)\)\s*\n\s*(\{[^}]*\})\s*\*\*([^*]+)\*\*.*?(?=\n\n|\Z)",
            re.MULTILINE | re.DOTALL,
        ),  # ![](path)\n{attrs} **caption**
    }

    # Attribute patterns
    ATTRIBUTE_PATTERNS = {
        "id": re.compile(r"#([a-zA-Z0-9_:-]+)"),
        "width": re.compile(r'width=(["\'])([^"\']*)\1'),
        "tex_position": re.compile(r'tex_position=(["\'])([^"\']*)\1'),
        "span": re.compile(r'span=(["\'])([^"\']*)\1'),
        "twocolumn": re.compile(r'twocolumn=(["\'])([^"\']*)\1'),
    }

    # Valid file extensions for figures
    VALID_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".pdf",
        ".svg",
        ".eps",
        ".py",
        ".mmd",
        ".r",
    }

    # Valid width formats
    WIDTH_PATTERNS = {
        "percentage": re.compile(r"^\d+(\.\d+)?%$"),  # 80%
        "decimal": re.compile(r"^0?\.\d+$"),  # 0.8
        "textwidth": re.compile(r"^\\textwidth$"),  # \textwidth
        "columnwidth": re.compile(r"^\\columnwidth$"),  # \columnwidth
    }

    def __init__(self, manuscript_path: str):
        """Initialize figure validator.

        Args:
            manuscript_path: Path to the manuscript directory
        """
        super().__init__(manuscript_path)
        self.figures_dir = os.path.join(manuscript_path, "FIGURES")
        self.found_figures: list[dict] = []
        self.available_files: set[str] = set()

    def validate(self) -> ValidationResult:
        """Validate figures in manuscript files."""
        errors = []
        metadata = {}

        # Check if FIGURES directory exists
        if not os.path.exists(self.figures_dir):
            errors.append(
                create_validation_error(
                    ErrorCode.DIRECTORY_NOT_FOUND,
                    "FIGURES directory not found",
                    suggestion="Create FIGURES/ directory in manuscript folder",
                )
            )
            return ValidationResult("FigureValidator", errors, {"figures_dir_missing": True})

        # Scan available figure files
        self.available_files = self._scan_available_files()
        metadata["available_files"] = len(self.available_files)

        # Process manuscript files
        files_to_check = [
            ("01_MAIN.md", "main"),
            ("02_SUPPLEMENTARY_INFO.md", "supplementary"),
        ]

        for filename, file_type in files_to_check:
            file_path = os.path.join(self.manuscript_path, filename)
            if os.path.exists(file_path):
                file_errors = self._validate_file_figures(file_path, file_type)
                errors.extend(file_errors)

        # Check for unused figure files
        unused_warnings = self._check_unused_files()
        errors.extend(unused_warnings)

        # Add statistics to metadata
        metadata.update(self._generate_figure_statistics())

        return ValidationResult("FigureValidator", errors, metadata)

    def _scan_available_files(self) -> set[str]:
        """Scan FIGURES directory for available files."""
        available = set()

        try:
            for root, _, files in os.walk(self.figures_dir):
                for file in files:
                    # Skip hidden files and temporary files
                    if file.startswith(".") or file.startswith("~"):
                        continue

                    full_path = os.path.join(root, file)
                    # Store relative path from FIGURES directory
                    rel_path = os.path.relpath(full_path, self.figures_dir)
                    available.add(rel_path)

        except OSError:
            pass  # Directory access issues handled elsewhere

        return available

    def _validate_file_figures(self, file_path: str, file_type: str) -> list:
        """Validate figures in a specific file."""
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

        # Find all figure references
        figure_errors = self._find_and_validate_figures(content, file_path, file_type)
        errors.extend(figure_errors)

        return errors

    def _find_and_validate_figures(self, content: str, file_path: str, file_type: str) -> list:
        """Find and validate all figures in content."""
        errors = []
        processed_positions = set()

        # First, check for new format figures to avoid double-matching
        for match in self.FIGURE_PATTERNS["new_format"].finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            fig_path = match.group(1)
            attrs_str = match.group(2)
            caption = match.group(3)

            figure_info = {
                "format": "new",
                "caption": caption,
                "path": fig_path,
                "attributes": attrs_str,
                "line": line_num,
                "file": os.path.basename(file_path),
                "file_type": file_type,
            }

            self.found_figures.append(figure_info)

            figure_errors = self._validate_single_figure(figure_info, file_path, line_num)
            errors.extend(figure_errors)

            # Mark this position as processed to avoid traditional pattern match
            processed_positions.add(match.start())

        # Then check traditional format, but skip already processed positions
        for match in self.FIGURE_PATTERNS["traditional"].finditer(content):
            # Skip if this position was already processed by new format
            if match.start() in processed_positions:
                continue

            line_num = content[: match.start()].count("\n") + 1
            caption = match.group(1)
            fig_path = match.group(2)
            attrs_str = match.group(3) or ""

            figure_info = {
                "format": "traditional",
                "caption": caption,
                "path": fig_path,
                "attributes": attrs_str,
                "line": line_num,
                "file": os.path.basename(file_path),
                "file_type": file_type,
            }

            self.found_figures.append(figure_info)

            figure_errors = self._validate_single_figure(figure_info, file_path, line_num)
            errors.extend(figure_errors)

        return errors

    def _validate_single_figure(self, figure_info: dict, file_path: str, line_num: int) -> list:
        """Validate a single figure reference."""
        errors = []

        # Validate file path and existence
        path_errors = self._validate_figure_path(figure_info, file_path, line_num)
        errors.extend(path_errors)

        # Validate attributes
        attr_errors = self._validate_figure_attributes(figure_info, file_path, line_num)
        errors.extend(attr_errors)

        # Validate caption
        caption_errors = self._validate_figure_caption(figure_info, file_path, line_num)
        errors.extend(caption_errors)

        return errors

    def _validate_figure_path(self, figure_info: dict, file_path: str, line_num: int) -> list:
        """Validate figure file path and existence."""
        errors = []
        fig_path = figure_info["path"]

        # Check if path starts with FIGURES/
        if not fig_path.startswith("FIGURES/"):
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    f"Figure path should start with 'FIGURES/': {fig_path}",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=("Use relative paths from manuscript root: FIGURES/filename.ext"),
                    error_code="non_standard_path",
                )
            )

        # Extract file path relative to FIGURES directory
        rel_path = fig_path[8:] if fig_path.startswith("FIGURES/") else fig_path

        # Check file extension
        _, ext = os.path.splitext(rel_path.lower())
        if ext not in self.VALID_EXTENSIONS:
            errors.append(
                self._create_error(
                    ValidationLevel.ERROR,
                    f"Unsupported figure format: {ext}",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=(f"Use supported formats: {', '.join(sorted(self.VALID_EXTENSIONS))}"),
                    error_code="unsupported_format",
                )
            )

        # Check if file exists
        if rel_path not in self.available_files:
            # For .py and .mmd files, check if they will generate the expected output
            if ext in {".py", ".mmd"}:
                expected_outputs = self._get_expected_outputs(rel_path)
                if not any(output in self.available_files for output in expected_outputs):
                    errors.append(
                        self._create_error(
                            ValidationLevel.WARNING,
                            f"Figure source file not found: {fig_path}",
                            file_path=file_path,
                            line_number=line_num,
                            suggestion=("Ensure the figure source file exists in FIGURES/ directory"),
                            error_code="missing_source_file",
                        )
                    )
            else:
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Figure file not found: {fig_path}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=("Ensure the figure file exists in FIGURES/ directory"),
                        error_code="missing_figure_file",
                    )
                )

        return errors

    def _validate_figure_attributes(self, figure_info: dict, file_path: str, line_num: int) -> list[ValidationError]:
        """Validate figure attributes."""
        errors: list[ValidationError] = []
        attrs_str = figure_info["attributes"]

        if not attrs_str:
            return errors

        # Parse attributes
        attributes = self._parse_attributes(attrs_str)

        # Validate ID format
        if "id" in attributes:
            id_value = attributes["id"]
            if not re.match(r"^[a-zA-Z0-9_:-]+$", id_value):
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Non-standard figure ID format: {id_value}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=("Use letters, numbers, underscores, and hyphens for IDs"),
                        error_code="non_standard_id",
                    )
                )

        # Validate width format
        if "width" in attributes:
            width_value = attributes["width"]
            if not self._is_valid_width(width_value):
                errors.append(
                    self._create_error(
                        ValidationLevel.ERROR,
                        f"Invalid width format: {width_value}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="Use formats like '0.8', '80%', or '\\textwidth'",
                        error_code="invalid_width",
                    )
                )

        # Validate positioning
        if "tex_position" in attributes:
            pos_value = attributes["tex_position"]
            valid_positions = {
                "h",
                "t",
                "b",
                "p",
                "!h",
                "!t",
                "!b",
                "!p",
                "!ht",
                "!hb",
                "!tb",
                "!htb",
            }
            if pos_value not in valid_positions:
                errors.append(
                    self._create_error(
                        ValidationLevel.WARNING,
                        f"Non-standard LaTeX position: {pos_value}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=("Use standard LaTeX positions like 'h', 't', 'b', '!ht', etc."),
                        error_code="non_standard_position",
                    )
                )

        # Validate span/twocolumn consistency
        span_value = attributes.get("span")
        twocolumn_value = attributes.get("twocolumn")

        if span_value == "2col" and twocolumn_value and twocolumn_value.lower() != "true":
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "Conflicting span and twocolumn attributes",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="Use either span='2col' or twocolumn='true', not both",
                    error_code="conflicting_attributes",
                )
            )

        return errors

    def _validate_figure_caption(self, figure_info: dict, file_path: str, line_num: int) -> list:
        """Validate figure caption."""
        errors = []
        caption = figure_info["caption"]

        # Check if caption is empty
        if not caption or not caption.strip():
            errors.append(
                self._create_error(
                    ValidationLevel.WARNING,
                    "Figure has empty caption",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion="Add descriptive caption for accessibility and clarity",
                    error_code="empty_caption",
                )
            )

        # Check caption length (very long captions might be problematic)
        elif len(caption) > 500:
            errors.append(
                self._create_error(
                    ValidationLevel.INFO,
                    f"Very long figure caption ({len(caption)} characters)",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=("Consider shortening caption or moving details to main text"),
                    error_code="long_caption",
                )
            )

        return errors

    def _parse_attributes(self, attrs_str: str) -> dict[str, str]:
        """Parse figure attributes from string."""
        attributes = {}

        # Extract ID
        id_match = self.ATTRIBUTE_PATTERNS["id"].search(attrs_str)
        if id_match:
            attributes["id"] = id_match.group(1)

        # Extract other attributes
        for attr_name in ["width", "tex_position", "span", "twocolumn"]:
            pattern = self.ATTRIBUTE_PATTERNS[attr_name]
            match = pattern.search(attrs_str)
            if match:
                attributes[attr_name] = match.group(2)

        return attributes

    def _is_valid_width(self, width: str) -> bool:
        """Check if width format is valid."""
        return any(pattern.match(width) for pattern in self.WIDTH_PATTERNS.values())

    def _get_expected_outputs(self, source_file: str) -> list[str]:
        """Get expected output files for source files (.py, .mmd, .r)."""
        base_name = os.path.splitext(source_file)[0]
        ext = os.path.splitext(source_file)[1].lower()

        # Map file extensions to their expected output formats
        extension_outputs = {
            ".py": [f"{base_name}.pdf", f"{base_name}.png"],  # Python scripts
            ".mmd": [  # Mermaid files generate multiple formats
                f"{base_name}.pdf",
                f"{base_name}.png",
                f"{base_name}.svg",
            ],
            ".r": [  # R scripts generate multiple formats
                f"{base_name}.pdf",
                f"{base_name}.png",
                f"{base_name}.svg",
            ],
        }

        expected_outputs = extension_outputs.get(ext, [])

        # Also check for outputs in subdirectories (common pattern for figure generation)
        if expected_outputs:
            subdir_outputs = []
            for output in expected_outputs:
                # Add subdirectory version (e.g., SFigure__example/SFigure__example.svg)
                subdir_path = f"{base_name}/{os.path.basename(output)}"
                subdir_outputs.append(subdir_path)
            expected_outputs.extend(subdir_outputs)

        return expected_outputs

    def _check_unused_files(self) -> list:
        """Check for figure files that are not referenced."""
        warnings = []

        # Get all referenced file paths
        referenced_files = set()
        for figure in self.found_figures:
            fig_path = figure["path"]
            if fig_path.startswith("FIGURES/"):
                rel_path = fig_path[8:]
                referenced_files.add(rel_path)

                # For source files, also mark expected outputs as referenced
                _, ext = os.path.splitext(rel_path.lower())
                if ext in {".py", ".mmd", ".r"}:
                    expected_outputs = self._get_expected_outputs(rel_path)
                    referenced_files.update(expected_outputs)

        # Also mark all figure generation outputs as referenced to avoid false warnings
        # This includes all standard figure formats that are part of the pipeline
        pipeline_files = set()
        for file_path in self.available_files:
            base_name = os.path.splitext(file_path)[0]
            ext = os.path.splitext(file_path)[1].lower()

            # If we have a source file (.py, .mmd, or .r), mark potential outputs
            if ext in {".py", ".mmd", ".r"}:
                expected_outputs = self._get_expected_outputs(file_path)
                pipeline_files.update(expected_outputs)

            # If we have any figure file, mark other format variants as pipeline files
            elif ext in {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".eps"}:
                # Mark all format variants of this figure as pipeline files
                for output_ext in [".png", ".pdf", ".svg", ".jpg", ".jpeg", ".eps"]:
                    variant_file = base_name + output_ext
                    if variant_file in self.available_files:
                        pipeline_files.add(variant_file)

        # Add pipeline files to referenced files
        referenced_files.update(pipeline_files)

        # Find unused files (excluding data files, hidden files, and pipeline files)
        unused_files = []
        for file_path in self.available_files:
            if (
                file_path not in referenced_files
                and not file_path.startswith("DATA/")
                and not os.path.basename(file_path).startswith(".")
                and os.path.splitext(file_path)[1].lower()
                not in {
                    ".png",
                    ".pdf",
                    ".svg",
                    ".jpg",
                    ".jpeg",
                    ".eps",
                    ".py",
                    ".mmd",
                    ".r",
                }
            ):
                # Skip files in DATA/ subdirectory, hidden files, and
                # known pipeline extensions
                unused_files.append(file_path)

        for unused_file in unused_files:
            warnings.append(
                self._create_error(
                    ValidationLevel.INFO,
                    f"Unused figure file: FIGURES/{unused_file}",
                    suggestion=("Consider removing unused files to reduce repository size"),
                    error_code="unused_figure_file",
                )
            )

        return warnings

    def _generate_figure_statistics(self) -> dict[str, Any]:
        """Generate statistics about figures."""
        stats: dict[str, Any] = {
            "total_figures": len(self.found_figures),
            "figures_by_format": {"traditional": 0, "new": 0},
            "figures_by_type": {"main": 0, "supplementary": 0},
            "total_available_files": len(self.available_files),
            "file_types": {},
            "figures_with_ids": 0,
            "figures_with_custom_width": 0,
        }

        for figure in self.found_figures:
            # Count by format
            stats["figures_by_format"][figure["format"]] += 1

            # Count by file type
            stats["figures_by_type"][figure["file_type"]] += 1

            # Count figures with IDs
            if "#" in figure["attributes"]:
                stats["figures_with_ids"] += 1

            # Count figures with custom width
            if "width=" in figure["attributes"]:
                stats["figures_with_custom_width"] += 1

        # Count available files by extension
        file_types: dict[str, int] = stats["file_types"]
        for file_path in self.available_files:
            _, ext = os.path.splitext(file_path.lower())
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1

        return stats
