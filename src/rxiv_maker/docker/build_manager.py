"""Unified Docker Build Manager for Rxiv-Maker.

This module consolidates the functionality of build-accelerated.sh and build-safe.sh
into a single, comprehensive Python solution with better cross-platform compatibility
and maintainability.

Features:
- Speed-optimized builds with BuildKit, caching, and proxy support
- Safe builds with resource monitoring, timeouts, and graceful error handling
- Cross-platform compatibility
- Integrated logging and progress reporting
- Automatic build verification and cleanup
"""

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.logging_config import get_logger
from ..utils.platform import platform_detector
from .optimization import DockerBuildOptimizer, DockerResourceManager

logger = get_logger()


class DockerBuildMode:
    """Build mode configuration."""

    ACCELERATED = "accelerated"
    SAFE = "safe"
    BALANCED = "balanced"


class DockerBuildManager:
    """Unified Docker build manager with acceleration and safety features."""

    def __init__(
        self,
        mode: str = DockerBuildMode.BALANCED,
        image_name: str = "henriqueslab/rxiv-maker-base:latest",
        dockerfile_path: Optional[Path] = None,
        build_context: Optional[Path] = None,
        max_build_time: int = 7200,  # 2 hours
        use_proxy: bool = True,
        use_buildkit: bool = True,
        enable_verification: bool = True,
        cleanup_on_success: bool = True,
        verbose: bool = False,
    ):
        """Initialize Docker build manager.

        Args:
            mode: Build mode (accelerated, safe, balanced)
            image_name: Docker image name and tag
            dockerfile_path: Path to Dockerfile (auto-detected if None)
            build_context: Build context directory (current dir if None)
            max_build_time: Maximum build time in seconds
            use_proxy: Enable squid-deb-proxy if available
            use_buildkit: Use Docker BuildKit
            enable_verification: Verify build after completion
            cleanup_on_success: Clean up resources on successful build
            verbose: Enable verbose logging
        """
        self.mode = mode
        self.image_name = image_name
        self.dockerfile_path = dockerfile_path or self._find_dockerfile()
        self.build_context = build_context or Path.cwd()
        self.max_build_time = max_build_time
        self.use_proxy = use_proxy
        self.use_buildkit = use_buildkit
        self.enable_verification = enable_verification
        self.cleanup_on_success = cleanup_on_success
        self.verbose = verbose

        # Initialize components
        self.optimizer = DockerBuildOptimizer()
        self.resource_manager = DockerResourceManager()
        self.platform = platform_detector

        # Build state
        self.build_start_time: Optional[float] = None
        self.build_log_file: Optional[Path] = None
        self.temp_files: List[Path] = []

        logger.info(f"Initialized Docker build manager in {mode} mode")

    def _find_dockerfile(self) -> Path:
        """Find Dockerfile in common locations."""
        search_paths = [
            Path("Dockerfile"),
            Path("docker/Dockerfile"),
            Path("src/docker/Dockerfile"),
            Path("src/docker/images/base/Dockerfile"),
        ]

        for path in search_paths:
            if path.exists():
                logger.debug(f"Found Dockerfile at {path}")
                return path.resolve()

        # Default fallback
        default_path = Path("src/docker/images/base/Dockerfile")
        logger.warning(f"Dockerfile not found, using default: {default_path}")
        return default_path

    def check_prerequisites(self) -> Dict[str, Any]:
        """Check system prerequisites for Docker build."""
        checks: Dict[str, Any] = {
            "docker_available": False,
            "buildkit_available": False,
            "dockerfile_exists": False,
            "disk_space_sufficient": False,
            "proxy_available": False,
            "system_resources": {},
            "warnings": [],
            "errors": [],
        }

        # Check Docker availability
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            checks["docker_available"] = result.returncode == 0
            if not checks["docker_available"]:
                checks["errors"].append("Docker is not available or not running")
        except Exception as e:
            checks["errors"].append(f"Docker check failed: {e}")

        # Check Docker daemon
        if checks["docker_available"]:
            try:
                result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    checks["errors"].append("Docker daemon is not responding")
                    checks["docker_available"] = False
            except Exception:
                checks["errors"].append("Cannot connect to Docker daemon")
                checks["docker_available"] = False

        # Check BuildKit availability
        if checks["docker_available"] and self.use_buildkit:
            try:
                result = subprocess.run(["docker", "buildx", "version"], capture_output=True, text=True, timeout=5)
                checks["buildkit_available"] = result.returncode == 0
            except Exception:
                checks["buildkit_available"] = False
                if self.use_buildkit:
                    checks["warnings"].append("BuildKit requested but not available")

        # Check Dockerfile exists
        checks["dockerfile_exists"] = self.dockerfile_path.exists()
        if not checks["dockerfile_exists"]:
            checks["errors"].append(f"Dockerfile not found: {self.dockerfile_path}")

        # Check disk space (need at least 5GB)
        try:
            stat = shutil.disk_usage(self.build_context)
            available_gb = stat.free / (1024**3)
            checks["disk_space_sufficient"] = available_gb >= 5.0
            checks["system_resources"]["disk_space_gb"] = available_gb

            if not checks["disk_space_sufficient"]:
                checks["warnings"].append(f"Low disk space: {available_gb:.1f}GB available, 5GB+ recommended")
        except Exception as e:
            checks["warnings"].append(f"Could not check disk space: {e}")

        # Check proxy availability
        if self.use_proxy:
            try:
                result = subprocess.run(
                    ["docker", "ps", "--filter", "name=squid-deb-proxy"], capture_output=True, text=True, timeout=5
                )
                checks["proxy_available"] = "squid-deb-proxy" in result.stdout
            except Exception:
                checks["proxy_available"] = False

        # Get system resources
        checks["system_resources"].update(
            {
                "cpu_count": os.cpu_count() or 2,
                "memory_gb": self.optimizer._get_available_memory_gb(),
                "platform": platform.system(),
                "architecture": platform.machine(),
            }
        )

        return checks

    def _setup_build_logging(self) -> Path:
        """Setup build logging."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_file = log_dir / f"docker-build-{timestamp}.log"

        self.build_log_file = log_file
        self.temp_files.append(log_file)

        # Initialize log file
        with open(log_file, "w") as f:
            f.write(f"Docker build log - {time.ctime()}\n")
            f.write(f"Mode: {self.mode}\n")
            f.write(f"Image: {self.image_name}\n")
            f.write(f"Dockerfile: {self.dockerfile_path}\n")
            f.write(f"Context: {self.build_context}\n")
            f.write("=" * 50 + "\n\n")

        return log_file

    def _get_build_command(self) -> List[str]:
        """Construct optimized Docker build command."""
        # Use BuildKit if available and requested
        if self.use_buildkit and subprocess.run(["docker", "buildx", "version"], capture_output=True).returncode == 0:
            cmd = ["docker", "buildx", "build"]
        else:
            cmd = ["docker", "build"]

        # Get optimal build arguments
        build_args = self.optimizer.get_optimal_build_args()

        # Add build arguments
        for key, value in build_args.items():
            if key not in ["DOCKER_DEFAULT_PLATFORM"]:
                cmd.extend(["--build-arg", f"{key}={value}"])

        # Platform specification
        platform_arg = build_args.get("DOCKER_DEFAULT_PLATFORM", "linux/amd64")
        if self.use_buildkit:
            cmd.extend(["--platform", platform_arg])

        # Progress reporting
        if self.verbose:
            cmd.extend(["--progress", "plain"])
        else:
            cmd.extend(["--progress", "auto"])

        # Caching strategy based on mode
        if self.mode == DockerBuildMode.ACCELERATED:
            # Aggressive caching for speed
            cmd.extend(["--cache-from", f"type=registry,ref={self.image_name}:buildcache"])
            cmd.extend(["--cache-to", f"type=registry,ref={self.image_name}:buildcache,mode=max"])

            if os.environ.get("GITHUB_ACTIONS"):
                cmd.extend(["--cache-from", "type=gha"])
                cmd.extend(["--cache-to", "type=gha,mode=max"])

        elif self.mode == DockerBuildMode.SAFE:
            # Conservative caching to avoid issues
            cmd.extend(["--no-cache"])

        else:  # BALANCED
            # Moderate caching
            cmd.extend(["--cache-from", f"type=registry,ref={self.image_name}:buildcache"])

        # Proxy configuration
        if self.use_proxy and self.check_prerequisites().get("proxy_available", False):
            cmd.extend(["--network", "squid"])
            cmd.extend(["--build-arg", "http_proxy=http://squid-deb-proxy:8000"])
            cmd.extend(["--build-arg", "https_proxy=http://squid-deb-proxy:8000"])

        # Resource limits based on mode
        if self.mode == DockerBuildMode.SAFE:
            limits = self.resource_manager.get_optimal_container_limits("pdf_build", "low")
            for key, value in limits.items():
                if key in ["memory", "cpus"]:
                    cmd.extend([f"--{key}", value])

        # Dockerfile and tag
        cmd.extend(["-f", str(self.dockerfile_path)])
        cmd.extend(["-t", self.image_name])

        # Build context
        cmd.append(str(self.build_context))

        return cmd

    def _execute_build_safe(self, build_cmd: List[str]) -> Tuple[bool, str]:
        """Execute build with safety monitoring."""
        logger.info("Starting safe Docker build execution")

        # Setup logging
        log_file = self._setup_build_logging()

        try:
            # Execute build with timeout
            process = subprocess.Popen(
                build_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True,
            )

            # Monitor build progress
            build_success = False
            error_message = ""

            try:
                # Wait for process with timeout
                stdout, _ = process.communicate(timeout=self.max_build_time)

                # Log output
                with open(log_file, "a") as f:
                    f.write(stdout)

                if process.returncode == 0:
                    build_success = True
                    logger.info("Docker build completed successfully")
                else:
                    error_message = f"Build failed with exit code {process.returncode}"
                    logger.error(error_message)

            except subprocess.TimeoutExpired:
                # Kill the process
                process.kill()
                process.wait()
                error_message = f"Build timed out after {self.max_build_time // 60} minutes"
                logger.error(error_message)

        except Exception as e:
            error_message = f"Build execution failed: {e}"
            logger.error(error_message)

        # Analyze build log for common issues
        if not build_success and log_file.exists():
            log_content = log_file.read_text()

            if "No space left on device" in log_content:
                error_message += " (No space left on device)"
            elif "killed" in log_content.lower():
                error_message += " (Process killed - likely out of memory)"
            elif "permission denied" in log_content.lower():
                error_message += " (Permission denied)"

        return build_success, error_message

    def _execute_build_accelerated(self, build_cmd: List[str]) -> Tuple[bool, str]:
        """Execute build with acceleration optimizations."""
        logger.info("Starting accelerated Docker build execution")

        # Setup logging
        log_file = self._setup_build_logging()

        try:
            # Execute build with real-time output
            with open(log_file, "a") as f:
                result = subprocess.run(
                    build_cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=self.max_build_time,
                )

            if result.returncode == 0:
                logger.info("Accelerated Docker build completed successfully")
                return True, ""
            else:
                error_msg = f"Build failed with exit code {result.returncode}"
                logger.error(error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = f"Build timed out after {self.max_build_time // 60} minutes"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Build execution failed: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _verify_build(self) -> Tuple[bool, str]:
        """Verify the built Docker image."""
        if not self.enable_verification:
            return True, "Verification skipped"

        logger.info("Verifying Docker build")

        try:
            # Check if image exists
            result = subprocess.run(
                ["docker", "image", "inspect", self.image_name], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                return False, "Image not found after build"

            # Basic functionality test
            test_cmd = [
                "docker",
                "run",
                "--rm",
                self.image_name,
                "python3",
                "-c",
                "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor} OK')",
            ]

            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                logger.info("Build verification passed")
                return True, "Verification successful"
            else:
                return False, f"Verification failed: {result.stderr}"

        except Exception as e:
            return False, f"Verification error: {e}"

    def _get_image_info(self) -> Dict[str, Any]:
        """Get information about the built image."""
        info = {"size": "unknown", "created": "unknown", "id": "unknown"}

        try:
            result = subprocess.run(
                ["docker", "images", self.image_name, "--format", "json"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and result.stdout:
                import json

                data = json.loads(result.stdout.strip().split("\n")[0])
                info.update(
                    {
                        "size": data.get("Size", "unknown"),
                        "created": data.get("CreatedSince", "unknown"),
                        "id": data.get("ID", "unknown")[:12],
                    }
                )
        except Exception:
            pass

        return info

    def _cleanup_resources(self) -> None:
        """Clean up temporary resources."""
        if not self.cleanup_on_success:
            return

        logger.debug("Cleaning up build resources")

        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    if temp_file.is_file():
                        temp_file.unlink()
                    elif temp_file.is_dir():
                        shutil.rmtree(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_file}: {e}")

        # Clean Docker build cache if requested
        if self.mode == DockerBuildMode.SAFE:
            try:
                subprocess.run(["docker", "builder", "prune", "-f"], capture_output=True, timeout=30)
            except Exception:
                pass

    def build(self) -> Dict[str, Any]:
        """Execute Docker build with the configured mode and settings.

        Returns:
            Build result dictionary with success status, timing, and details
        """
        logger.info(f"Starting Docker build in {self.mode} mode")
        self.build_start_time = time.time()

        # Check prerequisites
        prereq_check = self.check_prerequisites()
        if prereq_check["errors"]:
            return {
                "success": False,
                "error": "Prerequisites not met: " + "; ".join(prereq_check["errors"]),
                "prerequisites": prereq_check,
                "build_time": 0,
            }

        # Log warnings
        for warning in prereq_check["warnings"]:
            logger.warning(warning)

        # Get build command
        try:
            build_cmd = self._get_build_command()
            logger.info(f"Build command: {' '.join(build_cmd)}")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to construct build command: {e}",
                "build_time": 0,
            }

        # Execute build based on mode
        if self.mode == DockerBuildMode.ACCELERATED:
            build_success, error_message = self._execute_build_accelerated(build_cmd)
        else:  # SAFE or BALANCED
            build_success, error_message = self._execute_build_safe(build_cmd)

        # Calculate build time
        build_duration = time.time() - self.build_start_time if self.build_start_time else 0
        build_minutes = int(build_duration // 60)
        build_seconds = int(build_duration % 60)

        # Verify build if successful
        verification_result = (True, "Skipped")
        if build_success:
            verification_result = self._verify_build()
            build_success = verification_result[0]

        # Get image information
        image_info = self._get_image_info() if build_success else {}

        # Prepare result
        result = {
            "success": build_success,
            "build_time": build_duration,
            "build_time_formatted": f"{build_minutes}m {build_seconds}s",
            "image_name": self.image_name,
            "image_info": image_info,
            "verification": {
                "enabled": self.enable_verification,
                "success": verification_result[0],
                "message": verification_result[1],
            },
            "mode": self.mode,
            "prerequisites": prereq_check,
        }

        if not build_success:
            result["error"] = error_message or verification_result[1]

        if self.build_log_file and self.build_log_file.exists():
            result["log_file"] = str(self.build_log_file)

        # Cleanup resources
        try:
            if build_success:
                self._cleanup_resources()
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

        # Log final result
        if build_success:
            logger.info(f"Docker build completed successfully in {result['build_time_formatted']}")
        else:
            logger.error(f"Docker build failed: {result.get('error', 'Unknown error')}")

        return result


def build_docker_image(
    mode: str = DockerBuildMode.BALANCED,
    image_name: str = "henriqueslab/rxiv-maker-base:latest",
    dockerfile_path: Optional[Path] = None,
    verbose: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Convenience function to build Docker image.

    Args:
        mode: Build mode (accelerated, safe, balanced)
        image_name: Docker image name and tag
        dockerfile_path: Path to Dockerfile
        verbose: Enable verbose logging
        **kwargs: Additional arguments for DockerBuildManager

    Returns:
        Build result dictionary
    """
    manager = DockerBuildManager(
        mode=mode, image_name=image_name, dockerfile_path=dockerfile_path, verbose=verbose, **kwargs
    )

    return manager.build()
