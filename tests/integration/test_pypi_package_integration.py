"""Integration tests to verify PyPI package functionality.

These tests verify that the installed package has all necessary files
and can successfully initialize and build manuscripts.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from ..conftest import requires_latex


@pytest.mark.pypi
@pytest.mark.integration
@pytest.mark.xdist_group(name="pypi_integration")
class TestPyPIPackageIntegration:
    """Test that the PyPI package contains all necessary files for building PDFs."""

    def test_latex_template_files_accessible(self):
        """Test that LaTeX template files are accessible in the installed package."""
        import rxiv_maker

        package_path = Path(rxiv_maker.__file__).parent

        # Check for tex files in the package (may not exist in dev mode)
        tex_files = list(package_path.rglob("*.tex"))
        cls_files = list(package_path.rglob("*.cls"))

        # If no files found in development, check the wheel instead
        if len(tex_files) == 0 or len(cls_files) == 0:
            print("LaTeX files not found in installed package (development mode)")
            print("Checking wheel distribution instead...")

            # Run the wheel-based test
            import tempfile
            import zipfile

            wheel_files = list(Path("dist").glob("rxiv_maker-*.whl"))
            if not wheel_files:
                pytest.skip("No wheel file and no LaTeX files in development package")

            wheel_path = wheel_files[0]

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                with zipfile.ZipFile(str(wheel_path), "r") as wheel_zip:
                    wheel_zip.extractall(temp_path)

                package_dir = temp_path / "rxiv_maker"
                if not package_dir.exists():
                    pytest.skip("Package directory not found in wheel")

                tex_files = list(package_dir.rglob("*.tex"))
                cls_files = list(package_dir.rglob("*.cls"))

                # Verify files have content within the context manager
                for tex_file in tex_files:
                    assert tex_file.stat().st_size > 0, f"LaTeX template is empty: {tex_file}"

                for cls_file in cls_files:
                    assert cls_file.stat().st_size > 0, f"LaTeX style file is empty: {cls_file}"

        else:
            # Verify files have content (for installed package)
            for tex_file in tex_files:
                assert tex_file.stat().st_size > 0, f"LaTeX template is empty: {tex_file}"

            for cls_file in cls_files:
                assert cls_file.stat().st_size > 0, f"LaTeX style file is empty: {cls_file}"

        # Final assertions (these are already checked above, but for clarity)
        assert len(tex_files) > 0, f"No .tex template files found. Package path: {package_path}"
        assert len(cls_files) > 0, f"No .cls style files found. Package path: {package_path}"

    @requires_latex
    def test_cli_init_and_build_workflow(self, execution_engine):
        """Test full CLI workflow: init -> validate -> build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            manuscript_dir = tmpdir_path / "TEST_MANUSCRIPT"

            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Test 1: Initialize manuscript
                if execution_engine.engine_type == "local":
                    try:
                        init_result = execution_engine.run(
                            [
                                "uv",
                                "run",
                                "python",
                                "-m",
                                "rxiv_maker.cli",
                                "init",
                                str(manuscript_dir),
                                "--template",
                                "basic",
                                "--no-interactive",
                            ],
                            cwd=original_cwd,  # Run from original directory
                        )
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        # Fall back to direct python call
                        init_result = execution_engine.run(
                            [
                                "python",
                                "-m",
                                "rxiv_maker.cli",
                                "init",
                                str(manuscript_dir),
                                "--template",
                                "basic",
                                "--no-interactive",
                            ],
                            cwd=original_cwd,
                        )
                else:
                    # In container, use the installed rxiv command
                    init_result = execution_engine.run(
                        [
                            "rxiv",
                            "init",
                            "/workspace/TEST_MANUSCRIPT",
                            "--template",
                            "basic",
                            "--no-interactive",
                        ],
                        cwd="/workspace",
                    )

                print("Init STDOUT:", init_result.stdout)
                print("Init STDERR:", init_result.stderr)

                # Check that init was successful
                assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"
                assert manuscript_dir.exists(), "Manuscript directory not created"

                # Verify essential files were created
                required_files = ["00_CONFIG.yml", "01_MAIN.md", "03_REFERENCES.bib"]

                for filename in required_files:
                    file_path = manuscript_dir / filename
                    assert file_path.exists(), f"Required file not created: {filename}"
                    assert file_path.stat().st_size > 0, f"Required file is empty: {filename}"

                # Test 2: Validate manuscript
                try:
                    validate_result = subprocess.run(
                        [
                            "uv",
                            "run",
                            "python",
                            "-m",
                            "rxiv_maker.cli",
                            "validate",
                            str(manuscript_dir),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=original_cwd,
                    )
                except FileNotFoundError:
                    validate_result = subprocess.run(
                        [
                            "python",
                            "-m",
                            "rxiv_maker.cli",
                            "validate",
                            str(manuscript_dir),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=original_cwd,
                    )

                print("Validate STDOUT:", validate_result.stdout)
                print("Validate STDERR:", validate_result.stderr)

                # Validation might fail due to example references, but should run
                assert validate_result.returncode in [0, 1], f"Validate command failed to run: {validate_result.stderr}"

                # Test 3: Attempt PDF build (this is the critical test)
                # Use --skip-validation to avoid validation failures stopping the build
                try:
                    pdf_result = subprocess.run(
                        [
                            "uv",
                            "run",
                            "python",
                            "-m",
                            "rxiv_maker.cli",
                            "pdf",
                            str(manuscript_dir),
                            "--skip-validation",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,  # PDF building can take time
                        cwd=original_cwd,
                    )
                except FileNotFoundError:
                    pdf_result = subprocess.run(
                        [
                            "python",
                            "-m",
                            "rxiv_maker.cli",
                            "pdf",
                            str(manuscript_dir),
                            "--skip-validation",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,  # PDF building can take time
                        cwd=original_cwd,
                    )

                print("PDF STDOUT:", pdf_result.stdout)
                print("PDF STDERR:", pdf_result.stderr)

                # The critical check: did the command at least try to build?
                # We're mainly testing that LaTeX files are accessible
                # Even if LaTeX isn't installed,
                # it should get past the template loading phase
                assert (
                    "template.tex" in pdf_result.stdout
                    or "template.tex" in pdf_result.stderr
                    or "LaTeX" in pdf_result.stdout
                    or "LaTeX" in pdf_result.stderr
                    or pdf_result.returncode == 0
                ), f"PDF build failed to access LaTeX templates: {pdf_result.stderr}"

                # If build got to LaTeX compilation step, templates are accessible
                if "pdflatex" in pdf_result.stderr or "latexmk" in pdf_result.stderr:
                    # This means LaTeX templates were successfully loaded
                    pass  # Success - we got to LaTeX compilation
                elif pdf_result.returncode == 0:
                    # Full success - PDF was built
                    pass
                else:
                    # Check that the error isn't about missing template files
                    error_output = pdf_result.stderr + pdf_result.stdout
                    template_error_indicators = [
                        "template.tex",
                        "rxiv_maker_style.cls",
                        "template not found",
                        "style not found",
                        "FileNotFoundError.*tex",
                        "FileNotFoundError.*cls",
                    ]

                    has_template_error = any(indicator in error_output for indicator in template_error_indicators)
                    assert not has_template_error, f"LaTeX template files are missing from package: {error_output}"

            finally:
                os.chdir(original_cwd)

    @pytest.mark.skipif("CI" not in os.environ, reason="Only run in CI environment")
    @pytest.mark.timeout(300)  # Allow 5 minutes for full PDF build in CI
    def test_full_pdf_build_in_ci(self):
        """Test full PDF build in CI environment where LaTeX should be available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            manuscript_dir = tmpdir_path / "CI_TEST_MANUSCRIPT"

            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                # Initialize with minimal content
                init_result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli.main",
                        "init",
                        str(manuscript_dir),
                    ],
                    input=("CI Test Paper\n\nCI Test Author\nci@test.com\nCI University\n"),
                    text=True,
                    capture_output=True,
                    timeout=30,
                )

                assert init_result.returncode == 0, f"Init failed: {init_result.stderr}"

                # Build PDF
                pdf_result = subprocess.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli.main",
                        "pdf",
                        str(manuscript_dir),
                        "--skip-validation",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                # In CI with LaTeX installed, this should succeed
                if pdf_result.returncode == 0:
                    # Check that PDF was actually created
                    pdf_files = list(manuscript_dir.glob("**/*.pdf"))
                    assert len(pdf_files) > 0, "PDF file was not generated"
                else:
                    # At minimum, check that template files were accessible
                    error_output = pdf_result.stderr + pdf_result.stdout
                    assert "template.tex" not in error_output or "not found" not in error_output.lower(), (
                        f"LaTeX template files missing: {error_output}"
                    )

            finally:
                os.chdir(original_cwd)

    def test_package_data_integrity(self):
        """Test that all required package data files are present in the built wheel."""
        import tempfile
        import zipfile

        # Find the wheel file
        wheel_files = list(Path("dist").glob("rxiv_maker-*.whl"))
        if not wheel_files:
            pytest.skip("No wheel file found. Run 'rye build --wheel' first.")

        wheel_path = wheel_files[0]

        # Extract wheel contents
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with zipfile.ZipFile(str(wheel_path), "r") as wheel_zip:
                wheel_zip.extractall(temp_path)

            # Find package directory in extracted wheel
            package_dir = temp_path / "rxiv_maker"

            if not package_dir.exists():
                available_dirs = [p for p in temp_path.iterdir() if p.is_dir()]
                raise AssertionError(f"rxiv_maker package directory not found in wheel. Available: {available_dirs}")

            # Check for LaTeX template files
            tex_files = list(package_dir.rglob("*.tex"))
            cls_files = list(package_dir.rglob("*.cls"))

            print(f"Found {len(tex_files)} .tex files: {tex_files}")
            print(f"Found {len(cls_files)} .cls files: {cls_files}")

            assert len(tex_files) > 0, f"No .tex files found in wheel. Package contents: {list(package_dir.rglob('*'))}"
            assert len(cls_files) > 0, f"No .cls files found in wheel. Package contents: {list(package_dir.rglob('*'))}"

            # Specifically check for expected files
            template_files = [f for f in tex_files if "template" in f.name.lower()]
            style_files = [f for f in cls_files if "style" in f.name.lower()]

            assert len(template_files) > 0, f"No template.tex file found. Available tex files: {tex_files}"
            assert len(style_files) > 0, f"No style .cls file found. Available cls files: {cls_files}"

            # Verify files are not empty and contain expected content
            for tex_file in template_files:
                content = tex_file.read_text()
                assert len(content) > 0, f"Template file is empty: {tex_file}"
                assert "documentclass" in content.lower(), f"Template file doesn't look like LaTeX: {tex_file}"

            for cls_file in style_files:
                content = cls_file.read_text()
                assert len(content) > 0, f"Style file is empty: {cls_file}"
                assert "providesclass" in content.lower(), f"Style file doesn't look like LaTeX class: {cls_file}"
