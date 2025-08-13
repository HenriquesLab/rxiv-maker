#!/usr/bin/env python3
"""Script to categorize tests based on performance benchmarks.

This script analyzes the test_durations.txt file and automatically
adds appropriate markers to tests based on their execution time.
"""

import re


def parse_duration_file(file_path: str) -> dict[str, float]:
    """Parse the test_durations.txt file and extract test durations."""
    durations = {}

    with open(file_path) as f:
        for line in f:
            # Match lines like "0.18s call tests/unit/test_example.py::test_function"
            match = re.match(r"(\d+\.\d+)s call\s+(.+)", line.strip())
            if match:
                duration = float(match.group(1))
                test_path = match.group(2)
                durations[test_path] = duration

    return durations


def categorize_tests(
    durations: dict[str, float],
) -> tuple[list[str], list[str], list[str]]:
    """Categorize tests based on duration thresholds."""
    fast_tests = []  # < 1.0s
    medium_tests = []  # 1.0s - 5.0s
    slow_tests = []  # > 5.0s

    for test_path, duration in durations.items():
        if duration < 1.0:
            fast_tests.append(test_path)
        elif duration > 5.0:
            slow_tests.append(test_path)
        else:
            medium_tests.append(test_path)

    return fast_tests, medium_tests, slow_tests


def extract_test_info(test_path: str) -> tuple[str, str]:
    """Extract file path and test name from test path."""
    # Example: tests/unit/test_example.py::TestClass::test_method
    parts = test_path.split("::")
    file_path = parts[0]
    test_name = parts[-1]  # Last part is the test method name

    return file_path, test_name


def generate_marker_recommendations(fast_tests: list[str], medium_tests: list[str], slow_tests: list[str]) -> None:
    """Generate recommendations for adding markers to test files."""
    print("\n=== MARKER RECOMMENDATIONS ===")

    # Group by file
    file_recommendations: dict[str, dict[str, list[str]]] = {}

    for test_path in fast_tests:
        file_path, test_name = extract_test_info(test_path)
        if file_path not in file_recommendations:
            file_recommendations[file_path] = {"fast": [], "medium": [], "slow": []}
        file_recommendations[file_path]["fast"].append(test_name)

    for test_path in medium_tests:
        file_path, test_name = extract_test_info(test_path)
        if file_path not in file_recommendations:
            file_recommendations[file_path] = {"fast": [], "medium": [], "slow": []}
        file_recommendations[file_path]["medium"].append(test_name)

    for test_path in slow_tests:
        file_path, test_name = extract_test_info(test_path)
        if file_path not in file_recommendations:
            file_recommendations[file_path] = {"fast": [], "medium": [], "slow": []}
        file_recommendations[file_path]["slow"].append(test_name)

    for file_path, markers in file_recommendations.items():
        if any(markers.values()):
            print(f"\n📁 {file_path}")
            if markers["fast"]:
                fast_preview = f"{', '.join(markers['fast'][:3])}{'...' if len(markers['fast']) > 3 else ''}"
                print(f"  ⚡ Fast tests ({len(markers['fast'])}): {fast_preview}")
            if markers["medium"]:
                print(f"  🔶 Medium tests ({len(markers['medium'])}): {', '.join(markers['medium'])}")
            if markers["slow"]:
                print(f"  🐌 Slow tests ({len(markers['slow'])}): {', '.join(markers['slow'])}")


def main():
    """Main function to analyze and report test categorization."""
    # Parse the duration data
    durations = parse_duration_file("../test-results/test_durations_complete.txt")

    # Categorize tests
    fast_tests, medium_tests, slow_tests = categorize_tests(durations)

    print("=== TEST PERFORMANCE ANALYSIS ===\n")
    print(f"Total tests analyzed: {len(durations)}")
    print(f"Fast tests (<1s): {len(fast_tests)}")
    print(f"Medium tests (1-5s): {len(medium_tests)}")
    print(f"Slow tests (>5s): {len(slow_tests)}")

    print("\n=== SLOWEST TESTS (>5s) ===")
    slow_with_duration = [(test, durations[test]) for test in slow_tests]
    slow_with_duration.sort(key=lambda x: x[1], reverse=True)

    for test_path, duration in slow_with_duration:
        file_path, test_name = extract_test_info(test_path)
        print(f"{duration:6.2f}s - {file_path}::{test_name}")

    print("\n=== FASTEST TESTS (<0.2s) ===")
    fastest_tests = [(test, durations[test]) for test in fast_tests if durations[test] < 0.2]
    fastest_tests.sort(key=lambda x: x[1])

    for test_path, duration in fastest_tests[:10]:  # Show top 10 fastest
        file_path, test_name = extract_test_info(test_path)
        print(f"{duration:6.2f}s - {file_path}::{test_name}")

    print("\n=== MEDIUM TESTS (1-5s) ===")
    medium_with_duration = [(test, durations[test]) for test in medium_tests]
    medium_with_duration.sort(key=lambda x: x[1], reverse=True)

    for test_path, duration in medium_with_duration:
        file_path, test_name = extract_test_info(test_path)
        print(f"{duration:6.2f}s - {file_path}::{test_name}")

    # Generate marker recommendations
    generate_marker_recommendations(fast_tests, medium_tests, slow_tests)


if __name__ == "__main__":
    main()
