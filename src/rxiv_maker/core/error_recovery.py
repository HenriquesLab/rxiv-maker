"""Enhanced error recovery capabilities for rxiv-maker centralized components.

This module provides comprehensive error recovery strategies, rollback mechanisms,
circuit breakers, and fault tolerance patterns that coordinate across all
centralized managers to ensure system resilience.
"""

import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from .logging_config import get_logger

logger = get_logger()

T = TypeVar("T")


class RecoveryStrategy(Enum):
    """Error recovery strategy types."""

    RETRY = "retry"  # Retry the operation
    ROLLBACK = "rollback"  # Rollback to previous state
    FALLBACK = "fallback"  # Use alternative approach
    CIRCUIT_BREAK = "circuit_break"  # Stop trying and fail fast
    GRACEFUL_DEGRADE = "graceful_degrade"  # Continue with reduced functionality


class ErrorSeverity(Enum):
    """Error severity levels for recovery decisions."""

    LOW = "low"  # Minor errors, continue normally
    MEDIUM = "medium"  # Moderate errors, apply recovery strategy
    HIGH = "high"  # Serious errors, require immediate action
    CRITICAL = "critical"  # System-threatening errors, emergency procedures


@dataclass
class RecoveryConfig:
    """Configuration for error recovery behavior."""

    max_retries: int = 3
    retry_delay_base: float = 1.0
    retry_delay_multiplier: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    rollback_enabled: bool = True
    graceful_degradation: bool = True
    log_recovery_attempts: bool = True
    recovery_timeout: float = 30.0


@dataclass
class ErrorContext:
    """Context information for error analysis and recovery."""

    error: Exception
    operation: str
    component: str
    attempt_count: int = 0
    timestamp: float = field(default_factory=time.time)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    recovery_history: List[str] = field(default_factory=list)

    def add_recovery_attempt(self, strategy: RecoveryStrategy, success: bool, details: str = "") -> None:
        """Record a recovery attempt."""
        result = "SUCCESS" if success else "FAILED"
        entry = f"{strategy.value.upper()}: {result}"
        if details:
            entry += f" - {details}"
        self.recovery_history.append(entry)


class RecoveryAction(ABC, Generic[T]):
    """Abstract base class for recovery actions."""

    @abstractmethod
    def execute(self, context: ErrorContext) -> T:
        """Execute the recovery action.

        Args:
            context: Error context

        Returns:
            Recovery result
        """
        pass

    @abstractmethod
    def can_handle(self, context: ErrorContext) -> bool:
        """Check if this action can handle the error.

        Args:
            context: Error context

        Returns:
            True if action can handle this error
        """
        pass


class RetryAction(RecoveryAction[T]):
    """Recovery action that retries the original operation."""

    def __init__(self, operation: Callable[[], T], config: RecoveryConfig):
        self.operation = operation
        self.config = config

    def can_handle(self, context: ErrorContext) -> bool:
        """Check if retry is appropriate."""
        return (
            context.attempt_count < self.config.max_retries
            and context.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
            and not isinstance(context.error, (TypeError, ValueError))  # Don't retry logic errors
        )

    def execute(self, context: ErrorContext) -> T:
        """Execute retry with exponential backoff."""
        delay = self.config.retry_delay_base * (self.config.retry_delay_multiplier**context.attempt_count)

        if self.config.log_recovery_attempts:
            logger.info(
                f"Retrying {context.operation} (attempt {context.attempt_count + 1}/{self.config.max_retries}) in {delay:.1f}s"
            )

        time.sleep(delay)

        try:
            result = self.operation()
            context.add_recovery_attempt(RecoveryStrategy.RETRY, True, f"attempt {context.attempt_count + 1}")
            return result
        except Exception as e:
            context.add_recovery_attempt(RecoveryStrategy.RETRY, False, str(e))
            raise


class RollbackAction(RecoveryAction[None]):
    """Recovery action that rolls back to a previous state."""

    def __init__(self, rollback_func: Callable[[ErrorContext], None]):
        self.rollback_func = rollback_func

    def can_handle(self, context: ErrorContext) -> bool:
        """Check if rollback is appropriate."""
        return context.severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]

    def execute(self, context: ErrorContext) -> None:
        """Execute rollback operation."""
        try:
            logger.info(f"Rolling back {context.operation} due to {type(context.error).__name__}")

            self.rollback_func(context)
            context.add_recovery_attempt(RecoveryStrategy.ROLLBACK, True)

        except Exception as rollback_error:
            context.add_recovery_attempt(RecoveryStrategy.ROLLBACK, False, str(rollback_error))
            logger.error(f"Rollback failed for {context.operation}: {rollback_error}")
            raise


