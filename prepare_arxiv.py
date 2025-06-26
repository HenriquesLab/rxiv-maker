#!/usr/bin/env python3
"""Prepare arXiv submission package from Rxiv-Maker output.

This script creates a clean, self-contained package suitable for arXiv submission
by copying and modifying the necessary files to remove dependencies on minted
and other shell-escape requiring packages.

Usage:
    python prepare_arxiv.py [--output-dir DIR]
"""

import argparse
import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def prepare_arxiv_package(output_dir="./output", arxiv_dir=None):
    """Prepare arXiv submission package.

    Args:
        output_dir (str): Path to the Rxiv-Maker output directory
        arxiv_dir (str): Path where arXiv submission files will be created
                        If None, defaults to {output_dir}/arxiv_submission
    """
    output_path = Path(output_dir)

    # Default arXiv directory to be inside the output directory
    if arxiv_dir is None:
        arxiv_dir = output_path / "arxiv_submission"

    arxiv_path = Path(arxiv_dir)

    # Create clean arxiv directory
    if arxiv_path.exists():
        shutil.rmtree(arxiv_path)
    arxiv_path.mkdir(parents=True)

    print(f"Preparing arXiv submission package in {arxiv_path}")

    # Copy the unified style file (already arXiv-compatible)
    style_source = Path("src/tex/style/rxiv_maker_style.cls")
    if not style_source.exists():
        raise FileNotFoundError(f"Style file not found: {style_source}")

    shutil.copy2(style_source, arxiv_path / "rxiv_maker_style.cls")
    print("✓ Copied unified arXiv-compatible style file")

    # Determine the main manuscript file name by looking for .tex files
    tex_files = list(output_path.glob("*.tex"))
    main_tex_file = None

    # Find the main manuscript file (not Supplementary.tex)
    for tex_file in tex_files:
        if tex_file.name != "Supplementary.tex":
            main_tex_file = tex_file.name
            break

    if not main_tex_file:
        raise FileNotFoundError("No main LaTeX file found in output directory")

    # Base name without extension for .bbl file
    main_name = main_tex_file.replace(".tex", "")

    # Copy main LaTeX files
    main_files = [
        main_tex_file,
        "Supplementary.tex",
        "03_REFERENCES.bib",
        f"{main_name}.bbl",  # Include compiled bibliography if it exists
        "rxiv_maker_style.bst",  # Bibliography style file
    ]

    for filename in main_files:
        source_file = output_path / filename
        if source_file.exists():
            # Copy and modify the main tex file to use arxiv style
            if filename == main_tex_file:
                with open(source_file) as f:
                    content = f.read()
                # No need to replace documentclass - unified style is arXiv-compatible
                # Keep the original style file name since it's unified
                # Write the modified content
                with open(arxiv_path / filename, "w") as f:
                    f.write(content)
                print(f"✓ Copied and modified {filename} for arXiv compatibility")
            else:
                shutil.copy2(source_file, arxiv_path / filename)
                print(f"✓ Copied {filename}")
        else:
            if filename.endswith(".bbl") or filename.endswith(".bst"):
                print(f"⚠ Optional file not found: {filename}")
            else:
                print(f"✗ Required file not found: {filename}")

    # Copy all figure files
    figures_source = output_path / "Figures"
    if figures_source.exists():
        figures_dest = arxiv_path / "Figures"

        # Copy figure directories with PNG files (arXiv preferred format)
        for figure_dir in figures_source.iterdir():
            if figure_dir.is_dir() and not figure_dir.name.startswith("."):
                dest_dir = figures_dest / figure_dir.name
                dest_dir.mkdir(parents=True, exist_ok=True)

                # Copy PNG files
                for png_file in figure_dir.glob("*.png"):
                    shutil.copy2(png_file, dest_dir / png_file.name)
                    print(f"✓ Copied {png_file.relative_to(output_path)}")

                # Also copy PDF files as backup
                for pdf_file in figure_dir.glob("*.pdf"):
                    shutil.copy2(pdf_file, dest_dir / pdf_file.name)
                    print(f"✓ Copied {pdf_file.relative_to(output_path)}")

        # Copy data files if they exist
        data_dir = figures_source / "DATA"
        if data_dir.exists():
            data_dest = figures_dest / "DATA"
            if data_dest.exists():
                shutil.rmtree(data_dest)
            shutil.copytree(data_dir, data_dest)
            print("✓ Copied DATA directory")

    print(f"\n📦 arXiv package prepared in {arxiv_path}")

    # Verify all required files are present
    package_valid = verify_package(arxiv_path)

    if not package_valid:
        print("⚠️  Package verification failed - some files are missing")
        return arxiv_path

    # Test compilation to ensure the package builds correctly
    compilation_success = test_arxiv_compilation(arxiv_path)

    if not compilation_success:
        print("❌ arXiv package compilation test failed!")
        print("   The package may not build correctly on arXiv.")
        print("   Please check the LaTeX errors above and fix them before submission.")
    else:
        print("✅ arXiv package compilation test passed!")
        print("   The package should build correctly on arXiv.")

    # Store compilation result for later use
    prepare_arxiv_package.compilation_success = compilation_success

    return arxiv_path


