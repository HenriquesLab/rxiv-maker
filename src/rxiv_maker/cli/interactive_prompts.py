"""Interactive prompts and validators for rxiv-maker CLI.

This module provides reusable prompt functions and validators using prompt_toolkit
for a user-friendly interactive experience similar to taskrepo.
"""

from pathlib import Path
from typing import List, Optional

from prompt_toolkit import prompt
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import FuzzyWordCompleter, PathCompleter, WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.validation import ValidationError, Validator

# ============================================================================
# Custom Validators
# ============================================================================


class PathValidator(Validator):
    """Validator for file system paths."""

    def __init__(self, must_exist: bool = True, must_be_dir: bool = True):
        """Initialize path validator.

        Args:
            must_exist: Whether path must exist
            must_be_dir: Whether path must be a directory
        """
        self.must_exist = must_exist
        self.must_be_dir = must_be_dir

    def validate(self, document):
        """Validate the path."""
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Path cannot be empty")

        path = Path(text).expanduser()

        if self.must_exist and not path.exists():
            raise ValidationError(message=f"Path does not exist: {path}")

        if self.must_be_dir and path.exists() and not path.is_dir():
            raise ValidationError(message=f"Path must be a directory: {path}")


class GithubOrgValidator(Validator):
    """Validator for GitHub organization names."""

    def validate(self, document):
        """Validate GitHub organization name."""
        text = document.text.strip()
        if not text:
            return  # Optional field

        # GitHub org names can contain alphanumeric and hyphens
        if not all(c.isalnum() or c == "-" for c in text):
            raise ValidationError(message="Organization name can only contain letters, numbers, and hyphens")

        if text.startswith("-") or text.endswith("-"):
            raise ValidationError(message="Organization name cannot start or end with a hyphen")


class NumericChoiceValidator(Validator):
    """Validator for numeric menu choices."""

    def __init__(self, max_choice: int, min_choice: int = 1, allow_empty: bool = False):
        """Initialize numeric choice validator.

        Args:
            max_choice: Maximum valid choice number
            min_choice: Minimum valid choice number
            allow_empty: Whether empty input is allowed
        """
        self.max_choice = max_choice
        self.min_choice = min_choice
        self.allow_empty = allow_empty

    def validate(self, document):
        """Validate numeric choice."""
        text = document.text.strip()

        if not text:
            if self.allow_empty:
                return
            raise ValidationError(message="Please enter a number")

        try:
            choice = int(text)
            if choice < self.min_choice or choice > self.max_choice:
                raise ValidationError(message=f"Enter a number between {self.min_choice} and {self.max_choice}")
        except ValueError:
            raise ValidationError(message="Please enter a valid number") from None


class TemplateValidator(Validator):
    """Validator for template names."""

    VALID_TEMPLATES = ["default", "minimal", "journal", "preprint"]

    def validate(self, document):
        """Validate template name."""
        text = document.text.strip().lower()
        if text and text not in self.VALID_TEMPLATES:
            raise ValidationError(message=f"Invalid template. Choose from: {', '.join(self.VALID_TEMPLATES)}")


class RepositoryNameValidator(Validator):
    """Validator for repository names."""

    def __init__(self, existing_names: Optional[List[str]] = None):
        """Initialize repository name validator.

        Args:
            existing_names: List of existing repository names to check for duplicates
        """
        self.existing_names = existing_names or []

    def validate(self, document):
        """Validate repository name."""
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Repository name cannot be empty")

        # Check for invalid characters
        if not all(c.isalnum() or c in "-_" for c in text):
            raise ValidationError(message="Repository name can only contain letters, numbers, hyphens, and underscores")

        # Check for spaces
        if " " in text:
            raise ValidationError(message="Repository name cannot contain spaces")

        # Check for duplicates
        if text in self.existing_names:
            raise ValidationError(message=f"Repository 'manuscript-{text}' already exists")


# ============================================================================
# Prompt Functions
# ============================================================================


def prompt_path(
    prompt_text: str = "Directory path: ",
    default: Optional[str] = None,
    must_exist: bool = True,
    must_be_dir: bool = True,
    show_expanded: bool = True,
) -> Path:
    """Prompt for a file system path with validation and completion.

    Args:
        prompt_text: Text to display in prompt
        default: Default value
        must_exist: Whether path must exist
        must_be_dir: Whether path must be a directory
        show_expanded: Show expanded path in bottom toolbar

    Returns:
        Path object
    """
    validator = PathValidator(must_exist=must_exist, must_be_dir=must_be_dir)
    completer = PathCompleter(expanduser=True)

    def get_toolbar():
        if show_expanded:
            app = get_app()
            current_text = app.current_buffer.text.strip()
            if current_text:
                expanded = Path(current_text).expanduser().resolve()
                return HTML(f"Expanded: <b>{expanded}</b>")
        return None

    result = prompt(
        prompt_text,
        completer=completer,
        complete_while_typing=True,
        validator=validator,
        default=default or "",
        bottom_toolbar=get_toolbar if show_expanded else None,
    )

    return Path(result.strip()).expanduser().resolve()


