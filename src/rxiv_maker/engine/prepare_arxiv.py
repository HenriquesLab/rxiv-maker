"""Prepare arXiv submission package from Rxiv-Maker output.

This script creates a clean, self-contained package suitable for arXiv submission
by copying and modifying the necessary files to remove dependencies on minted
and other shell-escape requiring packages.
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def prepare_arxiv_package(output_dir="./output", arxiv_dir=None, manuscript_path=None):
    """Prepare arXiv submission package.

    Args:
        output_dir (str): Path to the Rxiv-Maker output directory
        arxiv_dir (str): Path where arXiv submission files will be created
                        If None, defaults to {output_dir}/arxiv_submission
        manuscript_path (str): Path to the source manuscript directory
                              (for context and naming)
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

    manuscript_name = Path(manuscript_path).name if manuscript_path else "manuscript"
    print(f"Preparing arXiv submission package for '{manuscript_name}' in {arxiv_path}")

    # Copy the unified style file (already arXiv-compatible)
    # Try multiple possible locations for the style file
    style_candidates = [
        Path("src/tex/style/rxiv_maker_style.cls"),  # From repository root
        (Path(__file__).parent.parent.parent / "tex/style/rxiv_maker_style.cls"),  # Relative to script
        (Path(__file__).parent.parent.parent.parent / "src/tex/style/rxiv_maker_style.cls"),  # Alternative relative
        output_path / "rxiv_maker_style.cls",  # Already in output directory
    ]

    style_source = None
    for candidate in style_candidates:
        if candidate.exists():
            style_source = candidate
            break

    if style_source is None:
        raise FileNotFoundError(
            "Style file not found. Searched locations:\n"
            + "\n".join(f"  - {candidate}" for candidate in style_candidates)
            + "\nEnsure the script is run from the repository root or that "
            "the style file exists in the output directory."
        )

    shutil.copy2(style_source, arxiv_path / "rxiv_maker_style.cls")
    print(f"✓ Copied unified arXiv-compatible style file from {style_source}")

    # Determine the main manuscript file name by looking for .tex files
    tex_files = list(output_path.glob("*.tex"))
    main_tex_file = None

    # Find the main manuscript file (not Supplementary.tex)
    for tex_file in tex_files:
        if tex_file.name != "Supplementary.tex":
            main_tex_file = tex_file.name
            break

    if not main_tex_file:
        output_files = list(output_path.glob("*"))
        raise FileNotFoundError(
            f"No main LaTeX file found in output directory: {output_path}\n"
            f"Found files: {[f.name for f in output_files]}\n"
            f"Expected: A .tex file (not Supplementary.tex) from manuscript compilation"
        )

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
                with open(source_file, encoding="utf-8") as f:
                    content = f.read()

                # Fix arXiv-specific issues
                # 1. Fix escaped underscores in \includegraphics paths
                import re

                # Replace all \_ with _ inside \includegraphics{...} commands
                def fix_includegraphics_underscores(match):
                    graphics_cmd = match.group(0)
                    return graphics_cmd.replace("\\_", "_")

                content = re.sub(r"\\includegraphics\[[^\]]*\]\{[^}]*\}", fix_includegraphics_underscores, content)

                # 2. Fix malformed chemical equations with \textsuperscript in math mode
                content = re.sub(
                    r"\\text\{([^}]*)\}\\textsuperscript\{\{\\text\{([^}]*)\}\}([^\]]*?)\]",
                    r"\\text{\1}^{\\text{\2}}\3]",
                    content,
                )

                # Fix specific malformed equation patterns
                content = content.replace(
                    r"[\text{Ca}\textsuperscript{{\text{2+}}][\text{SO}_4}{\text{2-}}]",
                    r"[\text{Ca}^{\text{2+}}][\text{SO}_4^{\text{2-}}]",
                )

                # Also fix the case where SO4 part is malformed
                content = content.replace(r"[\text{SO}_4}{\text{2-}}]", r"[\text{SO}_4^{\text{2-}}]")

                # No need to replace documentclass - unified style is arXiv-compatible
                # Keep the original style file name since it's unified
                # Write the modified content
                with open(arxiv_path / filename, "w", encoding="utf-8") as f:
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

                # Copy markdown files for tables (STable directories)
                for md_file in figure_dir.glob("*.md"):
                    shutil.copy2(md_file, dest_dir / md_file.name)
                    print(f"✓ Copied {md_file.relative_to(output_path)}")

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
    package_valid = verify_package(arxiv_path, manuscript_path)

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


