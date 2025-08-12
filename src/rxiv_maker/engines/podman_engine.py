"""Podman container engine implementation."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional

from .abstract import ContainerSession
from .docker_engine import DockerEngine


class PodmanSession(ContainerSession):
    """Podman-specific container session implementation."""
    
    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        super().__init__(container_id, image, workspace_dir, "podman")
        self.created_at = time.time()
    
    def is_active(self) -> bool:
        """Check if the Podman container is still running."""
        if not self._active:
            return False
            
        try:
            result = subprocess.run(
                [
                    "podman", "container", "inspect", self.container_id,
                    "--format", "{{.State.Running}}",
                ],
                capture_output=True, text=True, timeout=5,
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
        """Stop and remove the Podman container."""
        if not self._active:
            return True
            
        try:
            # Stop the container
            subprocess.run(
                ["podman", "stop", self.container_id], 
                capture_output=True, timeout=10
            )
            
            # Remove the container
            subprocess.run(
                ["podman", "rm", self.container_id], 
                capture_output=True, timeout=10
            )
            
            self._active = False
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False


class PodmanEngine(DockerEngine):
    """Podman container engine implementation.
    
    Inherits from DockerEngine since Podman has a Docker-compatible API.
    Only overrides engine-specific behavior where needed.
    """
    
    @property
    def engine_name(self) -> str:
        """Return the name of the container engine."""
        return "podman"
    
    def check_available(self) -> bool:
        """Check if Podman is available and service is running."""
        try:
            # First check if podman binary exists
            version_result = subprocess.run(
                ["podman", "--version"], 
                capture_output=True, text=True, timeout=5
            )
            if version_result.returncode != 0:
                return False
            
            # Then check if Podman service is actually running
            ps_result = subprocess.run(
                ["podman", "ps"], 
                capture_output=True, text=True, timeout=10
            )
            return ps_result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def pull_image(self, image: Optional[str] = None, force_pull: bool = False) -> bool:
        """Pull the Podman image if not already available or force_pull is True."""
        target_image = image or self.default_image
        
        # If force_pull is False, check if image is already available locally
        if not force_pull:
            try:
                result = subprocess.run(
                    ["podman", "image", "inspect", target_image],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    return True  # Image already available locally
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass  # Image not available locally, proceed with pull
        
        # Pull the latest version of the image
        try:
            result = subprocess.run(
                ["podman", "pull", target_image],
                capture_output=True, text=True, timeout=300,  # 5 minutes
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
    
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
    
    def _get_or_create_session(self, session_key: str, image: str) -> Optional[PodmanSession]:
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
        try:
            podman_cmd = self._build_container_command(
                command=["sleep", "infinity"],  # Keep container alive
                image=image,
                detach=True,
                remove=False,
            )
            
            result = subprocess.run(
                podman_cmd, capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                container_id = result.stdout.strip()
                session = PodmanSession(container_id, image, self.workspace_dir)
                
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
    
    def _initialize_container(self, session: PodmanSession) -> bool:
        """Initialize a Podman container with health checks and verification."""
        try:
            # Basic connectivity test
            exec_cmd = [
                "podman", "exec", session.container_id, "echo", "container_ready",
            ]
            result = subprocess.run(
                exec_cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return False
            
            # Test Python availability and basic imports
            python_test = [
                "podman", "exec", session.container_id, "python3", "-c",
                "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}')",
            ]
            result = subprocess.run(
                python_test, capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                return False
            
            # Test critical Python dependencies
            deps_test = [
                "podman", "exec", session.container_id, "python3", "-c",
                """
try:
    import numpy, matplotlib, yaml, requests
    print('Critical dependencies verified')
except ImportError as e:
    print(f'Dependency error: {e}')
    exit(1)
""",
            ]
            result = subprocess.run(
                deps_test, capture_output=True, text=True, timeout=20
            )
            if result.returncode != 0:
                return False
            
            # Test R availability (non-blocking)
            r_test = [
                "podman", "exec", session.container_id, "sh", "-c",
                "which Rscript && Rscript --version || echo 'R not available'",
            ]
            subprocess.run(
                r_test, capture_output=True, text=True, timeout=10
            )
            
            # Test LaTeX availability (non-blocking)
            latex_test = [
                "podman", "exec", session.container_id, "sh", "-c",
                "which pdflatex && echo 'LaTeX ready' || echo 'LaTeX not available'",
            ]
            subprocess.run(
                latex_test, capture_output=True, text=True, timeout=10
            )
            
            # Set up workspace permissions (important for Podman rootless)
            workspace_setup = [
                "podman", "exec", session.container_id, "sh", "-c",
                "chmod -R 755 /workspace && mkdir -p /workspace/output",
            ]
            result = subprocess.run(
                workspace_setup, capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
    
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
                    "podman", "exec", "-w", working_dir,
                    session.container_id, "sh", "-c", command,
                ]
            else:
                exec_cmd = [
                    "podman", "exec", "-w", working_dir,
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