"""Unicode-safe console output utilities for rxiv-maker.

This module provides cross-platform safe console output functions that handle
Unicode encoding issues on Windows and other systems with limited Unicode support.
"""

import os
import sys

try:
    from rich.console import Console
except ImportError:
    Console = None  # type: ignore[assignment,misc]


def supports_unicode() -> bool:
    """Check if the current environment supports Unicode characters.

    Returns:
        bool: True if Unicode is supported, False otherwise
    """
    # Check for explicit environment variables first
    if os.environ.get("PYTHONIOENCODING", "").lower().startswith("utf"):
        return True
    if os.environ.get("PYTHONUTF8") == "1":
        return True

    # Check if we're on Windows with legacy console
    if os.name == "nt":
        try:
            # Try to encode a test emoji - use checkmark specifically since that's what fails
            test_chars = ["✅", "📦", "❌"]
            stdout_encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"

            # If encoding is cp1252 or similar, assume no Unicode support
            if stdout_encoding.lower() in ("cp1252", "cp1251", "cp1250", "ascii"):
                return False

            for char in test_chars:
                char.encode(stdout_encoding)
            return True
        except (UnicodeEncodeError, LookupError, AttributeError):
            return False

    # For non-Windows systems, assume Unicode support
    return True


def get_safe_icon(emoji: str, fallback: str) -> str:
    """Get a safe icon that works across different terminals.

    Args:
        emoji: Unicode emoji to use if supported
        fallback: ASCII fallback if Unicode is not supported

    Returns:
        str: The appropriate icon for the current environment
    """
    return emoji if supports_unicode() else fallback


def convert_to_ascii(message: str) -> str:
    """Convert Unicode emoji and symbols to ASCII equivalents.

    Args:
        message: The message to convert

    Returns:
        ASCII-safe version of the message
    """
    # Comprehensive emoji/symbol replacements
    replacements = {
        # Status indicators
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "ℹ️": "[INFO]",
        "🔍": "[SEARCH]",
        "🔧": "[CONFIG]",
        "💡": "[IDEA]",
        "📊": "[STATS]",
        "📋": "[LIST]",
        # Objects and tools
        "📦": "[PACKAGE]",
        "📁": "[FOLDER]",
        "📄": "[PDF]",
        "📝": "[NOTE]",
        "📚": "[LIBRARY]",
        "🖼️": "[IMAGE]",
        "🎨": "[ART]",
        "🐍": "[PYTHON]",
        "🐳": "[DOCKER]",
        # Actions and processes
        "🚀": "[LAUNCH]",
        "🔄": "[RELOAD]",
        "🧹": "[CLEAN]",
        "🎯": "[TARGET]",
        "🎉": "[SUCCESS]",
        "💾": "[SAVE]",
        # Arrows and directions
        "→": "->",
        "←": "<-",
        "↑": "^",
        "↓": "v",
        # Control symbols
        "⏹️": "[STOP]",
        "⏯️": "[PAUSE]",
        "⏭️": "[SKIP]",
        # Braille spinner characters (used in progress indicators)
        "⠋": "|",
        "⠙": "/",
        "⠹": "-",
        "⠸": "\\",
        "⠼": "|",
        "⠴": "/",
        "⠦": "-",
        "⠧": "\\",
        "⠇": "|",
        "⠏": "/",
    }

    # Apply replacements
    result = message
    for emoji, replacement in replacements.items():
        result = result.replace(emoji, replacement)

    return result


def safe_print(message: str, **kwargs) -> None:
    """Print a message with Unicode safety fallbacks.

    Args:
        message: The message to print
        **kwargs: Additional arguments to pass to print()
    """
    try:
        print(message, **kwargs)
    except UnicodeEncodeError:
        # Try with ASCII conversion
        ascii_message = convert_to_ascii(message)
        try:
            print(ascii_message, **kwargs)
        except UnicodeEncodeError:
            # Last resort: strip all non-ASCII characters
            safe_message = message.encode("ascii", "ignore").decode("ascii")
            print(safe_message, **kwargs)
    except Exception:
        # Silently ignore any other print issues to prevent crashes
        pass


def safe_console_print(console, message: str, style: str | None = None, **kwargs) -> None:
    """Print a message using Rich console with cross-platform Unicode fallback.

    Args:
        console: Rich console instance
        message: The message to print
        style: Rich style to apply
        **kwargs: Additional arguments to pass to console.print
    """
    if console is None:
        # Fallback to safe_print if Rich not available
        safe_print(message, **kwargs)
        return

    try:
        console.print(message, style=style, **kwargs)
    except UnicodeEncodeError:
        # Try with ASCII conversion
        ascii_message = convert_to_ascii(message)
        try:
            console.print(ascii_message, style=style, **kwargs)
        except UnicodeEncodeError:
            # Final fallback to safe_print
            safe_print(ascii_message, **kwargs)
    except Exception:
        # Silently ignore any other display issues to prevent CLI crashes
        pass


# Convenience functions for common status messages
def print_success(message: str) -> None:
    """Print a success message with safe Unicode handling."""
    icon = get_safe_icon("✅", "[OK]")
    safe_print(f"{icon} {message}")


def print_error(message: str) -> None:
    """Print an error message with safe Unicode handling."""
    icon = get_safe_icon("❌", "[ERROR]")
    safe_print(f"{icon} {message}")


def print_warning(message: str) -> None:
    """Print a warning message with safe Unicode handling."""
    icon = get_safe_icon("⚠️", "[WARNING]")
    safe_print(f"{icon} {message}")


def print_info(message: str) -> None:
    """Print an info message with safe Unicode handling."""
    icon = get_safe_icon("ℹ️", "[INFO]")
    safe_print(f"{icon} {message}")


# Rich console versions
def console_success(console, message: str) -> None:
    """Print a success message using Rich console with safe Unicode handling."""
    icon = get_safe_icon("✅", "[OK]")
    safe_console_print(console, f"{icon} {message}", style="green")


def console_error(console, message: str) -> None:
    """Print an error message using Rich console with safe Unicode handling."""
    icon = get_safe_icon("❌", "[ERROR]")
    safe_console_print(console, f"{icon} {message}", style="red")


def console_warning(console, message: str) -> None:
    """Print a warning message using Rich console with safe Unicode handling."""
    icon = get_safe_icon("⚠️", "[WARNING]")
    safe_console_print(console, f"{icon} {message}", style="yellow")


def console_info(console, message: str) -> None:
    """Print an info message using Rich console with safe Unicode handling."""
    icon = get_safe_icon("ℹ️", "[INFO]")
    safe_console_print(console, f"{icon} {message}", style="blue")
