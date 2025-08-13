"""Docker container engine implementation."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

from .abstract import AbstractContainerEngine, ContainerSession
from .exceptions import (
    ContainerEngineNotFoundError,
    ContainerEngineNotRunningError,
    ContainerImagePullError,
    ContainerPermissionError,
    ContainerTimeoutError,
)

logger = logging.getLogger(__name__)


class DockerSession(ContainerSession):
    """Docker-specific container session implementation."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        super().__init__(container_id, image, workspace_dir, "docker")
        self.created_at = time.time()

    def is_active(self) -> bool:
        """Check if the Docker container is still running."""
        if not self._active:
            return False

        try:
            result = subprocess.run(
                [
                    "docker",
                    "container",
                    "inspect",
                    self.container_id,
                    "--format",
                    "{{.State.Running}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                is_running = result.stdout.strip().lower() == "true"
                if not is_running:
                    self._active = False
                return is_running
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self._active = False

        return False

    def cleanup(self) -> bool:
        """Stop and remove the Docker container."""
        if not self._active:
            return True

        try:
            # Stop the container
            subprocess.run(["docker", "stop", self.container_id], capture_output=True, timeout=10)

            # Remove the container
            subprocess.run(["docker", "rm", self.container_id], capture_output=True, timeout=10)

            self._active = False
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False


class DockerEngine(AbstractContainerEngine):
    """Docker container engine implementation."""

    @property
    def engine_name(self) -> str:
        """Return the name of the container engine."""
        return "docker"

    def check_available(self) -> bool:
        """Check if Docker is available and daemon is running.

        Returns:
            True if Docker is available and running, False otherwise.

        Raises:
            ContainerEngineNotFoundError: If Docker binary is not found
            ContainerEngineNotRunningError: If Docker daemon is not running
            ContainerPermissionError: If permission denied accessing Docker
            ContainerTimeoutError: If Docker commands timeout
        """
        try:
            # First check if docker binary exists
            version_result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)

            if version_result.returncode != 0:
                if "permission denied" in version_result.stderr.lower():
                    raise ContainerPermissionError("docker", "check Docker version")
                else:
                    logger.debug(f"Docker version check failed: {version_result.stderr}")
                    return False

        except FileNotFoundError as e:
            raise ContainerEngineNotFoundError("docker") from e
        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError("docker", "version check", 5) from e

        try:
            # Then check if Docker daemon is actually running
            ps_result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=10)

            if ps_result.returncode != 0:
                stderr_lower = ps_result.stderr.lower()
                if "permission denied" in stderr_lower or "access denied" in stderr_lower:
                    raise ContainerPermissionError("docker", "list containers")
                elif "cannot connect" in stderr_lower or "connection refused" in stderr_lower:
                    raise ContainerEngineNotRunningError("docker")
                elif "daemon" in stderr_lower and "not running" in stderr_lower:
                    raise ContainerEngineNotRunningError("docker")
                else:
                    logger.debug(f"Docker ps failed: {ps_result.stderr}")
                    return False

            return True

        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError("docker", "daemon connectivity check", 10) from e
        except subprocess.CalledProcessError as e:
            logger.debug(f"Docker ps command failed with exit code {e.returncode}")
            return False

    def pull_image(self, image: Optional[str] = None, force_pull: bool = False) -> bool:
        """Pull the Docker image if not already available or force_pull is True.

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
                    ["docker", "image", "inspect", target_image],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.debug(f"Docker image {target_image} already available locally")
                    return True  # Image already available locally
            except subprocess.TimeoutExpired:
                logger.debug(f"Timeout checking local image {target_image}, proceeding with pull")
            except subprocess.CalledProcessError:
                logger.debug(f"Image {target_image} not available locally, proceeding with pull")

        # Pull the latest version of the image
        logger.info(f"Pulling Docker image: {target_image}")
        try:
            result = subprocess.run(
                ["docker", "pull", target_image],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.returncode == 0:
                logger.info(f"Successfully pulled Docker image: {target_image}")
                return True
            else:
                # Analyze the error to provide helpful feedback
                stderr_lower = result.stderr.lower()
                if "permission denied" in stderr_lower:
                    raise ContainerPermissionError("docker", f"pull image {target_image}")
                elif "not found" in stderr_lower or "no such image" in stderr_lower:
                    raise ContainerImagePullError("docker", target_image, "Image not found in registry")
                elif "network" in stderr_lower or "connection" in stderr_lower:
                    raise ContainerImagePullError("docker", target_image, "Network connectivity issue")
                elif "unauthorized" in stderr_lower or "authentication" in stderr_lower:
                    raise ContainerImagePullError("docker", target_image, "Authentication required for private image")
                else:
                    raise ContainerImagePullError("docker", target_image, result.stderr.strip())

        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError("docker", f"pull image {target_image}", 300) from e
        except subprocess.CalledProcessError as e:
            logger.debug(f"Docker pull failed with exit code {e.returncode}")
            raise ContainerImagePullError(
                "docker", target_image, f"Pull command failed with exit code {e.returncode}"
            ) from e

    def run_command(
        self,
        command: str | List[str],
        image: Optional[str] = None,
        working_dir: str = "/workspace",
        volumes: Optional[List[str]] = None,
        environment: Optional[Dict[str, str]] = None,
        session_key: Optional[str] = None,
        capture_output: bool = True,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """Execute a command in a Docker container with optimization."""
        target_image = image or self.default_image

        # Try to use existing session if session_key provided
        session = None
        if session_key:
            session = self._get_or_create_session(session_key, target_image)

        if session and session.is_active():
            # Execute in existing container
            if isinstance(command, str):
                exec_cmd = [
                    "docker",
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
                    "docker",
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

        # Execute the command
        return subprocess.run(
            exec_cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            **kwargs,
        )

    def _build_container_command(
        self,
        command: str | List[str],
        image: Optional[str] = None,
        working_dir: str = "/workspace",
        volumes: Optional[List[str]] = None,
        environment: Optional[Dict[str, str]] = None,
        user: Optional[str] = None,
        interactive: bool = False,
        remove: bool = True,
        detach: bool = False,
    ) -> List[str]:
        """Build a Docker run command with optimal settings."""
        docker_cmd = ["docker", "run"]

        # Container options
        if remove and not detach:
            docker_cmd.append("--rm")

        if detach:
            docker_cmd.append("-d")

        if interactive:
            docker_cmd.extend(["-i", "-t"])

        # Platform specification
        docker_cmd.extend(["--platform", self._platform])

        # Resource limits
        docker_cmd.extend(["--memory", self.memory_limit])
        docker_cmd.extend(["--cpus", self.cpu_limit])

        # Volume mounts
        all_volumes = self._base_volumes.copy()
        if volumes:
            all_volumes.extend(volumes)

        for volume in all_volumes:
            docker_cmd.extend(["-v", volume])

        # Working directory
        docker_cmd.extend(["-w", working_dir])

        # Environment variables
        all_env = self._base_env.copy()
        if environment:
            all_env.update(environment)

        for key, value in all_env.items():
            docker_cmd.extend(["-e", f"{key}={value}"])

        # User specification
        if user:
            docker_cmd.extend(["--user", user])

        # Image
        docker_cmd.append(image or self.default_image)

        # Command
        if isinstance(command, str):
            docker_cmd.extend(["sh", "-c", command])
        else:
            docker_cmd.extend(command)

        return docker_cmd

    def _get_or_create_session(self, session_key: str, image: str) -> Optional["DockerSession"]:
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
            docker_cmd = self._build_container_command(
                command=["sleep", "infinity"],  # Keep container alive
                image=image,
                detach=True,
                remove=False,
            )

            result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                container_id = result.stdout.strip()
                session = DockerSession(container_id, image, self.workspace_dir)

                # Initialize container with health checks
                if self._initialize_container(session):
                    self._active_sessions[session_key] = session
                    return session
                else:
                    # Cleanup failed session
                    session.cleanup()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass

        return None

    def _initialize_container(self, session: ContainerSession) -> bool:
        """Initialize a Docker container with health checks and verification."""
        try:
            # Basic connectivity test
            exec_cmd = [
                "docker",
                "exec",
                session.container_id,
                "echo",
                "container_ready",
            ]
            result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False

            # Test Python availability and basic imports
            python_test = [
                "docker",
                "exec",
                session.container_id,
                "python3",
                "-c",
                "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')",
            ]
            result = subprocess.run(python_test, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                return False

            # Test critical Python dependencies
            deps_test = [
                "docker",
                "exec",
                session.container_id,
                "python3",
                "-c",
                """
