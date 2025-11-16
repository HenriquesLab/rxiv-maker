"""Template manager for manuscript initialization.

This module provides the TemplateManager class which handles the creation
of manuscript files using templates from the template registry.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from .registry import TemplateFile, get_template_registry


class TemplateType(Enum):
    """Available template types."""

    DEFAULT = "default"
    MINIMAL = "minimal"
    JOURNAL = "journal"
    PREPRINT = "preprint"


class TemplateManager:
    """Manager for creating manuscripts from templates."""

    def __init__(self, template_type: str = "default"):
        """Initialize template manager.

        Args:
            template_type: Type of template to use (default, minimal, journal, preprint)
        """
        self.template_type = template_type
        self.registry = get_template_registry()

        # Validate template type
        if template_type not in self.registry.list_template_types():
            raise ValueError(
                f"Unknown template type: {template_type}. Available: {', '.join(self.registry.list_template_types())}"
            )

    def create_manuscript(
        self,
        manuscript_dir: Path,
        title: str = "Your Manuscript Title",
        author_name: str = "Your Name",
        author_email: str = "your.email@example.com",
        author_orcid: str = "0000-0000-0000-0000",
        author_affiliation: str = "Your Institution",
    ) -> Dict[str, Path]:
        """Create a complete manuscript structure from templates.

        Args:
            manuscript_dir: Directory to create manuscript in
            title: Manuscript title
            author_name: Author name
            author_email: Author email
            author_orcid: Author ORCID
            author_affiliation: Author affiliation

        Returns:
            Dictionary mapping file types to created file paths
        """
        manuscript_dir = Path(manuscript_dir)
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        # Create FIGURES directory
        figures_dir = manuscript_dir / "FIGURES"
        figures_dir.mkdir(exist_ok=True)

        # Template variables for substitution
        template_vars = {
            "title": title,
            "author_name": author_name,
            "author_email": author_email,
            "author_orcid": author_orcid,
            "author_affiliation": author_affiliation,
        }

        created_files = {}

        # Create each file from templates
        for file_type in TemplateFile:
            file_path = self._get_file_path(manuscript_dir, file_type)
            content = self.registry.get_template(self.template_type, file_type, **template_vars)

            # Write file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            created_files[file_type.name] = file_path

        return created_files

    def create_config_file(
        self,
        output_path: Path,
        title: str = "Your Manuscript Title",
        author_name: str = "Your Name",
        author_email: str = "your.email@example.com",
        author_orcid: str = "0000-0000-0000-0000",
        author_affiliation: str = "Your Institution",
    ) -> Path:
        """Create just the configuration file.

        Args:
            output_path: Path to write configuration file
            title: Manuscript title
            author_name: Author name
            author_email: Author email
            author_orcid: Author ORCID
            author_affiliation: Author affiliation

        Returns:
            Path to created configuration file
        """
        template_vars = {
            "title": title,
            "author_name": author_name,
            "author_email": author_email,
            "author_orcid": author_orcid,
            "author_affiliation": author_affiliation,
        }

        content = self.registry.get_template(self.template_type, TemplateFile.CONFIG, **template_vars)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        return output_path

    def get_template_content(self, file_type: TemplateFile, **kwargs) -> str:
        """Get template content for a specific file type.

        Args:
            file_type: Type of file template to retrieve
            **kwargs: Variables for template substitution

        Returns:
            Template content with variables substituted
        """
        return self.registry.get_template(self.template_type, file_type, **kwargs)

    def list_available_templates(self) -> list[str]:
        """List all available template types.

        Returns:
            List of template type names
        """
        return self.registry.list_template_types()

    def _get_file_path(self, manuscript_dir: Path, file_type: TemplateFile) -> Path:
        """Get the file path for a given template file type.

        Args:
            manuscript_dir: Base manuscript directory
            file_type: Type of file

        Returns:
            Path where the file should be created
        """
        # Map template file enums to actual paths
        file_name = file_type.value

        # Handle files in subdirectories
        if "/" in file_name:
            return manuscript_dir / file_name
        else:
            return manuscript_dir / file_name


# Singleton instance
_template_manager: Optional[Dict[str, TemplateManager]] = None


def get_template_manager(template_type: str = "default") -> TemplateManager:
    """Get template manager instance.

    Args:
        template_type: Type of template to use

    Returns:
        TemplateManager instance
    """
    global _template_manager
    if _template_manager is None:
        _template_manager = {}

    if template_type not in _template_manager:
        _template_manager[template_type] = TemplateManager(template_type)

    return _template_manager[template_type]


__all__ = ["TemplateManager", "TemplateType", "get_template_manager"]
