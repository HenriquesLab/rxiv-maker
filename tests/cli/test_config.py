"""Test config command functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from rxiv_maker.cli.config import Config, config_cmd
from rxiv_maker.core import logging_config


class TestConfigCommand:
    """Test config command functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up test environment, especially for Windows."""
        # Ensure logging cleanup for Windows file locking issues
        logging_config.cleanup()

    def _strip_ansi_codes(self, text: str) -> str:
        """Strip ANSI escape codes from text for reliable string matching."""
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def test_config_help(self):
        """Test config command help."""
        result = self.runner.invoke(config_cmd, ["--help"])
        assert result.exit_code == 0
        assert "Configuration management" in result.output
        assert "show" in result.output
        assert "set" in result.output
        assert "get" in result.output
        assert "reset" in result.output

    def test_config_show(self):
        """Test config show command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(config_cmd, ["show"])
                assert result.exit_code == 0
                assert "Configuration" in result.output
                assert "general.default_engine" in result.output
                assert "Config file:" in result.output

    def test_config_get_existing_key(self):
        """Test config get with existing key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                # Reset config to defaults before test
                from rxiv_maker.cli.config import config

                config.config_data = config.get_default_config()

                result = self.runner.invoke(config_cmd, ["get", "general.default_engine"])
                assert result.exit_code == 0
                assert "general.default_engine = local" in result.output

    def test_config_get_nonexistent_key(self):
        """Test config get with nonexistent key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(config_cmd, ["get", "nonexistent.key"])
                assert result.exit_code == 0
                assert "not found" in result.output

    def test_config_set_string_value(self):
        """Test config set with string value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(config_cmd, ["set", "general.default_engine", "docker"])
                assert result.exit_code == 0
                assert "Set general.default_engine = docker" in result.output

                # Verify the value was set
                result = self.runner.invoke(config_cmd, ["get", "general.default_engine"])
                assert "general.default_engine = docker" in result.output

    def test_config_set_boolean_value(self):
        """Test config set with boolean value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(config_cmd, ["set", "general.verbose", "true"])
                assert result.exit_code == 0
                # Strip ANSI codes for reliable string matching in CI
                clean_output = self._strip_ansi_codes(result.output)
                # Check for success indicator (either emoji or ASCII fallback)
                assert any(
                    indicator in clean_output
                    for indicator in [
                        "✅ Set general.verbose = True",
                        "[OK] Set general.verbose = True",
                    ]
                )

                # Verify the value was set
                result = self.runner.invoke(config_cmd, ["get", "general.verbose"])
                clean_output = self._strip_ansi_codes(result.output)
                assert "general.verbose = True" in clean_output

    def test_config_set_integer_value(self):
        """Test config set with integer value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                result = self.runner.invoke(config_cmd, ["set", "figures.default_dpi", "600"])
                assert result.exit_code == 0
                # Strip ANSI codes for reliable string matching in CI
                clean_output = self._strip_ansi_codes(result.output)
                # Check for success indicator (either emoji or ASCII fallback)
                assert any(
                    indicator in clean_output
                    for indicator in [
                        "✅ Set figures.default_dpi = 600",
                        "[OK] Set figures.default_dpi = 600",
                    ]
                )

                # Verify the value was set
                result = self.runner.invoke(config_cmd, ["get", "figures.default_dpi"])
                clean_output = self._strip_ansi_codes(result.output)
                assert "figures.default_dpi = 600" in clean_output

    def test_config_reset(self):
        """Test config reset command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                # First set a custom value
                self.runner.invoke(config_cmd, ["set", "general.default_engine", "docker"])

                # Reset configuration
                result = self.runner.invoke(config_cmd, ["reset"], input="y\n")
                assert result.exit_code == 0
                assert "Configuration reset" in result.output

                # Verify the value was reset
                result = self.runner.invoke(config_cmd, ["get", "general.default_engine"])
                assert "general.default_engine = local" in result.output

    def test_config_reset_cancelled(self):
        """Test config reset command when cancelled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                # First set a custom value
                self.runner.invoke(config_cmd, ["set", "general.default_engine", "docker"])

                # Try to reset but cancel
                result = self.runner.invoke(config_cmd, ["reset"], input="n\n")
                assert result.exit_code == 0

                # Verify the value was not reset
                result = self.runner.invoke(config_cmd, ["get", "general.default_engine"])
                assert "general.default_engine = docker" in result.output

    def test_config_edit(self):
        """Test config edit command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch("click.edit") as mock_edit:
                    result = self.runner.invoke(config_cmd, ["edit"])
                    assert result.exit_code == 0
                    mock_edit.assert_called_once()
                    assert "Configuration file edited" in result.output


class TestConfigClass:
    """Test Config class functionality."""

    def test_config_initialization(self):
        """Test config initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                config = Config()
                assert config.config_dir == Path(tmpdir) / ".rxiv"
                assert config.config_file == Path(tmpdir) / ".rxiv" / "config.toml"
                assert isinstance(config.config_data, dict)

    def test_config_get_default_config(self):
        """Test get_default_config method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                config = Config()
                defaults = config.get_default_config()

                assert "general" in defaults
                assert "build" in defaults
                assert "validation" in defaults
                assert "figures" in defaults
                assert "bibliography" in defaults
                assert "output" in defaults

                assert defaults["general"]["default_engine"] == "local"
                assert defaults["general"]["default_manuscript_path"] == "MANUSCRIPT"
                assert defaults["figures"]["default_format"] == "png"
                assert defaults["figures"]["default_dpi"] == 300

    def test_config_get_set_methods(self):
        """Test get and set methods."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                config = Config()

                # Test get with default value
                assert config.get("general.default_engine") == "local"
                assert config.get("nonexistent.key", "default") == "default"

                # Test set and get
                config.set("general.default_engine", "docker")
                assert config.get("general.default_engine") == "docker"

                # Test nested set
                config.set("new.nested.key", "value")
                assert config.get("new.nested.key") == "value"

    def test_config_fallback_toml_handling(self):
        """Test TOML fallback handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                config = Config()

                # Test dict to TOML conversion
                test_dict = {
                    "general": {
                        "default_engine": "local",
                        "verbose": True,
                        "timeout": 30,
                    }
                }

                toml_content = config._dict_to_toml(test_dict)
                assert "[general]" in toml_content
                assert 'default_engine = "local"' in toml_content
                assert "verbose = true" in toml_content
                assert "timeout = 30" in toml_content

    def test_config_format_value(self):
        """Test _format_value method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                config = Config()

                assert config._format_value("string") == '"string"'
                assert config._format_value(True) == "true"
                assert config._format_value(False) == "false"
                assert config._format_value(42) == "42"
                assert config._format_value(3.14) == "3.14"