def verify_package(arxiv_path):
    """Verify that the arXiv package contains all necessary files."""
    print("\n🔍 Verifying package contents...")

    # Find the main manuscript file dynamically
    tex_files = list(arxiv_path.glob("*.tex"))
    main_tex_file = None

    for tex_file in tex_files:
        if tex_file.name != "Supplementary.tex":
            main_tex_file = tex_file.name
            break

    if not main_tex_file:
        print("✗ No main LaTeX file found")
        return False

    required_files = [
        main_tex_file,
        "Supplementary.tex",
        "rxiv_maker_style.cls",
        "03_REFERENCES.bib",
    ]

    required_figures = [
        "Figures/Figure_1/Figure_1.png",
        "Figures/Figure_2/Figure_2.png",
        "Figures/SFigure_1/SFigure_1.png",
        "Figures/SFigure_2/SFigure_2.png",
    ]

    missing_files = []

    # Check required files
    for filename in required_files:
        file_path = arxiv_path / filename
        if file_path.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ Missing: {filename}")
            missing_files.append(filename)

    # Check required figures
    for figure_path in required_figures:
        file_path = arxiv_path / figure_path
        if file_path.exists():
            print(f"✓ {figure_path}")
        else:
            print(f"✗ Missing: {figure_path}")
            missing_files.append(figure_path)

    if missing_files:
        print(f"\n⚠ Warning: {len(missing_files)} files are missing!")
        print("The package may not compile correctly on arXiv.")
    else:
        print("\n✅ All required files present!")

    return len(missing_files) == 0


def test_arxiv_compilation(arxiv_path):
    """Test compilation of the arXiv package to ensure it builds correctly."""
    print("\n🔨 Testing arXiv package compilation...")

    # Change to the arXiv directory for compilation
    original_cwd = os.getcwd()
    os.chdir(arxiv_path)

    try:
        # Find the main manuscript file dynamically
        tex_files = list(Path(".").glob("*.tex"))
        tex_file = None

        for tf in tex_files:
            if tf.name != "Supplementary.tex":
                tex_file = tf.name
                break

        if not tex_file or not Path(tex_file).exists():
            print(f"❌ LaTeX file not found: {tex_file}")
            return False

        # First pass
        print("  Running first pdflatex pass...")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        # BibTeX pass
        if Path("03_REFERENCES.bib").exists():
            print("  Running bibtex...")
            main_name = tex_file.replace(".tex", "")
            subprocess.run(
                ["bibtex", main_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

        # Second pass
        print("  Running second pdflatex pass...")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        # Third pass for cross-references
        print("  Running final pdflatex pass...")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        # Check if PDF was created
        main_name = tex_file.replace(".tex", "")
        pdf_file = f"{main_name}.pdf"
        log_file = f"{main_name}.log"

        if Path(pdf_file).exists():
            pdf_size = Path(pdf_file).stat().st_size
            print(f"✅ PDF compilation successful! Size: {pdf_size:,} bytes")

            # Check for common LaTeX warnings/errors in log
            if Path(log_file).exists():
                with open(log_file) as f:
                    log_content = f.read()

                error_count = log_content.count("! ")
                warning_count = log_content.count("Warning:")

                if error_count > 0:
                    print(f"⚠️  Found {error_count} LaTeX errors in log")
                    # Extract first few errors for display
                    errors = []
                    for line in log_content.split("\n"):
                        if line.startswith("! "):
                            errors.append(line)
                            if len(errors) >= 3:  # Show first 3 errors
                                break
                    for error in errors:
                        print(f"    {error}")

                if warning_count > 0:
                    print(f"📝 Found {warning_count} LaTeX warnings in log")

                if error_count == 0:
                    print("✅ No LaTeX errors detected")

            return True
        else:
            print("❌ PDF compilation failed - no output PDF generated")

            # Show compilation errors from log if available
            if Path(log_file).exists():
                with open(log_file) as f:
                    log_content = f.read()
                    print("\n📋 Last few lines from compilation log:")
                    lines = log_content.split("\n")
                    for line in lines[-10:]:  # Show last 10 lines
                        if line.strip():
                            print(f"    {line}")

            return False

    except Exception as e:
        print(f"❌ Compilation test failed with exception: {e}")
        return False
    finally:
        # Always return to original directory
        os.chdir(original_cwd)


def create_zip_package(arxiv_path, zip_filename="for_arxiv.zip"):
    """Create a ZIP file for arXiv submission."""
    zip_path = Path(zip_filename).resolve()

    print(f"\n📁 Creating ZIP package: {zip_path}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in arxiv_path.rglob("*"):
            if file_path.is_file():
                # Store files with relative paths
                arcname = file_path.relative_to(arxiv_path)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")

    print(f"✅ ZIP package created: {zip_path}")
    print("📤 Ready for arXiv submission!")

    return zip_path


def main():
    """Main entry point for preparing arXiv submission package."""
    parser = argparse.ArgumentParser(description="Prepare arXiv submission package")
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Path to Rxiv-Maker output directory (default: ./output)",
    )
    parser.add_argument(
        "--arxiv-dir",
        default=None,
        help="Path for arXiv submission files (default: {output_dir}/arxiv_submission)",
    )
    parser.add_argument(
        "--zip", action="store_true", help="Create ZIP file for submission"
    )
    parser.add_argument(
        "--zip-filename",
        default="for_arxiv.zip",
        help="Name of ZIP file (default: for_arxiv.zip)",
    )

    args = parser.parse_args()

    try:
        # Prepare the package
        arxiv_path = prepare_arxiv_package(args.output_dir, args.arxiv_dir)

        # Create ZIP if requested (only if compilation was successful)
        if args.zip:
            # Check if compilation test was run and passed
            if hasattr(prepare_arxiv_package, "compilation_success"):
                if prepare_arxiv_package.compilation_success:
                    create_zip_package(arxiv_path, args.zip_filename)
                else:
                    print("⚠️  Skipping ZIP creation due to compilation test failure")
                    print("   Fix the LaTeX errors and try again")
                    return 1
            else:
                # If no test was run, create ZIP anyway (backward compatibility)
                create_zip_package(arxiv_path, args.zip_filename)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
