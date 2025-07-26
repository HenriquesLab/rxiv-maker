#!/usr/bin/env python3
"""Performance regression checker for rxiv-maker test suite."""

import json
import sys
from pathlib import Path


class PerformanceRegression:
    """Check for performance regressions in benchmark results."""

    def __init__(
        self,
        baseline_file: str = "performance_baseline.json",
        current_file: str = "benchmark_results.json",
        regression_threshold: float = 0.20,
    ):  # 20% regression threshold
        self.baseline_file = Path(baseline_file)
        self.current_file = Path(current_file)
        self.regression_threshold = regression_threshold

    def load_benchmark_data(self, file_path: Path) -> dict | None:
        """Load benchmark data from JSON file."""
        if not file_path.exists():
            return None

        try:
            with open(file_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def extract_benchmark_stats(self, data: dict) -> dict[str, float]:
        """Extract benchmark statistics from data."""
        stats = {}
        for benchmark in data.get("benchmarks", []):
            name = benchmark["name"]
            mean_time = benchmark["stats"]["mean"]
            stats[name] = mean_time
        return stats

    def check_regressions(self) -> list[dict]:
        """Check for performance regressions."""
        baseline_data = self.load_benchmark_data(self.baseline_file)
        current_data = self.load_benchmark_data(self.current_file)

        if not baseline_data:
            print(f"No baseline data found at {self.baseline_file}")
            return []

        if not current_data:
            print(f"No current benchmark data found at {self.current_file}")
            return []

        baseline_stats = self.extract_benchmark_stats(baseline_data)
        current_stats = self.extract_benchmark_stats(current_data)

        regressions = []
        improvements = []

        for benchmark_name, current_time in current_stats.items():
            baseline_time = baseline_stats.get(benchmark_name)

            if baseline_time is None:
                print(f"New benchmark: {benchmark_name} ({current_time:.4f}s)")
                continue

            # Calculate percentage change
            change_ratio = (current_time - baseline_time) / baseline_time

            if change_ratio > self.regression_threshold:
                regressions.append(
                    {
                        "name": benchmark_name,
                        "baseline": baseline_time,
                        "current": current_time,
                        "change_ratio": change_ratio,
                        "change_percent": change_ratio * 100,
                    }
                )
            elif change_ratio < -0.10:  # 10% improvement threshold
                improvements.append(
                    {
                        "name": benchmark_name,
                        "baseline": baseline_time,
                        "current": current_time,
                        "change_ratio": change_ratio,
                        "change_percent": change_ratio * 100,
                    }
                )

        return regressions, improvements

    def report_results(self, regressions: list[dict], improvements: list[dict]) -> bool:
        """Report regression results and return True if tests should fail."""
        if improvements:
            print("\n🚀 PERFORMANCE IMPROVEMENTS:")
            for improvement in improvements:
                print(f"  {improvement['name']}")
                print(
                    f"    {improvement['baseline']:.4f}s → {improvement['current']:.4f}s "
                    f"({improvement['change_percent']:.1f}% faster)"
                )

        if regressions:
            print("\n⚠️  PERFORMANCE REGRESSIONS DETECTED:")
            for regression in regressions:
                print(f"  {regression['name']}")
                print(
                    f"    {regression['baseline']:.4f}s → {regression['current']:.4f}s "
                    f"({regression['change_percent']:.1f}% slower)"
                )

            print(
                f"\n❌ {len(regressions)} performance regression(s) exceed the "
                f"{self.regression_threshold * 100:.0f}% threshold"
            )
            return True

        print("\n✅ No significant performance regressions detected")
        return False


def main():
    """Main entry point for performance regression checking."""
    import argparse

    parser = argparse.ArgumentParser(description="Check for performance regressions")
    parser.add_argument(
        "--baseline",
        default="performance_baseline.json",
        help="Baseline benchmark file",
    )
    parser.add_argument(
        "--current",
        default="benchmark_results.json",
        help="Current benchmark results file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.20,
        help="Regression threshold (default: 20%)",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with non-zero code on regression",
    )

    args = parser.parse_args()

    checker = PerformanceRegression(
        baseline_file=args.baseline,
        current_file=args.current,
        regression_threshold=args.threshold,
    )

    regressions, improvements = checker.check_regressions()
    has_regressions = checker.report_results(regressions, improvements)

    if args.fail_on_regression and has_regressions:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
