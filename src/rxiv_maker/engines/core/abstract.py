"""Abstract base class for container engines."""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContainerSession:
    """Represents a persistent container session for multiple operations."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path, engine_type: str):
        """Initialize container session.

        Args:
            container_id: Container ID
            image: Container image name
            workspace_dir: Workspace directory path
            engine_type: Type of container engine (docker, podman, etc.)
        """
        self.container_id: str = container_id
        self.image: str = image
        self.workspace_dir: Path = workspace_dir
        self.engine_type: str = engine_type
        self.created_at: Optional[float] = None  # Will be set by derived classes
        self._active: bool = True

    def is_active(self) -> bool:
        """Check if the container is still running."""
        if not self._active:
            return False

        try:
            result = subprocess.run(
                [
                    self.engine_type,
                    "container",
                    "inspect",
                    self.container_id,
                    "--format",
                    "{{.State.Running}}",
                ],
                capture_output=True,
                text=True,
                encoding="latin-1",
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
        """Stop and remove the container."""
        if not self._active:
            return True

        import logging

        logger = logging.getLogger(__name__)

        try:
            # Stop the container
            stop_result = subprocess.run(
                [self.engine_type, "stop", self.container_id],
                capture_output=True,
                text=True,
                encoding="latin-1",
                timeout=10,
            )
            if stop_result.returncode != 0:
                logger.debug(
                    f"Failed to stop {self.engine_type} container {self.container_id[:12]}: {stop_result.stderr}"
                )

            # Remove the container
            rm_result = subprocess.run(
                [self.engine_type, "rm", self.container_id],
                capture_output=True,
                text=True,
                encoding="latin-1",
                timeout=10,
            )
            if rm_result.returncode != 0:
                logger.debug(
                    f"Failed to remove {self.engine_type} container {self.container_id[:12]}: {rm_result.stderr}"
                )

            self._active = False
            return True
        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout during {self.engine_type} container {self.container_id[:12]} cleanup")
            self._active = False  # Mark as inactive even if cleanup timed out
            return False
        except subprocess.CalledProcessError as e:
            logger.debug(
                f"Error during {self.engine_type} container {self.container_id[:12]} cleanup: exit code {e.returncode}"
            )
            self._active = False  # Mark as inactive even if cleanup failed
            return False


class AbstractContainerEngine(ABC):
    """Abstract base class for container engines (Docker, Podman, etc.)."""

    def __init__(
        self,
        default_image: str = "henriqueslab/rxiv-maker-base:latest",
        workspace_dir: Optional[Path] = None,
        enable_session_reuse: bool = True,
        memory_limit: str = "2g",
        cpu_limit: str = "2.0",
    ):
        """Initialize container engine.

        Args:
            default_image: Default container image to use
            workspace_dir: Workspace directory (defaults to current working directory)
            enable_session_reuse: Whether to reuse containers across operations
            memory_limit: Memory limit for containers (e.g., "2g", "512m")
            cpu_limit: CPU limit for containers (e.g., "2.0" for 2 cores)
        """
        self.default_image = default_image
        self.workspace_dir = workspace_dir or Path.cwd().resolve()
        self.enable_session_reuse = enable_session_reuse
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit

        # Session management
        self._active_sessions: Dict[str, ContainerSession] = {}
        self._session_timeout = 600  # 10 minutes
        self._max_sessions = 5
        self._last_cleanup = 0.0

        # Engine-specific configuration
        self._platform = self._detect_platform()
        self._base_volumes = self._get_base_volumes()
        self._base_env = self._get_base_environment()

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the name of the container engine (e.g., 'docker', 'podman')."""
        pass

    def check_available(self) -> bool:
        """Check if the container engine is available and running.

        Returns:
            True if engine is available and running, False otherwise.

        Raises:
            ContainerEngineNotFoundError: If engine binary is not found
            ContainerEngineNotRunningError: If engine daemon/service is not running
            ContainerPermissionError: If permission denied accessing engine
            ContainerTimeoutError: If engine commands timeout
        """
        import logging
        import subprocess

        logger = logging.getLogger(__name__)

        # Import exceptions here to avoid circular imports
        from .exceptions import (
            ContainerEngineNotFoundError,
            ContainerEngineNotRunningError,
            ContainerPermissionError,
            ContainerTimeoutError,
        )

        try:
            # First check if engine binary exists
            version_result = subprocess.run(
                [self.engine_name, "--version"], capture_output=True, text=True, encoding="latin-1", timeout=5
            )

            if version_result.returncode != 0:
                if "permission denied" in version_result.stderr.lower():
                    raise ContainerPermissionError(self.engine_name, f"check {self.engine_name.title()} version")
                else:
                    logger.debug(f"{self.engine_name.title()} version check failed: {version_result.stderr}")
                    return False

        except FileNotFoundError as e:
            raise ContainerEngineNotFoundError(self.engine_name) from e
        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError(self.engine_name, "version check", 5) from e

        try:
            # Then check if engine daemon/service is actually running
            ps_result = subprocess.run(
                [self.engine_name, "ps"], capture_output=True, text=True, encoding="latin-1", timeout=10
            )

            if ps_result.returncode != 0:
                stderr_lower = ps_result.stderr.lower()
                if "permission denied" in stderr_lower or "access denied" in stderr_lower:
                    raise ContainerPermissionError(self.engine_name, "list containers")
                elif "cannot connect" in stderr_lower or "connection refused" in stderr_lower:
                    raise ContainerEngineNotRunningError(self.engine_name)
                elif self._is_service_not_running_error(stderr_lower):
                    raise ContainerEngineNotRunningError(self.engine_name)
                else:
                    logger.debug(f"{self.engine_name.title()} ps failed: {ps_result.stderr}")
                    return False

            return True

        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError(self.engine_name, "daemon/service connectivity check", 10) from e
        except subprocess.CalledProcessError as e:
            logger.debug(f"{self.engine_name.title()} ps command failed with exit code {e.returncode}")
            return False

    def _is_service_not_running_error(self, stderr_lower: str) -> bool:
        """Check if the error indicates the container service is not running.

        This method can be overridden by subclasses to provide engine-specific
        error pattern matching.

        Args:
            stderr_lower: The stderr output in lowercase

        Returns:
            True if the error indicates service is not running
        """
        # Common patterns for both Docker and Podman
        service_not_running_patterns = [
            "daemon" in stderr_lower and "not running" in stderr_lower,
            "service" in stderr_lower and "not running" in stderr_lower,
            "machine" in stderr_lower and ("not running" in stderr_lower or "stopped" in stderr_lower),
        ]
        return any(service_not_running_patterns)

    def pull_image(self, image: Optional[str] = None, force_pull: bool = False) -> bool:
        """Pull a container image if not already available or force_pull is True.

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
        import logging
        import subprocess

        logger = logging.getLogger(__name__)
        target_image = image or self.default_image

        # Import exceptions here to avoid circular imports
        from .exceptions import (
            ContainerImagePullError,
            ContainerPermissionError,
            ContainerTimeoutError,
        )

        # If force_pull is False, check if image is already available locally
        if not force_pull:
            try:
                result = subprocess.run(
                    [self.engine_name, "image", "inspect", target_image],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.debug(f"{self.engine_name.title()} image {target_image} already available locally")
                    return True  # Image already available locally
            except subprocess.TimeoutExpired:
                logger.debug(f"Timeout checking local image {target_image}, proceeding with pull")
            except subprocess.CalledProcessError:
                logger.debug(f"Image {target_image} not available locally, proceeding with pull")

        # Pull the latest version of the image
        logger.info(f"Pulling {self.engine_name.title()} image: {target_image}")
        try:
            result = subprocess.run(
                [self.engine_name, "pull", target_image],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.returncode == 0:
                logger.info(f"Successfully pulled {self.engine_name.title()} image: {target_image}")
                return True
            else:
                # Analyze the error to provide helpful feedback
                stderr_lower = result.stderr.lower()
                if "permission denied" in stderr_lower:
                    raise ContainerPermissionError(self.engine_name, f"pull image {target_image}")
                elif "not found" in stderr_lower or "no such image" in stderr_lower:
                    raise ContainerImagePullError(self.engine_name, target_image, "Image not found in registry")
                elif "network" in stderr_lower or "connection" in stderr_lower:
                    raise ContainerImagePullError(self.engine_name, target_image, "Network connectivity issue")
                elif "unauthorized" in stderr_lower or "authentication" in stderr_lower:
                    raise ContainerImagePullError(
                        self.engine_name, target_image, "Authentication required for private image"
                    )
                else:
                    raise ContainerImagePullError(self.engine_name, target_image, result.stderr.strip())

        except subprocess.TimeoutExpired as e:
            raise ContainerTimeoutError(self.engine_name, f"pull image {target_image}", 300) from e
        except subprocess.CalledProcessError as e:
            logger.debug(f"{self.engine_name.title()} pull failed with exit code {e.returncode}")
            raise ContainerImagePullError(
                self.engine_name, target_image, f"Pull command failed with exit code {e.returncode}"
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
        timeout: Optional[int] = 1800,  # Default 30 minute timeout to prevent infinite hangs
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """Execute a command in a container with optimization.

        Args:
            command: Command to execute (string or list)
            image: Container image to use (defaults to default_image)
            working_dir: Working directory inside container
            volumes: Additional volume mounts
            environment: Additional environment variables
            session_key: Session key for container reuse (enables session reuse)
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds (default: 30 minutes)
            **kwargs: Additional arguments passed to subprocess.run

        Returns:
            CompletedProcess result
        """
        import logging

        logger = logging.getLogger(__name__)

        target_image = image or self.default_image

        # Try to use existing session if session_key provided
        session = None
        if session_key:
            session = self._get_or_create_session(session_key, target_image)

        if session and session.is_active():
            # Execute in existing container
            exec_cmd = self._build_exec_command(command, working_dir, session.container_id)
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
                encoding="latin-1",  # Handle all byte values gracefully
                timeout=timeout,
                **kwargs,
            )

            # If we used a session and the command failed, check if the session is still active
            if session and result.returncode != 0:
                if not session.is_active():
                    logger.debug(
                        f"{self.engine_name.title()} session {session.container_id[:12]} died during command execution"
                    )
                    # Remove the dead session from our tracking
                    if session_key in self._active_sessions:
                        del self._active_sessions[session_key]

            return result

        except subprocess.TimeoutExpired as e:
            # If using a session, check if it's still alive after timeout
            if session:
                if not session.is_active():
                    logger.debug(f"{self.engine_name.title()} session {session.container_id[:12]} died during timeout")
                    if session_key in self._active_sessions:
                        del self._active_sessions[session_key]
            raise e
        except Exception as e:
            # Log unexpected errors for debugging
            cmd_preview = " ".join(exec_cmd[:5]) + ("..." if len(exec_cmd) > 5 else "")
            logger.debug(f"Unexpected error executing {self.engine_name} command '{cmd_preview}': {e}")
            raise e

    def _build_exec_command(self, command: str | List[str], working_dir: str, container_id: str) -> List[str]:
        """Build an exec command for running in an existing container.

        Args:
            command: Command to execute (string or list)
            working_dir: Working directory inside container
            container_id: Container ID to execute in

        Returns:
            List of command arguments for container exec
        """
        if isinstance(command, str):
            return [
                self.engine_name,
                "exec",
                "-w",
                working_dir,
                container_id,
                "sh",
                "-c",
                command,
            ]
        else:
            return [
                self.engine_name,
                "exec",
                "-w",
                working_dir,
                container_id,
            ] + command

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
        """Build a container run command with optimal settings."""
        container_cmd = [self.engine_name, "run"]

        # Container options
        if remove and not detach:
            container_cmd.append("--rm")

        if detach:
            container_cmd.append("-d")

        if interactive:
            container_cmd.extend(["-i", "-t"])

        # Platform specification
        container_cmd.extend(["--platform", self._platform])

        # Resource limits
        container_cmd.extend(["--memory", self.memory_limit])
        container_cmd.extend(["--cpus", self.cpu_limit])

        # Volume mounts
        all_volumes = self._base_volumes.copy()
        if volumes:
            all_volumes.extend(volumes)

        for volume in all_volumes:
            container_cmd.extend(["-v", volume])

        # Working directory
        container_cmd.extend(["-w", working_dir])

        # Environment variables
        all_env = self._base_env.copy()
        if environment:
            all_env.update(environment)

        for key, value in all_env.items():
            container_cmd.extend(["-e", f"{key}={value}"])

        # User specification
        if user:
            container_cmd.extend(["--user", user])

        # Image
        container_cmd.append(image or self.default_image)

        # Command
        if isinstance(command, str):
            container_cmd.extend(["sh", "-c", command])
        else:
            container_cmd.extend(command)

        return container_cmd

    def _get_or_create_session(self, session_key: str, image: str) -> Optional[ContainerSession]:
        """Get an existing session or create a new one if session reuse is enabled."""
        if not self.enable_session_reuse:
            return None

        # Clean up expired sessions
        self._cleanup_expired_sessions()

        # Check if we have an active session
        if session_key in self._active_sessions:
            session = self._active_sessions[session_key]
            if session.is_active():
                return session
            else:
                # Session is dead, remove it
                del self._active_sessions[session_key]

        # Create new session
        import logging

        logger = logging.getLogger(__name__)

        try:
            container_cmd = self._build_container_command(
                command=["sleep", "infinity"],  # Keep container alive
                image=image,
                detach=True,
                remove=False,
            )

            result = subprocess.run(container_cmd, capture_output=True, text=True, encoding="latin-1", timeout=30)

            if result.returncode == 0:
                container_id = result.stdout.strip()
                session = self._create_session_instance(container_id, image, self.workspace_dir)

                # Initialize container with health checks
                if self._initialize_container(session):
                    self._active_sessions[session_key] = session
                    logger.debug(f"Created new {self.engine_name} session: {container_id[:12]}")
                    return session
                else:
                    # Cleanup failed session
                    logger.debug(f"Failed to initialize {self.engine_name} session {container_id[:12]}, cleaning up")
                    session.cleanup()
            else:
                # Log session creation failure details
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.debug(f"Failed to create {self.engine_name} session for {session_key}: {error_msg}")

        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout creating {self.engine_name} session for {session_key}")
        except subprocess.CalledProcessError as e:
            logger.debug(
                f"Command failed creating {self.engine_name} session for {session_key}: exit code {e.returncode}"
            )
        except Exception as e:
            logger.debug(f"Unexpected error creating {self.engine_name} session for {session_key}: {e}")

        return None

    @abstractmethod
    def _create_session_instance(self, container_id: str, image: str, workspace_dir: Path) -> ContainerSession:
        """Create an engine-specific session instance.

        Args:
            container_id: Container ID
            image: Container image name
            workspace_dir: Workspace directory path

        Returns:
            Engine-specific ContainerSession instance
        """
        pass

    def _detect_platform(self) -> str:
        """Detect the optimal container platform for the current architecture."""
        import platform

        machine = platform.machine().lower()
        if machine in ["arm64", "aarch64"]:
            return "linux/arm64"
        elif machine in ["x86_64", "amd64"]:
            return "linux/amd64"
        else:
            return "linux/amd64"  # fallback

    def _get_base_volumes(self) -> List[str]:
        """Get base volume mounts for all container operations."""
        return [f"{self.workspace_dir}:/workspace"]

    def _get_base_environment(self) -> Dict[str, str]:
        """Get base environment variables for containers."""
        import os

        env = {}

        # Pass through Rxiv-specific environment variables
        rxiv_vars = [
            "RXIV_ENGINE",
            "RXIV_VERBOSE",
            "RXIV_NO_UPDATE_CHECK",
            "MANUSCRIPT_PATH",
            "FORCE_FIGURES",
        ]

        for var in rxiv_vars:
            if var in os.environ:
                env[var] = os.environ[var]

        # Ensure UTF-8 encoding in containers
        env.update({"PYTHONIOENCODING": "utf-8", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})

        return env

    def run_mermaid_generation(
        self,
        input_file: Path,
        output_file: Path,
        background_color: str = "transparent",
        config_file: Optional[Path] = None,
    ) -> subprocess.CompletedProcess:
        """Generate SVG from Mermaid diagram using online service."""
        # Build relative paths for container
        try:
            input_rel = input_file.relative_to(self.workspace_dir)
        except ValueError:
            input_rel = Path(input_file.name)

        try:
            output_rel = output_file.relative_to(self.workspace_dir)
        except ValueError:
            output_rel = Path("output") / output_file.name

        # Python script for Mermaid generation using Kroki service
        python_script = f'''
import sys
import base64
import urllib.request
import urllib.parse
import zlib
from pathlib import Path

def generate_mermaid_svg():
    """Generate SVG from Mermaid using Kroki service."""
    try:
        # Read the Mermaid file
        with open("/workspace/{input_rel}", "r") as f:
            mermaid_content = f.read().strip()

        # Use Kroki service for Mermaid rendering
        encoded_content = base64.urlsafe_b64encode(
            zlib.compress(mermaid_content.encode("utf-8"))
        ).decode("ascii")

        kroki_url = f"https://kroki.io/mermaid/svg/{{encoded_content}}"

        try:
            with urllib.request.urlopen(kroki_url, timeout=30) as response:
                if response.status == 200:
                    svg_content = response.read().decode("utf-8")

                    with open("/workspace/{output_rel}", "w") as f:
                        f.write(svg_content)

                    print("Generated SVG using Kroki service")
                    return 0
                else:
                    raise Exception(f"Kroki service returned status {{response.status}}")

        except Exception as kroki_error:
            print(f"Kroki service unavailable: {{kroki_error}}")
            # Fall back to a simple SVG placeholder
            fallback_svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="{background_color}" stroke="#ddd" stroke-width="2"/>
  <text x="400" y="180" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#666">
    <tspan x="400" dy="0">Mermaid Diagram</tspan>
    <tspan x="400" dy="30">(Service temporarily unavailable)</tspan>
  </text>
  <text x="400" y="250" text-anchor="middle" font-family="monospace" font-size="12" fill="#999">
    Source: {input_rel.name}
  </text>
</svg>"""

            with open("/workspace/{output_rel}", "w") as f:
                f.write(fallback_svg)

            print("Generated fallback SVG (Kroki service unavailable)")
            return 0

    except Exception as e:
        print(f"Error generating Mermaid SVG: {{e}}")
        return 1

