"""Custom exceptions for container engine operations."""

import platform
from typing import Optional


class ContainerEngineError(Exception):
    """Base exception for container engine errors."""

    def __init__(self, message: str, engine_type: str, suggestion: Optional[str] = None):
        """Initialize container engine error.

        Args:
            message: Error message
            engine_type: Type of engine (docker, podman)
            suggestion: Optional suggestion for fixing the issue
        """
        self.engine_type = engine_type
        self.suggestion = suggestion

        full_message = f"{engine_type.title()} Error: {message}"
        if suggestion:
            full_message += f"\n💡 Suggestion: {suggestion}"

        super().__init__(full_message)


class ContainerEngineNotFoundError(ContainerEngineError):
    """Exception raised when container engine binary is not found."""

    def __init__(self, engine_type: str):
        """Initialize not found error with installation suggestions."""
        system = platform.system().lower()

        if engine_type == "docker":
            if system == "darwin":
                suggestion = (
                    "Install Docker Desktop from https://docker.com/get-started or use 'brew install --cask docker'"
                )
            elif system == "linux":
                suggestion = (
                    "Install Docker using your package manager: "
                    "'sudo apt install docker.io' (Ubuntu/Debian) or "
                    "'sudo yum install docker' (RHEL/CentOS)"
                )
            elif system == "windows":
                suggestion = "Install Docker Desktop from https://docker.com/get-started"
            else:
                suggestion = f"Install Docker for your {system} system"
        else:  # podman
            if system == "darwin":
                suggestion = "Install Podman using 'brew install podman'"
            elif system == "linux":
                suggestion = (
                    "Install Podman using your package manager: "
                    "'sudo apt install podman' (Ubuntu/Debian) or "
                    "'sudo yum install podman' (RHEL/CentOS)"
                )
            elif system == "windows":
                suggestion = "Install Podman Desktop from https://podman-desktop.io"
            else:
                suggestion = f"Install Podman for your {system} system"

        super().__init__(f"{engine_type.title()} is not installed or not found in PATH", engine_type, suggestion)


class ContainerEngineNotRunningError(ContainerEngineError):
    """Exception raised when container engine daemon is not running."""

    def __init__(self, engine_type: str):
        """Initialize not running error with startup suggestions."""
        system = platform.system().lower()

        if engine_type == "docker":
            if system == "darwin":
                suggestion = "Start Docker Desktop application or run 'open -a Docker' in Terminal"
            elif system == "linux":
                suggestion = "Start Docker daemon: 'sudo systemctl start docker' or 'sudo service docker start'"
            elif system == "windows":
                suggestion = "Start Docker Desktop application"
            else:
                suggestion = f"Start Docker daemon on your {system} system"
        else:  # podman
            if system == "darwin":
                suggestion = (
                    "Start Podman machine: 'podman machine start' or initialize first with 'podman machine init'"
                )
            elif system == "linux":
                suggestion = (
                    "Start Podman service: 'sudo systemctl start podman' or "
                    "run 'podman system service' for rootless mode"
                )
            elif system == "windows":
                suggestion = "Start Podman machine: 'podman machine start'"
            else:
                suggestion = f"Start Podman service on your {system} system"

        super().__init__(f"{engine_type.title()} daemon is not running", engine_type, suggestion)


class ContainerImagePullError(ContainerEngineError):
    """Exception raised when container image pull fails."""

    def __init__(self, engine_type: str, image: str, details: Optional[str] = None):
        """Initialize image pull error.

        Args:
            engine_type: Type of engine (docker, podman)
            image: Image name that failed to pull
            details: Optional error details from the engine
        """
        message = f"Failed to pull image '{image}'"
        if details:
            message += f": {details}"

        suggestion = (
            f"Check your internet connection and verify the image name is correct. "
            f"Try running '{engine_type} pull {image}' manually to see detailed error."
        )

        super().__init__(message, engine_type, suggestion)


class ContainerPermissionError(ContainerEngineError):
    """Exception raised when container operations fail due to permissions."""

    def __init__(self, engine_type: str, operation: str):
        """Initialize permission error.

        Args:
            engine_type: Type of engine (docker, podman)
            operation: Operation that failed (e.g., 'run container', 'pull image')
        """
        system = platform.system().lower()

        if engine_type == "docker" and system == "linux":
            suggestion = (
                "Add your user to the docker group: 'sudo usermod -aG docker $USER' "
                "then log out and back in, or run with sudo"
            )
        elif engine_type == "podman":
            suggestion = (
                "Try running in rootless mode or check Podman permissions. "
                "You may need to configure subuid/subgid mappings"
            )
        else:
            suggestion = f"Check {engine_type} permissions and try running with elevated privileges"

        super().__init__(f"Permission denied while trying to {operation}", engine_type, suggestion)


class ContainerSessionError(ContainerEngineError):
    """Exception raised when container session operations fail."""

    def __init__(
        self, engine_type: str, operation: str, container_id: Optional[str] = None, details: Optional[str] = None
    ):
        """Initialize session error.

        Args:
            engine_type: Type of engine (docker, podman)
            operation: Operation that failed (e.g., 'start', 'stop', 'exec')
            container_id: Optional container ID
            details: Optional error details
        """
        message = f"Container session {operation} failed"
        if container_id:
            message += f" for container {container_id[:12]}"
        if details:
            message += f": {details}"

        container_ref = container_id[:12] if container_id else "<container>"
        suggestion = (
            f"Check container logs: '{engine_type} logs {container_ref}' "
            f"or inspect container: '{engine_type} inspect {container_ref}'"
        )

        super().__init__(message, engine_type, suggestion)


class ContainerTimeoutError(ContainerEngineError):
    """Exception raised when container operations timeout."""

    def __init__(self, engine_type: str, operation: str, timeout_seconds: int):
        """Initialize timeout error.

        Args:
            engine_type: Type of engine (docker, podman)
            operation: Operation that timed out
            timeout_seconds: Timeout value in seconds
        """
        message = f"Container {operation} timed out after {timeout_seconds} seconds"

        suggestion = (
            "The operation is taking longer than expected. This might be due to "
            "slow network, large image downloads, or system resource constraints. "
            "Try increasing timeout or check system resources."
        )

        super().__init__(message, engine_type, suggestion)
