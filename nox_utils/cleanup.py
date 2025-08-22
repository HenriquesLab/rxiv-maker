"""Shared cleanup utilities for Nox test sessions.

This module provides comprehensive cleanup functions for managing containers,
images, volumes, and disk space during testing to optimize resource usage
and prevent disk space issues.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class CleanupError(Exception):
    """Exception raised when cleanup operations fail."""

    pass


class DiskSpaceMonitor:
    """Monitor and report disk space usage."""

    @staticmethod
    def get_disk_usage(path: str = ".") -> Tuple[int, int, int]:
        """Get disk usage statistics for a path.

        Returns:
            Tuple of (total, used, free) space in bytes
        """
        try:
            total, used, free = shutil.disk_usage(path)
            return total, used, free
        except OSError as e:
            logger.warning(f"Could not get disk usage for {path}: {e}")
            return 0, 0, 0

    @staticmethod
    def format_bytes(bytes_size: int) -> str:
        """Format bytes into human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    @classmethod
    def report_disk_usage(cls, path: str = ".", prefix: str = "💾") -> str:
        """Generate disk usage report."""
        total, used, free = cls.get_disk_usage(path)
        if total == 0:
            return f"{prefix} Disk usage: Unable to determine"

        used_pct = (used / total) * 100
        free_pct = (free / total) * 100

        return (
            f"{prefix} Disk usage: {cls.format_bytes(used)} used "
            f"({used_pct:.1f}%), {cls.format_bytes(free)} free "
            f"({free_pct:.1f}%), {cls.format_bytes(total)} total"
        )

    @classmethod
    def check_disk_space_critical(cls, path: str = ".", threshold_pct: float = 90.0) -> bool:
        """Check if disk space usage is critical."""
        total, used, free = cls.get_disk_usage(path)
        if total == 0:
            return False

        used_pct = (used / total) * 100
        return used_pct >= threshold_pct