def prompt_github_org(
    prompt_text: str = "GitHub organization: ",
    default: Optional[str] = None,
    existing_orgs: Optional[List[str]] = None,
) -> Optional[str]:
    """Prompt for GitHub organization with completion and validation.

    Args:
        prompt_text: Text to display in prompt
        default: Default value
        existing_orgs: List of existing organizations for completion

    Returns:
        Organization name or None if empty
    """
    validator = GithubOrgValidator()
    completer = FuzzyWordCompleter(existing_orgs) if existing_orgs else None

    result = prompt(
        prompt_text,
        completer=completer,
        complete_while_typing=True if completer else False,
        validator=validator,
        default=default or "",
    )

    result = result.strip()
    return result if result else None


def prompt_editor(
    prompt_text: str = "Default editor: ",
    default: Optional[str] = None,
) -> Optional[str]:
    """Prompt for editor with common choices.

    Args:
        prompt_text: Text to display in prompt
        default: Default value

    Returns:
        Editor command or None if empty
    """
    common_editors = ["code", "vim", "nvim", "nano", "emacs", "subl", "atom"]
    completer = WordCompleter(common_editors, ignore_case=True)

    result = prompt(
        prompt_text,
        completer=completer,
        complete_while_typing=True,
        default=default or "",
    )

    result = result.strip()
    return result if result else None


def prompt_template_choice(
    prompt_text: str = "Template: ",
    default: str = "default",
) -> str:
    """Prompt for template type with validation.

    Args:
        prompt_text: Text to display in prompt
        default: Default template

    Returns:
        Template name
    """
    templates = TemplateValidator.VALID_TEMPLATES
    completer = WordCompleter(templates, ignore_case=True)
    validator = TemplateValidator()

    result = prompt(
        prompt_text,
        completer=completer,
        complete_while_typing=True,
        validator=validator,
        default=default,
    )

    return result.strip().lower()


def prompt_numbered_choice(
    items: List[str],
    prompt_text: str = "Enter choice: ",
    default: Optional[int] = None,
    allow_empty: bool = False,
) -> Optional[int]:
    """Prompt for a choice from a numbered list.

    Args:
        items: List of items to choose from
        prompt_text: Text to display in prompt
        default: Default choice number (1-indexed)
        allow_empty: Whether empty input is allowed

    Returns:
        Chosen index (0-indexed) or None if empty and allowed
    """
    # Display numbered list
    for idx, item in enumerate(items, start=1):
        marker = " (default)" if idx == default else ""
        print(f"  {idx}. {item}{marker}")

    # Create validator
    validator = NumericChoiceValidator(
        max_choice=len(items),
        min_choice=1,
        allow_empty=allow_empty,
    )

    # Create completer for valid choices
    choices = [str(i) for i in range(1, len(items) + 1)]
    completer = WordCompleter(choices)

    # Get choice
    default_str = str(default) if default else ""

    result = prompt(
        prompt_text,
        completer=completer,
        validator=validator,
        default=default_str,
    )

    result = result.strip()
    if not result and allow_empty:
        return None

    return int(result) - 1  # Convert to 0-indexed


def prompt_yes_no(
    question: str,
    default: bool = True,
) -> bool:
    """Prompt for yes/no confirmation.

    Args:
        question: Question to ask
        default: Default answer

    Returns:
        True for yes, False for no
    """
    return confirm(question, default=default)


def prompt_config_key(
    available_keys: List[str],
    prompt_text: str = "Configuration key: ",
) -> str:
    """Prompt for a configuration key with completion.

    Args:
        available_keys: List of valid configuration keys
        prompt_text: Text to display in prompt

    Returns:
        Configuration key
    """
    completer = FuzzyWordCompleter(available_keys)

    result = prompt(
        prompt_text,
        completer=completer,
        complete_while_typing=True,
    )

    return result.strip()


def prompt_repository_name(
    prompt_text: str = "Repository name: ",
    existing_names: Optional[List[str]] = None,
    show_prefix: bool = True,
) -> str:
    """Prompt for repository name with validation.

    Args:
        prompt_text: Text to display in prompt
        existing_names: List of existing repository names
        show_prefix: Show manuscript- prefix in toolbar

    Returns:
        Repository name (without manuscript- prefix)
    """
    validator = RepositoryNameValidator(existing_names=existing_names)

    def get_toolbar():
        if show_prefix:
            app = get_app()
            current_text = app.current_buffer.text.strip()
            if current_text:
                return HTML(f"Will create: <b>manuscript-{current_text}</b>")
            else:
                return HTML("Repository names are automatically prefixed with <b>manuscript-</b>")
        return None

    result = prompt(
        prompt_text,
        validator=validator,
        bottom_toolbar=get_toolbar if show_prefix else None,
    )

    return result.strip()
