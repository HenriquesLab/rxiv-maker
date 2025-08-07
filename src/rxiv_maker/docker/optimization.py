"""Docker optimization utilities for improved performance.

This module provides advanced Docker optimizations including:
- Build cache management
- Multi-stage build optimization
- Resource-aware container configuration
- Build context optimization
- Layer caching strategies
"""

import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.advanced_cache import AdvancedCache


class DockerBuildOptimizer:
    """Optimizes Docker builds with advanced caching and resource management."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize Docker build optimizer.

        Args:
            cache_dir: Directory for build caches
        """
        self.cache = AdvancedCache(name="docker_builds", max_memory_items=50, max_disk_size_mb=500, ttl_hours=72)
        self.build_context_cache = AdvancedCache(
            name="build_contexts", max_memory_items=20, max_disk_size_mb=200, ttl_hours=24
        )

    def get_optimal_build_args(self) -> Dict[str, str]:
        """Get optimal build arguments based on system resources."""
        # Detect system capabilities
        cpu_count = os.cpu_count() or 2
        memory_gb = self._get_available_memory_gb()

        # Optimal build arguments
        build_args = {"BUILDKIT_INLINE_CACHE": "1", "DOCKER_BUILDKIT": "1", "BUILDX_EXPERIMENTAL": "1"}

        # Adjust based on resources
        if cpu_count >= 4:
            build_args["MAKEFLAGS"] = f"-j{min(cpu_count, 8)}"

        if memory_gb >= 8:
            build_args["NODE_OPTIONS"] = "--max-old-space-size=4096"

        # Platform-specific optimizations
        system = platform.system().lower()
        if system == "darwin":  # macOS
            build_args["DOCKER_DEFAULT_PLATFORM"] = "linux/amd64"
        elif system == "linux":
            arch = platform.machine().lower()
            if "aarch64" in arch or "arm64" in arch:
                build_args["DOCKER_DEFAULT_PLATFORM"] = "linux/arm64"
            else:
                build_args["DOCKER_DEFAULT_PLATFORM"] = "linux/amd64"

        return build_args

    def _get_available_memory_gb(self) -> float:
        """Get available system memory in GB."""
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemAvailable:"):
                            kb = int(line.split()[1])
                            return kb / (1024 * 1024)
            elif platform.system() == "Darwin":  # macOS
                result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    bytes_mem = int(result.stdout.strip())
                    return bytes_mem / (1024**3)
            elif platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "OS", "get", "TotalVisibleMemorySize", "/value"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if line.startswith("TotalVisibleMemorySize="):
                            kb = int(line.split("=")[1])
                            return kb / (1024 * 1024)
        except Exception:
            pass

        # Fallback: assume 4GB
        return 4.0

    def optimize_build_context(self, context_dir: Path) -> Path:
        """Optimize build context by creating minimal context."""
        context_key = f"context_{context_dir.name}_{self._calculate_dir_hash(context_dir)}"

        # Check cache first
        cached_context = self.build_context_cache.get_data(context_key)
        if cached_context:
            cached_path = Path(cached_context)
            if cached_path.exists():
                return cached_path

        # Create optimized build context
        optimized_context = self._create_optimized_context(context_dir)

        # Cache the result
        self.build_context_cache.set(
            context_key, str(optimized_context), metadata={"original_dir": str(context_dir)}, content_based=True
        )

        return optimized_context

    def _calculate_dir_hash(self, directory: Path) -> str:
        """Calculate hash of directory contents for caching."""
        import hashlib

        hash_obj = hashlib.md5()

        # Include essential files only
        essential_files = ["Dockerfile", "requirements.txt", "pyproject.toml", "package.json", "Makefile"]

        for file_name in essential_files:
            file_path = directory / file_name
            if file_path.exists():
                hash_obj.update(file_name.encode())
                hash_obj.update(file_path.read_bytes())

        return hash_obj.hexdigest()[:12]

    def _create_optimized_context(self, source_dir: Path) -> Path:
        """Create optimized build context with minimal files."""
        # Create temporary directory for optimized context
        optimized_dir = Path(tempfile.mkdtemp(prefix="rxiv_build_"))

        # Essential files to include
        essential_files = [
            "Dockerfile",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "Makefile",
            ".dockerignore",
        ]

        # Copy essential files
        for file_name in essential_files:
            source_file = source_dir / file_name
            if source_file.exists():
                target_file = optimized_dir / file_name
                target_file.write_bytes(source_file.read_bytes())

        # Create optimized .dockerignore if it doesn't exist
        dockerignore_path = optimized_dir / ".dockerignore"
        if not dockerignore_path.exists():
            self._create_optimized_dockerignore(dockerignore_path)

        return optimized_dir

    def _create_optimized_dockerignore(self, dockerignore_path: Path) -> None:
        """Create optimized .dockerignore file."""
        ignore_patterns = [
            # Version control
            ".git",
            ".gitignore",
            ".gitmodules",
            # Python cache
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "*.so",
            ".coverage",
            ".pytest_cache",
            # Virtual environments
            "venv",
            ".venv",
            "env",
            ".env",
            # IDE and editor files
            ".vscode",
            ".idea",
            "*.swp",
            "*.swo",
            "*~",
            # Documentation build
            "docs/_build",
            "site",
            # Test and CI
            ".tox",
            ".nox",
            "coverage.xml",
            "*.log",
            # OS specific
            ".DS_Store",
            "Thumbs.db",
            # Build artifacts
            "build",
            "dist",
            "*.egg-info",
            # Cache directories
            "cache",
            ".cache",
            "output",
            # Large binary files
            "*.pdf",
            "*.zip",
            "*.tar.gz",
        ]

        dockerignore_path.write_text("\n".join(ignore_patterns))

    def get_optimized_build_command(
        self,
        dockerfile_path: Path,
        image_name: str,
        build_context: Optional[Path] = None,
        target_stage: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[str]:
        """Generate optimized Docker build command."""
        build_args = self.get_optimal_build_args()

        # Base command with BuildKit
        cmd = ["docker", "buildx", "build"]

        # Enable BuildKit features
        cmd.extend(["--platform", build_args.get("DOCKER_DEFAULT_PLATFORM", "linux/amd64")])

        if use_cache:
            # Use inline cache and registry cache if available
            cmd.extend(["--cache-from", f"type=registry,ref={image_name}:buildcache"])
            cmd.extend(["--cache-to", f"type=registry,ref={image_name}:buildcache,mode=max"])
            cmd.extend(["--cache-from", "type=gha"])  # GitHub Actions cache
            cmd.extend(["--cache-to", "type=gha,mode=max"])

        # Build arguments
        for key, value in build_args.items():
            if key not in ["DOCKER_DEFAULT_PLATFORM"]:  # Skip platform arg
                cmd.extend(["--build-arg", f"{key}={value}"])

        # Target stage for multi-stage builds
        if target_stage:
            cmd.extend(["--target", target_stage])

        # Dockerfile and context
        cmd.extend(["-f", str(dockerfile_path)])
        cmd.extend(["-t", image_name])

        # Build context (use optimized if provided)
        if build_context:
            cmd.append(str(build_context))
        else:
            cmd.append(str(dockerfile_path.parent))

        return cmd

    def estimate_build_time(self, dockerfile_path: Path, use_cache: bool = True) -> Tuple[int, str]:
        """Estimate Docker build time based on Dockerfile analysis.

        Returns:
            Tuple of (estimated_minutes, explanation)
        """
        if not dockerfile_path.exists():
            return 60, "Unknown Dockerfile"

        dockerfile_content = dockerfile_path.read_text()

        # Analyze Dockerfile for time-consuming operations
        base_time = 5  # Base build time
        factors = []

        # Check for expensive operations
        if "apt-get update" in dockerfile_content:
            base_time += 3
            factors.append("Package updates")

        if "install -y" in dockerfile_content:
            package_installs = dockerfile_content.count("install -y")
            base_time += package_installs * 2
            factors.append(f"{package_installs} package installations")

        if "pip install" in dockerfile_content:
            pip_installs = dockerfile_content.count("pip install")
            base_time += pip_installs * 3
            factors.append(f"{pip_installs} pip installations")

        if "npm install" in dockerfile_content:
            base_time += 5
            factors.append("Node.js dependencies")

        if "R -e" in dockerfile_content or "install.packages" in dockerfile_content:
            r_installs = dockerfile_content.count("install.packages")
            base_time += r_installs * 4
            factors.append(f"{r_installs} R package installations")

        if "texlive" in dockerfile_content.lower():
            base_time += 10
            factors.append("LaTeX installation")

        # Cache benefit
        if use_cache:
            base_time = int(base_time * 0.3)  # 70% reduction with cache
            factors.append("Cache enabled")

        explanation = "Time factors: " + ", ".join(factors) if factors else "Simple build"

        return max(base_time, 2), explanation

    def optimize_multi_stage_build(self, dockerfile_path: Path) -> Dict[str, any]:
        """Analyze and suggest optimizations for multi-stage builds."""
        if not dockerfile_path.exists():
            return {"error": "Dockerfile not found"}

        content = dockerfile_path.read_text()
        stages = []
        current_stage = None

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line.upper().startswith("FROM "):
                # Parse stage
                parts = line.split()
                if len(parts) >= 2:
                    base_image = parts[1]
                    stage_name = None
                    if "AS" in parts:
                        as_index = [p.upper() for p in parts].index("AS")
                        if as_index + 1 < len(parts):
                            stage_name = parts[as_index + 1]

                    current_stage = {
                        "name": stage_name or f"stage_{len(stages)}",
                        "base_image": base_image,
                        "line": line_num,
                        "instructions": [],
                        "size_estimate": 0,
                    }
                    stages.append(current_stage)
            elif current_stage:
                current_stage["instructions"].append(line)

                # Estimate layer size impact
                if line.upper().startswith("RUN "):
                    current_stage["size_estimate"] += 50  # MB estimate
                elif line.upper().startswith("COPY ") or line.upper().startswith("ADD "):
                    current_stage["size_estimate"] += 20

        # Generate optimization suggestions
        suggestions = []

        if len(stages) == 1:
            suggestions.append(
                {
                    "type": "multi_stage",
                    "priority": "medium",
                    "description": "Consider multi-stage build to reduce final image size",
                }
            )

        for stage in stages:
            # Check for optimization opportunities
            run_commands = [inst for inst in stage["instructions"] if inst.upper().startswith("RUN ")]

            if len(run_commands) > 5:
                suggestions.append(
                    {
                        "type": "layer_optimization",
                        "priority": "high",
                        "stage": stage["name"],
                        "description": f"Combine {len(run_commands)} RUN commands to reduce layers",
                    }
                )

            if stage["size_estimate"] > 200:  # > 200MB
                suggestions.append(
                    {
                        "type": "size_optimization",
                        "priority": "medium",
                        "stage": stage["name"],
                        "description": f"Large stage (~{stage['size_estimate']}MB), consider cleanup",
                    }
                )

        return {
            "stages": len(stages),
            "total_instructions": sum(len(s["instructions"]) for s in stages),
            "estimated_size_mb": sum(s["size_estimate"] for s in stages),
            "suggestions": suggestions,
            "analysis": stages,
        }

    def cleanup_build_cache(self, max_age_hours: int = 72) -> Dict[str, int]:
        """Clean up old build caches and temporary files."""
        cleaned = {"disk_cache": 0, "memory_cache": 0, "docker_cache": 0}

        # Clean advanced caches
        cleaned["disk_cache"] += self.cache._cleanup_expired()
        cleaned["disk_cache"] += self.build_context_cache._cleanup_expired()

        # Clean memory caches
        self.cache._memory_cache.clear()
        self.build_context_cache._memory_cache.clear()
        cleaned["memory_cache"] = 1

        # Clean Docker build cache (if available)
        try:
            result = subprocess.run(
                ["docker", "builder", "prune", "--filter", f"until={max_age_hours}h", "-f"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                cleaned["docker_cache"] = 1
        except Exception:
            pass

        return cleaned


class DockerResourceManager:
    """Manages Docker container resources and limits."""

    def __init__(self):
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict[str, any]:
        """Get system resource information."""
        info = {
            "cpu_count": os.cpu_count() or 2,
            "memory_gb": 4.0,  # Default fallback
            "platform": platform.system().lower(),
            "architecture": platform.machine().lower(),
        }

        # Get more accurate memory info
        optimizer = DockerBuildOptimizer()
        info["memory_gb"] = optimizer._get_available_memory_gb()

        return info

    def get_optimal_container_limits(self, operation_type: str = "general", priority: str = "normal") -> Dict[str, str]:
        """Get optimal container resource limits.

        Args:
            operation_type: Type of operation (pdf_build, figure_gen, validation, etc.)
            priority: Resource priority (low, normal, high)

        Returns:
            Dictionary with Docker resource limit arguments
        """
        # Base limits
        cpu_limit = self.system_info["cpu_count"]
        memory_limit_gb = self.system_info["memory_gb"]

        # Adjust for operation type
        if operation_type == "pdf_build":
            # LaTeX builds are CPU-intensive but don't need much memory
            cpu_limit = min(cpu_limit, 4)
            memory_limit_gb = min(memory_limit_gb * 0.6, 3.0)

        elif operation_type == "figure_gen":
            # Figure generation can be memory-intensive (R, Python plots)
            cpu_limit = min(cpu_limit, 2)
            memory_limit_gb = min(memory_limit_gb * 0.8, 4.0)

        elif operation_type == "validation":
            # Validation is lightweight
            cpu_limit = min(cpu_limit, 2)
            memory_limit_gb = min(memory_limit_gb * 0.3, 2.0)

        elif operation_type == "batch":
            # Batch operations can use more resources
            cpu_limit = max(cpu_limit - 1, 1)  # Leave one CPU for system
            memory_limit_gb = memory_limit_gb * 0.9

        # Adjust for priority
        if priority == "low":
            cpu_limit = max(cpu_limit // 2, 1)
            memory_limit_gb = memory_limit_gb * 0.5
        elif priority == "high":
            cpu_limit = min(cpu_limit * 1.5, self.system_info["cpu_count"])
            memory_limit_gb = min(memory_limit_gb * 1.2, self.system_info["memory_gb"])

        # Convert to Docker format
        limits = {}

        if cpu_limit < self.system_info["cpu_count"]:
            limits["cpus"] = str(cpu_limit)

        if memory_limit_gb < self.system_info["memory_gb"]:
            limits["memory"] = f"{int(memory_limit_gb)}g"

        # Add swap limit to prevent memory issues
        limits["memory-swap"] = f"{int(memory_limit_gb * 1.5)}g"

        # Add additional constraints for CI environments
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            limits["cpus"] = "2"  # GitHub Actions limit
            limits["memory"] = "3.5g"  # Conservative for CI
            limits["memory-swap"] = "4g"

        return limits

    def get_docker_run_args(
        self, operation_type: str = "general", priority: str = "normal", additional_args: Optional[List[str]] = None
    ) -> List[str]:
        """Get complete docker run arguments with optimal resource limits."""
        args = []

        # Get resource limits
        limits = self.get_optimal_container_limits(operation_type, priority)

        # Add resource limit arguments
        for key, value in limits.items():
            args.extend([f"--{key}", value])

        # Add security and performance options
        args.extend(
            [
                "--rm",  # Auto-remove container
                "--init",  # Use init process
                "--security-opt",
                "no-new-privileges",  # Security
            ]
        )

        # Add platform-specific optimizations
        if self.system_info["platform"] == "linux":
            args.extend(["--tmpfs", "/tmp:rw,noexec,nosuid,size=1g"])

        # Add additional arguments if provided
        if additional_args:
            args.extend(additional_args)

        return args