try:
    import numpy, matplotlib, yaml, requests
    print('Critical dependencies verified')
except ImportError as e:
    print(f'Dependency error: {e}')
    exit(1)
""",
            ]
            result = subprocess.run(deps_test, capture_output=True, text=True, timeout=20)
            if result.returncode != 0:
                return False

            # Test R availability (non-blocking)
            r_test = [
                "docker",
                "exec",
                session.container_id,
                "sh",
                "-c",
                "which Rscript && Rscript --version || echo 'R not available'",
            ]
            subprocess.run(r_test, capture_output=True, text=True, timeout=10)

            # Test LaTeX availability (non-blocking)
            latex_test = [
                "docker",
                "exec",
                session.container_id,
                "sh",
                "-c",
                "which pdflatex && echo 'LaTeX ready' || echo 'LaTeX not available'",
            ]
            subprocess.run(latex_test, capture_output=True, text=True, timeout=10)

            # Set up workspace permissions
            workspace_setup = [
                "docker",
                "exec",
                session.container_id,
                "sh",
                "-c",
                "chmod -R 755 /workspace && mkdir -p /workspace/output",
            ]
            result = subprocess.run(workspace_setup, capture_output=True, text=True, timeout=10)
            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    def _cleanup_expired_sessions(self, force: bool = False) -> None:
        """Clean up expired or inactive Docker sessions."""
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