class ContainerEngine:
    """Base class for container engine operations."""

    def __init__(self, engine_type: str):
        self.engine_type = engine_type.lower()
        if self.engine_type not in ["docker", "podman"]:
            raise ValueError(f"Unsupported engine type: {engine_type}")

    def is_available(self) -> bool:
        """Check if the container engine is available."""
        try:
            result = subprocess.run([self.engine_type, "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_command(self, args: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a container engine command.

        Returns:
            Tuple of (success, stdout, stderr)
        """
        cmd = [self.engine_type] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def get_containers(self, all_containers: bool = True) -> List[Dict[str, str]]:
        """Get list of containers."""
        args = ["ps", "--format", "json"]
        if all_containers:
            args.append("--all")

        success, stdout, stderr = self.run_command(args)
        if not success:
            logger.warning(f"Failed to list containers: {stderr}")
            return []

        containers = []
        for line in stdout.strip().split("\n"):
            if line:
                try:
                    import json

                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return containers

    def get_images(self) -> List[Dict[str, str]]:
        """Get list of images."""
        args = ["images", "--format", "json"]
        success, stdout, stderr = self.run_command(args)
        if not success:
            logger.warning(f"Failed to list images: {stderr}")
            return []

        images = []
        for line in stdout.strip().split("\n"):
            if line:
                try:
                    import json

                    images.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return images

    def prune_containers(self, force: bool = True) -> Tuple[bool, str]:
        """Remove stopped containers."""
        args = ["container", "prune"]
        if force:
            args.append("--force")

        success, stdout, stderr = self.run_command(args, timeout=60)
        if success:
            logger.info(f"{self.engine_type}: Pruned stopped containers")
        else:
            logger.warning(f"{self.engine_type}: Failed to prune containers: {stderr}")

        return success, stdout if success else stderr

    def prune_images(self, force: bool = True, all_images: bool = False) -> Tuple[bool, str]:
        """Remove unused images."""
        args = ["image", "prune"]
        if force:
            args.append("--force")
        if all_images:
            args.append("--all")

        success, stdout, stderr = self.run_command(args, timeout=120)
        if success:
            logger.info(f"{self.engine_type}: Pruned unused images")
        else:
            logger.warning(f"{self.engine_type}: Failed to prune images: {stderr}")

        return success, stdout if success else stderr

    def prune_volumes(self, force: bool = True) -> Tuple[bool, str]:
        """Remove unused volumes."""
        args = ["volume", "prune"]
        if force:
            args.append("--force")

        success, stdout, stderr = self.run_command(args, timeout=60)
        if success:
            logger.info(f"{self.engine_type}: Pruned unused volumes")
        else:
            logger.warning(f"{self.engine_type}: Failed to prune volumes: {stderr}")

        return success, stdout if success else stderr

    def prune_networks(self, force: bool = True) -> Tuple[bool, str]:
        """Remove unused networks."""
        args = ["network", "prune"]
        if force:
            args.append("--force")

        success, stdout, stderr = self.run_command(args, timeout=60)
        if success:
            logger.info(f"{self.engine_type}: Pruned unused networks")
        else:
            logger.warning(f"{self.engine_type}: Failed to prune networks: {stderr}")

        return success, stdout if success else stderr

    def system_prune(self, force: bool = True, volumes: bool = False) -> Tuple[bool, str]:
        """Comprehensive system cleanup."""
        args = ["system", "prune"]
        if force:
            args.append("--force")
        if volumes:
            args.append("--volumes")

        success, stdout, stderr = self.run_command(args, timeout=180)
        if success:
            logger.info(f"{self.engine_type}: Performed system prune")
        else:
            logger.warning(f"{self.engine_type}: Failed to perform system prune: {stderr}")

        return success, stdout if success else stderr

    def stop_test_containers(self, name_pattern: str = "rxiv") -> Tuple[bool, int]:
        """Stop containers matching a name pattern."""
        containers = self.get_containers(all_containers=True)
        stopped_count = 0

        for container in containers:
            if name_pattern.lower() in container.get("Names", "").lower():
                container_id = container.get("ID", "")
                if container_id:
                    success, stdout, stderr = self.run_command(["stop", container_id], timeout=30)
                    if success:
                        stopped_count += 1
                        logger.info(f"{self.engine_type}: Stopped container {container_id[:12]}")
                    else:
                        logger.warning(f"{self.engine_type}: Failed to stop container {container_id[:12]}: {stderr}")

        return stopped_count > 0, stopped_count


class CleanupManager:
    """Comprehensive cleanup manager for test environments."""

    def __init__(self):
        self.engines = []
        self.disk_monitor = DiskSpaceMonitor()

        # Initialize available engines
        for engine_type in ["docker", "podman"]:
            try:
                engine = ContainerEngine(engine_type)
                if engine.is_available():
                    self.engines.append(engine)
                    logger.info(f"Initialized {engine_type} engine")
            except Exception as e:
                logger.warning(f"Failed to initialize {engine_type} engine: {e}")

    def pre_test_cleanup(self, aggressive: bool = False) -> Dict[str, any]:
        """Perform cleanup before running tests."""
        logger.info("🧹 Starting pre-test cleanup...")
        results = {
            "engines_cleaned": 0,
            "containers_stopped": 0,
            "disk_usage_before": self.disk_monitor.report_disk_usage(),
            "operations": [],
        }

        for engine in self.engines:
            engine_results = {"engine": engine.engine_type, "operations": []}

            # Stop test containers
            stopped_success, stopped_count = engine.stop_test_containers()
            if stopped_success:
                results["containers_stopped"] += stopped_count
                engine_results["operations"].append(f"Stopped {stopped_count} test containers")

            # Prune stopped containers
            prune_success, prune_msg = engine.prune_containers()
            if prune_success:
                engine_results["operations"].append("Pruned stopped containers")

            if aggressive:
                # More aggressive cleanup
                img_success, img_msg = engine.prune_images(all_images=False)
                if img_success:
                    engine_results["operations"].append("Pruned dangling images")

                vol_success, vol_msg = engine.prune_volumes()
                if vol_success:
                    engine_results["operations"].append("Pruned unused volumes")

            if engine_results["operations"]:
                results["engines_cleaned"] += 1
                results["operations"].append(engine_results)

        results["disk_usage_after"] = self.disk_monitor.report_disk_usage()
        logger.info("✅ Pre-test cleanup completed")
        return results

    def post_test_cleanup(self, aggressive: bool = True) -> Dict[str, any]:
        """Perform comprehensive cleanup after tests."""
        logger.info("🧹 Starting post-test cleanup...")
        results = {
            "engines_cleaned": 0,
            "total_operations": 0,
            "disk_usage_before": self.disk_monitor.report_disk_usage(),
            "operations": [],
        }

        for engine in self.engines:
            engine_results = {"engine": engine.engine_type, "operations": []}

            # Stop and remove test containers
            stopped_success, stopped_count = engine.stop_test_containers()
            if stopped_success:
                engine_results["operations"].append(f"Stopped {stopped_count} test containers")

            # Comprehensive system prune
            if aggressive:
                system_success, system_msg = engine.system_prune(volumes=True)
                if system_success:
                    engine_results["operations"].append("System prune with volumes")
                    results["total_operations"] += 1
            else:
                # Individual cleanup operations
                container_success, _ = engine.prune_containers()
                if container_success:
                    engine_results["operations"].append("Pruned containers")

                image_success, _ = engine.prune_images()
                if image_success:
                    engine_results["operations"].append("Pruned images")

                volume_success, _ = engine.prune_volumes()
                if volume_success:
                    engine_results["operations"].append("Pruned volumes")

                results["total_operations"] += sum([container_success, image_success, volume_success])

            if engine_results["operations"]:
                results["engines_cleaned"] += 1
                results["operations"].append(engine_results)

        results["disk_usage_after"] = self.disk_monitor.report_disk_usage()
        logger.info("✅ Post-test cleanup completed")
        return results

    def emergency_cleanup(self) -> Dict[str, any]:
        """Emergency cleanup when disk space is critical."""
        logger.warning("🚨 Starting emergency cleanup - disk space critical!")
        results = {"disk_usage_before": self.disk_monitor.report_disk_usage(), "emergency_actions": []}

        for engine in self.engines:
            # Stop all containers
            containers = engine.get_containers(all_containers=True)
            for container in containers:
                container_id = container.get("ID", "")
                if container_id:
                    engine.run_command(["stop", container_id], timeout=10)
                    engine.run_command(["rm", "-f", container_id], timeout=10)

            # Aggressive system prune
            engine.system_prune(force=True, volumes=True)

            # Remove all dangling/unused images
            engine.prune_images(force=True, all_images=True)

            results["emergency_actions"].append(f"Emergency cleanup: {engine.engine_type}")

        # Clean nox environments
        nox_dir = Path(".nox")
        if nox_dir.exists():
            try:
                shutil.rmtree(nox_dir)
                results["emergency_actions"].append("Removed .nox directory")
            except Exception as e:
                logger.warning(f"Failed to remove .nox directory: {e}")

        results["disk_usage_after"] = self.disk_monitor.report_disk_usage()
        logger.warning("🚨 Emergency cleanup completed")
        return results

    def report_cleanup_results(self, results: Dict[str, any], session_name: str = "") -> None:
        """Report cleanup results to console."""
        session_prefix = f"[{session_name}] " if session_name else ""

        print(f"\n🧹 {session_prefix}Cleanup Results:")
        print("=" * 50)

        if "disk_usage_before" in results and "disk_usage_after" in results:
            print(f"📊 Before: {results['disk_usage_before']}")
            print(f"📊 After:  {results['disk_usage_after']}")

        if "engines_cleaned" in results:
            print(f"🐳 Engines cleaned: {results['engines_cleaned']}")

        if "containers_stopped" in results:
            print(f"🛑 Containers stopped: {results['containers_stopped']}")

        if "total_operations" in results:
            print(f"⚙️  Total operations: {results['total_operations']}")

        if "operations" in results:
            for engine_op in results["operations"]:
                engine_name = engine_op["engine"].capitalize()
                print(f"  {engine_name}: {', '.join(engine_op['operations'])}")

        if "emergency_actions" in results:
            print("🚨 Emergency actions:")
            for action in results["emergency_actions"]:
                print(f"  - {action}")

        print("=" * 50)


# Global cleanup manager instance
cleanup_manager = CleanupManager()


def cleanup_containers_and_images(aggressive: bool = True, session_name: str = "") -> Dict[str, any]:
    """Convenience function for container and image cleanup."""
    return cleanup_manager.post_test_cleanup(aggressive=aggressive)


def check_and_cleanup_if_needed(threshold_pct: float = 85.0) -> bool:
    """Check disk space and cleanup if needed."""
    if DiskSpaceMonitor.check_disk_space_critical(threshold_pct=threshold_pct):
        logger.warning(f"Disk space usage above {threshold_pct}% - starting emergency cleanup")
        cleanup_manager.emergency_cleanup()
        return True
    return False