class FallbackAction(RecoveryAction[T]):
    """Recovery action that uses an alternative approach."""

    def __init__(self, fallback_func: Callable[[ErrorContext], T], config: RecoveryConfig):
        self.fallback_func = fallback_func
        self.config = config

    def can_handle(self, context: ErrorContext) -> bool:
        """Check if fallback is appropriate."""
        return context.severity != ErrorSeverity.CRITICAL

    def execute(self, context: ErrorContext) -> T:
        """Execute fallback operation."""
        try:
            if self.config.log_recovery_attempts:
                logger.info(f"Using fallback for {context.operation}")

            result = self.fallback_func(context)
            context.add_recovery_attempt(RecoveryStrategy.FALLBACK, True)
            return result

        except Exception as fallback_error:
            context.add_recovery_attempt(RecoveryStrategy.FALLBACK, False, str(fallback_error))
            raise


class CircuitBreaker:
    """Circuit breaker pattern implementation for preventing cascading failures."""

    def __init__(self, config: RecoveryConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.RLock()

    def call(self, operation: Callable[[], T]) -> T:
        """Execute operation with circuit breaker protection."""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - (self.last_failure_time or 0) < self.config.circuit_breaker_timeout:
                    raise RuntimeError("Circuit breaker is OPEN - operation blocked")
                else:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioning to HALF_OPEN")

            try:
                result = operation()

                # Success - reset circuit breaker
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED")

                return result

            except Exception:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.config.circuit_breaker_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

                raise


class ErrorRecoveryManager:
    """Central manager for error recovery across all rxiv-maker components.

    Features:
    - Coordinated recovery strategies across components
    - Circuit breaker patterns for preventing cascading failures
    - Transaction-like rollback capabilities
    - Graceful degradation when components fail
    - Recovery attempt tracking and analysis
    """

    def __init__(self, config: Optional[RecoveryConfig] = None):
        """Initialize error recovery manager.

        Args:
            config: Recovery configuration
        """
        self.config = config or RecoveryConfig()
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._recovery_stats: Dict[str, Dict[str, int]] = {}
        self._active_transactions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        logger.debug("ErrorRecoveryManager initialized")

    def get_circuit_breaker(self, component: str) -> CircuitBreaker:
        """Get circuit breaker for a component.

        Args:
            component: Component name

        Returns:
            Circuit breaker instance
        """
        with self._lock:
            if component not in self._circuit_breakers:
                self._circuit_breakers[component] = CircuitBreaker(self.config)
            return self._circuit_breakers[component]

    @contextmanager
    def recovery_context(self, operation: str, component: str):
        """Context manager for operations with automatic error recovery.

        Args:
            operation: Operation name
            component: Component name
        """
        context = None
        try:
            yield
        except Exception as e:
            context = ErrorContext(
                error=e, operation=operation, component=component, severity=self._assess_error_severity(e)
            )

            logger.error(f"Error in {component}.{operation}: {e}")

            # Try recovery strategies
            recovered = self._attempt_recovery(context)
            if not recovered:
                self._record_failure(component, operation)
                raise

    def _assess_error_severity(self, error: Exception) -> ErrorSeverity:
        """Assess error severity based on error type and context.

        Args:
            error: Exception to assess

        Returns:
            Error severity level
        """
        if isinstance(error, (SystemError, MemoryError, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (OSError, IOError, ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.MEDIUM

    def _attempt_recovery(self, context: ErrorContext) -> bool:
        """Attempt to recover from an error.

        Args:
            context: Error context

        Returns:
            True if recovery was successful
        """
        # Record recovery attempt
        with self._lock:
            if context.component not in self._recovery_stats:
                self._recovery_stats[context.component] = {}

            operation_key = f"{context.operation}_{type(context.error).__name__}"
            self._recovery_stats[context.component][operation_key] = (
                self._recovery_stats[context.component].get(operation_key, 0) + 1
            )

        # For this base implementation, we primarily log and track
        # Individual managers should implement their specific recovery logic
        logger.info(f"Recovery attempted for {context.component}.{context.operation}: {context.error}")

        # Check if circuit breaker should be triggered
        self.get_circuit_breaker(context.component)

        return False  # Base implementation doesn't recover

    def _record_failure(self, component: str, operation: str) -> None:
        """Record operation failure for statistics.

        Args:
            component: Component name
            operation: Operation name
        """
        with self._lock:
            if component not in self._recovery_stats:
                self._recovery_stats[component] = {}

            failure_key = f"{operation}_failures"
            self._recovery_stats[component][failure_key] = self._recovery_stats[component].get(failure_key, 0) + 1

    @contextmanager
    def transaction(self, transaction_id: str, components: List[str]):
        """Context manager for transactional operations across components.

        Args:
            transaction_id: Unique transaction identifier
            components: List of components involved
        """
        with self._lock:
            self._active_transactions[transaction_id] = {
                "components": components,
                "start_time": time.time(),
                "checkpoints": {},
            }

        try:
            yield TransactionContext(transaction_id, self)
            # Transaction completed successfully
            logger.debug(f"Transaction {transaction_id} completed successfully")
        except Exception as e:
            # Transaction failed - attempt rollback
            logger.error(f"Transaction {transaction_id} failed: {e}")
            self._rollback_transaction(transaction_id)
            raise
        finally:
            with self._lock:
                self._active_transactions.pop(transaction_id, None)

    def create_checkpoint(self, transaction_id: str, component: str, state: Dict[str, Any]) -> None:
        """Create a checkpoint for transaction rollback.

        Args:
            transaction_id: Transaction ID
            component: Component name
            state: State to checkpoint
        """
        with self._lock:
            if transaction_id in self._active_transactions:
                self._active_transactions[transaction_id]["checkpoints"][component] = state
                logger.debug(f"Checkpoint created for {component} in transaction {transaction_id}")

    def _rollback_transaction(self, transaction_id: str) -> None:
        """Rollback a failed transaction.

        Args:
            transaction_id: Transaction to rollback
        """
        with self._lock:
            if transaction_id not in self._active_transactions:
                return

            transaction = self._active_transactions[transaction_id]
            checkpoints = transaction["checkpoints"]

            logger.info(f"Rolling back transaction {transaction_id}")

            # Rollback in reverse order
            for component in reversed(transaction["components"]):
                if component in checkpoints:
                    try:
                        # This would call component-specific rollback
                        logger.debug(f"Rolling back {component} in transaction {transaction_id}")
                        # Component managers should register rollback handlers
                    except Exception as rollback_error:
                        logger.error(f"Rollback failed for {component}: {rollback_error}")

    def get_recovery_stats(self) -> Dict[str, Dict[str, int]]:
        """Get recovery statistics.

        Returns:
            Recovery statistics by component
        """
        with self._lock:
            return {k: v.copy() for k, v in self._recovery_stats.items()}

    def reset_circuit_breaker(self, component: str) -> None:
        """Reset circuit breaker for a component.

        Args:
            component: Component name
        """
        with self._lock:
            if component in self._circuit_breakers:
                breaker = self._circuit_breakers[component]
                breaker.state = "CLOSED"
                breaker.failure_count = 0
                breaker.last_failure_time = None
                logger.info(f"Circuit breaker reset for {component}")


class TransactionContext:
    """Context for transactional operations."""

    def __init__(self, transaction_id: str, recovery_manager: ErrorRecoveryManager):
        self.transaction_id = transaction_id
        self.recovery_manager = recovery_manager

    def checkpoint(self, component: str, state: Dict[str, Any]) -> None:
        """Create a checkpoint for this component.

        Args:
            component: Component name
            state: State to checkpoint
        """
        self.recovery_manager.create_checkpoint(self.transaction_id, component, state)


class RecoveryEnhancedMixin:
    """Mixin class to add recovery capabilities to existing managers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._recovery_manager = get_error_recovery_manager()
        self._component_name = self.__class__.__name__

    def execute_with_recovery(self, operation: str, func: Callable[[], T], **kwargs) -> T:
        """Execute operation with automatic recovery.

        Args:
            operation: Operation name
            func: Function to execute
            **kwargs: Additional arguments

        Returns:
            Operation result
        """
        circuit_breaker = self._recovery_manager.get_circuit_breaker(self._component_name)

        with self._recovery_manager.recovery_context(operation, self._component_name):
            return circuit_breaker.call(func)

    def create_transaction_checkpoint(self, transaction_id: str, state: Dict[str, Any]) -> None:
        """Create checkpoint for transaction.

        Args:
            transaction_id: Transaction ID
            state: State to checkpoint
        """
        self._recovery_manager.create_checkpoint(transaction_id, self._component_name, state)


# Global error recovery manager instance
_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager(config: Optional[RecoveryConfig] = None) -> ErrorRecoveryManager:
    """Get the global error recovery manager instance.

    Args:
        config: Optional recovery configuration

    Returns:
        Global error recovery manager
    """
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager(config)
    return _error_recovery_manager


# Convenience decorators
def with_recovery(operation: str):
    """Decorator to add error recovery to functions.

    Args:
        operation: Operation name
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            recovery_manager = get_error_recovery_manager()
            component = func.__module__.split(".")[-1]

            with recovery_manager.recovery_context(operation, component):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def with_circuit_breaker(component: str):
    """Decorator to add circuit breaker protection.

    Args:
        component: Component name
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            recovery_manager = get_error_recovery_manager()
            circuit_breaker = recovery_manager.get_circuit_breaker(component)

            return circuit_breaker.call(lambda: func(*args, **kwargs))

        return wrapper

    return decorator


# Export public API
__all__ = [
    "ErrorRecoveryManager",
    "RecoveryStrategy",
    "ErrorSeverity",
    "RecoveryConfig",
    "ErrorContext",
    "RecoveryAction",
    "CircuitBreaker",
    "TransactionContext",
    "RecoveryEnhancedMixin",
    "get_error_recovery_manager",
    "with_recovery",
    "with_circuit_breaker",
]
