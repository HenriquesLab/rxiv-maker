"""Tests for EnvironmentManager class."""

import os
from unittest.mock import Mock, patch

import pytest

from rxiv_maker.core.environment_manager import EnvironmentManager


class TestEnvironmentManager:
    """Test EnvironmentManager functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Clear environment before each test
        self.original_env = os.environ.copy()
        EnvironmentManager.clear_rxiv_vars()

    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)


class TestManuscriptPath:
    """Test manuscript path environment variable handling."""

    def test_get_manuscript_path_valid(self):
        """Test getting valid manuscript path."""
        test_path = "/path/to/manuscript"
        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = test_path

        result = EnvironmentManager.get_manuscript_path()
        assert result == test_path

    def test_get_manuscript_path_with_trailing_slash(self):
        """Test manuscript path with trailing slash normalization."""
        test_path = "/path/to/manuscript/"
        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = test_path

        result = EnvironmentManager.get_manuscript_path()
        assert result == "/path/to/manuscript"

    def test_get_manuscript_path_empty(self):
        """Test empty manuscript path."""
        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = ""

        result = EnvironmentManager.get_manuscript_path()
        assert result is None

    def test_get_manuscript_path_invalid_values(self):
        """Test invalid manuscript path values."""
        invalid_values = [".", "..", "   ", "/"]

        for invalid_value in invalid_values:
            os.environ[EnvironmentManager.MANUSCRIPT_PATH] = invalid_value
            result = EnvironmentManager.get_manuscript_path()
            assert result is None

    def test_get_manuscript_path_not_set(self):
        """Test manuscript path when not set."""
        if EnvironmentManager.MANUSCRIPT_PATH in os.environ:
            del os.environ[EnvironmentManager.MANUSCRIPT_PATH]

        result = EnvironmentManager.get_manuscript_path()
        assert result is None

    def test_set_manuscript_path(self, tmp_path):
        """Test setting manuscript path."""
        test_path = tmp_path / "manuscript"

        EnvironmentManager.set_manuscript_path(test_path)

        result = os.environ[EnvironmentManager.MANUSCRIPT_PATH]
        assert result == str(test_path.resolve())


class TestRxivEngine:
    """Test rxiv engine environment variable handling."""

    def test_get_rxiv_engine_valid_values(self):
        """Test getting valid engine values."""
        valid_engines = ["local", "docker", "podman"]

        for engine in valid_engines:
            os.environ[EnvironmentManager.RXIV_ENGINE] = engine
            result = EnvironmentManager.get_rxiv_engine()
            assert result == engine

    def test_get_rxiv_engine_case_insensitive(self):
        """Test engine value case insensitivity."""
        test_cases = [
            ("LOCAL", "local"),
            ("Docker", "docker"),
            ("PODMAN", "podman"),
            ("  local  ", "local"),
        ]

        for input_value, expected in test_cases:
            os.environ[EnvironmentManager.RXIV_ENGINE] = input_value
            result = EnvironmentManager.get_rxiv_engine()
            assert result == expected

    def test_get_rxiv_engine_invalid_values(self):
        """Test invalid engine values default to local."""
        invalid_values = ["invalid", "kubernetes", "", "   "]

        for invalid_value in invalid_values:
            os.environ[EnvironmentManager.RXIV_ENGINE] = invalid_value
            result = EnvironmentManager.get_rxiv_engine()
            assert result == "local"

    def test_get_rxiv_engine_default(self):
        """Test default engine when not set."""
        if EnvironmentManager.RXIV_ENGINE in os.environ:
            del os.environ[EnvironmentManager.RXIV_ENGINE]

        result = EnvironmentManager.get_rxiv_engine()
        assert result == "local"

    def test_set_rxiv_engine_valid(self):
        """Test setting valid engine values."""
        valid_engines = ["local", "docker", "podman"]

        for engine in valid_engines:
            EnvironmentManager.set_rxiv_engine(engine)
            assert os.environ[EnvironmentManager.RXIV_ENGINE] == engine

    def test_set_rxiv_engine_case_normalization(self):
        """Test engine setting normalizes case."""
        EnvironmentManager.set_rxiv_engine("DOCKER")
        assert os.environ[EnvironmentManager.RXIV_ENGINE] == "docker"

    def test_set_rxiv_engine_invalid(self):
        """Test setting invalid engine raises error."""
        with pytest.raises(ValueError, match="Invalid engine type"):
            EnvironmentManager.set_rxiv_engine("invalid")


class TestBooleanVariables:
    """Test boolean environment variable handling."""

    @pytest.mark.parametrize(
        "method,env_var",
        [
            (EnvironmentManager.is_verbose, EnvironmentManager.RXIV_VERBOSE),
            (EnvironmentManager.is_update_check_disabled, EnvironmentManager.RXIV_NO_UPDATE_CHECK),
            (EnvironmentManager.is_force_figures, EnvironmentManager.FORCE_FIGURES),
            (EnvironmentManager.is_docker_available, EnvironmentManager.DOCKER_AVAILABLE),
        ],
    )
    def test_boolean_true_values(self, method, env_var):
        """Test various true boolean representations."""
        true_values = ["true", "1", "yes", "on", "enabled", "TRUE", "True"]

        for true_value in true_values:
            os.environ[env_var] = true_value
            assert method() is True

    @pytest.mark.parametrize(
        "method,env_var",
        [
            (EnvironmentManager.is_verbose, EnvironmentManager.RXIV_VERBOSE),
            (EnvironmentManager.is_update_check_disabled, EnvironmentManager.RXIV_NO_UPDATE_CHECK),
            (EnvironmentManager.is_force_figures, EnvironmentManager.FORCE_FIGURES),
            (EnvironmentManager.is_docker_available, EnvironmentManager.DOCKER_AVAILABLE),
        ],
    )
    def test_boolean_false_values(self, method, env_var):
        """Test various false boolean representations."""
        false_values = ["false", "0", "no", "off", "disabled", "FALSE", "False"]

        for false_value in false_values:
            os.environ[env_var] = false_value
            assert method() is False

    @pytest.mark.parametrize(
        "method,env_var",
        [
            (EnvironmentManager.is_verbose, EnvironmentManager.RXIV_VERBOSE),
            (EnvironmentManager.is_update_check_disabled, EnvironmentManager.RXIV_NO_UPDATE_CHECK),
            (EnvironmentManager.is_force_figures, EnvironmentManager.FORCE_FIGURES),
            (EnvironmentManager.is_docker_available, EnvironmentManager.DOCKER_AVAILABLE),
        ],
    )
    def test_boolean_default_values(self, method, env_var):
        """Test default values when not set."""
        if env_var in os.environ:
            del os.environ[env_var]

        assert method() is False

    @pytest.mark.parametrize(
        "method,env_var",
        [
            (EnvironmentManager.is_verbose, EnvironmentManager.RXIV_VERBOSE),
            (EnvironmentManager.is_update_check_disabled, EnvironmentManager.RXIV_NO_UPDATE_CHECK),
            (EnvironmentManager.is_force_figures, EnvironmentManager.FORCE_FIGURES),
            (EnvironmentManager.is_docker_available, EnvironmentManager.DOCKER_AVAILABLE),
        ],
    )
    def test_boolean_invalid_values(self, method, env_var):
        """Test invalid boolean values default to false."""
        invalid_values = ["maybe", "invalid", "2", ""]

        for invalid_value in invalid_values:
            os.environ[env_var] = invalid_value
            assert method() is False

    def test_set_verbose(self):
        """Test setting verbose mode."""
        EnvironmentManager.set_verbose(True)
        assert os.environ[EnvironmentManager.RXIV_VERBOSE] == "true"

        EnvironmentManager.set_verbose(False)
        assert os.environ[EnvironmentManager.RXIV_VERBOSE] == "false"

    def test_disable_update_check(self):
        """Test disabling update check."""
        EnvironmentManager.disable_update_check(True)
        assert os.environ[EnvironmentManager.RXIV_NO_UPDATE_CHECK] == "true"

        EnvironmentManager.disable_update_check(False)
        assert os.environ[EnvironmentManager.RXIV_NO_UPDATE_CHECK] == "false"

    def test_set_force_figures(self):
        """Test setting force figures."""
        EnvironmentManager.set_force_figures(True)
        assert os.environ[EnvironmentManager.FORCE_FIGURES] == "true"

        EnvironmentManager.set_force_figures(False)
        assert os.environ[EnvironmentManager.FORCE_FIGURES] == "false"

    def test_set_docker_available(self):
        """Test setting Docker availability."""
        EnvironmentManager.set_docker_available(True)
        assert os.environ[EnvironmentManager.DOCKER_AVAILABLE] == "true"

        EnvironmentManager.set_docker_available(False)
        assert os.environ[EnvironmentManager.DOCKER_AVAILABLE] == "false"


class TestDockerConfiguration:
    """Test Docker-related configuration."""

    def test_get_docker_image_default(self):
        """Test default Docker image."""
        if EnvironmentManager.DOCKER_IMAGE in os.environ:
            del os.environ[EnvironmentManager.DOCKER_IMAGE]

        result = EnvironmentManager.get_docker_image()
        assert result == "henriqueslab/rxiv-maker-base:latest"

    def test_get_docker_image_custom(self):
        """Test custom Docker image."""
        custom_image = "custom/image:tag"
        os.environ[EnvironmentManager.DOCKER_IMAGE] = custom_image

        result = EnvironmentManager.get_docker_image()
        assert result == custom_image

    def test_set_docker_image(self):
        """Test setting Docker image."""
        test_image = "test/image:v1.0"
        EnvironmentManager.set_docker_image(test_image)

        assert os.environ[EnvironmentManager.DOCKER_IMAGE] == test_image

    def test_set_docker_image_strips_whitespace(self):
        """Test Docker image setting strips whitespace."""
        test_image = "  test/image:v1.0  "
        EnvironmentManager.set_docker_image(test_image)

        assert os.environ[EnvironmentManager.DOCKER_IMAGE] == "test/image:v1.0"


class TestMermaidConfiguration:
    """Test Mermaid CLI configuration."""

    def test_get_mermaid_cli_options_default(self):
        """Test default Mermaid CLI options."""
        if EnvironmentManager.MERMAID_CLI_OPTIONS in os.environ:
            del os.environ[EnvironmentManager.MERMAID_CLI_OPTIONS]

        result = EnvironmentManager.get_mermaid_cli_options()
        assert result == ""

    def test_get_mermaid_cli_options_custom(self):
        """Test custom Mermaid CLI options."""
        custom_options = '--puppeteerConfig \'{"args":["--no-sandbox"]}\''
        os.environ[EnvironmentManager.MERMAID_CLI_OPTIONS] = custom_options

        result = EnvironmentManager.get_mermaid_cli_options()
        assert result == custom_options

    def test_set_mermaid_cli_options(self):
        """Test setting Mermaid CLI options."""
        test_options = "--theme dark"
        EnvironmentManager.set_mermaid_cli_options(test_options)

        assert os.environ[EnvironmentManager.MERMAID_CLI_OPTIONS] == test_options


class TestEnvironmentDetection:
    """Test environment detection functionality."""

    def test_is_google_colab_with_env_vars(self):
        """Test Google Colab detection via environment variables."""
        # Test COLAB_GPU
        os.environ[EnvironmentManager.COLAB_GPU] = "0"
        assert EnvironmentManager.is_google_colab() is True

        del os.environ[EnvironmentManager.COLAB_GPU]

        # Test COLAB_TPU_ADDR
        os.environ[EnvironmentManager.COLAB_TPU_ADDR] = "grpc://10.0.0.1:8470"
        assert EnvironmentManager.is_google_colab() is True

    def test_is_google_colab_with_module(self):
        """Test Google Colab detection via module import."""
        # Mock the google.colab module
        with patch("builtins.__import__") as mock_import:
            mock_import.return_value = Mock()

            # Clear environment variables
            for var in [EnvironmentManager.COLAB_GPU, EnvironmentManager.COLAB_TPU_ADDR]:
                if var in os.environ:
                    del os.environ[var]

            # Should still detect Colab via module
            assert EnvironmentManager.is_google_colab() is True

    def test_is_google_colab_false(self):
        """Test Google Colab detection returns false."""
        # Clear environment variables
        for var in [EnvironmentManager.COLAB_GPU, EnvironmentManager.COLAB_TPU_ADDR]:
            if var in os.environ:
                del os.environ[var]

        # Mock import to fail
        with patch("builtins.__import__", side_effect=ImportError):
            assert EnvironmentManager.is_google_colab() is False

    def test_is_ci_environment(self):
        """Test CI environment detection."""
        # Test CI variable
        os.environ[EnvironmentManager.CI] = "true"
        assert EnvironmentManager.is_ci_environment() is True

        del os.environ[EnvironmentManager.CI]

        # Test GITHUB_ACTIONS variable
        os.environ[EnvironmentManager.GITHUB_ACTIONS] = "true"
        assert EnvironmentManager.is_ci_environment() is True

        del os.environ[EnvironmentManager.GITHUB_ACTIONS]

        # Test no CI environment
        assert EnvironmentManager.is_ci_environment() is False


class TestPythonPathHandling:
    """Test PYTHONPATH environment variable handling."""

    def test_get_pythonpath_empty(self):
        """Test getting empty PYTHONPATH."""
        if EnvironmentManager.PYTHONPATH in os.environ:
            del os.environ[EnvironmentManager.PYTHONPATH]

        result = EnvironmentManager.get_pythonpath()
        assert result == []

    def test_get_pythonpath_single_path(self):
        """Test getting single path in PYTHONPATH."""
        test_path = "/path/to/module"
        os.environ[EnvironmentManager.PYTHONPATH] = test_path

        result = EnvironmentManager.get_pythonpath()
        assert result == [test_path]

    def test_get_pythonpath_multiple_paths_unix(self):
        """Test getting multiple paths in PYTHONPATH (Unix)."""
        paths = ["/path/one", "/path/two", "/path/three"]
        os.environ[EnvironmentManager.PYTHONPATH] = ":".join(paths)

        with patch("os.name", "posix"):
            result = EnvironmentManager.get_pythonpath()
            assert result == paths

    def test_get_pythonpath_multiple_paths_windows(self):
        """Test getting multiple paths in PYTHONPATH (Windows)."""
        paths = ["C:\\path\\one", "C:\\path\\two", "C:\\path\\three"]
        os.environ[EnvironmentManager.PYTHONPATH] = ";".join(paths)

        with patch("os.name", "nt"):
            result = EnvironmentManager.get_pythonpath()
            assert result == paths

    def test_add_to_pythonpath_new_path(self, tmp_path):
        """Test adding new path to PYTHONPATH."""
        test_path = tmp_path / "new_module"
        test_path.mkdir()

        # Clear PYTHONPATH
        if EnvironmentManager.PYTHONPATH in os.environ:
            del os.environ[EnvironmentManager.PYTHONPATH]

        EnvironmentManager.add_to_pythonpath(test_path)

        result = EnvironmentManager.get_pythonpath()
        assert str(test_path.resolve()) in result

    def test_add_to_pythonpath_existing_path(self, tmp_path):
        """Test adding existing path to PYTHONPATH (should not duplicate)."""
        test_path = tmp_path / "existing_module"
        test_path.mkdir()

        # Set initial PYTHONPATH
        os.environ[EnvironmentManager.PYTHONPATH] = str(test_path.resolve())

        # Add same path again
        EnvironmentManager.add_to_pythonpath(test_path)

        result = EnvironmentManager.get_pythonpath()
        assert result.count(str(test_path.resolve())) == 1


class TestEnvironmentManagement:
    """Test overall environment management functionality."""

    def test_get_all_rxiv_vars(self):
        """Test getting all rxiv-maker variables."""
        # Set some variables
        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = "/test/manuscript"
        os.environ[EnvironmentManager.RXIV_ENGINE] = "docker"
        os.environ[EnvironmentManager.RXIV_VERBOSE] = "true"

        result = EnvironmentManager.get_all_rxiv_vars()

        assert result[EnvironmentManager.MANUSCRIPT_PATH] == "/test/manuscript"
        assert result[EnvironmentManager.RXIV_ENGINE] == "docker"
        assert result[EnvironmentManager.RXIV_VERBOSE] == "true"

    def test_set_environment_for_subprocess(self):
        """Test setting environment for subprocess."""
        # Set some rxiv variables
        os.environ[EnvironmentManager.RXIV_ENGINE] = "docker"
        os.environ[EnvironmentManager.RXIV_VERBOSE] = "true"

        additional_vars = {"CUSTOM_VAR": "custom_value"}

        result = EnvironmentManager.set_environment_for_subprocess(additional_vars)

        # Should include original environment
        assert "PATH" in result  # Standard env var

        # Should include rxiv variables
        assert result[EnvironmentManager.RXIV_ENGINE] == "docker"
        assert result[EnvironmentManager.RXIV_VERBOSE] == "true"

        # Should include additional variables
        assert result["CUSTOM_VAR"] == "custom_value"

    def test_clear_rxiv_vars(self):
        """Test clearing all rxiv-maker variables."""
        # Set some variables
        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = "/test/manuscript"
        os.environ[EnvironmentManager.RXIV_ENGINE] = "docker"
        os.environ[EnvironmentManager.RXIV_VERBOSE] = "true"

        EnvironmentManager.clear_rxiv_vars()

        # Variables should be removed
        assert EnvironmentManager.MANUSCRIPT_PATH not in os.environ
        assert EnvironmentManager.RXIV_ENGINE not in os.environ
        assert EnvironmentManager.RXIV_VERBOSE not in os.environ


class TestEnvironmentValidation:
    """Test environment validation functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Clear environment before each test
        self.original_env = os.environ.copy()
        EnvironmentManager.clear_rxiv_vars()

    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_validate_environment_valid_manuscript_path(self, tmp_path):
        """Test validation with valid manuscript path."""
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = str(manuscript_dir)

        warnings = EnvironmentManager.validate_environment()
        assert len(warnings) == 0

    def test_validate_environment_nonexistent_manuscript_path(self, tmp_path):
        """Test validation with nonexistent manuscript path."""
        nonexistent = tmp_path / "nonexistent"

        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = str(nonexistent)

        warnings = EnvironmentManager.validate_environment()
        assert any("non-existent directory" in warning for warning in warnings)

    def test_validate_environment_file_as_manuscript_path(self, tmp_path):
        """Test validation with file instead of directory as manuscript path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = str(test_file)

        warnings = EnvironmentManager.validate_environment()
        assert any("not a directory" in warning for warning in warnings)

    def test_validate_environment_docker_unavailable(self):
        """Test validation with Docker engine but Docker unavailable."""
        os.environ[EnvironmentManager.RXIV_ENGINE] = "docker"
        os.environ[EnvironmentManager.DOCKER_AVAILABLE] = "false"

        warnings = EnvironmentManager.validate_environment()
        assert any("Docker is not available" in warning for warning in warnings)

    def test_validate_environment_colab_with_wrong_engine(self):
        """Test validation in Colab with wrong engine."""
        os.environ[EnvironmentManager.COLAB_GPU] = "0"
        os.environ[EnvironmentManager.RXIV_ENGINE] = "docker"

        warnings = EnvironmentManager.validate_environment()
        assert any("Google Colab detected" in warning for warning in warnings)


class TestDebugInfo:
    """Test debug information functionality."""

    def test_get_debug_info(self, tmp_path):
        """Test getting debug information."""
        # Set up test environment
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        os.environ[EnvironmentManager.MANUSCRIPT_PATH] = str(manuscript_dir)
        os.environ[EnvironmentManager.RXIV_ENGINE] = "docker"
        os.environ[EnvironmentManager.RXIV_VERBOSE] = "true"
        os.environ[EnvironmentManager.DOCKER_AVAILABLE] = "true"
        os.environ[EnvironmentManager.PYTHONPATH] = "/path/one:/path/two"

        debug_info = EnvironmentManager.get_debug_info()

        # Check structure
        assert "rxiv_vars" in debug_info
        assert "engine" in debug_info
        assert "verbose" in debug_info
        assert "docker_available" in debug_info
        assert "google_colab" in debug_info
        assert "ci_environment" in debug_info
        assert "pythonpath_entries" in debug_info
        assert "validation_warnings" in debug_info

        # Check values
        assert debug_info["engine"] == "docker"
        assert debug_info["verbose"] is True
        assert debug_info["docker_available"] is True
        assert debug_info["pythonpath_entries"] == 2
        assert isinstance(debug_info["validation_warnings"], list)
