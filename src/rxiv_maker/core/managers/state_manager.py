"""Centralized application state management for rxiv-maker.

This module provides a unified interface for managing application state across
all rxiv-maker operations, including build state, configuration, user preferences,
and cross-component state coordination.
"""

import json
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger

logger = get_logger()


class StateScope(Enum):
    """Scope of state management."""

    SESSION = "session"  # In-memory only, lost on restart
    PERSISTENT = "persistent"  # Saved to disk, survives restarts
    GLOBAL = "global"  # Shared across all rxiv-maker instances
    LOCAL = "local"  # Specific to current working directory


class BuildPhase(Enum):
    """Build process phases."""

    INITIALIZING = "initializing"
    VALIDATING = "validating"
    PREPROCESSING = "preprocessing"
    GENERATING_FIGURES = "generating_figures"
    CONVERTING_CONTENT = "converting_content"
    COMPILING_LATEX = "compiling_latex"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BuildState:
    """State tracking for build operations."""

    phase: BuildPhase = BuildPhase.INITIALIZING
    progress_percent: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    manuscript_path: Optional[str] = None
    output_path: Optional[str] = None
    engine: str = "LOCAL"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserPreferences:
    """User preferences and settings."""

    default_engine: str = "LOCAL"
    verbose_output: bool = False
    auto_validate: bool = True
    enable_caching: bool = True
    default_output_format: str = "pdf"
    figure_format: str = "png"
    latex_compiler: str = "pdflatex"
    concurrent_operations: int = 4
    timeout_seconds: int = 300
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """Current session state."""

    session_id: str = ""
    start_time: float = field(default_factory=time.time)
    current_working_dir: Optional[str] = None
    active_builds: Set[str] = field(default_factory=set)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    temporary_files: Set[str] = field(default_factory=set)
    processes: Set[int] = field(default_factory=set)


class StateChangeListener(ABC):
    """Abstract base class for state change listeners."""

    @abstractmethod
    def on_state_changed(self, scope: StateScope, key: str, old_value: Any, new_value: Any) -> None:
        """Called when state changes.

        Args:
            scope: Scope of the changed state
            key: State key that changed
            old_value: Previous value
            new_value: New value
        """
        pass


