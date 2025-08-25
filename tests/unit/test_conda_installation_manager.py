"""Tests for conda installation manager functionality.

This module tests the conda-specific installation paths in the InstallManager
to ensure dependencies are installed correctly in conda environments.
"""

import os
import subprocess
import unittest
from unittest.mock import Mock, patch

from rxiv_maker.core.managers.install_manager import InstallManager, InstallMode


class TestCondaInstallationManager(unittest.TestCase):
    """Test InstallManager conda functionality."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment
        self.original_env = {
            key: os.environ.get(key)
            for key in ["CONDA_DEFAULT_ENV", "CONDA_PREFIX", "MAMBA_DEFAULT_ENV", "MAMBA_PREFIX"]
        }

        # Clear conda environment by default
        for key in self.original_env:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Restore original environment."""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]

    def test_conda_environment_detection(self):
        """Test that InstallManager detects conda environments."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"
        os.environ["CONDA_PREFIX"] = "/conda/envs/test_env"

        manager = InstallManager()
        self.assertTrue(manager._is_in_conda())

    def test_mamba_environment_detection(self):
        """Test that InstallManager detects mamba environments."""
        os.environ["MAMBA_DEFAULT_ENV"] = "test_env"
        os.environ["MAMBA_PREFIX"] = "/mamba/envs/test_env"

        manager = InstallManager()
        self.assertTrue(manager._is_in_conda())

    def test_no_conda_environment(self):
        """Test behavior when not in conda environment."""
        manager = InstallManager()
        self.assertFalse(manager._is_in_conda())

    @patch("shutil.which")
    def test_get_conda_executable_mamba_preferred(self, mock_which):
        """Test that mamba is preferred over conda."""

        def which_side_effect(cmd):
            if cmd == "mamba":
                return "/usr/bin/mamba"
            elif cmd == "conda":
                return "/usr/bin/conda"
            return None

        mock_which.side_effect = which_side_effect

        manager = InstallManager()
        result = manager._get_conda_executable()
        self.assertEqual(result, "mamba")

    @patch("shutil.which")
    def test_get_conda_executable_conda_fallback(self, mock_which):
        """Test conda fallback when mamba unavailable."""

        def which_side_effect(cmd):
            if cmd == "conda":
                return "/usr/bin/conda"
            return None

        mock_which.side_effect = which_side_effect

        manager = InstallManager()
        result = manager._get_conda_executable()
        self.assertEqual(result, "conda")

    @patch("shutil.which")
    def test_get_conda_executable_none(self, mock_which):
        """Test when neither conda nor mamba are available."""
        mock_which.return_value = None

        manager = InstallManager()
        result = manager._get_conda_executable()
        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_conda_installation_full_mode(self, mock_which, mock_run):
        """Test conda installation in full mode."""
        # Set up conda environment
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        mock_which.return_value = "/usr/bin/conda"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        # Mock platform installer and other dependencies
        manager = InstallManager(mode=InstallMode.FULL)

        with patch.object(manager, "logger"):
            with patch.object(manager, "progress"):
                with patch.object(manager, "platform_installer") as mock_platform:
                    with patch.object(manager, "_post_install_verification", return_value=True):
                        with patch.object(manager, "_generate_report"):
                            mock_platform.install_latex.return_value = True

                            result = manager._run_conda_installation()
                            self.assertTrue(result)

                            # Check that conda install was called with expected packages
                            self.assertTrue(mock_run.called)
                            conda_calls = [call for call in mock_run.call_args_list if "install" in str(call)]
                            self.assertEqual(len(conda_calls), 1)
                            call_args = conda_calls[0][0][0]  # Get the command list
                            self.assertIn("install", call_args)
                            self.assertIn("-y", call_args)
                            self.assertIn("-c", call_args)
                            self.assertIn("conda-forge", call_args)
                            self.assertIn("r-base", call_args)
                            self.assertIn("nodejs", call_args)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_conda_installation_minimal_mode(self, mock_which, mock_run):
        """Test conda installation in minimal mode."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        mock_which.return_value = "/usr/bin/mamba"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        manager = InstallManager(mode=InstallMode.MINIMAL)

        with patch.object(manager, "logger"):
            with patch.object(manager, "progress"):
                with patch.object(manager, "platform_installer") as mock_platform:
                    with patch.object(manager, "_post_install_verification", return_value=True):
                        with patch.object(manager, "_generate_report"):
                            mock_platform.install_latex.return_value = True

                            result = manager._run_conda_installation()
                            self.assertTrue(result)

                            # In minimal mode, should not install R or Node.js via conda
                            conda_calls = [call for call in mock_run.call_args_list if "install" in str(call)]
                            # Should have no conda install calls in minimal mode
                            self.assertEqual(len(conda_calls), 0)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_conda_installation_failure(self, mock_which, mock_run):
        """Test conda installation failure handling."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        mock_which.return_value = "/usr/bin/conda"
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Installation failed")

        manager = InstallManager(mode=InstallMode.FULL)

        with patch.object(manager, "logger") as mock_logger:
            with patch.object(manager, "progress"):
                with patch.object(manager, "platform_installer"):
                    with patch.object(manager, "_post_install_verification", return_value=True):
                        with patch.object(manager, "_generate_report"):
                            result = manager._run_conda_installation()
                            self.assertFalse(result)

                            # Should log warning about conda failure
                            conda_calls = [call for call in mock_run.call_args_list if "install" in str(call)]
                            if conda_calls:  # Only check if conda install was attempted
                                mock_logger.warning.assert_called()

    @patch("subprocess.run")
    def test_conda_installation_no_executable(self, mock_run):
        """Test conda installation when executable is not found."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        with patch.object(InstallManager, "_get_conda_executable", return_value=None):
            manager = InstallManager()

            with patch.object(manager, "logger") as mock_logger:
                result = manager._run_conda_installation()
                self.assertFalse(result)

                # Should log error about missing executable
                mock_logger.error.assert_called()
                # Check that no conda install calls were made
                conda_calls = [call for call in mock_run.call_args_list if "install" in str(call)]
                self.assertEqual(len(conda_calls), 0)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_conda_installation_timeout(self, mock_which, mock_run):
        """Test conda installation timeout handling."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        mock_which.return_value = "/usr/bin/conda"
        mock_run.side_effect = subprocess.TimeoutExpired("conda", 300)

        manager = InstallManager(mode=InstallMode.FULL)

        with patch.object(manager, "logger") as mock_logger:
            with patch.object(manager, "progress"):
                result = manager._run_conda_installation()
                self.assertFalse(result)

                # Should log error about timeout
                mock_logger.error.assert_called()

    def test_install_method_conda_detection(self):
        """Test that install method detects and uses conda installation."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        manager = InstallManager()

        with patch.object(manager, "_run_conda_installation", return_value=True) as mock_conda_install:
            with patch.object(manager, "logger"):
                result = manager.install()
                self.assertTrue(result)
                mock_conda_install.assert_called_once()

    def test_install_method_fallback_to_regular(self):
        """Test that install method falls back to regular installation when not in conda."""
        manager = InstallManager()

        with patch.object(manager, "_is_in_docker", return_value=False):
            with patch.object(manager, "_is_in_conda", return_value=False):
                with patch.object(manager, "_pre_install_checks", return_value=True):
                    with patch.object(manager, "_run_platform_installation", return_value=True):
                        with patch.object(manager, "_post_install_verification", return_value=True):
                            with patch.object(manager, "_generate_report"):
                                with patch.object(manager, "logger"):
                                    result = manager.install()
                                    self.assertTrue(result)

    def test_conda_package_selection_by_mode(self):
        """Test that correct packages are selected based on install mode."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        test_cases = [
            (InstallMode.FULL, ["r-base", "nodejs"]),
            (InstallMode.CORE, ["nodejs"]),
            (InstallMode.MINIMAL, []),
            (InstallMode.SKIP_SYSTEM, []),
        ]

        for mode, expected_packages in test_cases:
            with self.subTest(mode=mode):
                with patch("subprocess.run") as mock_run:
                    with patch("shutil.which", return_value="/usr/bin/conda"):
                        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

                        manager = InstallManager(mode=mode)

                        with patch.object(manager, "logger"):
                            with patch.object(manager, "progress"):
                                with patch.object(manager, "platform_installer") as mock_platform:
                                    with patch.object(manager, "_post_install_verification", return_value=True):
                                        with patch.object(manager, "_generate_report"):
                                            mock_platform.install_latex.return_value = True

                                            manager._run_conda_installation()

                                            # Check conda install calls
                                            conda_calls = [
                                                call for call in mock_run.call_args_list if "install" in str(call)
                                            ]

                                            if expected_packages:
                                                self.assertEqual(len(conda_calls), 1)
                                                call_args = conda_calls[0][0][0]  # Get the command list
                                                for package in expected_packages:
                                                    self.assertIn(package, call_args)
                                            else:
                                                # Should not call conda install for packages
                                                self.assertEqual(len(conda_calls), 0)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_latex_installation_still_uses_system(self, mock_which, mock_run):
        """Test that LaTeX installation still uses system package manager even in conda."""
        os.environ["CONDA_DEFAULT_ENV"] = "test_env"

        mock_which.return_value = "/usr/bin/conda"
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        manager = InstallManager(mode=InstallMode.FULL)

        with patch.object(manager, "logger"):
            with patch.object(manager, "progress"):
                with patch.object(manager, "platform_installer") as mock_platform:
                    with patch.object(manager, "_post_install_verification", return_value=True):
                        with patch.object(manager, "_generate_report"):
                            mock_platform.install_latex.return_value = True

                            manager._run_conda_installation()

                            # Should call platform installer for LaTeX
                            mock_platform.install_latex.assert_called_once()


if __name__ == "__main__":
    unittest.main()
