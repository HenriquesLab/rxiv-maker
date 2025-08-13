"""Base class for platform-specific system dependency installers."""

from abc import ABC, abstractmethod

from ..utils.logging import InstallLogger
from ..utils.progress import ProgressIndicator


class BaseInstaller(ABC):
    """Abstract base class for platform-specific installers."""

    def __init__(self, logger: InstallLogger, progress: ProgressIndicator):
        """Initialize base installer.

        Args:
            logger: Logger instance
            progress: Progress indicator instance
        """
        self.logger = logger
        self.progress = progress

    @abstractmethod
    def install_system_libraries(self) -> bool:
        """Install required system libraries.

        Returns:
            True if installation succeeded, False otherwise
        """
        pass

    @abstractmethod
    def install_latex(self) -> bool:
        """Install LaTeX distribution and packages.

        Returns:
            True if installation succeeded, False otherwise
        """
        pass

    @abstractmethod
    def install_nodejs(self) -> bool:
        """Install Node.js and npm packages.

        Returns:
            True if installation succeeded, False otherwise
        """
        pass

    @abstractmethod
    def install_r(self) -> bool:
        """Install R language and packages.

        Returns:
            True if installation succeeded, False otherwise
        """
        pass

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH.

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        import shutil

        return shutil.which(command) is not None