def verify_package(arxiv_path, manuscript_path=None):
    """Verify that the arXiv package contains all necessary files."""
    manuscript_name = Path(manuscript_path).name if manuscript_path else "manuscript"
    print(f"\n🔍 Verifying package contents for '{manuscript_name}'...")

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

    # Dynamic figure detection - scan for actual figure directories
    required_figures = []
    figures_dir = arxiv_path / "Figures"
    if figures_dir.exists():
        # Find all figure directories and check for PNG/PDF files
        for figure_dir in figures_dir.iterdir():
            if figure_dir.is_dir() and not figure_dir.name.startswith("."):
                # Look for PNG files first (preferred by arXiv)
                png_files = list(figure_dir.glob("*.png"))
                pdf_files = list(figure_dir.glob("*.pdf"))
                md_files = list(figure_dir.glob("*.md"))

                if png_files:
                    # Use first PNG file found
                    required_figures.append(f"Figures/{figure_dir.name}/{png_files[0].name}")
                elif pdf_files:
                    # Fallback to PDF if no PNG
                    required_figures.append(f"Figures/{figure_dir.name}/{pdf_files[0].name}")
                elif md_files:
                    # Use markdown files for tables (STable directories)
                    required_figures.append(f"Figures/{figure_dir.name}/{md_files[0].name}")
                elif figure_dir.name == "DATA":
                    # DATA directory may be empty or contain data files - don't flag as missing
                    pass
                else:
                    # Directory exists but no suitable figure files
                    required_figures.append(f"Figures/{figure_dir.name}/<missing figure files>")

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
        print(f"\n⚠ Warning: {len(missing_files)} files are missing from '{manuscript_name}' package!")
        print("The package may not compile correctly on arXiv.")
        print("Missing files:")
        for missing in missing_files:
            print(f"  - {missing}")
    else:
        print(f"\n✅ All required files present for '{manuscript_name}' package!")

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
                with open(log_file, encoding="utf-8") as f:
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
                with open(log_file, encoding="utf-8") as f:
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


def create_zip_package(arxiv_path, zip_filename="for_arxiv.zip", manuscript_path=None):
    """Create a ZIP file for arXiv submission."""
    # Use manuscript-aware naming if manuscript path is provided
    if manuscript_path and zip_filename == "for_arxiv.zip":
        manuscript_name = Path(manuscript_path).name
        zip_filename = f"{manuscript_name}_for_arxiv.zip"

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


def main() -> int:
    """Main entry point for the prepare arxiv command.

    Returns:
        0 for success, 1 for failure
    """
    import argparse

    parser = argparse.ArgumentParser(description="Prepare arXiv submission package")
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Path to the Rxiv-Maker output directory (default: ./output)",
    )
    parser.add_argument("--arxiv-dir", help="Path where arXiv submission files will be created")
    parser.add_argument(
        "--manuscript-path",
        default=".",
        help="Path to the source manuscript directory (default: .)",
    )
    parser.add_argument(
        "--test-compilation",
        action="store_true",
        help="Test LaTeX compilation after preparing package",
    )
    parser.add_argument("--create-zip", action="store_true", help="Create ZIP package for submission")
    parser.add_argument(
        "--zip-filename",
        default="for_arxiv.zip",
        help="Name of the ZIP file to create (default: for_arxiv.zip)",
    )

    args = parser.parse_args()

    try:
        # Prepare the arXiv package
        arxiv_path = prepare_arxiv_package(
            output_dir=args.output_dir,
            arxiv_dir=args.arxiv_dir,
            manuscript_path=args.manuscript_path,
        )

        # Verify the package
        verify_result = verify_package(arxiv_path, args.manuscript_path)
        if not verify_result:
            print("❌ Package verification failed")
            return 1

        # Test compilation if requested
        if args.test_compilation:
            test_result = test_arxiv_compilation(arxiv_path)
            if not test_result:
                print("❌ Test compilation failed")
                return 1

        # Create ZIP package if requested
        if args.create_zip:
            zip_path = create_zip_package(arxiv_path, args.zip_filename, args.manuscript_path)
            print(f"✅ arXiv package ready: {zip_path}")
        else:
            print(f"✅ arXiv package ready: {arxiv_path}")

        return 0

    except Exception as e:
        print(f"❌ Error preparing arXiv package: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