if __name__ == "__main__":
    sys.exit(generate_mermaid_svg())
'''

        from ...core.session_optimizer import get_optimized_session_key

        return self.run_command(
            command=["python3", "-c", python_script], session_key=get_optimized_session_key("mermaid_generation")
        )

    def run_python_script(
        self,
        script_file: Path,
        working_dir: Optional[Path] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        """Execute a Python script with optimized container execution."""
        docker_working_dir = "/workspace"

        if working_dir:
            try:
                work_rel = working_dir.relative_to(self.workspace_dir)
                docker_working_dir = f"/workspace/{work_rel}"
            except ValueError:
                docker_working_dir = "/workspace/output"

        from ...core.session_optimizer import get_optimized_session_key

        optimized_session_key = get_optimized_session_key("python_execution")

        try:
            script_rel = script_file.relative_to(self.workspace_dir)
            return self.run_command(
                command=["python", f"/workspace/{script_rel}"],
                working_dir=docker_working_dir,
                environment=environment,
                session_key=optimized_session_key,
            )
        except ValueError:
            # Script is outside workspace, execute by reading content
            script_content = script_file.read_text(encoding="utf-8")
            return self.run_command(
                command=["python", "-c", script_content],
                working_dir=docker_working_dir,
                environment=environment,
                session_key=optimized_session_key,
            )

    def run_r_script(
        self,
        script_file: Path,
        working_dir: Optional[Path] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        """Execute an R script with optimized container execution."""
        docker_working_dir = "/workspace"

        if working_dir:
            try:
                work_rel = working_dir.relative_to(self.workspace_dir)
                docker_working_dir = f"/workspace/{work_rel}"
            except ValueError:
                docker_working_dir = "/workspace/output"

        from ...core.session_optimizer import get_optimized_session_key

        optimized_session_key = get_optimized_session_key("r_execution")

        try:
            script_rel = script_file.relative_to(self.workspace_dir)
            return self.run_command(
                command=["Rscript", f"/workspace/{script_rel}"],
                working_dir=docker_working_dir,
                environment=environment,
                session_key=optimized_session_key,
            )
        except ValueError:
            # Script is outside workspace, execute by reading content
            import shlex

            script_content = script_file.read_text(encoding="utf-8")
            temp_script = f"/tmp/{script_file.name}"
            escaped_content = shlex.quote(script_content)
            return self.run_command(
                command=[
                    "sh",
                    "-c",
                    f"echo {escaped_content} > {temp_script} && Rscript {temp_script}",
                ],
                working_dir=docker_working_dir,
                environment=environment,
                session_key=optimized_session_key,
            )

    def run_latex_compilation(
        self, tex_file: Path, working_dir: Optional[Path] = None, passes: int = 3, timeout: int = 300
    ) -> List[subprocess.CompletedProcess]:
        """Run LaTeX compilation with multiple passes in container.

        Args:
            tex_file: Path to the TeX file to compile
            working_dir: Working directory for compilation
            passes: Number of LaTeX passes to run
            timeout: Timeout in seconds for each LaTeX command (default: 5 minutes)
        """
        try:
            tex_rel = tex_file.relative_to(self.workspace_dir)
        except ValueError:
            tex_rel = Path(tex_file.name)

        docker_working_dir = "/workspace"

        if working_dir:
            try:
                work_rel = working_dir.relative_to(self.workspace_dir)
                docker_working_dir = f"/workspace/{work_rel}"
            except ValueError:
                docker_working_dir = "/workspace/output"

        from ...core.session_optimizer import get_optimized_session_key

        results = []
        session_key = get_optimized_session_key("latex_compilation")

        for i in range(passes):
            result = self.run_command(
                command=["pdflatex", "-interaction=nonstopmode", tex_rel.name],
                working_dir=docker_working_dir,
                session_key=session_key,
                timeout=timeout,
            )
            results.append(result)

            # Run bibtex after first pass if bib file exists
            if i == 0:
                bib_file_name = "03_REFERENCES.bib"
                bib_result = self.run_command(
                    command=[
                        "sh",
                        "-c",
                        f"if [ -f {bib_file_name} ]; then bibtex {tex_rel.stem}; fi",
                    ],
                    working_dir=docker_working_dir,
                    session_key=session_key,
                    timeout=60,  # BibTeX should be much faster
                )
                results.append(bib_result)

        return results

    def cleanup_all_sessions(self) -> None:
        """Clean up all active container sessions."""
        import logging

        logger = logging.getLogger(__name__)

        for session_key, session in list(self._active_sessions.items()):
            try:
                session.cleanup()
            except Exception as e:
                logger.debug(f"Failed to cleanup session {session_key}: {e}")
                # Continue with other sessions even if one fails
        self._active_sessions.clear()

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active container sessions."""
        import time

        stats: Dict[str, Any] = {
            "total_sessions": len(self._active_sessions),
            "active_sessions": sum(1 for s in self._active_sessions.values() if s.is_active()),
            "session_details": [],
        }

        for key, session in self._active_sessions.items():
            session_info = {
                "key": key,
                "container_id": session.container_id[:12],
                "image": session.image,
                "active": session.is_active(),
                "age_seconds": time.time() - (session.created_at or 0),
            }
            stats["session_details"].append(session_info)

        return stats

    def _initialize_container(self, session: "ContainerSession") -> bool:
        """Initialize a container with health checks and verification.

        This method performs common initialization tasks for all container engines.
        Subclasses can override this method to add engine-specific initialization.

        Args:
            session: Container session to initialize

        Returns:
            True if initialization successful, False otherwise
        """
        engine_type = session.engine_type
        container_id = session.container_id

        try:
            # Basic connectivity test
            exec_cmd = [
                engine_type,
                "exec",
                container_id,
                "echo",
                "container_ready",
            ]
            result = subprocess.run(exec_cmd, capture_output=True, text=True, encoding="latin-1", timeout=10)
            if result.returncode != 0:
                return False

            # Upgrade to latest rxiv-maker version from PyPI (for cutting-edge features)
            upgrade_cmd = [
                engine_type,
                "exec",
                container_id,
                "/usr/local/bin/upgrade-to-latest-rxiv.sh",
            ]
            result = subprocess.run(upgrade_cmd, capture_output=True, text=True, encoding="latin-1", timeout=60)
            # Don't fail initialization if upgrade fails - APT version will work
            if result.returncode != 0:
                import logging

                logger = logging.getLogger(__name__)
                logger.debug(f"Rxiv-maker upgrade failed, using APT version: {result.stderr.strip()}")

            # Test Python availability and basic imports
            python_test = [
                engine_type,
                "exec",
                container_id,
                "python3",
                "-c",
                "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')",
            ]
            result = subprocess.run(python_test, capture_output=True, text=True, encoding="latin-1", timeout=15)
            if result.returncode != 0:
                return False

            # Test critical Python dependencies and rxiv-maker availability
            deps_test = [
                engine_type,
                "exec",
                container_id,
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
            result = subprocess.run(deps_test, capture_output=True, text=True, encoding="latin-1", timeout=20)
            if result.returncode != 0:
                return False

            # Test rxiv-maker CLI availability (from APT or upgraded version)
            rxiv_test = [
                engine_type,
                "exec",
                container_id,
                "rxiv",
                "--version",
            ]
            result = subprocess.run(rxiv_test, capture_output=True, text=True, encoding="latin-1", timeout=10)
            if result.returncode != 0:
                return False

            # Test R availability (non-blocking)
            r_test = [
                engine_type,
                "exec",
                container_id,
                "sh",
                "-c",
                "which Rscript && Rscript --version || echo 'R not available'",
            ]
            subprocess.run(r_test, capture_output=True, text=True, encoding="latin-1", timeout=10)

            # Test LaTeX availability (non-blocking)
            latex_test = [
                engine_type,
                "exec",
                container_id,
                "sh",
                "-c",
                "which pdflatex && echo 'LaTeX ready' || echo 'LaTeX not available'",
            ]
            subprocess.run(latex_test, capture_output=True, text=True, encoding="latin-1", timeout=10)

            # Set up workspace permissions
            workspace_setup = [
                engine_type,
                "exec",
                container_id,
                "sh",
                "-c",
                "chmod -R 755 /workspace && mkdir -p /workspace/output",
            ]
            result = subprocess.run(workspace_setup, capture_output=True, text=True, encoding="latin-1", timeout=10)
            return result.returncode == 0

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    def _cleanup_expired_sessions(self, force: bool = False) -> None:
        """Clean up expired or inactive container sessions."""
        import time

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
