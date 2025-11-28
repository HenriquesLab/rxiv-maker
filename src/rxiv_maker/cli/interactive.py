"""Unified interactive prompt system for rxiv-maker CLI.

This module provides a consistent interface for all interactive prompts,
replacing scattered usage of Click and prompt_toolkit throughout the codebase.
"""

import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional

from prompt_toolkit import prompt
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import FuzzyWordCompleter, PathCompleter, WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import checkboxlist_dialog, confirm
from prompt_toolkit.validation import ValidationError, Validator
from rich.console import Console

console = Console()


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
    """Validator for repository names.

    Validates repository names according to GitHub's naming rules:
    - Only alphanumeric characters and hyphens allowed
    - Cannot start or end with a hyphen
    - Cannot contain consecutive hyphens
    - Maximum 39 characters (leaving room for 'manuscript-' prefix)
    """

    def __init__(self, existing_names: Optional[List[str]] = None):
        """Initialize repository name validator.

        Args:
            existing_names: List of existing repository names to check for duplicates
        """
        self.existing_names = existing_names or []

    def validate(self, document):
        """Validate repository name according to GitHub rules."""
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Repository name cannot be empty")

        # Check length (GitHub limits: 1-39 characters, but we add 'manuscript-' prefix)
        if len(text) > 39:
            raise ValidationError(message="Repository name cannot exceed 39 characters")

        # Check for invalid characters (only alphanumeric and hyphens, NO underscores)
        if not all(c.isalnum() or c == "-" for c in text):
            raise ValidationError(
                message="Repository name can only contain letters, numbers, and hyphens (no underscores)"
            )

        # Check doesn't start or end with hyphen
        if text.startswith("-") or text.endswith("-"):
            raise ValidationError(message="Repository name cannot start or end with a hyphen")

        # Check no consecutive hyphens
        if "--" in text:
            raise ValidationError(message="Repository name cannot contain consecutive hyphens")

        # Check for spaces (redundant but explicit)
        if " " in text:
            raise ValidationError(message="Repository name cannot contain spaces")

        # Check for duplicates
        if text in self.existing_names:
            raise ValidationError(message=f"Repository 'manuscript-{text}' already exists")


# ============================================================================
# Standard Prompt Functions
# ============================================================================


def prompt_confirm(question: str, default: bool = True) -> bool:
    """Standard confirmation prompt using prompt_toolkit.

    Args:
        question: Question to ask
        default: Default answer

    Returns:
        True for yes, False for no
    """
    # prompt_toolkit.shortcuts.confirm doesn't support default parameter in all versions
    # Use the more flexible approach
    try:
        return confirm(question, default=default)
    except TypeError:
        # Fallback for older versions that don't support default
        return confirm(question)


def prompt_confirm_with_path_change(
    current_path: Path,
    action_description: str = "Clone repositories",
) -> tuple[bool, Optional[Path]]:
    """Confirm action with option to change target path.

    This function presents a 3-option menu allowing the user to:
    1. Proceed with the current path
    2. Change the path (with validation and directory creation)
    3. Cancel the operation

    When changing the path, the function:
    - Prompts for a new path with validation
    - Offers to create the directory if it doesn't exist
    - Validates write permissions
    - Loops back to the menu if there are errors

    Args:
        current_path: Current target path
        action_description: Description of action (e.g., "Clone repositories")

    Returns:
        Tuple of (should_proceed, final_path):
        - (True, Path): User confirmed with final path
        - (False, None): User cancelled

    Example:
        >>> proceed, path = prompt_confirm_with_path_change(
        ...     Path("~/manuscripts"),
        ...     "Clone repositories"
        ... )
        >>> if proceed:
        ...     # Use path for cloning
        ...     pass
    """
    while True:
        # Display current path
        console.print(f"\nTarget directory: [bold cyan]{current_path}[/bold cyan]\n")

        # Create 3-option menu
        choices = [
            f"Yes, {action_description.lower()} to this path",
            "Change path",
            "Cancel",
        ]

        try:
            choice = prompt_choice(choices, prompt_text="Select option: ", default=1)
        except KeyboardInterrupt:
            # Allow Ctrl+C to cancel
            console.print("\n[yellow]Cancelled[/yellow]")
            return (False, None)

        if choice == 0:  # Yes, proceed
            return (True, current_path)

        elif choice == 1:  # Change path
            try:
                # Prompt for new path
                new_path = prompt_path(
                    "New target directory: ",
                    default=str(current_path),
                    must_exist=False,  # Allow non-existent paths
                    must_be_dir=True,
                )

                # Create directory if it doesn't exist
                if not new_path.exists():
                    if prompt_confirm("Directory does not exist. Create it?", default=True):
                        try:
                            new_path.mkdir(parents=True, exist_ok=True)
                            console.print(f"[green]✓[/green] Created directory: {new_path}")
                        except PermissionError:
                            console.print(f"[red]Error: Permission denied creating {new_path}[/red]")
                            continue  # Loop back to options
                        except Exception as e:
                            console.print(f"[red]Error creating directory: {e}[/red]")
                            continue  # Loop back to options
                    else:
                        # User declined to create, loop back
                        continue

                # Validate write permissions
                if not os.access(new_path, os.W_OK):
                    console.print(f"[red]Error: No write permission for {new_path}[/red]")
                    continue  # Loop back to options

                # Success - update current path and show confirmation
                current_path = new_path
                console.print(f"[green]✓ Path changed to: {current_path}[/green]\n")
                # Loop back to show updated path in menu

            except KeyboardInterrupt:
                # Allow Ctrl+C during path input to go back to menu
                console.print("\n")
                continue

        elif choice == 2:  # Cancel
            return (False, None)


