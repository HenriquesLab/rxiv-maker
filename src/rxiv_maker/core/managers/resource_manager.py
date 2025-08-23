"""Centralized resource lifecycle management for rxiv-maker.

This module provides unified resource management including temporary files,
processes, containers, file handles, and memory monitoring with automatic
cleanup and error recovery.
"""

import atexit
import os
import shutil
import subprocess
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger

logger = get_logger()


class ResourceType(Enum):
    """Types of resources that can be managed."""

    TEMP_FILE = "temp_file"
    TEMP_DIRECTORY = "temp_directory"
    PROCESS = "process"
    CONTAINER = "container"
    FILE_HANDLE = "file_handle"
    NETWORK_CONNECTION = "network_connection"
    CUSTOM = "custom"


class ResourceStatus(Enum):
    """Resource lifecycle status."""

    CREATED = "created"
    ACTIVE = "active"
    CLEANING = "cleaning"
    CLEANED = "cleaned"
    FAILED = "failed"


@dataclass
class ResourceInfo:
    """Information about a managed resource."""

    resource_id: str
    resource_type: ResourceType
    resource: Any
    status: ResourceStatus = ResourceStatus.CREATED
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    cleanup_function: Optional[Callable[[Any], bool]] = None
    cleanup_priority: int = 0  # Higher priority cleaned first


@dataclass
class ResourceUsage:
    """Current resource usage metrics."""

    memory_mb: float
    cpu_percent: float
    disk_usage_gb: float
    open_files: int
    running_processes: int
    temporary_files: int
    containers: int
    timestamp: float = field(default_factory=time.time)


class ResourceCleaner(ABC):
    """Abstract base class for resource cleaners."""

    @abstractmethod
    def cleanup(self, resource: Any, metadata: Dict[str, Any]) -> bool:
        """Clean up a resource.

        Args:
            resource: The resource to clean up
            metadata: Resource metadata

        Returns:
            True if cleanup was successful
        """
        pass

    @abstractmethod
    def can_handle(self, resource_type: ResourceType) -> bool:
        """Check if this cleaner can handle the resource type.

        Args:
            resource_type: Type of resource

        Returns:
            True if this cleaner can handle the resource type
        """
        pass


