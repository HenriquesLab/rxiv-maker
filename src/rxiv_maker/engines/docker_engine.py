"""Docker container engine implementation."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

from .abstract import AbstractContainerEngine, ContainerSession

logger = logging.getLogger(__name__)


class DockerSession(ContainerSession):
    """Docker-specific container session implementation."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        super().__init__(container_id, image, workspace_dir, "docker")
        self.created_at = time.time()


class DockerEngine(AbstractContainerEngine):
    """Docker container engine implementation."""

    @property
    def engine_name(self) -> str:
        """Return the name of the container engine."""
        return "docker"

    # Note: check_available() method is now inherited from AbstractContainerEngine base class

    # Note: pull_image() method is now inherited from AbstractContainerEngine base class

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

    # Note: _initialize_container() method is now inherited from AbstractContainerEngine base class

    # Note: _cleanup_expired_sessions() method is now inherited from AbstractContainerEngine base class
