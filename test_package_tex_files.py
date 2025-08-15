#!/usr/bin/env python3
"""Test script to verify that tex files are correctly packaged and detected.

Test script to verify that tex files are correctly packaged and detected
when rxiv-maker is installed as a PyPI package.

This script will:
1. Build the package using the current source
2. Install it in a temporary virtual environment
3. Test that style files are properly detected and accessible
4. Verify the fix works outside the development directory
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None, capture_output=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    if cwd:
        print(f"  in directory: {cwd}")

    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=capture_output, text=True)

    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.stdout:
            print(f"Output: {result.stdout}")

    return result


def test_package_installation():
    """Test that the package can be built and installed with tex files."""
    print("=" * 80)
    print("TESTING RXIV-MAKER PACKAGE INSTALLATION AND TEX FILE DETECTION")
    print("=" * 80)

    # Get current directory (should be rxiv-maker root)
    project_root = Path.cwd()
    print(f"Project root: {project_root}")

    # Verify we're in the right place
    if not (project_root / "pyproject.toml").exists():
        print("❌ ERROR: Not in rxiv-maker project root (no pyproject.toml found)")
        return False

    # Step 1: Build the package
    print("\n🔨 Step 1: Building the package...")
    build_result = run_command("python -m build", cwd=project_root)
    if build_result.returncode != 0:
        print("❌ ERROR: Failed to build package")
        return False

    # Check that wheel was created
    dist_dir = project_root / "dist"
    if not dist_dir.exists():
        print("❌ ERROR: dist directory not created")
        return False

    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("❌ ERROR: No wheel file found in dist/")
        return False

    latest_wheel = max(wheel_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ Built package: {latest_wheel.name}")

    # Step 2: Create temporary virtual environment and install package
    print("\n🏗️  Step 2: Creating temporary virtual environment...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        venv_path = temp_path / "test_venv"

        # Create virtual environment
        venv_result = run_command(f"python -m venv {venv_path}")
        if venv_result.returncode != 0:
            print("❌ ERROR: Failed to create virtual environment")
            return False

        # Determine the python executable in the venv
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"

        print(f"✅ Created virtual environment at: {venv_path}")

        # Install the wheel
        print(f"\n📦 Step 3: Installing wheel {latest_wheel.name}...")
        install_result = run_command(f"{pip_exe} install {latest_wheel}")
        if install_result.returncode != 0:
            print("❌ ERROR: Failed to install wheel")
            return False

        print("✅ Package installed successfully")

        # Step 4: Test that tex files are accessible
        print("\n🔍 Step 4: Testing tex file detection...")

        # Create a test script that imports rxiv-maker and checks for tex files
        test_script = temp_path / "test_tex_detection.py"
        test_script.write_text('''
import sys
import tempfile
from pathlib import Path

# Import rxiv-maker components
from rxiv_maker.engine.build_manager import BuildManager

def test_style_detection():
    """Test that style files are detected correctly."""
    print("Testing style file detection in installed package...")

    # Create a temporary manuscript directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Set up a minimal manuscript
        manuscript_dir = temp_path / "test_manuscript"
        manuscript_dir.mkdir()
        (manuscript_dir / "01_MAIN.md").write_text("# Test Manuscript")
        (manuscript_dir / "00_CONFIG.yml").write_text("title: Test")

        output_dir = temp_path / "output"

        try:
            # Create BuildManager instance
            build_manager = BuildManager(
                manuscript_path=str(manuscript_dir),
                output_dir=str(output_dir),
                skip_validation=True
            )

            print(f"Style directory detected: {build_manager.style_dir}")
            print(f"Style directory exists: {build_manager.style_dir is not None and build_manager.style_dir.exists()}")

            if build_manager.style_dir and build_manager.style_dir.exists():
                cls_files = list(build_manager.style_dir.glob("*.cls"))
                bst_files = list(build_manager.style_dir.glob("*.bst"))
                print(f"Found .cls files: {[f.name for f in cls_files]}")
                print(f"Found .bst files: {[f.name for f in bst_files]}")

                # Test copying style files
                output_dir.mkdir(exist_ok=True)
                copy_result = build_manager.copy_style_files()
                print(f"copy_style_files result: {copy_result}")

                # Check what was copied
                copied_cls = list(output_dir.glob("*.cls"))
                copied_bst = list(output_dir.glob("*.bst"))
                print(f"Copied .cls files: {[f.name for f in copied_cls]}")
                print(f"Copied .bst files: {[f.name for f in copied_bst]}")

                # Success criteria
                has_cls = len(cls_files) > 0 and any("rxiv_maker_style.cls" in f.name for f in cls_files)
                has_bst = len(bst_files) > 0 and any("rxiv_maker_style.bst" in f.name for f in bst_files)
                copied_successfully = len(copied_cls) > 0 and len(copied_bst) > 0

                if has_cls and has_bst and copied_successfully:
                    print("✅ SUCCESS: Style files detected and copied correctly!")
                    return True
                else:
                    print("❌ FAILURE: Style files not properly detected or copied")
                    return False
            else:
                print("❌ FAILURE: Style directory not found or doesn't exist")
                return False

        except Exception as e:
            print(f"❌ ERROR: Exception during testing: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_style_detection()
    sys.exit(0 if success else 1)
''')

        # Run the test script in the virtual environment
        test_result = run_command(f"{python_exe} {test_script}")

        if test_result.returncode == 0:
            print("✅ SUCCESS: Tex files are correctly packaged and detected!")
            print(f"Output:\n{test_result.stdout}")
            return True
        else:
            print("❌ FAILURE: Tex file detection test failed")
            if test_result.stdout:
                print(f"Output:\n{test_result.stdout}")
            if test_result.stderr:
                print(f"Error:\n{test_result.stderr}")
            return False


def test_wheel_contents():
    """Test that the wheel contains the expected tex files."""
    print("\n📋 Step 5: Inspecting wheel contents...")

    project_root = Path.cwd()
    dist_dir = project_root / "dist"
    wheel_files = list(dist_dir.glob("*.whl"))

    if not wheel_files:
        print("❌ ERROR: No wheel file found")
        return False

    latest_wheel = max(wheel_files, key=lambda p: p.stat().st_mtime)

    # Extract and inspect wheel contents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / "wheel_contents"

        # Extract wheel (it's a zip file)
        import zipfile

        with zipfile.ZipFile(latest_wheel, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"Extracted wheel to: {extract_dir}")

        # Look for tex files
        tex_files = []
        for root, _dirs, files in os.walk(extract_dir):
            for file in files:
                if file.endswith((".cls", ".bst", ".tex")):
                    rel_path = Path(root).relative_to(extract_dir) / file
                    tex_files.append(rel_path)

        print(f"Found {len(tex_files)} tex-related files in wheel:")
        for tex_file in tex_files:
            print(f"  - {tex_file}")

        # Check for expected files
        expected_files = ["rxiv_maker_style.cls", "rxiv_maker_style.bst"]
        found_files = [f.name for f in tex_files]

        missing_files = [f for f in expected_files if f not in found_files]
        if missing_files:
            print(f"❌ ERROR: Missing expected files: {missing_files}")
            return False

        print("✅ SUCCESS: All expected tex files found in wheel!")
        return True


def main():
    """Main test function."""
    print("Starting package installation and tex file detection test...\n")

    try:
        # Test wheel contents first
        wheel_test = test_wheel_contents()
        if not wheel_test:
            return False

        # Test actual installation and detection
        install_test = test_package_installation()
        if not install_test:
            return False

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Tex files are correctly packaged and detected in installed package")
        print("✅ Guillaume's issue should be resolved!")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
