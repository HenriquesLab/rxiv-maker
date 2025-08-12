"""Progress indicators for installation process."""

import sys
import threading
import time

from rxiv_maker.utils.unicode_safe import get_safe_icon


class ProgressIndicator:
    """Progress indicator for installation tasks."""

    def __init__(self, verbose: bool = False):
        """Initialize progress indicator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.current_task: str | None = None
        self.spinner_thread: threading.Thread | None = None
        self.stop_spinner = False
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def start_task(self, task_name: str):
        """Start a new task with progress indication.

        Args:
            task_name: Name of the task
        """
        self.current_task = task_name

        if self.verbose:
            print(f"🔄 {task_name}...")
        else:
            print(f"🔄 {task_name}...", end=" ", flush=True)
            self._start_spinner()

    def complete_task(self, success: bool = True):
        """Complete the current task.

        Args:
            success: Whether the task succeeded
        """
        if self.spinner_thread:
            self._stop_spinner()

        if self.current_task:
            if success:
                if not self.verbose:
                    success_icon = get_safe_icon("✅", "[SUCCESS]")
                    print("\r" + success_icon, self.current_task, "- completed")
                else:
                    success_icon = get_safe_icon("✅", "[SUCCESS]")
                    print(f"{success_icon} {self.current_task} - completed")
            else:
                if not self.verbose:
                    error_icon = get_safe_icon("❌", "[ERROR]")
                    print("\r" + error_icon, self.current_task, "- failed")
                else:
                    error_icon = get_safe_icon("❌", "[ERROR]")
                    print(f"{error_icon} {self.current_task} - failed")

        self.current_task = None

    def update_progress(self, message: str):
        """Update progress with a message.

        Args:
            message: Progress message
        """
        if self.verbose:
            print(f"  {message}")

    def _start_spinner(self):
        """Start the spinner animation."""
        self.stop_spinner = False
        self.spinner_thread = threading.Thread(target=self._spinner_animation)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()

    def _stop_spinner(self):
        """Stop the spinner animation."""
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join()
            self.spinner_thread = None

    def _spinner_animation(self):
        """Run the spinner animation."""
        i = 0
        while not self.stop_spinner:
            sys.stdout.write(f"\r🔄 {self.current_task}... {self.spinner_chars[i]}")
            sys.stdout.flush()
            i = (i + 1) % len(self.spinner_chars)
            time.sleep(0.1)

    def show_progress_bar(self, current: int, total: int, prefix: str = ""):
        """Show a progress bar.

        Args:
            current: Current progress
            total: Total items
            prefix: Prefix text
        """
        if total == 0:
            return

        percentage = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)

        print(
            f"\r{prefix} |{bar}| {percentage:.1f}% ({current}/{total})",
            end="",
            flush=True,
        )

        if current == total:
            print()  # New line when complete
