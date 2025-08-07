"""Performance tracking and baseline management for rxiv-maker."""

import json
import time
from pathlib import Path
from typing import Any

from ..__version__ import __version__


class PerformanceTracker:
    """Track and compare performance metrics across rxiv-maker versions."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize performance tracker.

        Args:
            cache_dir: Directory for storing performance baselines
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "rxiv-maker" / "performance"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.baseline_file = self.cache_dir / "baselines.json"
        self.current_version = __version__

        # Load existing baselines
        self.baselines = self._load_baselines()

        # Current session metrics
        self.session_metrics: dict[str, list[float]] = {}
        self.operation_timings: dict[str, float] = {}

    def _load_baselines(self) -> dict[str, Any]:
        """Load performance baselines from cache."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_baselines(self) -> None:
        """Save performance baselines to cache."""
        try:
            with open(self.baseline_file, "w") as f:
                json.dump(self.baselines, f, indent=2)
        except Exception:
            pass

    def start_operation(self, operation_id: str) -> float:
        """Start timing an operation.

        Args:
            operation_id: Unique identifier for the operation

        Returns:
            Start time
        """
        start_time = time.time()
        self.operation_timings[operation_id] = start_time
        return start_time

    def end_operation(self, operation_id: str, metadata: dict[str, Any] | None = None) -> float:
        """End timing an operation and record the metric.

        Args:
            operation_id: Unique identifier for the operation
            metadata: Additional metadata about the operation

        Returns:
            Operation duration in seconds
        """
        if operation_id not in self.operation_timings:
            return 0.0

        duration = time.time() - self.operation_timings[operation_id]

        # Store metric
        if operation_id not in self.session_metrics:
            self.session_metrics[operation_id] = []
        self.session_metrics[operation_id].append(duration)

        # Clean up timing
        del self.operation_timings[operation_id]

        return duration

    def get_baseline(self, operation_id: str, version: str | None = None) -> dict[str, float] | None:
        """Get performance baseline for an operation.

        Args:
            operation_id: Operation identifier
            version: Version to get baseline for (defaults to current)

        Returns:
            Baseline metrics or None if not found
        """
        target_version = version or self.current_version

        if target_version in self.baselines:
            version_data = self.baselines[target_version]
            if operation_id in version_data.get("operations", {}):
                return version_data["operations"][operation_id]

        return None

    def compare_to_baseline(self, operation_id: str, current_time: float) -> dict[str, Any]:
        """Compare current performance to baseline.

        Args:
            operation_id: Operation identifier
            current_time: Current operation time

        Returns:
            Comparison results
        """
        baseline = self.get_baseline(operation_id)

        if not baseline:
            return {"status": "no_baseline", "current": current_time}

        avg_baseline = baseline.get("average", current_time)
        improvement = ((avg_baseline - current_time) / avg_baseline) * 100

        return {
            "status": "compared",
            "current": current_time,
            "baseline_avg": avg_baseline,
            "baseline_min": baseline.get("min", avg_baseline),
            "baseline_max": baseline.get("max", avg_baseline),
            "improvement_percent": improvement,
            "regression": improvement < -10,  # 10% slower is considered regression
        }

    def save_session_as_baseline(self, version: str | None = None) -> None:
        """Save current session metrics as baseline for version.

        Args:
            version: Version to save baseline for (defaults to current)
        """
        target_version = version or self.current_version

        if target_version not in self.baselines:
            self.baselines[target_version] = {
                "operations": {},
                "timestamp": time.time(),
            }

        # Calculate statistics for each operation
        for operation_id, timings in self.session_metrics.items():
            if timings:
                self.baselines[target_version]["operations"][operation_id] = {
                    "average": sum(timings) / len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "samples": len(timings),
                }

        self._save_baselines()

    def get_performance_report(self) -> dict[str, Any]:
        """Generate performance report for current session.

        Returns:
            Performance report with comparisons
        """
        report: dict[str, Any] = {
            "version": self.current_version,
            "operations": {},
            "summary": {
                "total_operations": len(self.session_metrics),
                "regressions": 0,
                "improvements": 0,
            },
        }

        for operation_id, timings in self.session_metrics.items():
            if timings:
                avg_time = sum(timings) / len(timings)
                comparison = self.compare_to_baseline(operation_id, avg_time)

                report["operations"][operation_id] = {
                    "average": avg_time,
                    "samples": len(timings),
                    "comparison": comparison,
                }

                if comparison.get("regression"):
                    report["summary"]["regressions"] += 1
                elif comparison.get("improvement_percent", 0) > 10:
                    report["summary"]["improvements"] += 1

        return report

    def cleanup_old_baselines(self, keep_versions: int = 5) -> None:
        """Remove old performance baselines.

        Args:
            keep_versions: Number of recent versions to keep
        """
        if len(self.baselines) <= keep_versions:
            return

        # Sort by timestamp and keep most recent
        sorted_versions = sorted(self.baselines.items(), key=lambda x: x[1].get("timestamp", 0), reverse=True)

        self.baselines = dict(sorted_versions[:keep_versions])
        self._save_baselines()


# Global performance tracker instance
_performance_tracker: PerformanceTracker | None = None


def get_performance_tracker() -> PerformanceTracker:
    """Get or create the global performance tracker instance."""
    global _performance_tracker

    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()

    return _performance_tracker


def track_operation(operation_id: str):
    """Decorator to track operation performance.

    Args:
        operation_id: Unique identifier for the operation
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            tracker = get_performance_tracker()
            tracker.start_operation(operation_id)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                tracker.end_operation(operation_id)

        return wrapper

    return decorator