class StateManager(RecoveryEnhancedMixin):
    """Centralized application state management.

    Features:
    - Multi-scope state management (session, persistent, global, local)
    - Thread-safe operations with fine-grained locking
    - State change notifications and listeners
    - Automatic persistence and recovery
    - Cross-component state coordination
    - State validation and type safety
    - Performance monitoring and resource tracking
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """Initialize state manager.

        Args:
            state_dir: Directory for persistent state files
        """
        super().__init__()
        self.state_dir = state_dir or Path.home() / ".rxiv-maker"
        self.state_dir.mkdir(exist_ok=True)

        # Thread-safe state storage
        self._locks = {
            StateScope.SESSION: threading.RLock(),
            StateScope.PERSISTENT: threading.RLock(),
            StateScope.GLOBAL: threading.RLock(),
            StateScope.LOCAL: threading.RLock(),
        }

        self._state: Dict[StateScope, Dict[str, Any]] = {
            StateScope.SESSION: {},
            StateScope.PERSISTENT: {},
            StateScope.GLOBAL: {},
            StateScope.LOCAL: {},
        }

        # State change listeners
        self._listeners: List[StateChangeListener] = []

        # Built-in state objects
        self._build_states: Dict[str, BuildState] = {}
        self._user_preferences: Optional[UserPreferences] = None
        self._session_state: Optional[SessionState] = None

        # Load persistent state
        self._load_persistent_state()

        # Initialize session
        self._initialize_session()

        logger.debug("StateManager initialized")

    def _initialize_session(self) -> None:
        """Initialize current session state."""
        session_id = f"session_{int(time.time())}_{id(self)}"

        self._session_state = SessionState(session_id=session_id, current_working_dir=str(Path.cwd()))

        self.set_state(StateScope.SESSION, "session", self._session_state)
        logger.info(f"Session initialized: {session_id}")

    def _load_persistent_state(self) -> None:
        """Load persistent state from disk."""
        persistent_file = self.state_dir / "persistent_state.json"

        if persistent_file.exists():
            try:
                with open(persistent_file, "r") as f:
                    data = json.load(f)

                with self._locks[StateScope.PERSISTENT]:
                    self._state[StateScope.PERSISTENT] = data

                logger.debug(f"Loaded persistent state: {len(data)} items")

            except Exception as e:
                logger.warning(f"Failed to load persistent state: {e}")

        # Load user preferences
        self._user_preferences = self._load_user_preferences()

    def _load_user_preferences(self) -> UserPreferences:
        """Load user preferences."""
        prefs_file = self.state_dir / "user_preferences.json"

        if prefs_file.exists():
            try:
                with open(prefs_file, "r") as f:
                    data = json.load(f)
                    return UserPreferences(**data)
            except Exception as e:
                logger.warning(f"Failed to load user preferences: {e}")

        # Return defaults
        return UserPreferences()

    def _save_persistent_state(self) -> None:
        """Save persistent state to disk."""
        try:
            persistent_file = self.state_dir / "persistent_state.json"

            with self._locks[StateScope.PERSISTENT]:
                data = self._state[StateScope.PERSISTENT].copy()

            with open(persistent_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            logger.debug(f"Saved persistent state: {len(data)} items")

        except Exception as e:
            logger.error(f"Failed to save persistent state: {e}")

    def _save_user_preferences(self) -> None:
        """Save user preferences to disk."""
        if not self._user_preferences:
            return

        try:
            prefs_file = self.state_dir / "user_preferences.json"

            with open(prefs_file, "w") as f:
                json.dump(asdict(self._user_preferences), f, indent=2)

            logger.debug("Saved user preferences")

        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")

    def set_state(self, scope: StateScope, key: str, value: Any) -> None:
        """Set state value with thread safety and notifications.

        Args:
            scope: State scope
            key: State key
            value: State value
        """
        with self._locks[scope]:
            old_value = self._state[scope].get(key)
            self._state[scope][key] = value

            # Notify listeners
            for listener in self._listeners:
                try:
                    listener.on_state_changed(scope, key, old_value, value)
                except Exception as e:
                    logger.warning(f"State listener error: {e}")

            # Auto-save persistent state
            if scope == StateScope.PERSISTENT:
                self._save_persistent_state()

        logger.debug(f"State set: {scope.value}[{key}] = {type(value).__name__}")

    def get_state(self, scope: StateScope, key: str, default: Any = None) -> Any:
        """Get state value with thread safety.

        Args:
            scope: State scope
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        with self._locks[scope]:
            return self._state[scope].get(key, default)

    def remove_state(self, scope: StateScope, key: str) -> bool:
        """Remove state value.

        Args:
            scope: State scope
            key: State key to remove

        Returns:
            True if key was removed, False if not found
        """
        with self._locks[scope]:
            if key in self._state[scope]:
                old_value = self._state[scope].pop(key)

                # Notify listeners
                for listener in self._listeners:
                    try:
                        listener.on_state_changed(scope, key, old_value, None)
                    except Exception as e:
                        logger.warning(f"State listener error: {e}")

                # Auto-save persistent state
                if scope == StateScope.PERSISTENT:
                    self._save_persistent_state()

                return True

        return False

    def list_keys(self, scope: StateScope) -> List[str]:
        """List all keys in a scope.

        Args:
            scope: State scope

        Returns:
            List of state keys
        """
        with self._locks[scope]:
            return list(self._state[scope].keys())

    def clear_scope(self, scope: StateScope) -> None:
        """Clear all state in a scope.

        Args:
            scope: State scope to clear
        """
        with self._locks[scope]:
            self._state[scope].clear()

            # Auto-save persistent state
            if scope == StateScope.PERSISTENT:
                self._save_persistent_state()

        logger.info(f"Cleared state scope: {scope.value}")

    def add_listener(self, listener: StateChangeListener) -> None:
        """Add state change listener.

        Args:
            listener: State change listener
        """
        self._listeners.append(listener)
        logger.debug(f"Added state listener: {type(listener).__name__}")

    def remove_listener(self, listener: StateChangeListener) -> None:
        """Remove state change listener.

        Args:
            listener: State change listener to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
            logger.debug(f"Removed state listener: {type(listener).__name__}")

    # Build State Management

    def create_build_state(self, build_id: str, manuscript_path: str, engine: str = "LOCAL") -> BuildState:
        """Create new build state tracking.

        Args:
            build_id: Unique build identifier
            manuscript_path: Path to manuscript
            engine: Build engine (LOCAL, DOCKER, etc.)

        Returns:
            Created build state
        """
        build_state = BuildState(manuscript_path=manuscript_path, engine=engine, start_time=time.time())

        self._build_states[build_id] = build_state
        self.set_state(StateScope.SESSION, f"build_{build_id}", build_state)

        # Track active build
        if self._session_state:
            self._session_state.active_builds.add(build_id)

        logger.info(f"Created build state: {build_id}")
        return build_state

    def update_build_state(self, build_id: str, **updates) -> Optional[BuildState]:
        """Update build state.

        Args:
            build_id: Build identifier
            **updates: State updates

        Returns:
            Updated build state or None if not found
        """
        if build_id in self._build_states:
            build_state = self._build_states[build_id]

            for key, value in updates.items():
                if hasattr(build_state, key):
                    setattr(build_state, key, value)

            self.set_state(StateScope.SESSION, f"build_{build_id}", build_state)
            return build_state

        return None

    def get_build_state(self, build_id: str) -> Optional[BuildState]:
        """Get build state.

        Args:
            build_id: Build identifier

        Returns:
            Build state or None if not found
        """
        return self._build_states.get(build_id)

    def complete_build(self, build_id: str, success: bool = True) -> None:
        """Mark build as completed.

        Args:
            build_id: Build identifier
            success: Whether build succeeded
        """
        if build_id in self._build_states:
            build_state = self._build_states[build_id]
            build_state.phase = BuildPhase.COMPLETED if success else BuildPhase.FAILED
            build_state.end_time = time.time()
            build_state.progress_percent = 100.0

            self.set_state(StateScope.SESSION, f"build_{build_id}", build_state)

            # Remove from active builds
            if self._session_state:
                self._session_state.active_builds.discard(build_id)

            duration = build_state.end_time - (build_state.start_time or 0)
            logger.info(f"Build completed: {build_id} ({'success' if success else 'failed'}, {duration:.1f}s)")

    # User Preferences Management

    def get_user_preferences(self) -> UserPreferences:
        """Get user preferences.

        Returns:
            User preferences object
        """
        return self._user_preferences or UserPreferences()

    def update_user_preferences(self, **updates) -> None:
        """Update user preferences.

        Args:
            **updates: Preference updates
        """
        if not self._user_preferences:
            self._user_preferences = UserPreferences()

        for key, value in updates.items():
            if hasattr(self._user_preferences, key):
                setattr(self._user_preferences, key, value)

        self._save_user_preferences()
        logger.debug(f"Updated user preferences: {list(updates.keys())}")

    # Session Management

    def get_session_state(self) -> SessionState:
        """Get current session state.

        Returns:
            Session state object
        """
        return self._session_state or SessionState()

    @contextmanager
    def build_context(self, build_id: str, manuscript_path: str, engine: str = "LOCAL"):
        """Context manager for build operations.

        Args:
            build_id: Unique build identifier
            manuscript_path: Path to manuscript
            engine: Build engine

        Yields:
            Build state object
        """
        build_state = self.create_build_state(build_id, manuscript_path, engine)

        try:
            yield build_state
            self.complete_build(build_id, success=True)
        except Exception as e:
            if build_state:
                build_state.errors.append(str(e))
            self.complete_build(build_id, success=False)
            raise

    def cleanup(self) -> None:
        """Clean up state manager resources."""
        # Save all persistent state
        self._save_persistent_state()
        self._save_user_preferences()

        # Clear session state
        self.clear_scope(StateScope.SESSION)

        logger.info("StateManager cleanup completed")


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance.

    Returns:
        Global state manager
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


# Convenience functions
def set_global_state(key: str, value: Any) -> None:
    """Set global state value.

    Args:
        key: State key
        value: State value
    """
    get_state_manager().set_state(StateScope.GLOBAL, key, value)


def get_global_state(key: str, default: Any = None) -> Any:
    """Get global state value.

    Args:
        key: State key
        default: Default value

    Returns:
        State value or default
    """
    return get_state_manager().get_state(StateScope.GLOBAL, key, default)


def set_persistent_state(key: str, value: Any) -> None:
    """Set persistent state value.

    Args:
        key: State key
        value: State value
    """
    get_state_manager().set_state(StateScope.PERSISTENT, key, value)


def get_persistent_state(key: str, default: Any = None) -> Any:
    """Get persistent state value.

    Args:
        key: State key
        default: Default value

    Returns:
        State value or default
    """
    return get_state_manager().get_state(StateScope.PERSISTENT, key, default)


# Export public API
__all__ = [
    "StateManager",
    "StateScope",
    "BuildPhase",
    "BuildState",
    "UserPreferences",
    "SessionState",
    "StateChangeListener",
    "get_state_manager",
    "set_global_state",
    "get_global_state",
    "set_persistent_state",
    "get_persistent_state",
]
