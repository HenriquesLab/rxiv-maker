#!/usr/bin/env python3
"""Fix test import paths after architecture restructuring.

This script updates import statements in test files to reflect the new
module structure after Phase 1 architecture streamlining.
"""

import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """Fix imports in a single test file."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Map old imports to new ones based on our restructuring
    replacements = [
        # engine -> engines (plural)
        (r"from rxiv_maker\.engine\.", "from rxiv_maker.engines."),
        (r"import rxiv_maker\.engine\.", "import rxiv_maker.engines."),
        # Some modules may have moved to engines.operations
        (r"from rxiv_maker\.engines\.add_bibliography", "from rxiv_maker.engines.operations.add_bibliography"),
        (r"from rxiv_maker\.engines\.fix_bibliography", "from rxiv_maker.engines.operations.fix_bibliography"),
        (r"from rxiv_maker\.engines\.generate_preprint", "from rxiv_maker.engines.operations.generate_preprint"),
        (r"from rxiv_maker\.engines\.generate_figures", "from rxiv_maker.engines.operations.generate_figures"),
        (r"from rxiv_maker\.engines\.setup_environment", "from rxiv_maker.engines.operations.setup_environment"),
        (r"from rxiv_maker\.engines\.cleanup", "from rxiv_maker.engines.operations.cleanup"),
        (r"from rxiv_maker\.engines\.track_changes", "from rxiv_maker.engines.operations.track_changes"),
    ]

    for old_pattern, new_pattern in replacements:
        content = re.sub(old_pattern, new_pattern, content)

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True
    return False


def main():
    """Fix all test imports."""
    tests_dir = Path(__file__).parent.parent / "tests"

    # Find all Python test files
    test_files = list(tests_dir.rglob("test_*.py"))

    fixed_count = 0
    for test_file in test_files:
        if fix_imports_in_file(test_file):
            print(f"✅ Fixed imports in: {test_file.relative_to(tests_dir.parent)}")
            fixed_count += 1

    print(f"\n📊 Summary: Fixed {fixed_count} files out of {len(test_files)} test files")


if __name__ == "__main__":
    main()
