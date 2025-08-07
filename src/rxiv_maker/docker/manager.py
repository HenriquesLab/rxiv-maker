"""Centralized Docker management for Rxiv-Maker.

This module provides efficient Docker container management with session reuse,
volume caching, and optimized command construction for all Rxiv-Maker operations.
"""

import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

from ..utils.platform import platform_detector


class DockerSession:
    """Manages a persistent Docker container session for multiple operations."""

    def __init__(self, container_id: str, image: str, workspace_dir: Path):
        """Initialize Docker session.

        Args:
            container_id: Docker container ID
            image: Docker image name
            workspace_dir: Workspace directory path
        """
        self.container_id = container_id
        self.image = image
        self.workspace_dir = workspace_dir
        self.created_at = time.time()
        self._active = True

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


class DockerManager:
    """Centralized Docker operations manager with session reuse and optimization."""

    def __init__(
        self,
        default_image: str = "henriqueslab/rxiv-maker-base:latest",
        workspace_dir: Path | None = None,
        enable_session_reuse: bool = True,
        memory_limit: str = "2g",
        cpu_limit: str = "2.0",
    ):
        """Initialize Docker manager.

        Args:
            default_image: Default Docker image to use
            workspace_dir: Workspace directory (defaults to current working directory)
            enable_session_reuse: Whether to reuse Docker containers across operations
            memory_limit: Memory limit for Docker containers (e.g., "2g", "512m")
            cpu_limit: CPU limit for Docker containers (e.g., "2.0" for 2 cores)
        """
        self.default_image = default_image
        self.workspace_dir = workspace_dir or Path.cwd().resolve()
        self.enable_session_reuse = enable_session_reuse
        self.platform = platform_detector
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit

        # Session management
        self._active_sessions: dict[str, DockerSession] = {}
        self._session_timeout = 600  # 10 minutes for better reuse
        self._max_sessions = 5  # Limit concurrent sessions
        self._last_cleanup = time.time()

        # Docker configuration
        self._docker_platform = self._detect_docker_platform()
        self._base_volumes = self._get_base_volumes()
        self._base_env = self._get_base_environment()

        # Resource monitoring
        self._resource_warnings = 0
        self._last_resource_check = time.time()

    def _detect_docker_platform(self) -> str:
        """Detect the optimal Docker platform for the current architecture."""
        machine = platform.machine().lower()
        if machine in ["arm64", "aarch64"]:
            return "linux/arm64"
        elif machine in ["x86_64", "amd64"]:
            return "linux/amd64"
        else:
            return "linux/amd64"  # fallback

    def _get_base_volumes(self) -> list[str]:
        """Get base volume mounts for all Docker operations."""
        return [f"{self.workspace_dir}:/workspace"]

    def _get_base_environment(self) -> dict[str, str]:
        """Get base environment variables for Docker containers."""
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

        return env

    def _build_docker_command(
        self,
        command: str | list[str],
        image: str | None = None,
        working_dir: str = "/workspace",
        volumes: list[str] | None = None,
        environment: dict[str, str] | None = None,
        user: str | None = None,
        interactive: bool = False,
        remove: bool = True,
        detach: bool = False,
    ) -> list[str]:
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
        docker_cmd.extend(["--platform", self._docker_platform])

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

    def _get_or_create_session(self, session_key: str, image: str) -> DockerSession | None:
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
            docker_cmd = self._build_docker_command(
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

    def _initialize_container(self, session: DockerSession) -> bool:
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

            # Test critical Python dependencies (numpy, matplotlib, requests)
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

            # Test R availability if container supports it
            r_test = [
                "docker",
                "exec",
                session.container_id,
                "sh",
                "-c",
                "which Rscript && Rscript --version || echo 'R not available'",
            ]
            subprocess.run(r_test, capture_output=True, text=True, timeout=10)
            # R test is non-blocking, we just log availability

            # Test LaTeX availability
            latex_test = [
                "docker",
                "exec",
                session.container_id,
                "sh",
                "-c",
                "which pdflatex && echo 'LaTeX ready' || echo 'LaTeX not available'",
            ]
            subprocess.run(latex_test, capture_output=True, text=True, timeout=10)
            # LaTeX test is non-blocking

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
            if current_time - session.created_at > self._session_timeout or not session.is_active():
                session.cleanup()
                expired_keys.append(key)

        for key in expired_keys:
            del self._active_sessions[key]

        # If we have too many sessions, cleanup the oldest ones
        if len(self._active_sessions) > self._max_sessions:
            sorted_sessions = sorted(self._active_sessions.items(), key=lambda x: x[1].created_at)
            excess_count = len(self._active_sessions) - self._max_sessions
            for key, session in sorted_sessions[:excess_count]:
                session.cleanup()
                del self._active_sessions[key]

    def run_command(
        self,
        command: str | list[str],
        image: str | None = None,
        working_dir: str = "/workspace",
        volumes: list[str] | None = None,
        environment: dict[str, str] | None = None,
        session_key: str | None = None,
        capture_output: bool = True,
        timeout: int | None = None,
        **kwargs,
    ) -> subprocess.CompletedProcess:
        """Execute a command in a Docker container with optimization.

        Args:
            command: Command to execute (string or list)
            image: Docker image to use (defaults to default_image)
            working_dir: Working directory inside container
            volumes: Additional volume mounts
            environment: Additional environment variables
            session_key: Session key for container reuse (enables session reuse)
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds
            **kwargs: Additional arguments passed to subprocess.run

        Returns:
            CompletedProcess result
        """
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
            exec_cmd = self._build_docker_command(
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

    def run_mermaid_generation(
        self,
        input_file: Path,
        output_file: Path,
        background_color: str = "transparent",
        config_file: Path | None = None,
    ) -> subprocess.CompletedProcess:
        """Generate SVG from Mermaid diagram using mermaid.ink API."""
        # Build relative paths for Docker with proper error handling
        try:
            input_rel = input_file.relative_to(self.workspace_dir)
        except ValueError:
            # If input file is not within workspace, use absolute path resolution
            input_rel = Path(input_file.name)

        try:
            output_rel = output_file.relative_to(self.workspace_dir)
        except ValueError:
            # If output file is not within workspace, use absolute path resolution
            output_rel = Path("output") / output_file.name

        # Use Mermaid rendering via online service
        # This eliminates the need for local Puppeteer/Chromium dependencies
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

        # Use Kroki service for Mermaid rendering (no browser dependencies)
        # Encode the content for URL safety
        encoded_content = base64.urlsafe_b64encode(
            zlib.compress(mermaid_content.encode("utf-8"))
        ).decode("ascii")

        # Build Kroki URL for SVG generation
        kroki_url = f"https://kroki.io/mermaid/svg/{{encoded_content}}"

        # Try to fetch SVG from Kroki service
        try:
            with urllib.request.urlopen(kroki_url, timeout=30) as response:
                if response.status == 200:
                    svg_content = response.read().decode("utf-8")

                    # Write the SVG file
                    with open("/workspace/{output_rel}", "w") as f:
                        f.write(svg_content)

                    print("Generated SVG using Kroki service")
                    return 0
                else:
                    raise Exception(
                        f"Kroki service returned status {{response.status}}"
                    )

        except Exception as kroki_error:
            print(f"Kroki service unavailable: {{kroki_error}}")
            # Fall back to a simple SVG placeholder
            fallback_svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="{background_color}" stroke="#ddd" \
stroke-width="2"/>
  <text x="400" y="180" text-anchor="middle" \
font-family="Arial, sans-serif" font-size="18" fill="#666">
    <tspan x="400" dy="0">Mermaid Diagram</tspan>
    <tspan x="400" dy="30">(Service temporarily unavailable)</tspan>
  </text>
  <text x="400" y="250" text-anchor="middle" \
font-family="monospace" font-size="12" fill="#999">
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

        # Execute the Python-based Mermaid generation
        cmd_parts = ["python3", "-c", python_script]

        return self.run_command(command=cmd_parts, session_key="mermaid_generation")

    def run_python_script(
        self,
        script_file: Path,
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute a Python script with optimized Docker execution."""
        try:
            script_rel = script_file.relative_to(self.workspace_dir)
        except ValueError:
            # Script is outside workspace (e.g., in temp directory during tests)
            # Check if it's accessible through a mounted volume at /workspace
            # Try to find the script in the workspace
            # Use the script name but with a fallback to copy/read approach
            pass

        docker_working_dir = "/workspace"

        if working_dir:
            try:
                work_rel = working_dir.relative_to(self.workspace_dir)
                docker_working_dir = f"/workspace/{work_rel}"
            except ValueError:
                docker_working_dir = "/workspace/output"

        # If script is not in workspace, we need to copy it or execute it differently
        try:
            script_rel = script_file.relative_to(self.workspace_dir)
            # Script is in workspace, use direct path
            return self.run_command(
                command=["python", f"/workspace/{script_rel}"],
                working_dir=docker_working_dir,
                environment=environment,
                session_key="python_execution",
            )
        except ValueError:
            # Script is outside workspace, execute by reading content
            script_content = script_file.read_text(encoding="utf-8")
            return self.run_command(
                command=["python", "-c", script_content],
                working_dir=docker_working_dir,
                environment=environment,
                session_key="python_execution",
            )

    def run_r_script(
        self,
        script_file: Path,
        working_dir: Path | None = None,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute an R script with optimized Docker execution."""
        docker_working_dir = "/workspace"

        if working_dir:
            try:
                work_rel = working_dir.relative_to(self.workspace_dir)
                docker_working_dir = f"/workspace/{work_rel}"
            except ValueError:
                docker_working_dir = "/workspace/output"

        # If script is not in workspace, we need to copy it or execute it differently
        try:
            script_rel = script_file.relative_to(self.workspace_dir)
            # Script is in workspace, use direct path
            return self.run_command(
                command=["Rscript", f"/workspace/{script_rel}"],
                working_dir=docker_working_dir,
                environment=environment,
                session_key="r_execution",
            )
        except ValueError:
            # Script is outside workspace, execute by reading content
            script_content = script_file.read_text(encoding="utf-8")
            # Create a temporary file in the container and execute it
            temp_script = f"/tmp/{script_file.name}"
            # First write the script content to a temp file, then execute it
            import shlex

            escaped_content = shlex.quote(script_content)
            return self.run_command(
                command=[
                    "sh",
                    "-c",
                    f"echo {escaped_content} > {temp_script} && Rscript {temp_script}",
                ],
                working_dir=docker_working_dir,
                environment=environment,
                session_key="r_execution",
            )

    def run_latex_compilation(
        self, tex_file: Path, working_dir: Path | None = None, passes: int = 3
    ) -> list[subprocess.CompletedProcess]:
        """Run LaTeX compilation with multiple passes in Docker."""
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

        results = []
        session_key = "latex_compilation"

        for i in range(passes):
            result = self.run_command(
                command=["pdflatex", "-interaction=nonstopmode", tex_rel.name],
                working_dir=docker_working_dir,
                session_key=session_key,
            )
            results.append(result)

            # Run bibtex after first pass if bib file exists
            if i == 0:
                # Check for bib file in the working directory
                bib_file_name = "03_REFERENCES.bib"
                bib_result = self.run_command(
                    command=[
                        "sh",
                        "-c",
                        f"if [ -f {bib_file_name} ]; then bibtex {tex_rel.stem}; fi",
                    ],
                    working_dir=docker_working_dir,
                    session_key=session_key,
                )
                results.append(bib_result)

        return results

    def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            return False

    def pull_image(self, image: str | None = None, force_pull: bool = False) -> bool:
        """Pull the Docker image if not already available or force_pull is True."""
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
                    return True  # Image already available locally
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass  # Image not available locally, proceed with pull

        # Pull the latest version of the image
        try:
            result = subprocess.run(
                ["docker", "pull", target_image],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    def cleanup_all_sessions(self) -> None:
        """Clean up all active Docker sessions."""
        for session in self._active_sessions.values():
            session.cleanup()
        self._active_sessions.clear()

    def get_session_stats(self) -> dict[str, Any]:
        """Get statistics about active Docker sessions."""
        stats: dict[str, Any] = {
            "total_sessions": len(self._active_sessions),
            "active_sessions": sum(1 for s in self._active_sessions.values() if s.is_active()),
            "session_details": [],
        }

        for key, session in self._active_sessions.items():
            session_info = {
                "key": key,
                "container_id": session.container_id[:12],  # Short ID
                "image": session.image,
                "active": session.is_active(),
                "age_seconds": time.time() - session.created_at,
            }
            stats["session_details"].append(session_info)

        return stats

    def warmup_session(self, session_key: str, image: str | None = None, force_pull: bool = False) -> bool:
        """Pre-warm a Docker session for faster subsequent operations."""
        target_image = image or self.default_image

        # Ensure image is available (force pull if requested)
        if not self.pull_image(target_image, force_pull=force_pull):
            return False

        # Create session if it doesn't exist
        session = self._get_or_create_session(session_key, target_image)

        if session and session.is_active():
            # Run a simple health check to warm up the container
            try:
                result = self.run_command(command=["echo", "warmup"], session_key=session_key, timeout=10)
                return result.returncode == 0
            except Exception:
                return False

        return False

    def health_check_session(self, session_key: str) -> bool:
        """Check if a specific session is healthy and responsive."""
        if session_key not in self._active_sessions:
            return False

        session = self._active_sessions[session_key]
        if not session.is_active():
            return False

        try:
            result = self.run_command(command=["echo", "health_check"], session_key=session_key, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def initialize_common_sessions(self) -> dict[str, bool]:
        """Pre-initialize common Docker sessions for faster operations."""
        common_sessions = {
            "validation": self.warmup_session("validation"),
            "mermaid_generation": self.warmup_session("mermaid_generation"),
            "python_execution": self.warmup_session("python_execution"),
            "r_execution": self.warmup_session("r_execution"),
            "latex_compilation": self.warmup_session("latex_compilation"),
        }
        return common_sessions

    def get_container_info(self, session_key: str) -> dict[str, str] | None:
        """Get detailed information about a container session."""
        if session_key not in self._active_sessions:
            return None

        session = self._active_sessions[session_key]
        try:
            # Get container details
            inspect_cmd = [
                "docker",
                "container",
                "inspect",
                session.container_id,
                "--format",
                "{{json .}}",
            ]
            result = subprocess.run(inspect_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json

                container_info = json.loads(result.stdout)
                return {
                    "id": session.container_id[:12],
                    "image": session.image,
                    "status": container_info.get("State", {}).get("Status", "unknown"),
                    "created": container_info.get("Created", "unknown"),
                    "platform": container_info.get("Platform", "unknown"),
                }
        except Exception:
            pass

        return None

    def enable_aggressive_cleanup(self, enabled: bool = True) -> None:
        """Enable aggressive session cleanup for resource-constrained environments."""
        if enabled:
            self._session_timeout = 60  # 1 minute for aggressive cleanup
            self._max_sessions = 2  # Fewer concurrent sessions
            self.enable_session_reuse = False  # Disable session reuse
        else:
            self._session_timeout = 600  # 10 minutes default
            self._max_sessions = 5  # Normal concurrent sessions
            self.enable_session_reuse = True

    def get_resource_usage(self) -> dict[str, Any]:
        """Get Docker resource usage statistics."""
        stats = {
            "containers": {},
            "total_memory_mb": 0,
            "total_cpu_percent": 0.0,
            "warnings": [],
        }

        for key, session in self._active_sessions.items():
            if session.is_active():
                try:
                    # Get container stats
                    result = subprocess.run(
                        [
                            "docker",
                            "stats",
                            session.container_id,
                            "--no-stream",
                            "--format",
                            "{{json .}}",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    if result.returncode == 0 and result.stdout:
                        import json

                        container_stats = json.loads(result.stdout.strip())

                        # Parse memory usage
                        mem_usage = container_stats.get("MemUsage", "0MiB / 0MiB")
                        mem_parts = mem_usage.split(" / ")
                        if len(mem_parts) >= 1:
                            mem_current = self._parse_memory_str(mem_parts[0])
                            stats["total_memory_mb"] += mem_current

                        # Parse CPU usage
                        cpu_percent = container_stats.get("CPUPerc", "0%").rstrip("%")
                        try:
                            cpu_float = float(cpu_percent)
                            stats["total_cpu_percent"] += cpu_float
                        except ValueError:
                            pass

                        stats["containers"][key] = {
                            "memory_mb": mem_current,
                            "cpu_percent": cpu_float,
                            "container_id": session.container_id[:12],
                        }

                except Exception as e:
                    stats["warnings"].append(f"Failed to get stats for {key}: {e}")

        # Check for resource warnings
        if stats["total_memory_mb"] > 3072:  # Over 3GB
            stats["warnings"].append("High memory usage detected (>3GB)")
            self._resource_warnings += 1

        if stats["total_cpu_percent"] > 150:  # Over 150% CPU
            stats["warnings"].append("High CPU usage detected (>150%)")
            self._resource_warnings += 1

        # Auto-cleanup if too many warnings
        if self._resource_warnings > 5:
            self.enable_aggressive_cleanup(True)
            stats["warnings"].append("Enabled aggressive cleanup due to resource pressure")

        return stats

    def _parse_memory_str(self, mem_str: str) -> float:
        """Parse memory string like '512MiB' to MB float."""
        mem_str = mem_str.strip()
        if mem_str.endswith("GiB"):
            return float(mem_str[:-3]) * 1024
        elif mem_str.endswith("MiB"):
            return float(mem_str[:-3])
        elif mem_str.endswith("KiB"):
            return float(mem_str[:-3]) / 1024
        return 0.0

    def __del__(self):
        """Cleanup when manager is destroyed."""
        import contextlib

        with contextlib.suppress(Exception):
            self.cleanup_all_sessions()


# Global Docker manager instance
_docker_manager: DockerManager | None = None


def get_docker_manager(
    image: str | None = None,
    workspace_dir: Path | None = None,
    enable_session_reuse: bool = True,
    force_new: bool = False,
    memory_limit: str | None = None,
    cpu_limit: str | None = None,
) -> DockerManager:
    """Get or create the global Docker manager instance.

    Args:
        image: Docker image to use
        workspace_dir: Workspace directory
        enable_session_reuse: Whether to reuse Docker sessions
        force_new: Force creation of new manager
        memory_limit: Memory limit for containers (e.g., "2g")
        cpu_limit: CPU limit for containers (e.g., "2.0")
    """
    global _docker_manager

    if _docker_manager is None or force_new:
        if _docker_manager is not None and force_new:
            # Clean up existing manager before creating new one
            _docker_manager.cleanup_all_sessions()

        default_image = image or "henriqueslab/rxiv-maker-base:latest"

        # Get resource limits from environment or defaults
        memory = memory_limit or os.environ.get("RXIV_DOCKER_MEMORY", "2g")
        cpu = cpu_limit or os.environ.get("RXIV_DOCKER_CPU", "2.0")

        _docker_manager = DockerManager(
            default_image=default_image,
            workspace_dir=workspace_dir,
            enable_session_reuse=enable_session_reuse,
            memory_limit=memory,
            cpu_limit=cpu,
        )

    return _docker_manager


def cleanup_global_docker_manager() -> None:
    """Clean up the global Docker manager and all its sessions."""
    global _docker_manager
    if _docker_manager is not None:
        _docker_manager.cleanup_all_sessions()
        _docker_manager = None


def get_docker_stats() -> dict[str, Any] | None:
    """Get Docker session statistics from the global manager."""
    global _docker_manager
    if _docker_manager is not None:
        return _docker_manager.get_session_stats()
    return None
