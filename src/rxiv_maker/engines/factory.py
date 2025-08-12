"""Factory for creating container engine instances."""

import os
from pathlib import Path
from typing import Dict, Optional, Type

from .abstract import AbstractContainerEngine
from .docker_engine import DockerEngine
from .podman_engine import PodmanEngine


class ContainerEngineFactory:
    """Factory class for creating container engine instances."""
    
    # Registry of available engines
    _engines: Dict[str, Type[AbstractContainerEngine]] = {
        "docker": DockerEngine,
        "podman": PodmanEngine,
    }
    
    @classmethod
    def create_engine(
        cls,
        engine_type: str,
        default_image: str = "henriqueslab/rxiv-maker-base:latest",
        workspace_dir: Optional[Path] = None,
        enable_session_reuse: bool = True,
        memory_limit: str = "2g",
        cpu_limit: str = "2.0",
        **kwargs,
    ) -> AbstractContainerEngine:
        """Create a container engine instance.
        
        Args:
            engine_type: Type of engine to create ('docker' or 'podman')
            default_image: Default container image to use
            workspace_dir: Workspace directory (defaults to current working directory)
            enable_session_reuse: Whether to reuse containers across operations
            memory_limit: Memory limit for containers (e.g., "2g", "512m")
            cpu_limit: CPU limit for containers (e.g., "2.0" for 2 cores)
            **kwargs: Additional arguments passed to the engine constructor
            
        Returns:
            Container engine instance
            
        Raises:
            ValueError: If engine_type is not supported
            RuntimeError: If the requested engine is not available
        """
        engine_type_lower = engine_type.lower()
        
        if engine_type_lower not in cls._engines:
            available_engines = list(cls._engines.keys())
            raise ValueError(
                f"Unsupported engine type: {engine_type}. "
                f"Available engines: {available_engines}"
            )
        
        engine_class = cls._engines[engine_type_lower]
        
        # Create engine instance
        engine = engine_class(
            default_image=default_image,
            workspace_dir=workspace_dir,
            enable_session_reuse=enable_session_reuse,
            memory_limit=memory_limit,
            cpu_limit=cpu_limit,
            **kwargs,
        )
        
        # Check if engine is available
        if not engine.check_available():
            raise RuntimeError(
                f"{engine_type.title()} is not available. "
                f"Please ensure {engine_type} is installed and running."
            )
        
        return engine
    
    @classmethod
    def get_default_engine(
        cls,
        workspace_dir: Optional[Path] = None,
        **kwargs,
    ) -> AbstractContainerEngine:
        """Get the default container engine based on environment and availability.
        
        Priority order:
        1. RXIV_ENGINE environment variable
        2. Docker if available
        3. Podman if available
        4. Raise error if no container engine is available
        
        Args:
            workspace_dir: Workspace directory (defaults to current working directory)
            **kwargs: Additional arguments passed to the engine constructor
            
        Returns:
            Container engine instance
            
        Raises:
            RuntimeError: If no container engines are available
        """
        # Check environment variable first
        env_engine = os.environ.get("RXIV_ENGINE", "").lower()
        if env_engine in cls._engines:
            try:
                return cls.create_engine(env_engine, workspace_dir=workspace_dir, **kwargs)
            except RuntimeError:
                # Engine specified in env var is not available, continue to auto-detect
                pass
        
        # Auto-detect available engines in priority order
        priority_engines = ["docker", "podman"]
        
        for engine_type in priority_engines:
            if engine_type in cls._engines:
                engine_class = cls._engines[engine_type]
                # Create a minimal instance just for availability check
                temp_engine = engine_class(workspace_dir=workspace_dir or Path.cwd())
                if temp_engine.check_available():
                    return cls.create_engine(engine_type, workspace_dir=workspace_dir, **kwargs)
        
        # No engines available
        available_engines = list(cls._engines.keys())
        raise RuntimeError(
            f"No container engines are available. "
            f"Please install one of: {available_engines}"
        )
    
    @classmethod
    def list_available_engines(cls) -> Dict[str, bool]:
        """List all available engines and their availability status.
        
        Returns:
            Dictionary mapping engine names to their availability status
        """
        availability = {}
        
        for engine_name, engine_class in cls._engines.items():
            try:
                # Create a minimal instance just for availability check
                temp_engine = engine_class()
                availability[engine_name] = temp_engine.check_available()
            except Exception:
                availability[engine_name] = False
        
        return availability
    
    @classmethod
    def register_engine(
        cls,
        engine_name: str,
        engine_class: Type[AbstractContainerEngine],
    ) -> None:
        """Register a new container engine type.
        
        Args:
            engine_name: Name of the engine
            engine_class: Engine class that inherits from AbstractContainerEngine
            
        Raises:
            ValueError: If engine_class doesn't inherit from AbstractContainerEngine
        """
        if not issubclass(engine_class, AbstractContainerEngine):
            raise ValueError(
                f"Engine class must inherit from AbstractContainerEngine, "
                f"got {engine_class.__name__}"
            )
        
        cls._engines[engine_name.lower()] = engine_class
    
    @classmethod
    def get_supported_engines(cls) -> list[str]:
        """Get a list of all supported engine names.
        
        Returns:
            List of supported engine names
        """
        return list(cls._engines.keys())


# Global factory instance for convenience
container_engine_factory = ContainerEngineFactory()


def get_container_engine(
    engine_type: Optional[str] = None,
    workspace_dir: Optional[Path] = None,
    **kwargs,
) -> AbstractContainerEngine:
    """Convenience function to get a container engine instance.
    
    Args:
        engine_type: Type of engine to create (None for auto-detection)
        workspace_dir: Workspace directory (defaults to current working directory)
        **kwargs: Additional arguments passed to the engine constructor
        
    Returns:
        Container engine instance
    """
    if engine_type:
        return container_engine_factory.create_engine(
            engine_type, workspace_dir=workspace_dir, **kwargs
        )
    else:
        return container_engine_factory.get_default_engine(
            workspace_dir=workspace_dir, **kwargs
        )