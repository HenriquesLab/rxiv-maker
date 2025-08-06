"""Integration tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from rxiv_maker.cli.main import main
from rxiv_maker.core import logging_config


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test environment, especially for Windows."""
        # Ensure logging cleanup for Windows file locking issues
        logging_config.cleanup()

    def test_init_and_build_workflow(self):
        """Test init -> build workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "TEST_PAPER"

            # Test init command
            self.runner.invoke(
                main,
                ["init", str(manuscript_dir), "--template", "basic"],
                obj={"verbose": False, "engine": "local"},
                input="Test Paper\nTest Subtitle\nTest Author\ntest@example.com\nTest University\n",
            )

            # Init should create the directory and files
            assert manuscript_dir.exists()
            assert (manuscript_dir / "00_CONFIG.yml").exists()
            assert (manuscript_dir / "01_MAIN.md").exists()
            assert (manuscript_dir / "03_REFERENCES.bib").exists()
            assert (manuscript_dir / "FIGURES").exists()

            # Test validate command
            with patch("rxiv_maker.engine.validate.main") as mock_validate:
                mock_validate.return_value = None  # Success

                self.runner.invoke(
                    main,
                    ["validate", str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_validate.assert_called_once()

            # Test build command (mocked)
            with patch("rxiv_maker.cli.commands.build.BuildManager") as mock_build_manager:
                mock_build_manager.return_value.run_full_build.return_value = True

                self.runner.invoke(
                    main,
                    ["pdf", str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_build_manager.assert_called_once()

    def test_config_integration(self):
        """Test configuration integration across commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                # Set configuration
                result = self.runner.invoke(main, ["config", "set", "general.default_engine", "docker"])
                assert result.exit_code == 0

                # Get configuration
                result = self.runner.invoke(main, ["config", "get", "general.default_engine"])
                assert result.exit_code == 0
                assert "docker" in result.output

                # Show configuration
                result = self.runner.invoke(main, ["config", "show"])
                assert result.exit_code == 0
                assert "docker" in result.output

    def test_bibliography_workflow(self):
        """Test bibliography management workflow."""
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
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent with @test2024")
            (manuscript_dir / "03_REFERENCES.bib").write_text("")

            # Test bibliography add command
            with patch("rxiv_maker.engine.add_bibliography.main") as mock_add:
                mock_add.return_value = None

                self.runner.invoke(
                    main,
                    ["bibliography", "add", str(manuscript_dir), "10.1000/test.doi"],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_add.assert_called_once()

            # Test bibliography validate command
            with patch("rxiv_maker.engine.validate.main") as mock_validate:
                mock_validate.return_value = None

                self.runner.invoke(
                    main,
                    ["bibliography", "validate", str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_validate.assert_called_once()

            # Test bibliography fix command
            with patch("rxiv_maker.engine.fix_bibliography.main") as mock_fix:
                mock_fix.return_value = None

                self.runner.invoke(
                    main,
                    ["bibliography", "fix", str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_fix.assert_called_once()

    def test_clean_workflow(self):
        """Test clean command workflow."""
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
            (manuscript_dir / "03_REFERENCES.bib").write_text("")

            # Test clean command
            with patch("rxiv_maker.engine.cleanup.main") as mock_cleanup:
                mock_cleanup.return_value = None

                self.runner.invoke(
                    main,
                    ["clean", str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_cleanup.assert_called_once()

            # Test clean with options
            with patch("rxiv_maker.engine.cleanup.main") as mock_cleanup:
                mock_cleanup.return_value = None

                self.runner.invoke(
                    main,
                    ["clean", str(manuscript_dir), "--figures-only"],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_cleanup.assert_called_once()

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(main, ["version"])
        assert result.exit_code == 0

        result = self.runner.invoke(main, ["version", "--detailed"])
        assert result.exit_code == 0
        assert "Rxiv-Maker Version Information" in result.output

    def test_figures_command(self):
        """Test figures command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "MANUSCRIPT"
            manuscript_dir.mkdir()
            figures_dir = manuscript_dir / "FIGURES"
            figures_dir.mkdir()

            # Create minimal manuscript files
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
""")
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent")
            (manuscript_dir / "03_REFERENCES.bib").write_text("")

            # Test figures command
            with patch("rxiv_maker.engine.generate_figures.FigureGenerator") as mock_generator_class:
                mock_generator = Mock()
                mock_generator.generate_all_figures.return_value = None
                mock_generator_class.return_value = mock_generator

                self.runner.invoke(
                    main,
                    ["figures", str(manuscript_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                # Verify the FigureGenerator class was instantiated
                mock_generator_class.assert_called_once()

    def test_arxiv_command(self):
        """Test arxiv command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_dir = Path(tmpdir) / "MANUSCRIPT"
            manuscript_dir.mkdir()
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()

            # Create minimal manuscript files
            (manuscript_dir / "00_CONFIG.yml").write_text("""
title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
""")
            (manuscript_dir / "01_MAIN.md").write_text("# Test\n\nContent")
            (manuscript_dir / "03_REFERENCES.bib").write_text("")

            # Create fake PDF
            (output_dir / "MANUSCRIPT.pdf").write_text("fake pdf content")

            # Test arxiv command
            with patch("rxiv_maker.engine.prepare_arxiv.main") as mock_arxiv:
                mock_arxiv.return_value = None

                self.runner.invoke(
                    main,
                    ["arxiv", str(manuscript_dir), "--output-dir", str(output_dir)],
                    obj={"verbose": False, "engine": "local"},
                )

                mock_arxiv.assert_called_once()

    def test_setup_command(self):
        """Test setup command."""
        with patch("rxiv_maker.engine.setup_environment.main") as mock_setup:
            mock_setup.return_value = None

            self.runner.invoke(main, ["setup"], obj={"verbose": False, "engine": "local"})

            mock_setup.assert_called_once()

    def test_error_handling_integration(self):
        """Test error handling across commands."""
        # Test with nonexistent manuscript
        result = self.runner.invoke(
            main,
            ["pdf", "/nonexistent/path"],
            obj={"verbose": False, "engine": "local"},
        )
        assert result.exit_code == 2  # Click parameter validation error
        assert "does not exist" in result.output

        # Test with invalid engine
        result = self.runner.invoke(
            main,
            ["--engine", "invalid", "pdf"],
            obj={"verbose": False, "engine": "local"},
        )
        assert result.exit_code != 0

    def test_verbose_flag_integration(self):
        """Test verbose flag integration."""
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
            (manuscript_dir / "03_REFERENCES.bib").write_text("")

            # Test verbose flag
            with patch("rxiv_maker.engine.validate.main") as mock_validate:
                mock_validate.return_value = None

                self.runner.invoke(
                    main,
                    ["--verbose", "validate", str(manuscript_dir)],
                    obj={"verbose": True, "engine": "local"},
                )

                mock_validate.assert_called_once()