def prompt_text(
    message: str,
    default: str = "",
    validator: Optional[Validator] = None,
    completer: Optional[Any] = None,
    multiline: bool = False,
) -> str:
    """Standard text prompt with optional validation and completion.

    Args:
        message: Text to display in prompt
        default: Default value
        validator: Optional validator
        completer: Optional completer
        multiline: Whether to allow multiline input

    Returns:
        User input string
    """
    return prompt(
        message,
        default=default,
        validator=validator,
        completer=completer,
        complete_while_typing=bool(completer),
        multiline=multiline,
    ).strip()


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


def prompt_choice(
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
        console.print(f"  {idx}. {item}{marker}")

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


def prompt_multi_select(
    title: str,
    items: List[tuple],
    default_values: Optional[List] = None,
) -> List:
    """Prompt for multiple selections from a list using checkboxes.

    Args:
        title: Dialog title
        items: List of (value, label) tuples
        default_values: List of default selected values

    Returns:
        List of selected values
    """
    return checkboxlist_dialog(
        title=title,
        text="Use arrow keys to navigate, space to select, enter to confirm:",
        values=items,
        default_values=default_values or [],
    ).run()


def prompt_select_from_list(
    title: str,
    items: List[str],
    multiselect: bool = False,
) -> Optional[List[int]]:
    """Prompt for selection from a list with visual interface.

    Args:
        title: Dialog title
        items: List of items to select from
        multiselect: Whether to allow multiple selections

    Returns:
        List of selected indices (0-indexed) or None if cancelled
    """
    if multiselect:
        values = [(i, item) for i, item in enumerate(items)]
        selected = prompt_multi_select(title, values)
        return selected if selected else None
    else:
        console.print(f"\n[bold]{title}[/bold]\n")
        choice = prompt_choice(items)
        return [choice] if choice is not None else None


# ============================================================================
# Decorators
# ============================================================================


def interactive_mode(default: bool = False):
    """Decorator to add --interactive flag to a command.

    Args:
        default: Whether interactive mode is on by default
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if interactive flag is in kwargs
            is_interactive = kwargs.get("interactive", default)
            kwargs["interactive"] = is_interactive
            return func(*args, **kwargs)

        return wrapper

    return decorator


def confirm_action(message: str, default: bool = False):
    """Decorator to confirm an action before executing.

    Args:
        message: Confirmation message
        default: Default answer
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if prompt_confirm(message, default=default):
                return func(*args, **kwargs)
            else:
                console.print("[yellow]Action cancelled[/yellow]")
                return None

        return wrapper

    return decorator


# ============================================================================
# Export Compatibility with Old Module
# ============================================================================

# For backward compatibility with existing imports
prompt_yes_no = prompt_confirm
prompt_numbered_choice = prompt_choice


def prompt_editor(message="Default editor: ", default=None):
    """Prompt for editor selection with autocompletion."""
    return prompt(
        message,
        default=default or "",
        completer=WordCompleter(["code", "vim", "nvim", "nano", "emacs", "subl", "atom"], ignore_case=True),
    )


def prompt_template_choice(message="Template: ", default="default"):
    """Prompt for template selection with validation and autocompletion."""
    return prompt(
        message,
        default=default,
        validator=TemplateValidator(),
        completer=WordCompleter(TemplateValidator.VALID_TEMPLATES, ignore_case=True),
    )


def prompt_repository_name(message="Repository name: ", existing_names=None, show_prefix=True):
    """Prompt for repository name with validation."""
    return prompt(message, validator=RepositoryNameValidator(existing_names=existing_names))


def prompt_config_key(available_keys, message="Configuration key: "):
    """Prompt for configuration key with fuzzy autocompletion."""
    return prompt(message, completer=FuzzyWordCompleter(available_keys))