class TempFileCleaner(ResourceCleaner):
    """Cleaner for temporary files and directories."""

    def cleanup(self, resource: Any, metadata: Dict[str, Any]) -> bool:
        """Clean up temporary file or directory."""
        try:
            path = Path(resource)
            if path.exists():
                if path.is_file():
                    path.unlink()
                    logger.debug(f"Removed temporary file: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    logger.debug(f"Removed temporary directory: {path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {resource}: {e}")
            return False

    def can_handle(self, resource_type: ResourceType) -> bool:
        """Check if can handle temp files/directories."""
        return resource_type in [ResourceType.TEMP_FILE, ResourceType.TEMP_DIRECTORY]


class ProcessCleaner(ResourceCleaner):
    """Cleaner for processes."""

    def cleanup(self, resource: Any, metadata: Dict[str, Any]) -> bool:
        """Clean up process."""
        try:
            if isinstance(resource, subprocess.Popen):
                if resource.poll() is None:  # Process still running
                    # Try graceful termination first
                    resource.terminate()
                    try:
                        resource.wait(timeout=5)
                        logger.debug(f"Process {resource.pid} terminated gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if termination fails
                        resource.kill()
                        resource.wait()
                        logger.warning(f"Process {resource.pid} force killed")
                return True
            elif isinstance(resource, int):  # PID
                try:
                    process = psutil.Process(resource)
                    process.terminate()
                    process.wait(timeout=5)
                    logger.debug(f"Process {resource} terminated")
                except psutil.TimeoutExpired:
                    process.kill()
                    logger.warning(f"Process {resource} force killed")
                return True
        except (ProcessLookupError, psutil.NoSuchProcess):
            # Process already dead
            return True
        except Exception as e:
            logger.warning(f"Failed to clean up process {resource}: {e}")
            return False

        # If resource is not a recognized process type, consider it already cleaned
        return True

    def can_handle(self, resource_type: ResourceType) -> bool:
        """Check if can handle processes."""
        return resource_type == ResourceType.PROCESS


class ContainerCleaner(ResourceCleaner):
    """Cleaner for containers."""

    def cleanup(self, resource: Any, metadata: Dict[str, Any]) -> bool:
        """Clean up container."""
        try:
            container_id = str(resource)
            engine = metadata.get("engine", "docker")

            # Check if container exists and is running
            result = subprocess.run(
                [engine, "ps", "-q", "--filter", f"id={container_id}"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                # Container is running, stop it
                subprocess.run([engine, "stop", container_id], capture_output=True, timeout=30)
                logger.debug(f"Stopped {engine} container: {container_id}")

            # Remove container
            subprocess.run([engine, "rm", "-f", container_id], capture_output=True, timeout=10)
            logger.debug(f"Removed {engine} container: {container_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to clean up container {resource}: {e}")
            return False

    def can_handle(self, resource_type: ResourceType) -> bool:
        """Check if can handle containers."""
        return resource_type == ResourceType.CONTAINER


class FileHandleCleaner(ResourceCleaner):
    """Cleaner for file handles."""

    def cleanup(self, resource: Any, metadata: Dict[str, Any]) -> bool:
        """Clean up file handle."""
        try:
            if hasattr(resource, "close"):
                resource.close()
                logger.debug(f"Closed file handle: {resource}")
            return True
        except Exception as e:
            logger.warning(f"Failed to close file handle {resource}: {e}")
            return False

    def can_handle(self, resource_type: ResourceType) -> bool:
        """Check if can handle file handles."""
        return resource_type == ResourceType.FILE_HANDLE


class ResourceManager(RecoveryEnhancedMixin):
    """Centralized resource lifecycle management with automatic cleanup.

    Features:
    - Automatic registration and tracking of resources
    - Context manager support for automatic cleanup
    - Multiple cleanup strategies for different resource types
    - Resource usage monitoring
    - Error-resilient cleanup
    - Thread-safe operations
    """

    _instance: Optional["ResourceManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ResourceManager":
        """Singleton pattern to ensure single resource manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize resource manager."""
        if hasattr(self, "_initialized"):
            return

        super().__init__()
        self._initialized = True
        self.resources: Dict[str, ResourceInfo] = {}
        self.cleaners: List[ResourceCleaner] = [
            TempFileCleaner(),
            ProcessCleaner(),
            ContainerCleaner(),
            FileHandleCleaner(),
        ]

        # Thread safety
        self._resource_lock = threading.RLock()

        # Resource monitoring
        self._monitoring_enabled = False
        self._usage_history: List[ResourceUsage] = []

        # Cleanup state
        self._cleanup_in_progress = False
        self._atexit_registered = False

        logger.debug("ResourceManager initialized")

    def register_cleaner(self, cleaner: ResourceCleaner) -> None:
        """Register a custom resource cleaner.

        Args:
            cleaner: Custom resource cleaner
        """
        with self._resource_lock:
            self.cleaners.append(cleaner)
        logger.debug(f"Registered custom cleaner: {cleaner.__class__.__name__}")

    def register_resource(
        self,
        resource_id: str,
        resource: Any,
        resource_type: ResourceType,
        cleanup_function: Optional[Callable[[Any], bool]] = None,
        cleanup_priority: int = 0,
        **metadata,
    ) -> str:
        """Register a resource for management.

        Args:
            resource_id: Unique identifier for the resource
            resource: The resource object
            resource_type: Type of resource
            cleanup_function: Custom cleanup function
            cleanup_priority: Cleanup priority (higher = cleaned first)
            **metadata: Additional resource metadata

        Returns:
            Resource ID
        """
        with self._resource_lock:
            if resource_id in self.resources:
                logger.warning(f"Resource {resource_id} already registered, updating")

            resource_info = ResourceInfo(
                resource_id=resource_id,
                resource_type=resource_type,
                resource=resource,
                cleanup_function=cleanup_function,
                cleanup_priority=cleanup_priority,
                metadata=metadata,
            )

            self.resources[resource_id] = resource_info

            # Register atexit handler if first resource
            if not self._atexit_registered:
                atexit.register(self.cleanup_all)
                self._atexit_registered = True

        logger.debug(f"Registered resource: {resource_id} ({resource_type.value})")
        return resource_id

    def create_temp_file(
        self, suffix: str = "", prefix: str = "rxiv_", directory: Optional[Path] = None, cleanup_priority: int = 0
    ) -> Path:
        """Create and register a temporary file.

        Args:
            suffix: File suffix
            prefix: File prefix
            directory: Directory to create file in
            cleanup_priority: Cleanup priority

        Returns:
            Path to temporary file
        """
        fd, temp_path_str = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=str(directory) if directory else None)
        os.close(fd)  # Close the file descriptor

        temp_path = Path(temp_path_str)
        resource_id = f"temp_file_{temp_path.name}"

        self.register_resource(
            resource_id=resource_id,
            resource=temp_path,
            resource_type=ResourceType.TEMP_FILE,
            cleanup_priority=cleanup_priority,
            created_by="create_temp_file",
        )

        return temp_path

    def create_temp_directory(
        self, suffix: str = "", prefix: str = "rxiv_", directory: Optional[Path] = None, cleanup_priority: int = 0
    ) -> Path:
        """Create and register a temporary directory.

        Args:
            suffix: Directory suffix
            prefix: Directory prefix
            directory: Parent directory
            cleanup_priority: Cleanup priority

        Returns:
            Path to temporary directory
        """
        temp_dir = Path(tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(directory) if directory else None))

        resource_id = f"temp_dir_{temp_dir.name}"

        self.register_resource(
            resource_id=resource_id,
            resource=temp_dir,
            resource_type=ResourceType.TEMP_DIRECTORY,
            cleanup_priority=cleanup_priority,
            created_by="create_temp_directory",
        )

        return temp_dir

    def register_process(
        self, process: Union[subprocess.Popen, int], process_id: Optional[str] = None, cleanup_priority: int = 5
    ) -> str:
        """Register a process for management.

        Args:
            process: Process object or PID
            process_id: Optional custom process ID
            cleanup_priority: Cleanup priority

        Returns:
            Process resource ID
        """
        if isinstance(process, subprocess.Popen):
            pid = process.pid
            resource_id = process_id or f"process_{pid}"
        else:
            pid = process
            resource_id = process_id or f"process_{pid}"

        self.register_resource(
            resource_id=resource_id,
            resource=process,
            resource_type=ResourceType.PROCESS,
            cleanup_priority=cleanup_priority,
            pid=pid,
        )

        return resource_id

    def register_container(self, container_id: str, engine: str = "docker", cleanup_priority: int = 10) -> str:
        """Register a container for management.

        Args:
            container_id: Container ID
            engine: Container engine (docker/podman)
            cleanup_priority: Cleanup priority

        Returns:
            Container resource ID
        """
        resource_id = f"container_{container_id}"

        self.register_resource(
            resource_id=resource_id,
            resource=container_id,
            resource_type=ResourceType.CONTAINER,
            cleanup_priority=cleanup_priority,
            engine=engine,
        )

        return resource_id

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage metrics.

        Returns:
            Current resource usage
        """
        try:
            # Get system metrics
            memory_mb = psutil.virtual_memory().used / (1024 * 1024)
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Get disk usage for current directory
            disk_usage = shutil.disk_usage(".")
            disk_usage_gb = disk_usage.used / (1024 * 1024 * 1024)

            # Count open files for current process
            current_process = psutil.Process()
            open_files = len(current_process.open_files())

            # Count managed resources
            with self._resource_lock:
                running_processes = sum(
                    1
                    for r in self.resources.values()
                    if r.resource_type == ResourceType.PROCESS and r.status == ResourceStatus.ACTIVE
                )
                temporary_files = sum(
                    1
                    for r in self.resources.values()
                    if r.resource_type in [ResourceType.TEMP_FILE, ResourceType.TEMP_DIRECTORY]
                    and r.status == ResourceStatus.ACTIVE
                )
                containers = sum(
                    1
                    for r in self.resources.values()
                    if r.resource_type == ResourceType.CONTAINER and r.status == ResourceStatus.ACTIVE
                )

            return ResourceUsage(
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                disk_usage_gb=disk_usage_gb,
                open_files=open_files,
                running_processes=running_processes,
                temporary_files=temporary_files,
                containers=containers,
            )

        except Exception as e:
            logger.warning(f"Failed to get resource usage: {e}")
            return ResourceUsage(
                memory_mb=0.0,
                cpu_percent=0.0,
                disk_usage_gb=0.0,
                open_files=0,
                running_processes=0,
                temporary_files=0,
                containers=0,
            )

    def start_monitoring(self, interval: float = 30.0) -> None:
        """Start resource usage monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring_enabled:
            return

        self._monitoring_enabled = True

        def monitor():
            while self._monitoring_enabled:
                usage = self.get_resource_usage()
                self._usage_history.append(usage)

                # Keep only last 100 entries
                if len(self._usage_history) > 100:
                    self._usage_history.pop(0)

                time.sleep(interval)

        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()

        logger.debug(f"Started resource monitoring with {interval}s interval")

    def stop_monitoring(self) -> None:
        """Stop resource usage monitoring."""
        self._monitoring_enabled = False
        logger.debug("Stopped resource monitoring")

    def cleanup_resource(self, resource_id: str) -> bool:
        """Clean up a specific resource.

        Args:
            resource_id: ID of resource to clean up

        Returns:
            True if cleanup was successful
        """
        with self._resource_lock:
            if resource_id not in self.resources:
                logger.warning(f"Resource {resource_id} not found for cleanup")
                return False

            resource_info = self.resources[resource_id]

            if resource_info.status in [ResourceStatus.CLEANING, ResourceStatus.CLEANED]:
                return True

            resource_info.status = ResourceStatus.CLEANING

            try:
                # Try custom cleanup function first
                if resource_info.cleanup_function:
                    success = resource_info.cleanup_function(resource_info.resource)
                    if success:
                        resource_info.status = ResourceStatus.CLEANED
                        logger.debug(f"Custom cleanup successful for: {resource_id}")
                        return True

                # Try registered cleaners
                for cleaner in self.cleaners:
                    if cleaner.can_handle(resource_info.resource_type):
                        success = cleaner.cleanup(resource_info.resource, resource_info.metadata)
                        if success:
                            resource_info.status = ResourceStatus.CLEANED
                            logger.debug(f"Cleanup successful for: {resource_id}")
                            return True

                # No suitable cleaner found
                logger.warning(f"No cleaner found for resource {resource_id} ({resource_info.resource_type})")
                resource_info.status = ResourceStatus.FAILED
                return False

            except Exception as e:
                logger.error(f"Cleanup failed for resource {resource_id}: {e}")
                resource_info.status = ResourceStatus.FAILED
                return False

    def cleanup_all(self) -> Dict[str, bool]:
        """Clean up all registered resources.

        Returns:
            Dictionary mapping resource IDs to cleanup success status
        """
        if self._cleanup_in_progress:
            return {}

        self._cleanup_in_progress = True
        logger.info("Starting cleanup of all registered resources")

        results = {}

        try:
            with self._resource_lock:
                # Sort by cleanup priority (higher priority first)
                sorted_resources = sorted(self.resources.items(), key=lambda x: x[1].cleanup_priority, reverse=True)

            for resource_id, _ in sorted_resources:
                results[resource_id] = self.cleanup_resource(resource_id)

            # Clear resources after cleanup
            with self._resource_lock:
                cleaned_count = sum(1 for success in results.values() if success)
                total_count = len(results)

                logger.info(f"Cleanup completed: {cleaned_count}/{total_count} resources cleaned successfully")

                # Keep failed resources for debugging
                self.resources = {
                    rid: rinfo for rid, rinfo in self.resources.items() if rinfo.status == ResourceStatus.FAILED
                }

        finally:
            self._cleanup_in_progress = False

        return results

    def get_resource_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered resources.

        Returns:
            Dictionary with resource status information
        """
        with self._resource_lock:
            return {
                rid: {
                    "type": rinfo.resource_type.value,
                    "status": rinfo.status.value,
                    "created_at": rinfo.created_at,
                    "metadata": rinfo.metadata,
                }
                for rid, rinfo in self.resources.items()
            }

    @contextmanager
    def managed_execution(self):
        """Context manager for automatic resource cleanup.

        Usage:
            with resource_manager.managed_execution():
                # Resources created here will be automatically cleaned up
                temp_file = resource_manager.create_temp_file()
                # ... do work ...
            # Automatic cleanup happens here
        """
        # Get current resource IDs before entering context
        with self._resource_lock:
            initial_resources = set(self.resources.keys())

        try:
            yield self
        finally:
            # Clean up only resources created during this context
            with self._resource_lock:
                context_resources = set(self.resources.keys()) - initial_resources

            if context_resources:
                logger.debug(f"Cleaning up {len(context_resources)} context resources")
                for resource_id in context_resources:
                    self.cleanup_resource(resource_id)


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance.

    Returns:
        Global resource manager
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


# Convenience functions
def create_temp_file(*args, **kwargs) -> Path:
    """Create a managed temporary file."""
    return get_resource_manager().create_temp_file(*args, **kwargs)


def create_temp_directory(*args, **kwargs) -> Path:
    """Create a managed temporary directory."""
    return get_resource_manager().create_temp_directory(*args, **kwargs)


def register_process(*args, **kwargs) -> str:
    """Register a process for management."""
    return get_resource_manager().register_process(*args, **kwargs)


def register_container(*args, **kwargs) -> str:
    """Register a container for management."""
    return get_resource_manager().register_container(*args, **kwargs)


@contextmanager
def managed_resources():
    """Context manager for automatic resource cleanup."""
    with get_resource_manager().managed_execution():
        yield
