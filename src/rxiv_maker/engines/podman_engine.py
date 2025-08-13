"""Podman container engine implementation."""

import logging
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from .abstract import AbstractContainerEngine, ContainerSession
from .exceptions import (
    ContainerEngineNotFoundError,
    ContainerEngineNotRunningError,
    ContainerImagePullError,
    ContainerPermissionError,
    ContainerTimeoutError,
)

logger = logging.getLogger(__name__)


class PodmanSession(ContainerSession):
    """Podman-specific container session implementation."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        super().__init__(container_id, image, workspace_dir, "podman")
        self.created_at = time.time()

    # Note: is_active() and cleanup() methods are now inherited from ContainerSession base class


class PodmanEngine(AbstractContainerEngine):
    """Podman container engine implementation.

    Podman has a Docker-compatible API but needs its own engine implementation
    to handle rootless containers and other Podman-specific behavior.
    """

    @property
    def engine_name(self) -> str:
        """Return the name of the container engine."""
        return "podman"

    def check_available(self) -> bool:
        """Check if Podman is available and service is running.

        Returns:
            True if Podman is available and running, False otherwise.

        Raises:
            ContainerEngineNotFoundError: If Podman binary is not found
            ContainerEngineNotRunningError: If Podman service is not running
            ContainerPermissionError: If permission denied accessing Podman
            ContainerTimeoutError: If Podman commands timeout
        """
        try:
            # First check if podman binary exists
            version_result = subprocess.run(["podman", "--version"], capture_output=True, text=True, timeout=5)

            if version_result.returncode != 0:
                if "permission denied" in version_result.stderr.lower():
                    raise ContainerPermissionError("podman", "check Podman version")
                else:
                    logger.debug(f"Podman version check failed: {version_result.stderr}")
                    return False

        except FileNotFoundError as e:
            raise ContainerEngineNotFoundError("podman") from e
        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError("podman", "version check", 5) from e

        try:
            # Then check if Podman service is actually running
            ps_result = subprocess.run(["podman", "ps"], capture_output=True, text=True, timeout=10)

            if ps_result.returncode != 0:
                stderr_lower = ps_result.stderr.lower()
                if "permission denied" in stderr_lower or "access denied" in stderr_lower:
                    raise ContainerPermissionError("podman", "list containers")
                elif "cannot connect" in stderr_lower or "connection refused" in stderr_lower:
                    raise ContainerEngineNotRunningError("podman")
                elif "service" in stderr_lower and "not running" in stderr_lower:
                    raise ContainerEngineNotRunningError("podman")
                elif "machine" in stderr_lower and ("not running" in stderr_lower or "stopped" in stderr_lower):
                    raise ContainerEngineNotRunningError("podman")
                else:
                    logger.debug(f"Podman ps failed: {ps_result.stderr}")
                    return False

            return True

        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError("podman", "service connectivity check", 10) from e
        except subprocess.CalledProcessError as e:
            logger.debug(f"Podman ps command failed with exit code {e.returncode}")
            return False

    def pull_image(self, image: Optional[str] = None, force_pull: bool = False) -> bool:
        """Pull the Podman image if not already available or force_pull is True.

        Args:
            image: Image name to pull (defaults to default_image)
            force_pull: Force pull even if image exists locally

        Returns:
            True if image is available after operation, False otherwise

        Raises:
            ContainerImagePullError: If image pull fails with details
            ContainerTimeoutError: If pull operation times out
            ContainerPermissionError: If permission denied during pull
        """
        target_image = image or self.default_image

        # If force_pull is False, check if image is already available locally
        if not force_pull:
            try:
                result = subprocess.run(
                    ["podman", "image", "inspect", target_image],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.debug(f"Podman image {target_image} already available locally")
                    return True  # Image already available locally
            except subprocess.TimeoutExpired:
                logger.debug(f"Timeout checking local image {target_image}, proceeding with pull")
            except subprocess.CalledProcessError:
                logger.debug(f"Image {target_image} not available locally, proceeding with pull")

        # Pull the latest version of the image
        logger.info(f"Pulling Podman image: {target_image}")
        try:
            result = subprocess.run(
                ["podman", "pull", target_image],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.returncode == 0:
                logger.info(f"Successfully pulled Podman image: {target_image}")
                return True
            else:
                # Analyze the error to provide helpful feedback
                stderr_lower = result.stderr.lower()
                if "permission denied" in stderr_lower:
                    raise ContainerPermissionError("podman", f"pull image {target_image}")
                elif "not found" in stderr_lower or "no such image" in stderr_lower:
                    raise ContainerImagePullError("podman", target_image, "Image not found in registry")
                elif "network" in stderr_lower or "connection" in stderr_lower:
                    raise ContainerImagePullError("podman", target_image, "Network connectivity issue")
                elif "unauthorized" in stderr_lower or "authentication" in stderr_lower:
                    raise ContainerImagePullError("podman", target_image, "Authentication required for private image")
                else:
                    raise ContainerImagePullError("podman", target_image, result.stderr.strip())

        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError("podman", f"pull image {target_image}", 300) from e
        except subprocess.CalledProcessError as e:
            logger.debug(f"Podman pull failed with exit code {e.returncode}")
            raise ContainerImagePullError(
                "podman", target_image, f"Command failed with exit code {e.returncode}"
            ) from e

    def _build_container_command(
        self,
        command: str | List[str],
        image: Optional[str] = None,
        working_dir: str = "/workspace",
        volumes: Optional[List[str]] = None,
        environment: Optional[dict[str, str]] = None,
        user: Optional[str] = None,
        interactive: bool = False,
        remove: bool = True,
        detach: bool = False,
    ) -> List[str]:
        """Build a Podman run command with optimal settings."""
        podman_cmd = ["podman", "run"]

        # Container options
        if remove and not detach:
            podman_cmd.append("--rm")

        if detach:
            podman_cmd.append("-d")

        if interactive:
            podman_cmd.extend(["-i", "-t"])

        # Platform specification
        podman_cmd.extend(["--platform", self._platform])

        # Resource limits
        podman_cmd.extend(["--memory", self.memory_limit])
        podman_cmd.extend(["--cpus", self.cpu_limit])

        # Volume mounts
        all_volumes = self._base_volumes.copy()
        if volumes:
            all_volumes.extend(volumes)

        for volume in all_volumes:
            podman_cmd.extend(["-v", volume])

        # Working directory
        podman_cmd.extend(["-w", working_dir])

        # Environment variables
        all_env = self._base_env.copy()
        if environment:
            all_env.update(environment)

        for key, value in all_env.items():
            podman_cmd.extend(["-e", f"{key}={value}"])

        # User specification (Podman handles rootless containers differently)
        if user:
            podman_cmd.extend(["--user", user])

        # Image
        podman_cmd.append(image or self.default_image)

        # Command
        if isinstance(command, str):
            podman_cmd.extend(["sh", "-c", command])
        else:
            podman_cmd.extend(command)

        return podman_cmd

    def _get_or_create_session(self, session_key: str, image: str) -> Optional["PodmanSession"]:
        """Get an existing session or create a new one if session reuse is enabled."""
        if not self.enable_session_reuse:
            return None

        # Clean up expired sessions
        self._cleanup_expired_sessions()

        # Check if we have an active session
        if session_key in self._active_sessions:
            session = self._active_sessions[session_key]
            if session.is_active():
                return session  # type: ignore[return-value]
            else:
                # Session is dead, remove it
                del self._active_sessions[session_key]

        # Create new session
        try:
            podman_cmd = self._build_container_command(
                command=["sleep", "infinity"],  # Keep container alive
                image=image,
                detach=True,
                remove=False,
            )

            result = subprocess.run(podman_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                container_id = result.stdout.strip()
                session = PodmanSession(container_id, image, self.workspace_dir)

                # Initialize container with health checks
                if self._initialize_container(session):
                    self._active_sessions[session_key] = session
                    logger.debug(f"Created new Podman session: {container_id[:12]}")
                    return session
                else:
                    # Cleanup failed session
                    logger.debug(f"Failed to initialize Podman session {container_id[:12]}, cleaning up")
                    session.cleanup()
            else:
                # Log session creation failure details
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.debug(f"Failed to create Podman session for {session_key}: {error_msg}")

        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout creating Podman session for {session_key}")
        except subprocess.CalledProcessError as e:
            logger.debug(f"Command failed creating Podman session for {session_key}: exit code {e.returncode}")
        except Exception as e:
            logger.debug(f"Unexpected error creating Podman session for {session_key}: {e}")

        return None

    # Note: _initialize_container() method is now inherited from AbstractContainerEngine base class

    def run_command(
        self,
        command: str | List[str],
        image: Optional[str] = None,
        working_dir: str = "/workspace",
        volumes: Optional[List[str]] = None,
        environment: Optional[dict[str, str]] = None,
        session_key: Optional[str] = None,
        capture_output: bool = True,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """Execute a command in a Podman container with optimization."""
        target_image = image or self.default_image

        # Try to use existing session if session_key provided
        session = None
        if session_key:
            session = self._get_or_create_session(session_key, target_image)

        if session and session.is_active():
            # Execute in existing container
            if isinstance(command, str):
                exec_cmd = [
                    "podman",
                    "exec",
                    "-w",
                    working_dir,
                    session.container_id,
                    "sh",
                    "-c",
                    command,
                ]
            else:
                exec_cmd = [
                    "podman",
                    "exec",
                    "-w",
                    working_dir,
                    session.container_id,
                ] + command
        else:
            # Create new container for this command
            exec_cmd = self._build_container_command(
                command=command,
                image=target_image,
                working_dir=working_dir,
                volumes=volumes,
                environment=environment,
            )

        # Execute the command with enhanced error handling
        try:
            result = subprocess.run(
                exec_cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                **kwargs,
            )

            # If we used a session and the command failed, check if the session is still active
            if session and result.returncode != 0:
                if not session.is_active():
                    logger.debug(f"Podman session {session.container_id[:12]} died during command execution")
                    # Remove the dead session from our tracking
                    if session_key in self._active_sessions:
                        del self._active_sessions[session_key]

            return result

        except subprocess.TimeoutExpired as e:
            # If using a session, check if it's still alive after timeout
            if session:
                if not session.is_active():
                    logger.debug(f"Podman session {session.container_id[:12]} died during timeout")
                    if session_key in self._active_sessions:
                        del self._active_sessions[session_key]
            raise e
        except Exception as e:
            # Log unexpected errors for debugging
            cmd_preview = " ".join(exec_cmd[:5]) + ("..." if len(exec_cmd) > 5 else "")
            logger.debug(f"Unexpected error executing Podman command '{cmd_preview}': {e}")
            raise e

    def _cleanup_expired_sessions(self, force: bool = False) -> None:
        """Clean up expired or inactive Podman sessions."""
        current_time = time.time()

        # Only run cleanup every 30 seconds unless forced
        if not force and current_time - self._last_cleanup < 30:
            return

        self._last_cleanup = current_time
        expired_keys = []

        for key, session in self._active_sessions.items():
            session_age = current_time - (session.created_at or 0.0)
            if session_age > self._session_timeout or not session.is_active():
                session.cleanup()
                expired_keys.append(key)

        for key in expired_keys:
            del self._active_sessions[key]

        # If we have too many sessions, cleanup the oldest ones
        if len(self._active_sessions) > self._max_sessions:
            sorted_sessions = sorted(self._active_sessions.items(), key=lambda x: x[1].created_at or 0.0)
            excess_count = len(self._active_sessions) - self._max_sessions
            for key, session in sorted_sessions[:excess_count]:
                session.cleanup()
                del self._active_sessions[key]
