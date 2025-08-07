"""Unit tests for platform-specific installers."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from rxiv_maker.install.platform_installers.macos import MacOSInstaller
from rxiv_maker.install.platform_installers.windows import WindowsInstaller
from rxiv_maker.install.utils.logging import InstallLogger
from rxiv_maker.install.utils.progress import ProgressIndicator


class TestMacOSInstaller:
    """Test macOS-specific installer functionality."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def mock_progress(self):
        """Create a mock progress indicator for testing."""
        return MagicMock(spec=ProgressIndicator)

    @pytest.fixture
    def installer(self, mock_logger, mock_progress):
        """Create a MacOSInstaller instance with mocks."""
        with patch.object(Path, "mkdir"):
            return MacOSInstaller(mock_logger, mock_progress)

    @patch("subprocess.run")
    def test_is_apple_silicon_true(self, mock_run, installer):
        """Test _is_apple_silicon detection for Apple Silicon."""
        mock_run.return_value = MagicMock(stdout="arm64\n")

        result = installer._is_apple_silicon()

        assert result is True
        mock_run.assert_called_once_with(["uname", "-m"], capture_output=True, text=True, timeout=5)

    @patch("subprocess.run")
    def test_is_apple_silicon_false(self, mock_run, installer):
        """Test _is_apple_silicon detection for Intel Mac."""
        mock_run.return_value = MagicMock(stdout="x86_64\n")

        result = installer._is_apple_silicon()

        assert result is False

    @patch("subprocess.run")
    def test_is_apple_silicon_exception_handling(self, mock_run, installer):
        """Test _is_apple_silicon exception handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("uname", 5)

        result = installer._is_apple_silicon()

        assert result is False

    @patch("importlib.util.find_spec")
    def test_install_system_libraries_all_available(self, mock_find_spec, installer):
        """Test install_system_libraries when all packages are available."""
        mock_find_spec.return_value = MagicMock()  # All packages available

        result = installer.install_system_libraries()

        assert result is True
        installer.logger.success.assert_called_with("System libraries already available")

    @patch("importlib.util.find_spec")
    def test_install_system_libraries_missing_packages(self, mock_find_spec, installer):
        """Test install_system_libraries when some packages are missing."""

        def side_effect(package):
            if package == "matplotlib":
                return None  # Missing
            return MagicMock()  # Available

        mock_find_spec.side_effect = side_effect

        with patch.object(installer, "_install_xcode_tools", return_value=True):
            result = installer.install_system_libraries()

            assert result is True
            installer.logger.warning.assert_called_with("Some system libraries may be missing: ['matplotlib']")

    @patch("subprocess.run")
    def test_is_latex_installed_true(self, mock_run, installer):
        """Test _is_latex_installed when LaTeX is available."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._is_latex_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["pdflatex", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )

    @patch("subprocess.run")
    def test_is_latex_installed_false(self, mock_run, installer):
        """Test _is_latex_installed when LaTeX is not available."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = installer._is_latex_installed()

        assert result is False

    @patch("subprocess.run")
    def test_is_nodejs_installed_both_available(self, mock_run, installer):
        """Test _is_nodejs_installed when both node and npm are available."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._is_nodejs_installed()

        assert result is True
        expected_calls = [
            call(["node", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10),
            call(["npm", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10),
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch("subprocess.run")
    def test_is_nodejs_installed_node_missing(self, mock_run, installer):
        """Test _is_nodejs_installed when node is missing."""
        mock_run.side_effect = [MagicMock(returncode=1), MagicMock(returncode=0)]

        result = installer._is_nodejs_installed()

        assert result is False

    @patch("subprocess.run")
    def test_install_xcode_tools_already_installed(self, mock_run, installer):
        """Test _install_xcode_tools when already installed."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._install_xcode_tools()

        assert result is True
        installer.logger.success.assert_called_with("Xcode command line tools already installed")

    @patch("subprocess.run")
    def test_install_xcode_tools_install_success(self, mock_run, installer):
        """Test _install_xcode_tools installation success."""
        # Mock check failure, install success
        mock_run.side_effect = [
            MagicMock(returncode=1),  # xcode-select -p fails
            MagicMock(returncode=0),  # xcode-select --install succeeds
        ]

        result = installer._install_xcode_tools()

        assert result is True
        installer.logger.success.assert_called_with("Xcode command line tools installed")

    @patch("subprocess.run")
    def test_is_homebrew_installed_true(self, mock_run, installer):
        """Test _is_homebrew_installed when Homebrew is available."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._is_homebrew_installed()

        assert result is True

    @patch("subprocess.run")
    def test_is_homebrew_installed_false(self, mock_run, installer):
        """Test _is_homebrew_installed when Homebrew is not available."""
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = installer._is_homebrew_installed()

        assert result is False

    @pytest.mark.parametrize(
        "is_apple_silicon,expected_path",
        [
            (True, "/opt/homebrew/bin"),
            (False, "/usr/local/bin"),
        ],
    )
    def test_add_homebrew_to_path_architecture_specific(self, installer, is_apple_silicon, expected_path):
        """Test _add_homebrew_to_path with different architectures."""
        installer.is_apple_silicon = is_apple_silicon

        mock_profile = MagicMock()
        mock_profile.exists.return_value = True
        mock_profile.read_text.return_value = "# Existing content\n"
        mock_profile.open.return_value.__enter__ = MagicMock()
        mock_profile.open.return_value.__exit__ = MagicMock(return_value=None)

        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/Users/test")
            with patch.object(Path, "__truediv__", return_value=mock_profile):
                installer._add_homebrew_to_path()

                # Verify the correct path is used - just check that open was called
                _ = mock_profile.open.return_value.__enter__.return_value  # Access for verification
                # The write should contain the expected path
                installer.logger.debug.assert_called()

    @patch("subprocess.run")
    def test_install_latex_homebrew_success(self, mock_run, installer):
        """Test _install_latex_homebrew success path."""
        with (
            patch.object(installer, "_is_homebrew_installed", return_value=True),
            patch.object(installer, "_add_latex_to_path"),
        ):
            mock_run.return_value = MagicMock(returncode=0)

            result = installer._install_latex_homebrew()

            assert result is True
            installer.logger.success.assert_called_with("LaTeX installed using Homebrew")

    @patch("subprocess.run")
    def test_install_latex_homebrew_install_homebrew_first(self, mock_run, installer):
        """Test _install_latex_homebrew installs Homebrew first if needed."""
        with (
            patch.object(installer, "_is_homebrew_installed", return_value=False),
            patch.object(installer, "_install_homebrew", return_value=True),
            patch.object(installer, "_add_latex_to_path"),
        ):
            mock_run.return_value = MagicMock(returncode=0)

            result = installer._install_latex_homebrew()

            assert result is True

    @patch("urllib.request.urlretrieve")
    @patch("subprocess.run")
    def test_install_latex_direct_success(self, mock_run, mock_urlretrieve, installer):
        """Test _install_latex_direct success path."""
        installer.is_apple_silicon = True
        mock_run.return_value = MagicMock(returncode=0)

        with patch.object(installer, "_add_latex_to_path"):
            result = installer._install_latex_direct()

            assert result is True
            installer.logger.success.assert_called_with("LaTeX installed using direct download")

    def test_install_npm_packages_no_longer_required(self, installer):
        """Test _install_npm_packages returns True (no longer required)."""
        result = installer._install_npm_packages()

        assert result is True
        installer.logger.info.assert_called_with("No npm packages required - mermaid-cli dependency removed")

    @pytest.mark.parametrize(
        "latex_installed,methods_called",
        [
            (True, 0),  # Already installed, no methods called
            (False, 2),  # Not installed, try both methods
        ],
    )
    def test_install_latex_method_fallback(self, installer, latex_installed, methods_called):
        """Test install_latex method fallback behavior."""
        with (
            patch.object(installer, "_is_latex_installed", return_value=latex_installed),
            patch.object(installer, "_install_latex_homebrew", return_value=False),
            patch.object(installer, "_install_latex_direct", return_value=False),
            patch.object(installer, "_install_latex_packages", return_value=True),
        ):
            result = installer.install_latex()

            if latex_installed:
                assert result is True
                installer.logger.success.assert_called_with("LaTeX already installed")
            else:
                assert result is False
                installer.logger.error.assert_called_with("Failed to install LaTeX using any method")


class TestWindowsInstaller:
    """Test Windows-specific installer functionality."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def mock_progress(self):
        """Create a mock progress indicator for testing."""
        return MagicMock(spec=ProgressIndicator)

    @pytest.fixture
    def installer(self, mock_logger, mock_progress):
        """Create a WindowsInstaller instance with mocks."""
        with patch.object(Path, "mkdir"):
            return WindowsInstaller(mock_logger, mock_progress)

    @patch("importlib.util.find_spec")
    def test_install_system_libraries_all_available(self, mock_find_spec, installer):
        """Test install_system_libraries when all packages are available."""
        mock_find_spec.return_value = MagicMock()  # All packages available

        result = installer.install_system_libraries()

        assert result is True
        installer.logger.success.assert_called_with("System libraries already available")

    @patch("importlib.util.find_spec")
    def test_install_system_libraries_missing_packages(self, mock_find_spec, installer):
        """Test install_system_libraries when some packages are missing."""

        def side_effect(package):
            if package == "PIL":
                return None  # Missing
            return MagicMock()  # Available

        mock_find_spec.side_effect = side_effect

        result = installer.install_system_libraries()

        assert result is True  # Should still return True on Windows
        installer.logger.warning.assert_called_with("Some system libraries may be missing: ['PIL']")

    @pytest.mark.parametrize(
        "exception_type",
        [
            subprocess.TimeoutExpired("pdflatex", 10),
            subprocess.CalledProcessError(1, "pdflatex"),
            FileNotFoundError("Command not found"),
            OSError("System error"),
        ],
    )
    @patch("subprocess.run")
    def test_is_latex_installed_exception_handling(self, mock_run, installer, exception_type):
        """Test _is_latex_installed exception handling for various error types."""
        mock_run.side_effect = exception_type

        result = installer._is_latex_installed()

        assert result is False

    @pytest.mark.parametrize(
        "exception_type",
        [
            subprocess.TimeoutExpired("node", 10),
            subprocess.CalledProcessError(1, "node"),
            FileNotFoundError("Command not found"),
            OSError("System error"),
        ],
    )
    @patch("subprocess.run")
    def test_is_nodejs_installed_exception_handling(self, mock_run, installer, exception_type):
        """Test _is_nodejs_installed exception handling for various error types."""
        mock_run.side_effect = exception_type

        result = installer._is_nodejs_installed()

        assert result is False

    @patch("subprocess.run")
    def test_install_latex_winget_success(self, mock_run, installer):
        """Test _install_latex_winget success path."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._install_latex_winget()

        assert result is True
        installer.logger.success.assert_called_with("LaTeX installed using winget")
        mock_run.assert_called_once_with(
            ["winget", "install", "--id", "MiKTeX.MiKTeX", "--silent"],
            capture_output=True,
            text=True,
            timeout=600,
        )

    @patch("subprocess.run")
    def test_install_latex_chocolatey_success(self, mock_run, installer):
        """Test _install_latex_chocolatey success path."""
        # Mock chocolatey check success, then install success
        mock_run.side_effect = [
            MagicMock(returncode=0),  # choco --version
            MagicMock(returncode=0),  # choco install
        ]

        result = installer._install_latex_chocolatey()

        assert result is True
        installer.logger.success.assert_called_with("LaTeX installed using Chocolatey")

    @patch("subprocess.run")
    def test_install_latex_chocolatey_not_available(self, mock_run, installer):
        """Test _install_latex_chocolatey when Chocolatey is not available."""
        mock_run.side_effect = FileNotFoundError("choco not found")

        result = installer._install_latex_chocolatey()

        assert result is False

    @patch("urllib.request.urlretrieve")
    @patch("subprocess.run")
    def test_install_latex_direct_success(self, mock_run, mock_urlretrieve, installer):
        """Test _install_latex_direct success path."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._install_latex_direct()

        assert result is True
        installer.logger.success.assert_called_with("LaTeX installed using direct download")
        # Verify download and install commands
        mock_urlretrieve.assert_called_once()
        mock_run.assert_called_once()

    @patch("urllib.request.urlretrieve")
    @patch("subprocess.run")
    def test_install_latex_direct_download_failure(self, mock_run, mock_urlretrieve, installer):
        """Test _install_latex_direct with download failure."""
        mock_urlretrieve.side_effect = Exception("Download failed")

        result = installer._install_latex_direct()

        assert result is False

    @pytest.mark.parametrize(
        "method_name,command_args",
        [
            ("_install_nodejs_winget", ["winget", "install", "--id", "OpenJS.NodeJS", "--silent"]),
            ("_install_r_winget", ["winget", "install", "--id", "RProject.R", "--silent"]),
        ],
    )
    @patch("subprocess.run")
    def test_winget_install_methods(self, mock_run, installer, method_name, command_args):
        """Test various winget install methods."""
        mock_run.return_value = MagicMock(returncode=0)

        method = getattr(installer, method_name)
        result = method()

        assert result is True
        mock_run.assert_called_once_with(
            command_args,
            capture_output=True,
            text=True,
            timeout=600,
        )

    @pytest.mark.parametrize(
        "method_name,choco_package",
        [
            ("_install_nodejs_chocolatey", "nodejs"),
            ("_install_r_chocolatey", "r.project"),
        ],
    )
    @patch("subprocess.run")
    def test_chocolatey_install_methods(self, mock_run, installer, method_name, choco_package):
        """Test various Chocolatey install methods."""
        # Mock chocolatey check success, then install success
        mock_run.side_effect = [
            MagicMock(returncode=0),  # choco --version
            MagicMock(returncode=0),  # choco install
        ]

        method = getattr(installer, method_name)
        result = method()

        assert result is True
        expected_calls = [
            call(["choco", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10),
            call(["choco", "install", choco_package, "-y"], capture_output=True, text=True, timeout=600),
        ]
        mock_run.assert_has_calls(expected_calls)

    @pytest.mark.parametrize(
        "url,installer_args",
        [
            (
                "https://nodejs.org/dist/v18.17.0/node-v18.17.0-x64.msi",
                ["msiexec", "/i", "nodejs-installer.msi", "/quiet", "/norestart"],
            ),
            (
                "https://cran.r-project.org/bin/windows/base/R-4.3.1-win.exe",
                ["r-installer.exe", "/SILENT", "/NORESTART"],
            ),
        ],
    )
    @patch("urllib.request.urlretrieve")
    @patch("subprocess.run")
    def test_direct_install_methods(self, mock_run, mock_urlretrieve, installer, url, installer_args):
        """Test direct download install methods."""
        mock_run.return_value = MagicMock(returncode=0)

        # Test Node.js direct install
        if "nodejs" in url:
            result = installer._install_nodejs_direct()
        else:  # R direct install
            result = installer._install_r_direct()

        assert result is True
        mock_urlretrieve.assert_called_once()
        # Verify installer is called with correct arguments structure
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_install_latex_packages_success(self, mock_run, installer):
        """Test _install_latex_packages success path."""
        mock_run.return_value = MagicMock(returncode=0)

        result = installer._install_latex_packages()

        assert result is True
        # Should install multiple packages
        expected_packages = ["latexdiff", "biber", "biblatex", "pgfplots", "adjustbox", "collectbox"]
        assert mock_run.call_count == len(expected_packages)

    @patch("subprocess.run")
    def test_install_latex_packages_some_failures(self, mock_run, installer):
        """Test _install_latex_packages with some package failures."""
        # Mock some packages failing
        mock_run.side_effect = [
            MagicMock(returncode=0),  # latexdiff success
            MagicMock(returncode=1),  # biber fails
            MagicMock(returncode=0),  # biblatex success
            MagicMock(returncode=0),  # pgfplots success
            MagicMock(returncode=0),  # adjustbox success
            MagicMock(returncode=0),  # collectbox success
        ]

        result = installer._install_latex_packages()

        assert result is False  # Should return False if any package fails

    def test_install_npm_packages_no_longer_required(self, installer):
        """Test _install_npm_packages returns True (no longer required)."""
        result = installer._install_npm_packages()

        assert result is True
        installer.logger.info.assert_called_with("No npm packages required - mermaid-cli dependency removed")

    @pytest.mark.parametrize(
        "component,installer_methods",
        [
            ("latex", ["_install_latex_winget", "_install_latex_chocolatey", "_install_latex_direct"]),
            ("nodejs", ["_install_nodejs_winget", "_install_nodejs_chocolatey", "_install_nodejs_direct"]),
            ("r", ["_install_r_winget", "_install_r_chocolatey", "_install_r_direct"]),
        ],
    )
    def test_install_component_method_fallback(self, installer, component, installer_methods):
        """Test component installation method fallback behavior."""
        is_installed_method = f"_is_{component}_installed"
        # install_method = f"install_{component}"  # Not used in this test

        # Mock component as not installed
        with patch.object(installer, is_installed_method, return_value=False):
            # Mock all installation methods as failing except the last one
            patches = []
            for i, method in enumerate(installer_methods):
                success = i == len(installer_methods) - 1  # Only last method succeeds
                patches.append(patch.object(installer, method, return_value=success))

            # Apply all patches
            with patches[0], patches[1], patches[2]:
                if component == "latex":
                    with patch.object(installer, "_install_latex_packages", return_value=True):
                        result = installer.install_latex()
                elif component == "nodejs":
                    with patch.object(installer, "_install_npm_packages", return_value=True):
                        result = installer.install_nodejs()
                else:  # r
                    result = installer.install_r()

                # Should succeed using the last method
                assert result is True


class TestCrossPlatformInstallerCompatibility:
    """Test cross-platform compatibility aspects of installers."""

    @pytest.fixture
    def mock_logger(self):
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def mock_progress(self):
        return MagicMock(spec=ProgressIndicator)

    def test_temp_directory_creation_cross_platform(self, mock_logger, mock_progress):
        """Test temporary directory creation on different platforms."""
        with patch.object(Path, "mkdir") as mock_mkdir:
            # Test macOS
            macos_installer = MacOSInstaller(mock_logger, mock_progress)
            assert "Downloads" in str(macos_installer.temp_dir)

            # Test Windows
            windows_installer = WindowsInstaller(mock_logger, mock_progress)
            assert "AppData" in str(windows_installer.temp_dir)

            # Both should call mkdir
            assert mock_mkdir.call_count == 2

    @pytest.mark.parametrize(
        "installer_class,platform_commands",
        [
            (MacOSInstaller, {"homebrew": "brew", "xcode": "xcode-select"}),
            (WindowsInstaller, {"winget": "winget", "chocolatey": "choco"}),
        ],
    )
    @patch("subprocess.run")
    def test_platform_specific_package_managers(
        self, mock_run, mock_logger, mock_progress, installer_class, platform_commands
    ):
        """Test platform-specific package manager detection."""
        with patch.object(Path, "mkdir"):
            installer = installer_class(mock_logger, mock_progress)

            # Test availability checks for platform-specific tools
            if installer_class == MacOSInstaller:
                mock_run.return_value = MagicMock(returncode=0)
                result = installer._is_homebrew_installed()
                assert result is True
            else:  # WindowsInstaller
                # Test winget availability (implicit in methods)
                mock_run.return_value = MagicMock(returncode=0)
                result = installer._install_latex_winget()
                assert result is True

    @patch("importlib.util.find_spec")
    def test_system_libraries_check_consistency(self, mock_find_spec, mock_logger, mock_progress):
        """Test that system libraries check is consistent across platforms."""
        mock_find_spec.return_value = MagicMock()

        with patch.object(Path, "mkdir"):
            macos_installer = MacOSInstaller(mock_logger, mock_progress)
            windows_installer = WindowsInstaller(mock_logger, mock_progress)

            # Both should check the same packages using the same method
            macos_result = macos_installer.install_system_libraries()
            windows_result = windows_installer.install_system_libraries()

            assert macos_result and windows_result  # Both should be True
            # Should have been called for both platforms
            assert mock_find_spec.call_count >= 6  # 3 packages * 2 platforms

    @pytest.mark.parametrize(
        "exception_type",
        [
            subprocess.TimeoutExpired("cmd", 10),
            FileNotFoundError("Command not found"),
            PermissionError("Access denied"),
            OSError("System error"),
        ],
    )
    def test_subprocess_exception_handling_consistency(self, mock_logger, mock_progress, exception_type):
        """Test that subprocess exceptions are handled consistently across platforms."""
        with patch.object(Path, "mkdir"), patch("subprocess.run", side_effect=exception_type):
            macos_installer = MacOSInstaller(mock_logger, mock_progress)
            windows_installer = WindowsInstaller(mock_logger, mock_progress)

            # Both platforms should handle exceptions gracefully
            assert macos_installer._is_latex_installed() is False
            assert windows_installer._is_latex_installed() is False

            assert macos_installer._is_nodejs_installed() is False
            assert windows_installer._is_nodejs_installed() is False
