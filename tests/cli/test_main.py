"""Test main CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from rxiv_maker.cli.main import main
from rxiv_maker.core import logging_config


class TestMainCLI:
    """Test main CLI functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test environment, especially for Windows."""
        # Ensure logging cleanup for Windows file locking issues
        logging_config.cleanup()

    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "rxiv-maker" in result.output
        assert "pdf" in result.output
        assert "validate" in result.output
        assert "clean" in result.output

    def test_cli_version(self):
        """Test CLI version output."""
        result = self.runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "rxiv" in result.output

    def test_cli_verbose_flag(self):
        """Test verbose flag is properly passed."""
        result = self.runner.invoke(main, ["--verbose", "--help"])
        assert result.exit_code == 0
        # Environment variable should be set
        # Note: This tests the flag parsing, actual env var testing requires integration

    def test_cli_engine_flag(self):
        """Test engine flag is properly parsed."""
        result = self.runner.invoke(main, ["--engine", "docker", "--help"])
        assert result.exit_code == 0

        result = self.runner.invoke(main, ["--engine", "local", "--help"])
        assert result.exit_code == 0

        # Invalid engine should fail
        result = self.runner.invoke(main, ["--engine", "invalid", "version"])
        assert result.exit_code != 0

    @pytest.mark.skip(reason="Completion installation not implemented yet")
    def test_install_completion_bash(self):
        """Test bash completion installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc_path = Path(tmpdir) / ".bashrc"
            bashrc_path.touch()

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(main, ["--install-completion", "bash"])
                assert result.exit_code == 0
                assert "completion installed" in result.output

                # Check if completion was added to bashrc
                content = bashrc_path.read_text()
                assert "eval" in content
                assert "RXIV_COMPLETE" in content

    @pytest.mark.skip(reason="Completion installation not implemented yet")
    def test_install_completion_zsh(self):
        """Test zsh completion installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zshrc_path = Path(tmpdir) / ".zshrc"
            zshrc_path.touch()

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(main, ["--install-completion", "zsh"])
                assert result.exit_code == 0
                assert "completion installed" in result.output

                # Check if completion was added to zshrc
                content = zshrc_path.read_text()
                assert "eval" in content
                assert "RXIV_COMPLETE" in content

    @pytest.mark.skip(reason="Completion installation not implemented yet")
    def test_install_completion_fish(self):
        """Test fish completion installation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_fish_dir = Path(tmpdir) / ".config" / "fish"
            config_fish_dir.mkdir(parents=True)
            config_fish_path = config_fish_dir / "config.fish"
            config_fish_path.touch()

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(main, ["--install-completion", "fish"])
                assert result.exit_code == 0
                assert "completion installed" in result.output

                # Check if completion was added to config.fish
                content = config_fish_path.read_text()
                assert "eval" in content
                assert "RXIV_COMPLETE" in content

    @pytest.mark.skip(reason="Completion installation not implemented yet")
    def test_install_completion_already_installed(self):
        """Test completion installation when already installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc_path = Path(tmpdir) / ".bashrc"
            bashrc_path.write_text('eval "$(_RXIV_COMPLETE=bash_source rxiv)"')

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(main, ["--install-completion", "bash"])
                assert result.exit_code == 0
                assert "already installed" in result.output

    def test_command_registration(self):
        """Test that all commands are properly registered."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0

        expected_commands = [
            "pdf",
            "validate",
            "clean",
            "figures",
            "arxiv",
            "init",
            "bibliography",
            "track-changes",
            "setup",
            "version",
            "config",
        ]

        for cmd in expected_commands:
            assert cmd in result.output

    def test_context_passing(self):
        """Test that context is properly passed to commands."""
        # This would need to be tested with actual command invocation
        # For now, we test that the context object is created properly
        result = self.runner.invoke(main, ["--verbose", "--engine", "docker", "version"])
        assert result.exit_code == 0
        # The actual context testing would require mocking the command handlers
