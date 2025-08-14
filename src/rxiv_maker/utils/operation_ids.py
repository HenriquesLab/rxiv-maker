"""Operation ID management for debugging and tracing."""

import random
import string
import time
from typing import Any


class OperationContext:
    """Context manager for operation tracking with unique IDs."""

    def __init__(self, operation_type: str, metadata: dict[str, Any] | None = None):
        """Initialize operation context.

        Args:
            operation_type: Type of operation (e.g., "pdf_build", "validation")
            metadata: Additional metadata for the operation
        """
        self.operation_type = operation_type
        self.operation_id = self._generate_id()
        self.metadata = metadata or {}
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.logs: list[tuple[float, str]] = []

    def _generate_id(self) -> str:
        """Generate unique operation ID."""
        # Format: TYPE_TIMESTAMP_RANDOM
        timestamp = int(time.time() * 1000) % 1000000  # Last 6 digits of timestamp
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{self.operation_type.upper()}_{timestamp}_{random_suffix}"

    def log(self, message: str) -> None:
        """Add a log entry to the operation."""
        self.logs.append((time.time(), message))

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the operation."""
        self.metadata[key] = value

    def __enter__(self):
        """Enter operation context."""
        self.start_time = time.time()
        self.log(f"Started {self.operation_type}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit operation context."""
        self.end_time = time.time()
        duration = self.end_time - (self.start_time or 0)

        if exc_type:
            self.log(f"Failed with error: {exc_val}")
            self.metadata["error"] = str(exc_val)
            self.metadata["error_type"] = exc_type.__name__
        else:
            self.log("Completed successfully")

        self.metadata["duration_seconds"] = duration

        # Store in operation history
        get_operation_history().add_operation(self)


class OperationHistory:
    """Manages history of operations for debugging."""

    def __init__(self, max_operations: int = 100):
        """Initialize operation history.

        Args:
            max_operations: Maximum operations to keep in history
        """
        self.max_operations = max_operations
        self.operations: list[OperationContext] = []
        self._operation_map: dict[str, OperationContext] = {}

    def add_operation(self, operation: OperationContext) -> None:
        """Add operation to history."""
        self.operations.append(operation)
        self._operation_map[operation.operation_id] = operation

        # Trim old operations
        if len(self.operations) > self.max_operations:
            removed = self.operations[: -self.max_operations]
            self.operations = self.operations[-self.max_operations :]

            # Clean up map
            for op in removed:
                self._operation_map.pop(op.operation_id, None)

    def get_operation(self, operation_id: str) -> OperationContext | None:
        """Get operation by ID."""
        return self._operation_map.get(operation_id)

    def get_recent_operations(self, count: int = 10) -> list[OperationContext]:
        """Get recent operations."""
        return self.operations[-count:]

    def get_failed_operations(self) -> list[OperationContext]:
        """Get all failed operations."""
        return [op for op in self.operations if "error" in op.metadata]

    def get_operations_by_type(self, operation_type: str) -> list[OperationContext]:
        """Get operations by type."""
        return [op for op in self.operations if op.operation_type == operation_type]

    def generate_debug_report(self) -> dict[str, Any]:
        """Generate debug report with operation history."""
        report: dict[str, Any] = {
            "total_operations": len(self.operations),
            "failed_operations": len(self.get_failed_operations()),
            "operation_types": {},
            "recent_failures": [],
        }

        # Count by type
        for op in self.operations:
            op_type = op.operation_type
            if op_type not in report["operation_types"]:
                report["operation_types"][op_type] = {"count": 0, "failures": 0}

            report["operation_types"][op_type]["count"] += 1
            if "error" in op.metadata:
                report["operation_types"][op_type]["failures"] += 1

        # Recent failures
        for op in self.get_failed_operations()[-5:]:
            report["recent_failures"].append(
                {
                    "id": op.operation_id,
                    "type": op.operation_type,
                    "error": op.metadata.get("error", "Unknown"),
                    "duration": op.metadata.get("duration_seconds", 0),
                }
            )

        return report

    def clear(self) -> None:
        """Clear operation history."""
        self.operations.clear()
        self._operation_map.clear()


# Global operation history instance
_operation_history: OperationHistory | None = None


def get_operation_history() -> OperationHistory:
    """Get or create the global operation history instance."""
    global _operation_history

    if _operation_history is None:
        _operation_history = OperationHistory()

    return _operation_history


def create_operation(operation_type: str, **metadata) -> OperationContext:
    """Create a new operation context.

    Args:
        operation_type: Type of operation
        **metadata: Additional metadata

    Returns:
        Operation context
    """
    return OperationContext(operation_type, metadata)


def get_current_operation_id() -> str | None:
    """Get the ID of the most recent operation."""
    history = get_operation_history()
    recent = history.get_recent_operations(1)
    return recent[0].operation_id if recent else None
