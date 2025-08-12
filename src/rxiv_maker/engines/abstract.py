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
        self.container_id = container_id
        self.image = image
        self.workspace_dir = workspace_dir
        self.engine_type = engine_type
        self.created_at = None
        self._active = True

    def is_active(self) -> bool:
        """Check if the container is still running."""
        return self._active

    def cleanup(self) -> bool:
        """Stop and remove the container."""
        self._active = False
        return True


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

    @abstractmethod
    def check_available(self) -> bool:
        """Check if the container engine is available and running."""
        pass

    @abstractmethod
    def pull_image(self, image: Optional[str] = None, force_pull: bool = False) -> bool:
        """Pull a container image if not already available or force_pull is True."""
        pass

    @abstractmethod
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
        """Execute a command in a container with optimization.

        Args:
            command: Command to execute (string or list)
            image: Container image to use (defaults to default_image)
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
        pass

    @abstractmethod
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

        return self.run_command(command=["python3", "-c", python_script], session_key="mermaid_generation")

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

        try:
            script_rel = script_file.relative_to(self.workspace_dir)
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

        try:
            script_rel = script_file.relative_to(self.workspace_dir)
            return self.run_command(
                command=["Rscript", f"/workspace/{script_rel}"],
                working_dir=docker_working_dir,
                environment=environment,
                session_key="r_execution",
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
                session_key="r_execution",
            )

    def run_latex_compilation(
        self, tex_file: Path, working_dir: Optional[Path] = None, passes: int = 3
    ) -> List[subprocess.CompletedProcess]:
        """Run LaTeX compilation with multiple passes in container."""
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

    def cleanup_all_sessions(self) -> None:
        """Clean up all active container sessions."""
        for session in self._active_sessions.values():
            session.cleanup()
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
