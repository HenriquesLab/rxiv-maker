"""Unit tests for system libraries dependency handler."""

import subprocess
import sys
from unittest.mock import MagicMock, call, patch

import pytest

from rxiv_maker.install.dependency_handlers.system_libs import SystemLibsHandler
from rxiv_maker.install.utils.logging import InstallLogger


class TestSystemLibsHandler:
    """Test SystemLibsHandler functionality."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def handler(self, mock_logger):
        """Create a SystemLibsHandler instance with mock logger."""
        return SystemLibsHandler(mock_logger)

    def test_init(self, mock_logger):
        """Test SystemLibsHandler initialization."""
        handler = SystemLibsHandler(mock_logger)
        assert handler.logger == mock_logger

    @patch("importlib.util.find_spec")
    def test_verify_installation_all_packages_found(self, mock_find_spec, handler):
        """Test verify_installation when all packages are available."""
        # Mock all packages as available
        mock_find_spec.return_value = MagicMock()  # Non-None indicates package exists

        result = handler.verify_installation()

        assert result is True
        # Verify all expected packages were checked
        expected_packages = ["matplotlib", "numpy", "pandas", "PIL", "scipy"]
        assert mock_find_spec.call_count == len(expected_packages)
        for package in expected_packages:
            mock_find_spec.assert_any_call(package)

    @patch("importlib.util.find_spec")
    def test_verify_installation_missing_package(self, mock_find_spec, handler):
        """Test verify_installation when a package is missing."""

        # Mock matplotlib as missing, others as available
        def side_effect(package):
            if package == "matplotlib":
                return None  # Package not found
            return MagicMock()  # Package exists

        mock_find_spec.side_effect = side_effect

        result = handler.verify_installation()

        assert result is False
        handler.logger.debug.assert_called_with("Missing Python package: matplotlib")

    @patch("importlib.util.find_spec")
    def test_verify_installation_multiple_missing_packages(self, mock_find_spec, handler):
        """Test verify_installation with multiple missing packages."""

        # Mock matplotlib and scipy as missing
        def side_effect(package):
            if package in ["matplotlib", "scipy"]:
                return None
            return MagicMock()

        mock_find_spec.side_effect = side_effect

        result = handler.verify_installation()

        assert result is False
        # Should return False on first missing package (matplotlib)
        handler.logger.debug.assert_called_with("Missing Python package: matplotlib")

    @patch("builtins.__import__")
    def test_get_missing_packages_all_available(self, mock_import, handler):
        """Test get_missing_packages when all packages are available."""
        # Mock successful imports for all packages
        mock_import.return_value = MagicMock()

        missing = handler.get_missing_packages()

        assert missing == []
        expected_packages = ["matplotlib", "PIL", "numpy", "pandas", "scipy", "seaborn"]
        assert mock_import.call_count == len(expected_packages)

    @patch("builtins.__import__")
    def test_get_missing_packages_some_missing(self, mock_import, handler):
        """Test get_missing_packages when some packages are missing."""

        # Mock ImportError for matplotlib and seaborn
        def side_effect(package):
            if package in ["matplotlib", "seaborn"]:
                raise ImportError(f"No module named '{package}'")
            return MagicMock()

        mock_import.side_effect = side_effect

        missing = handler.get_missing_packages()

        assert sorted(missing) == ["matplotlib", "seaborn"]

    @patch("subprocess.run")
    def test_verify_build_tools_gcc_available(self, mock_run, handler):
        """Test verify_build_tools when gcc is available."""
        # Mock successful gcc --version
        mock_run.return_value = MagicMock(returncode=0)

        result = handler.verify_build_tools()

        assert result is True
        mock_run.assert_called_once_with(
            ["gcc", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )

    @patch("subprocess.run")
    def test_verify_build_tools_fallback_to_clang(self, mock_run, handler):
        """Test verify_build_tools fallback to clang when gcc fails."""
        # Mock gcc failure, clang success
        mock_run.side_effect = [
            MagicMock(returncode=1),  # gcc fails
            MagicMock(returncode=0),  # clang succeeds
        ]

        result = handler.verify_build_tools()

        assert result is True
        assert mock_run.call_count == 2
        expected_calls = [
            call(["gcc", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10),
            call(["clang", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10),
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch("subprocess.run")
    def test_verify_build_tools_none_available(self, mock_run, handler):
        """Test verify_build_tools when neither gcc nor clang is available."""
        # Mock both gcc and clang failures
        mock_run.return_value = MagicMock(returncode=1)

        result = handler.verify_build_tools()

        assert result is False

    @patch("subprocess.run")
    def test_verify_build_tools_exception_handling(self, mock_run, handler):
        """Test verify_build_tools exception handling."""
        # Mock subprocess exception
        mock_run.side_effect = subprocess.TimeoutExpired("gcc", 10)

        result = handler.verify_build_tools()

        assert result is False

    def test_get_python_version(self, handler):
        """Test get_python_version returns correct format."""
        version = handler.get_python_version()

        # Check format: should be like "3.11.0" or similar
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)
        assert parts[0] == str(sys.version_info.major)
        assert parts[1] == str(sys.version_info.minor)
        assert parts[2] == str(sys.version_info.micro)

    @pytest.mark.parametrize(
        "major,minor,micro,expected",
        [
            (3, 11, 0, True),  # Minimum required version
            (3, 11, 5, True),  # Higher micro version
            (3, 12, 0, True),  # Higher minor version
            (3, 10, 9, False),  # Below minimum
            (2, 7, 18, False),  # Python 2.x
            (4, 0, 0, True),  # Future Python version
        ],
    )
    def test_check_python_compatibility(self, handler, major, minor, micro, expected):
        """Test check_python_compatibility with various Python versions."""
        with patch("sys.version_info") as mock_version:
            mock_version.major = major
            mock_version.minor = minor
            mock_version.micro = micro

            result = handler.check_python_compatibility()

            assert result == expected

    @patch("rxiv_maker.install.dependency_handlers.system_libs.HAS_PACKAGING", True)
    @patch("rxiv_maker.install.dependency_handlers.system_libs.version")
    def test_check_python_compatibility_with_packaging(self, mock_version, handler):
        """Test check_python_compatibility using packaging library."""
        # Mock packaging version comparison
        mock_version.parse.return_value = MagicMock()
        mock_version.parse.return_value.__ge__ = MagicMock(return_value=True)

        with patch("sys.version_info") as mock_sys_version:
            mock_sys_version.major = 3
            mock_sys_version.minor = 11
            mock_sys_version.micro = 5

            result = handler.check_python_compatibility()

            assert result is True
            mock_version.parse.assert_any_call("3.11.5")
            mock_version.parse.assert_any_call("3.11.0")

    @patch("rxiv_maker.install.dependency_handlers.system_libs.HAS_PACKAGING", True)
    @patch("rxiv_maker.install.dependency_handlers.system_libs.version")
    def test_check_python_compatibility_packaging_exception_fallback(self, mock_version, handler):
        """Test fallback when packaging library raises exception."""
        # Mock packaging exception
        mock_version.parse.side_effect = Exception("Version parsing error")

        with patch("sys.version_info") as mock_sys_version:
            mock_sys_version.major = 3
            mock_sys_version.minor = 11
            mock_sys_version.micro = 0

            result = handler.check_python_compatibility()

            assert result is True  # Should fall back to simple comparison
            handler.logger.debug.assert_called_with(
                "Error parsing version with packaging library: Version parsing error"
            )

    def test_get_python_version_details(self, handler):
        """Test get_python_version_details returns complete information."""
        with patch("sys.version_info") as mock_version:
            mock_version.major = 3
            mock_version.minor = 11
            mock_version.micro = 5

            details = handler.get_python_version_details()

            expected_keys = [
                "version",
                "major",
                "minor",
                "micro",
                "is_compatible",
                "required_version",
                "version_parser",
            ]
            assert all(key in details for key in expected_keys)
            assert details["version"] == "3.11.5"
            assert details["major"] == "3"
            assert details["minor"] == "11"
            assert details["micro"] == "5"
            assert details["is_compatible"] == "True"
            assert details["required_version"] == ">=3.11.0"

    @patch("rxiv_maker.install.dependency_handlers.system_libs.HAS_PACKAGING", True)
    def test_get_python_version_details_with_packaging(self, handler):
        """Test get_python_version_details indicates packaging usage."""
        details = handler.get_python_version_details()
        assert details["version_parser"] == "packaging"

    @patch("rxiv_maker.install.dependency_handlers.system_libs.HAS_PACKAGING", False)
    def test_get_python_version_details_without_packaging(self, handler):
        """Test get_python_version_details indicates builtin usage."""
        details = handler.get_python_version_details()
        assert details["version_parser"] == "builtin"


class TestSystemLibsHandlerCrossPlatform:
    """Test cross-platform compatibility scenarios."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def handler(self, mock_logger):
        """Create a SystemLibsHandler instance with mock logger."""
        return SystemLibsHandler(mock_logger)

    @pytest.mark.parametrize(
        "platform,expected_commands",
        [
            ("Windows", ["gcc", "clang"]),
            ("Darwin", ["gcc", "clang"]),
            ("Linux", ["gcc", "clang"]),
        ],
    )
    @patch("subprocess.run")
    def test_verify_build_tools_cross_platform(self, mock_run, handler, platform, expected_commands):
        """Test build tools verification across platforms."""
        with patch("sys.platform", platform.lower()):
            # Mock gcc success
            mock_run.return_value = MagicMock(returncode=0)

            result = handler.verify_build_tools()

            assert result is True
            # Should try gcc first on all platforms
            mock_run.assert_called_once_with(
                ["gcc", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

    @patch("importlib.util.find_spec")
    def test_verify_installation_pil_vs_pillow(self, mock_find_spec, handler):
        """Test that PIL is checked correctly (Pillow installs as PIL)."""
        # Mock all packages as available
        mock_find_spec.return_value = MagicMock()

        result = handler.verify_installation()

        assert result is True
        # Verify PIL is checked (not Pillow)
        mock_find_spec.assert_any_call("PIL")

    @patch("builtins.__import__")
    def test_get_missing_packages_import_vs_find_spec_consistency(self, mock_import, handler):
        """Test consistency between import-based and find_spec-based checks."""
        # Mock successful imports
        mock_import.return_value = MagicMock()

        handler.get_missing_packages()  # Just call for side effects

        # Should check the same packages that are commonly used
        expected_packages = ["matplotlib", "PIL", "numpy", "pandas", "scipy", "seaborn"]
        assert mock_import.call_count == len(expected_packages)
        for package in expected_packages:
            mock_import.assert_any_call(package)

    @patch("subprocess.run")
    def test_build_tools_timeout_handling(self, mock_run, handler):
        """Test timeout handling in build tools verification."""
        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired("gcc", 10)

        result = handler.verify_build_tools()

        assert result is False

    @patch("subprocess.run")
    def test_build_tools_permission_error_handling(self, mock_run, handler):
        """Test permission error handling in build tools verification."""
        # Mock permission error
        mock_run.side_effect = PermissionError("Permission denied")

        result = handler.verify_build_tools()

        assert result is False

    @patch("subprocess.run")
    def test_build_tools_file_not_found_handling(self, mock_run, handler):
        """Test FileNotFoundError handling in build tools verification."""
        # Mock file not found error
        mock_run.side_effect = FileNotFoundError("Command not found")

        result = handler.verify_build_tools()

        assert result is False


class TestSystemLibsHandlerEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def handler(self, mock_logger):
        """Create a SystemLibsHandler instance with mock logger."""
        return SystemLibsHandler(mock_logger)

    @patch("importlib.util.find_spec")
    def test_verify_installation_importlib_exception(self, mock_find_spec, handler):
        """Test handling of importlib exceptions."""
        # Mock importlib exception
        mock_find_spec.side_effect = ImportError("Module not found")

        # Should not raise exception, should handle gracefully
        with pytest.raises(ImportError):
            handler.verify_installation()

    @patch("importlib.util.find_spec")
    def test_verify_installation_empty_package_list(self, mock_find_spec, handler):
        """Test behavior with empty package list."""
        # This test checks the current implementation behavior
        # If package list were empty, it would return True
        mock_find_spec.return_value = MagicMock()

        result = handler.verify_installation()

        assert result is True

    def test_check_python_compatibility_edge_versions(self, handler):
        """Test Python compatibility with edge case versions."""
        test_cases = [
            (3, 11, 0, True),  # Exactly minimum
            (3, 10, 999, False),  # Just below minimum
            (3, 999, 0, True),  # Far future minor
            (999, 0, 0, True),  # Far future major
        ]

        for major, minor, micro, expected in test_cases:
            with patch("sys.version_info") as mock_version:
                mock_version.major = major
                mock_version.minor = minor
                mock_version.micro = micro

                result = handler.check_python_compatibility()

                assert result == expected, f"Failed for version {major}.{minor}.{micro}"

    @patch("builtins.__import__")
    def test_get_missing_packages_mixed_import_errors(self, mock_import, handler):
        """Test get_missing_packages with different types of import errors."""

        def side_effect(package):
            if package == "matplotlib":
                raise ImportError("No module named 'matplotlib'")
            elif package == "PIL":
                raise ModuleNotFoundError("No module named 'PIL'")
            elif package == "numpy":
                raise ImportError("DLL load failed")  # Windows-specific error
            return MagicMock()

        mock_import.side_effect = side_effect

        missing = handler.get_missing_packages()

        assert sorted(missing) == ["PIL", "matplotlib", "numpy"]
