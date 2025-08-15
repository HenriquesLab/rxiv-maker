"""Track changes functionality for Rxiv-Maker.

This module provides change tracking capabilities by comparing the current
manuscript against a specified git tag using latexdiff.
"""

import builtins
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Local implementations to avoid import issues
import yaml


def extract_yaml_metadata_local(yaml_file_path: str) -> dict:
    """Extract YAML metadata from a config file."""
    try:
        with open(yaml_file_path, encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except Exception:
        return {}


def get_custom_pdf_filename_local(yaml_metadata: dict) -> str:
    """Generate custom PDF filename from metadata."""
    # Get current year as fallback
    current_year = str(datetime.now().year)

    # Extract date (year only)
    date = yaml_metadata.get("date", current_year)
    year = date[:4] if isinstance(date, str) and len(date) >= 4 else current_year

    # Extract lead_author from title metadata
    title_info = yaml_metadata.get("title", {})
    if isinstance(title_info, list):
        # Find lead_author in the list
        lead_author = None
        for item in title_info:
            if isinstance(item, dict) and "lead_author" in item:
                lead_author = item["lead_author"]
                break
        if not lead_author:
            lead_author = "unknown"
    elif isinstance(title_info, dict):
        lead_author = title_info.get("lead_author", "unknown")
    else:
        lead_author = "unknown"

    # Clean the lead author name (remove spaces, make lowercase)
    lead_author_clean = lead_author.lower().replace(" ", "_").replace(".", "")

    # Generate filename: year__lead_author_et_al__rxiv.pdf
    filename = f"{year}__{lead_author_clean}_et_al__rxiv.pdf"

    return filename


class TrackChangesManager:
    """Manage change tracking between current manuscript and a git tag."""

    def __init__(
        self,
        manuscript_path: str,
        output_dir: str = "output",
        git_tag: str = "",
        verbose: bool = False,
    ):
        """Initialize track changes manager.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory for generated files
            git_tag: Git tag to compare against
            verbose: Enable verbose output
        """
        self.manuscript_path = Path(manuscript_path)
        self.output_dir = Path(output_dir)
        self.git_tag = git_tag
        self.verbose = verbose

        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)

        # Define expected manuscript files
        self.manuscript_files = [
            "01_MAIN.md",
            "02_SUPPLEMENTARY_INFO.md",
            "00_CONFIG.yml",
            "03_REFERENCES.bib",
        ]

    def log(self, message: str, force: bool = False):
        """Log a message if verbose mode is enabled.

        Args:
            message: Message to log
            force: Force logging even if not in verbose mode
        """
        if self.verbose or force:
            print(f"🔍 {message}")

    def validate_git_tag(self) -> bool:
        """Validate that the specified git tag exists.

        Returns:
            True if tag exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "tag", "-l", self.git_tag],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip() == self.git_tag
        except subprocess.CalledProcessError:
            return False

    def extract_files_from_tag(self, temp_dir: Path) -> bool:
        """Extract manuscript files from the specified git tag.

        Args:
            temp_dir: Temporary directory to extract files to

        Returns:
            True if extraction successful, False otherwise
        """
        self.log(f"Extracting files from git tag: {self.git_tag}")

        # Create manuscript directory in temp location
        tag_manuscript_dir = temp_dir / "tag_manuscript"
        tag_manuscript_dir.mkdir()

        # Extract each manuscript file from the tag
        for file_name in self.manuscript_files:
            file_path = self.manuscript_path / file_name
            if not file_path.exists():
                self.log(f"Skipping {file_name} (not found in current manuscript)")
                continue

            try:
                # Try to extract file from git tag
                result = subprocess.run(
                    [
                        "git",
                        "show",
                        f"{self.git_tag}:{self.manuscript_path.name}/{file_name}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Write extracted content to temp directory
                (tag_manuscript_dir / file_name).write_text(result.stdout, encoding="utf-8")
                self.log(f"Extracted {file_name} from tag {self.git_tag}")

            except subprocess.CalledProcessError as e:
                self.log(f"Warning: Could not extract {file_name} from tag {self.git_tag}: {e}")
                continue

        return True

    def generate_latex_files(self, manuscript_dir: Path, output_subdir: str) -> bool:
        """Generate LaTeX files from a manuscript directory.

        Args:
            manuscript_dir: Directory containing manuscript files
            output_subdir: Subdirectory name in output directory

        Returns:
            True if generation successful, False otherwise
        """
        latex_output_dir = self.output_dir / output_subdir
        latex_output_dir.mkdir(exist_ok=True)

        try:
            self.log(f"Generating LaTeX files from {manuscript_dir}")

            # Use subprocess approach like BuildManager does
            cmd = [
                sys.executable,
                "src/rxiv_maker/commands/generate_preprint.py",
                "--output-dir",
                str(latex_output_dir),
            ]

            # Set environment variables like BuildManager does
            env = os.environ.copy()
            env["MANUSCRIPT_PATH"] = str(manuscript_dir)

            result = subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)

            if self.verbose:
                self.log(f"LaTeX generation output: {result.stdout}")

            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Error generating LaTeX files: {e}", force=True)
            if e.stderr:
                self.log(f"stderr: {e.stderr}", force=True)
            return False
        except Exception as e:
            self.log(f"Error generating LaTeX files: {e}", force=True)
            return False

    def run_latexdiff(self, old_tex: Path, new_tex: Path, diff_tex: Path) -> bool:
        """Run latexdiff to generate difference file.

        Args:
            old_tex: Path to old LaTeX file
            new_tex: Path to new LaTeX file
            diff_tex: Path to output difference file

        Returns:
            True if latexdiff successful, False otherwise
        """
        if not old_tex.exists():
            self.log(f"Warning: Old LaTeX file {old_tex} does not exist")
            return False

        if not new_tex.exists():
            self.log(f"Warning: New LaTeX file {new_tex} does not exist")
            return False

        try:
            self.log(f"Running latexdiff: {old_tex.name} -> {new_tex.name}")

            # Run latexdiff with appropriate options
            cmd = [
                "latexdiff",
                "--type=UNDERLINE",
                "--subtype=SAFE",
                "--flatten",
                "--encoding=utf8",
                str(old_tex),
                str(new_tex),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace",
            )

            # Write diff output to file
            diff_tex.write_text(result.stdout, encoding="utf-8")
            self.log(f"Generated diff file: {diff_tex}")

            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Error running latexdiff: {e}", force=True)
            if e.stderr:
                self.log(f"latexdiff stderr: {e.stderr}", force=True)
            return False

    def compile_diff_pdf(self, diff_tex: Path) -> bool:
        """Compile the difference LaTeX file to PDF.

        Args:
            diff_tex: Path to difference LaTeX file

        Returns:
            True if compilation successful, False otherwise
        """
        if not diff_tex.exists():
            self.log(f"Error: Diff LaTeX file {diff_tex} does not exist", force=True)
            return False

        try:
            self.log("Compiling change-tracked PDF...")

            # Change to output directory for compilation
            original_cwd = os.getcwd()
            os.chdir(diff_tex.parent)

            # Extract base name for bibtex
            tex_basename = diff_tex.stem

            # First LaTeX compilation pass - initial document processing
            self.log("LaTeX compilation pass 1/3 - processing document structure")
            result1 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", diff_tex.name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if result1.returncode != 0:
                self.log(f"LaTeX compilation pass 1 completed with warnings/errors (return code: {result1.returncode})")
                if self.verbose:
                    self.log(f"LaTeX output: {result1.stdout}")
                    self.log(f"LaTeX errors: {result1.stderr}")

            # Run bibtex if references exist (check in current working directory)
            # which is output_dir
            output_references = Path("03_REFERENCES.bib")
            if output_references.exists():
                self.log("Running BibTeX to process bibliography...")
                bibtex_result = subprocess.run(
                    ["bibtex", tex_basename],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                # Log BibTeX warnings and errors only
                if bibtex_result.stderr:
                    self.log(f"BibTeX errors: {bibtex_result.stderr}")
                elif "warning" in bibtex_result.stdout.lower():
                    # Count warnings but don't spam the output
                    warning_count = bibtex_result.stdout.lower().count("warning")
                    self.log(f"BibTeX completed with {warning_count} warning(s)")

                # Check for serious bibtex errors that would prevent citation resolution
                if bibtex_result.returncode != 0:
                    self.log(f"BibTeX returned error code {bibtex_result.returncode}")
                    # Check if .bbl file was still created despite errors
                    bbl_file = Path(f"{tex_basename}.bbl")
                    if not bbl_file.exists():
                        self.log(
                            "BibTeX failed to create .bbl file - citations will appear as ?",
                            force=True,
                        )
                        # Don't fail the build, just warn
                    else:
                        self.log("BibTeX created .bbl file despite errors")
                else:
                    self.log("BibTeX completed successfully")
            else:
                self.log("No bibliography file found, skipping BibTeX")

            # Second LaTeX compilation pass - bibliography integration
            self.log("LaTeX compilation pass 2/3 - integrating bibliography references")
            result2 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", diff_tex.name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if result2.returncode != 0:
                self.log(f"LaTeX compilation pass 2 completed with warnings/errors (return code: {result2.returncode})")
                if self.verbose:
                    self.log(f"LaTeX output: {result2.stdout}")
                    self.log(f"LaTeX errors: {result2.stderr}")

            # Final LaTeX compilation pass - cross-references and finalization
            self.log("LaTeX compilation pass 3/3 - finalizing cross-references and citations")
            result3 = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", diff_tex.name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if result3.returncode != 0:
                self.log(f"LaTeX compilation pass 3 completed with warnings/errors (return code: {result3.returncode})")
                if self.verbose:
                    self.log(f"LaTeX output: {result3.stdout}")
                    self.log(f"LaTeX errors: {result3.stderr}")

            # Check if PDF was generated (use the name from the current directory)
            pdf_name = diff_tex.with_suffix(".pdf").name
            Path(pdf_name)

            # Return to original directory for absolute path checking
            os.chdir(original_cwd)
            pdf_file = diff_tex.with_suffix(".pdf")

            if pdf_file.exists():
                self.log(f"✅ Change-tracked PDF generated: {pdf_file}")
                return True
            else:
                self.log("❌ PDF generation failed", force=True)
                return False

        except Exception as e:
            self.log(f"Error compiling PDF: {e}", force=True)
            return False
        finally:
            # Ensure we return to original directory
            with contextlib.suppress(builtins.BaseException):
                os.chdir(original_cwd)

    def generate_custom_filename(self) -> str:
        """Generate custom filename using the same convention as regular PDF generation.

        Returns:
            Custom filename with format: year__first_author_et_al__changes_vs_TAG.pdf
        """
        try:
            # Extract YAML metadata from current manuscript
            config_file = self.manuscript_path / "00_CONFIG.yml"
            if config_file.exists():
                yaml_metadata = extract_yaml_metadata_local(str(config_file))
                base_filename = get_custom_pdf_filename_local(yaml_metadata)
                # Replace the __rxiv.pdf suffix with __changes_vs_TAG.pdf
                custom_filename = base_filename.replace("__rxiv.pdf", f"__changes_vs_{self.git_tag}.pdf")
                return custom_filename
            else:
                self.log("Warning: 00_CONFIG.yml not found, using fallback naming")
                manuscript_name = self.manuscript_path.name
                return f"{manuscript_name}_changes_vs_{self.git_tag}.pdf"
        except Exception as e:
            self.log(f"Error generating custom filename: {e}")
            manuscript_name = self.manuscript_path.name
            return f"{manuscript_name}_changes_vs_{self.git_tag}.pdf"

    def generate_change_tracked_pdf(self) -> bool:
        """Generate a PDF with changes tracked against the specified git tag.

        Returns:
            True if successful, False otherwise
        """
        self.log(f"Starting change tracking against git tag: {self.git_tag}", force=True)

        # Validate git tag
        if not self.validate_git_tag():
            self.log(f"❌ Error: Git tag '{self.git_tag}' does not exist", force=True)
            return False

        # Create temporary directory for work
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract files from git tag
            if not self.extract_files_from_tag(temp_path):
                return False

            # Generate LaTeX files for both versions
            tag_manuscript_dir = temp_path / "tag_manuscript"

            self.log("Generating LaTeX files for current version...")
            if not self.generate_latex_files(self.manuscript_path, "current"):
                return False

            self.log("Generating LaTeX files for tag version...")
            if not self.generate_latex_files(tag_manuscript_dir, "tag"):
                return False

            # Find the main LaTeX files
            current_tex = self.output_dir / "current" / f"{self.manuscript_path.name}.tex"
            tag_tex = self.output_dir / "tag" / f"{tag_manuscript_dir.name}.tex"

            # Generate custom filename using the same convention as regular PDF
            # generation
            custom_filename = self.generate_custom_filename()
            diff_basename = custom_filename.replace(".pdf", "")
            diff_tex = self.output_dir / f"{diff_basename}.tex"

            # Run latexdiff
            if not self.run_latexdiff(tag_tex, current_tex, diff_tex):
                return False

            # Copy necessary files for compilation BEFORE compiling
            self.copy_compilation_files()

            # Compile to PDF
            if not self.compile_diff_pdf(diff_tex):
                return False

            # Copy PDF to manuscript directory
            pdf_file = self.output_dir / f"{diff_basename}.pdf"
            self.copy_pdf_to_manuscript(pdf_file)

            self.log("✅ Change tracking completed successfully!", force=True)
            self.log(f"📄 Output PDF: {custom_filename}", force=True)

            return True

    def copy_compilation_files(self):
        """Copy necessary files for LaTeX compilation."""
        # Copy style files from source
        style_files = [
            ("src/tex/style/rxiv_maker_style.cls", "rxiv_maker_style.cls"),
            ("src/tex/style/rxiv_maker_style.bst", "rxiv_maker_style.bst"),
        ]

        for src_path, dst_name in style_files:
            src_file = Path(src_path)
            dst_file = self.output_dir / dst_name

            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                self.log(f"Copied {dst_name} from {src_path}")
            else:
                self.log(f"Warning: Style file {src_path} not found")

        # Copy bibliography from current version
        self.output_dir / "current"
        bib_src = self.manuscript_path / "03_REFERENCES.bib"
        bib_dst = self.output_dir / "03_REFERENCES.bib"

        if bib_src.exists():
            shutil.copy2(bib_src, bib_dst)
            self.log("Copied 03_REFERENCES.bib")

        # Copy Figures directory from manuscript
        src_figures = self.manuscript_path / "FIGURES"
        dst_figures = self.output_dir / "Figures"

        if src_figures.exists():
            if dst_figures.exists():
                shutil.rmtree(dst_figures)
            shutil.copytree(src_figures, dst_figures)
            self.log("Copied Figures directory")
        else:
            self.log("No Figures directory found in manuscript")

    def copy_pdf_to_manuscript(self, pdf_file: Path) -> bool:
        """Copy the generated change tracking PDF to the manuscript directory.

        Args:
            pdf_file: Path to the generated PDF file

        Returns:
            True if copy successful, False otherwise
        """
        if not pdf_file.exists():
            self.log(f"Error: PDF file {pdf_file} does not exist", force=True)
            return False

        try:
            # Generate destination filename
            dest_filename = pdf_file.name
            dest_path = self.manuscript_path / dest_filename

            # Copy the PDF file
            shutil.copy2(pdf_file, dest_path)
            self.log(f"📄 PDF copied to manuscript directory: {dest_path}", force=True)

            return True

        except Exception as e:
            self.log(f"Error copying PDF to manuscript directory: {e}", force=True)
            return False
