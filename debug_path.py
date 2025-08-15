#!/usr/bin/env python3
"""Debug the path issue."""

import os
from pathlib import Path

# Test Guillaume's scenario
manuscript_path = "TEST_CCT8_paper/"

print(f"manuscript_path: '{manuscript_path}'")
print(f"Path(manuscript_path): {Path(manuscript_path)}")

# Test how the md_path gets constructed
for md_file in ["01_MAIN.md", "MAIN.md", "manuscript.md"]:
    md_path = Path(manuscript_path) / md_file
    print(f"md_path for {md_file}: {md_path}")
    print(f"md_path.parent: {md_path.parent}")

    config_file = md_path.parent / "00_CONFIG.yml"
    print(f"config_file: {config_file}")
    print(f"config_file.exists(): {config_file.exists()}")
    print()

# Test what MANUSCRIPT_PATH environment variable will be set to
normalized_path = manuscript_path.rstrip("/")
manuscript_name = os.path.basename(normalized_path)
if not manuscript_name or manuscript_name in (".", ".."):
    manuscript_name = "MANUSCRIPT"

print(f"normalized_path: '{normalized_path}'")
print(f"manuscript_name: '{manuscript_name}'")
print(f"MANUSCRIPT_PATH will be set to: '{manuscript_name}'")

# But what if the find_manuscript_md function also depends on MANUSCRIPT_PATH?
print(f"MANUSCRIPT_PATH env var currently: '{os.getenv('MANUSCRIPT_PATH', 'Not Set')}'")
