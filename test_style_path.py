#!/usr/bin/env python3
"""Test script to check style file path resolution."""

from pathlib import Path

# Test the path resolution logic
build_manager_file = Path("src/rxiv_maker/engine/build_manager.py")
print(f"build_manager.py location: {build_manager_file.resolve()}")

possible_style_dirs = [
    # Installed package location (when installed via pip) - hatch maps src/tex to rxiv_maker/tex
    build_manager_file.resolve().parent.parent / "tex" / "style",
    # Development location
    build_manager_file.resolve().parent.parent.parent.parent / "src" / "tex" / "style",
    # Alternative development location
    build_manager_file.resolve().parent.parent.parent / "tex" / "style",
]

print("\nTesting style directory locations:")
for i, style_dir in enumerate(possible_style_dirs):
    exists = style_dir.exists()
    has_cls = exists and any(style_dir.glob("*.cls"))
    print(f"{i + 1}. {style_dir}")
    print(f"   Exists: {exists}")
    if exists:
        print(f"   Has .cls files: {has_cls}")
        if has_cls:
            cls_files = list(style_dir.glob("*.cls"))
            print(f"   .cls files: {[f.name for f in cls_files]}")
    print()

# Test which one would be selected
selected_dir = None
for style_dir in possible_style_dirs:
    if style_dir.exists() and any(style_dir.glob("*.cls")):
        selected_dir = style_dir
        break

print(f"Selected style directory: {selected_dir}")
