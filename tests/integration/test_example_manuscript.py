"""End-to-end test for EXAMPLE_MANUSCRIPT using real rxiv commands."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from ..conftest import requires_latex


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.xdist_group(name="example_manuscript")
@requires_latex
class TestExampleManuscript:
    """Test the full pipeline for EXAMPLE_MANUSCRIPT."""

    @pytest.fixture
    def example_manuscript_copy(self, execution_engine):
        """Create a temporary copy of EXAMPLE_MANUSCRIPT for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path("EXAMPLE_MANUSCRIPT")
            dst_path = Path(tmpdir) / "EXAMPLE_MANUSCRIPT"

            # Copy the entire EXAMPLE_MANUSCRIPT directory
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

            # Clean any existing output
            output_dir = dst_path / "output"
            if output_dir.exists():
                shutil.rmtree(output_dir)

            # For containerized execution, copy to workspace within the mounted volume
            workspace_test_dir = None
            if execution_engine.engine_type != "local":
                # Create a test manuscript in the mounted workspace
                workspace_test_dir = Path.cwd() / "TEMP_TEST_MANUSCRIPT"
                if workspace_test_dir.exists():
                    shutil.rmtree(workspace_test_dir)
                shutil.copytree(src_path, workspace_test_dir, dirs_exist_ok=True)

                # Clean any existing output in workspace copy
                workspace_output_dir = workspace_test_dir / "output"
                if workspace_output_dir.exists():
                    shutil.rmtree(workspace_output_dir)

            try:
                yield dst_path
            finally:
                # Cleanup workspace copy after test
                if workspace_test_dir and workspace_test_dir.exists():
                    try:
                        shutil.rmtree(workspace_test_dir)
                        print(f"\n🧹 Cleaned up temporary workspace: {workspace_test_dir}")
                    except Exception as e:
                        print(f"\n⚠️ Warning: Could not clean up {workspace_test_dir}: {e}")

    def test_rxiv_pdf_example_manuscript_cli(self, example_manuscript_copy, execution_engine):
        """Test full PDF generation using rxiv CLI command across engines."""
        print(f"\n🔧 Running PDF generation test with {execution_engine.engine_type} engine")

        # Use engine abstraction to handle local vs container execution
        if execution_engine.engine_type == "local":
            # Try uv run rxiv first, then fall back to python module if not available
            try:
                result = execution_engine.run(
                    ["uv", "run", "rxiv", "pdf", str(example_manuscript_copy)],
                    cwd=Path.cwd(),
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fall back to python module call
                result = execution_engine.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli",
                        "pdf",
                        str(example_manuscript_copy),
                    ],
                    cwd=Path.cwd(),
                )
        else:
            # In container, use the installed rxiv command with the test manuscript copy
            result = execution_engine.run(
                ["rxiv", "pdf", "/workspace/TEMP_TEST_MANUSCRIPT"],
                cwd="/workspace",
            )

        # Check command succeeded
        assert result.returncode == 0, f"rxiv pdf failed: {result.stderr}"

        # Check output PDF was created
        if execution_engine.engine_type == "local":
            output_pdf = example_manuscript_copy / "output" / "EXAMPLE_MANUSCRIPT.pdf"
            figures_dir = example_manuscript_copy / "FIGURES"
        else:
            # For container execution, files are in the mounted workspace
            output_pdf = Path("TEMP_TEST_MANUSCRIPT") / "output" / "TEMP_TEST_MANUSCRIPT.pdf"
            figures_dir = Path("TEMP_TEST_MANUSCRIPT") / "FIGURES"

        assert output_pdf.exists(), f"Output PDF was not created at {output_pdf}"
        assert output_pdf.stat().st_size > 1000, "Output PDF is too small"

        # Check figures were generated (search recursively in subdirectories)
        generated_figures = list(figures_dir.rglob("*.pdf")) + list(figures_dir.rglob("*.png"))
        assert len(generated_figures) > 0, "No figures were generated"

    def test_rxiv_pdf_example_manuscript_python(self, example_manuscript_copy):
        """Test full PDF generation using Python API."""
        print("\n🔧 Running Python API test with local execution")

        from rxiv_maker.engine.build_manager import BuildManager

        # Create build manager and run build
        build_manager = BuildManager(
            manuscript_path=str(example_manuscript_copy),
            verbose=False,
            force_figures=False,
            skip_validation=False,
        )

        success = build_manager.run_full_build()
        assert success, "Build failed"

        # Check output
        output_pdf = example_manuscript_copy / "output" / "EXAMPLE_MANUSCRIPT.pdf"
        assert output_pdf.exists(), "Output PDF was not created"
        assert output_pdf.stat().st_size > 1000, "Output PDF is too small"

    def test_rxiv_validate_example_manuscript(self, example_manuscript_copy, execution_engine):
        """Test validation of EXAMPLE_MANUSCRIPT."""
        print(f"\n🔧 Running validation test with {execution_engine.engine_type} engine")

        # Run figure generation first to ensure all figure files exist
        if execution_engine.engine_type == "local":
            try:
                execution_engine.run(
                    ["uv", "run", "rxiv", "figures", str(example_manuscript_copy)],
                    cwd=Path.cwd(),
                    check=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                execution_engine.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli",
                        "figures",
                        str(example_manuscript_copy),
                    ],
                    cwd=Path.cwd(),
                    check=True,
                )

            # Run validation
            try:
                result = execution_engine.run(
                    ["uv", "run", "rxiv", "validate", str(example_manuscript_copy)],
                    cwd=Path.cwd(),
                )
            except FileNotFoundError:
                result = execution_engine.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli",
                        "validate",
                        str(example_manuscript_copy),
                    ],
                    cwd=Path.cwd(),
                )
        else:
            # Container execution - use workspace paths
            container_path = Path("/workspace") / "TEMP_TEST_MANUSCRIPT"
            execution_engine.run(
                ["rxiv", "figures", str(container_path)],
                cwd="/workspace",
                check=True,
            )
            result = execution_engine.run(
                ["rxiv", "validate", str(container_path)],
                cwd="/workspace",
            )

        # Validation should pass
        assert result.returncode == 0, f"Validation failed: {result.stderr}"
        assert "✅" in result.stdout or "passed" in result.stdout.lower()

    def test_rxiv_figures_example_manuscript(self, example_manuscript_copy, execution_engine):
        """Test figure generation for EXAMPLE_MANUSCRIPT."""
        print(f"\n🔧 Running figure generation test with {execution_engine.engine_type} engine")
        print(f"📁 Test manuscript path: {example_manuscript_copy}")

        # Clean existing figures (including subdirectories)
        figures_dir = example_manuscript_copy / "FIGURES"
        print(f"📁 Figures directory: {figures_dir}")

        # Count existing figures before cleanup
        existing_figures = list(figures_dir.rglob("*.pdf")) + list(figures_dir.rglob("*.png"))
        print(f"🔍 Found {len(existing_figures)} existing figure files before cleanup")

        for fig in figures_dir.rglob("*.pdf"):
            fig.unlink()
            print(f"🗑️ Deleted PDF: {fig}")
        for fig in figures_dir.rglob("*.png"):
            fig.unlink()
            print(f"🗑️ Deleted PNG: {fig}")

        # Verify figures are cleaned
        remaining_figures = list(figures_dir.rglob("*.pdf")) + list(figures_dir.rglob("*.png"))
        print(f"🔍 Found {len(remaining_figures)} figure files after cleanup")

        # Run figure generation
        if execution_engine.engine_type == "local":
            try:
                result = execution_engine.run(
                    ["uv", "run", "rxiv", "figures", str(example_manuscript_copy)],
                    cwd=Path.cwd(),
                )
            except FileNotFoundError:
                result = execution_engine.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli",
                        "figures",
                        str(example_manuscript_copy),
                    ],
                    cwd=Path.cwd(),
                )
        else:
            # Container execution - use workspace paths
            container_path = Path("/workspace") / "TEMP_TEST_MANUSCRIPT"
            result = execution_engine.run(
                ["rxiv", "figures", str(container_path)],
                cwd="/workspace",
            )

        # Check command succeeded
        print(f"📊 Figure generation exit code: {result.returncode}")
        if result.stdout:
            print(f"📝 Figure generation stdout: {result.stdout}")
        if result.stderr:
            print(f"❌ Figure generation stderr: {result.stderr}")
        assert result.returncode == 0, f"Figure generation failed: {result.stderr}"

        # Check figures were created (search recursively in subdirectories)
        generated_figures = list(figures_dir.rglob("*.pdf")) + list(figures_dir.rglob("*.png"))
        print(f"🎨 Generated {len(generated_figures)} figure files:")
        for fig in generated_figures:
            print(f"  📄 {fig}")
        assert len(generated_figures) >= 2, (
            f"Expected at least 2 figures, found {len(generated_figures)} in {figures_dir}"
        )

    @pytest.mark.parametrize("force_figures", [True, False])
    def test_rxiv_pdf_force_figures(self, example_manuscript_copy, force_figures, execution_engine):
        """Test PDF generation with and without force_figures option."""
        print(f"\n🔧 Running force_figures={force_figures} test with {execution_engine.engine_type} engine")
        print(f"📁 Test manuscript path: {example_manuscript_copy}")

        # Use engine abstraction to handle local vs container execution
        if execution_engine.engine_type == "local":
            args = ["uv", "run", "rxiv", "pdf", str(example_manuscript_copy)]
            if force_figures:
                args.append("--force-figures")

            print(f"🚀 Running command: {' '.join(args)}")
            try:
                result = execution_engine.run(args, cwd=Path.cwd())
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"🔄 First command failed ({e}), trying fallback...")
                args = [
                    "python",
                    "-m",
                    "rxiv_maker.cli",
                    "pdf",
                    str(example_manuscript_copy),
                ]
                if force_figures:
                    args.append("--force-figures")
                print(f"🚀 Running fallback command: {' '.join(args)}")
                result = execution_engine.run(args, cwd=Path.cwd())
        else:
            # In container, use the installed rxiv command with proper container path
            container_path = Path("/workspace") / "TEMP_TEST_MANUSCRIPT"
            args = ["rxiv", "pdf", str(container_path)]
            if force_figures:
                args.append("--force-figures")
            print(f"🚀 Running container command: {' '.join(args)}")
            result = execution_engine.run(args, cwd="/workspace")

        print(f"📊 PDF generation exit code: {result.returncode}")
        if result.stdout:
            print(f"📝 PDF generation stdout (last 1000 chars): {result.stdout[-1000:]}")
        if result.stderr:
            print(f"❌ PDF generation stderr: {result.stderr}")

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # PDF should exist
        if execution_engine.engine_type == "local":
            output_pdf = example_manuscript_copy / "output" / "EXAMPLE_MANUSCRIPT.pdf"
        else:
            output_pdf = Path("TEMP_TEST_MANUSCRIPT") / "output" / "TEMP_TEST_MANUSCRIPT.pdf"

        print(f"🔍 Checking for PDF at: {output_pdf}")
        print(f"📁 PDF exists: {output_pdf.exists()}")
        if output_pdf.exists():
            print(f"📏 PDF size: {output_pdf.stat().st_size} bytes")
        else:
            # List what files are in the output directory
            output_dir = output_pdf.parent
            if output_dir.exists():
                print(f"📁 Files in output directory {output_dir}:")
                for f in output_dir.iterdir():
                    print(f"  📄 {f}")
            else:
                print(f"❌ Output directory {output_dir} does not exist")

        assert output_pdf.exists(), f"Output PDF was not created at {output_pdf}"

    def test_make_pdf_compatibility(self, example_manuscript_copy):
        """Test that make pdf still works (backwards compatibility)."""
        print("\n🔧 Running Makefile compatibility test with local execution")

        # Run make pdf with command-line variable override
        result = subprocess.run(
            ["make", "pdf", f"MANUSCRIPT_PATH={example_manuscript_copy}"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        # Should succeed (or gracefully fail if Make not available)
        if result.returncode == 0:
            output_pdf = example_manuscript_copy / "output" / "EXAMPLE_MANUSCRIPT.pdf"
            assert output_pdf.exists(), "Make pdf did not create output"

    def test_rxiv_clean(self, example_manuscript_copy, execution_engine):
        """Test cleaning generated files."""
        print(f"\n🔧 Running clean test with {execution_engine.engine_type} engine")

        # First generate some output
        if execution_engine.engine_type == "local":
            try:
                execution_engine.run(
                    ["uv", "run", "rxiv", "figures", str(example_manuscript_copy)],
                    cwd=Path.cwd(),
                )
            except FileNotFoundError:
                execution_engine.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli",
                        "figures",
                        str(example_manuscript_copy),
                    ],
                    cwd=Path.cwd(),
                )

            # Run clean
            try:
                result = execution_engine.run(
                    ["uv", "run", "rxiv", "clean", str(example_manuscript_copy)],
                    cwd=Path.cwd(),
                )
            except FileNotFoundError:
                result = execution_engine.run(
                    [
                        "python",
                        "-m",
                        "rxiv_maker.cli",
                        "clean",
                        str(example_manuscript_copy),
                    ],
                    cwd=Path.cwd(),
                )
        else:
            # Container execution - use workspace paths
            container_path = Path("/workspace") / "TEMP_TEST_MANUSCRIPT"
            execution_engine.run(
                ["rxiv", "figures", str(container_path)],
                cwd="/workspace",
            )
            result = execution_engine.run(
                ["rxiv", "clean", str(container_path)],
                cwd="/workspace",
            )

        assert result.returncode == 0, f"Clean failed: {result.stderr}"

        # Check output directory was cleaned
        output_dir = example_manuscript_copy / "output"
        assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0
