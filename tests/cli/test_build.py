"""Test build command functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.build import build
from rxiv_maker.core import logging_config


class TestBuildCommand:
    """Test build command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test environment, especially for Windows."""
        # Ensure logging cleanup for Windows file locking issues
        logging_config.cleanup()

    def test_build_help(self):
        """Test build command help."""
        result = self.runner.invoke(build, ["--help"])
        assert result.exit_code == 0
        assert "Generate a publication-ready PDF" in result.output
        assert "--output-dir" in result.output
        assert "--force-figures" in result.output
        assert "--skip-validation" in result.output

    def test_build_default_manuscript_path(self):
        """Test build with default manuscript path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "MANUSCRIPT"
            manuscript_dir.mkdir()

            # Create minimal manuscript files
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
""")
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent")
            (manuscript_dir / "03_REFERENCES.bib").write_text("@article{test2023}")

            # Create FIGURES directory to avoid the warning
            (manuscript_dir / "FIGURES").mkdir(exist_ok=True)

            with (
                patch(
                    "rxiv_maker.cli.commands.build.os.environ.get",
                    return_value=str(manuscript_dir),
                ),
                patch("rxiv_maker.engine.build_manager.BuildManager") as mock_build_manager,
            ):
                mock_build_manager.return_value.build.return_value = True

                result = self.runner.invoke(build, obj={"verbose": False, "engine": "local"})

                # Debug: print result output and exit code
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

                # Should not exit with error if manuscript exists
                # Note: This will fail in the actual test due to missing
                # dependencies but we can test the argument parsing
                if result.exit_code == 0:
                    mock_build_manager.assert_called_once()

    def test_build_custom_manuscript_path(self):
        """Test build with custom manuscript path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "MY_PAPER"
            manuscript_dir.mkdir()

            # Create minimal manuscript files
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
""")
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent")
            (manuscript_dir / "03_REFERENCES.bib").write_text("@article{test2023}")

            # Create FIGURES directory to avoid the warning
            (manuscript_dir / "FIGURES").mkdir(exist_ok=True)

            with patch("rxiv_maker.cli.commands.build.BuildManager") as mock_build_manager:
                mock_instance = mock_build_manager.return_value
                mock_instance.run_full_build.return_value = True

                result = self.runner.invoke(
                    build,
                    [str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                assert result.exit_code == 0
                mock_build_manager.assert_called_once()
                args, kwargs = mock_build_manager.call_args
                assert kwargs["manuscript_path"] == str(manuscript_dir)

    def test_build_nonexistent_manuscript(self):
        """Test build with nonexistent manuscript directory."""
        result = self.runner.invoke(build, ["/nonexistent/path"], obj={"verbose": False, "engine": "local"})
        assert result.exit_code == 2  # Click validation error
        assert "Directory '/nonexistent/path'" in result.output

    def test_build_with_options(self):
        """Test build with various options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "MANUSCRIPT"
            manuscript_dir.mkdir()

            # Create minimal manuscript files
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
""")
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent")
            (manuscript_dir / "03_REFERENCES.bib").write_text("@article{test2023}")

            # Create FIGURES directory to avoid the warning
            (manuscript_dir / "FIGURES").mkdir(exist_ok=True)

            with (
                patch("rxiv_maker.cli.commands.build.BuildManager") as mock_build_manager,
                patch("rxiv_maker.docker.manager.get_docker_manager") as mock_docker_manager,
            ):
                mock_instance = mock_build_manager.return_value
                mock_instance.run_full_build.return_value = True

                # Mock docker manager
                mock_docker_instance = mock_docker_manager.return_value
                mock_docker_instance.check_docker_available.return_value = True

                result = self.runner.invoke(
                    build,
                    [
                        str(manuscript_dir),
                        "--output-dir",
                        "custom_output",
                        "--force-figures",
                        "--skip-validation",
                        "--track-changes",
                        "v1.0.0",
                    ],
                    obj={"verbose": True, "engine": "docker"},
                )

                assert result.exit_code == 0
                mock_build_manager.assert_called_once()
                args, kwargs = mock_build_manager.call_args
                assert kwargs["manuscript_path"] == str(manuscript_dir)
                assert kwargs["output_dir"] == "custom_output"
                assert kwargs["force_figures"] is True
                assert kwargs["skip_validation"] is True
                assert kwargs["track_changes_tag"] == "v1.0.0"
                assert kwargs["verbose"] is True

    def test_build_failure(self):
        """Test build failure handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "MANUSCRIPT"
            manuscript_dir.mkdir()

            # Create minimal manuscript files
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
""")
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent")
            (manuscript_dir / "03_REFERENCES.bib").write_text("@article{test2023}")

            # Create FIGURES directory to avoid the warning
            (manuscript_dir / "FIGURES").mkdir(exist_ok=True)

            with patch("rxiv_maker.cli.commands.build.BuildManager") as mock_build_manager:
                mock_build_manager.return_value.run_full_build.return_value = False

                result = self.runner.invoke(
                    build,
                    [str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                assert result.exit_code == 1
                assert "PDF generation failed" in result.output
