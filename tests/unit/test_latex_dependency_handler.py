"""Test for LaTeX dependency handler."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from rxiv_maker.install.dependency_handlers.latex import LaTeXHandler
from rxiv_maker.install.utils.logging import InstallLogger


class TestLaTeXHandler:
    """Test LaTeX dependency handler functionality."""

    @pytest.fixture
    def latex_handler(self):
        """Create LaTeX handler instance with mock logger."""
        logger = MagicMock(spec=InstallLogger)
        return LaTeXHandler(logger)

    def test_essential_packages_includes_siunitx(self, latex_handler):
        """Test that siunitx package is included in essential packages list."""
        essential_packages = latex_handler.get_essential_packages()

        # Verify siunitx is in the list
        assert "siunitx" in essential_packages

        # Verify other critical packages are still there
        expected_packages = [
            "latexdiff",
            "biber",
            "biblatex",
            "pgfplots",
            "adjustbox",
            "collectbox",
            "xcolor",
            "graphicx",
            "hyperref",
            "amsmath",
            "amsfonts",
            "amssymb",
            "siunitx",
        ]

        for package in expected_packages:
            assert package in essential_packages, f"Package {package} missing from essential packages"

    def test_essential_packages_list_structure(self, latex_handler):
        """Test that essential packages list has correct structure."""
        essential_packages = latex_handler.get_essential_packages()

        # Should be a list
        assert isinstance(essential_packages, list)

        # Should have reasonable number of packages
        assert len(essential_packages) >= 10

        # All items should be strings
        for package in essential_packages:
            assert isinstance(package, str)
            assert len(package) > 0

    @patch("subprocess.run")
    def test_verify_installation_success(self, mock_run, latex_handler):
        """Test successful LaTeX installation verification."""
        # Mock successful pdflatex and bibtex calls
        mock_run.return_value = MagicMock(returncode=0)

        result = latex_handler.verify_installation()
        assert result is True

        # Should call both pdflatex and bibtex
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_verify_installation_pdflatex_failure(self, mock_run, latex_handler):
        """Test LaTeX installation verification when pdflatex fails."""
        # Mock pdflatex failure
        mock_run.return_value = MagicMock(returncode=1)

        result = latex_handler.verify_installation()
        assert result is False

    @patch("subprocess.run")
    def test_verify_installation_file_not_found(self, mock_run, latex_handler):
        """Test LaTeX installation verification when command not found."""
        # Mock FileNotFoundError (command not installed)
        mock_run.side_effect = FileNotFoundError("pdflatex not found")

        result = latex_handler.verify_installation()
        assert result is False

    @patch("subprocess.run")
    def test_verify_installation_timeout(self, mock_run, latex_handler):
        """Test LaTeX installation verification when command times out."""
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(["pdflatex"], 10)

        result = latex_handler.verify_installation()
        assert result is False

    @patch("subprocess.run")
    def test_get_version_success(self, mock_run, latex_handler):
        """Test successful version retrieval."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="pdfTeX 3.141592653-2.6-1.40.25 (TeX Live 2023)\nkpathsea version 6.3.5\n"
        )

        version = latex_handler.get_version()
        assert version is not None
        assert "pdfTeX" in version

    @patch("subprocess.run")
    def test_get_version_failure(self, mock_run, latex_handler):
        """Test version retrieval when command fails."""
        mock_run.return_value = MagicMock(returncode=1)

        version = latex_handler.get_version()
        assert version is None

    @patch("subprocess.run")
    def test_install_packages_success(self, mock_run, latex_handler):
        """Test successful package installation."""
        mock_run.return_value = MagicMock(returncode=0)

        packages = ["siunitx", "pgfplots"]
        result = latex_handler.install_packages(packages)

        assert result is True
        assert mock_run.call_count == len(packages)

    @patch("subprocess.run")
    def test_install_packages_partial_failure(self, mock_run, latex_handler):
        """Test package installation with some failures."""
        # First package succeeds, second fails
        mock_run.side_effect = [
            MagicMock(returncode=0),  # siunitx success
            MagicMock(returncode=1, stderr="Package not found"),  # pgfplots failure
        ]

        packages = ["siunitx", "pgfplots"]
        result = latex_handler.install_packages(packages)

        assert result is False  # Overall failure due to partial failure
        assert mock_run.call_count == len(packages)

    def test_install_packages_empty_list(self, latex_handler):
        """Test package installation with empty package list."""
        result = latex_handler.install_packages([])
        assert result is True

    @patch("subprocess.run")
    def test_install_packages_exception(self, mock_run, latex_handler):
        """Test package installation when tlmgr raises exception."""
        mock_run.side_effect = Exception("tlmgr not available")

        packages = ["siunitx"]
        result = latex_handler.install_packages(packages)

        assert result is False


class TestLaTeXStyleFileRequirements:
    """Test that style file requirements match essential packages."""

    def test_siunitx_requirement_coverage(self):
        """Test that siunitx requirement in style file is covered by essential packages."""
        # Read the style file to check for siunitx requirement
        style_file_path = "src/tex/style/rxiv_maker_style.cls"

        try:
            with open(style_file_path, "r", encoding="utf-8") as f:
                style_content = f.read()
        except FileNotFoundError:
            pytest.skip("Style file not found in test environment")

        # Check if siunitx is required in the style file
        if "\\RequirePackage{siunitx}" in style_content:
            # Verify it's in essential packages
            logger = MagicMock(spec=InstallLogger)
            handler = LaTeXHandler(logger)
            essential_packages = handler.get_essential_packages()

            assert "siunitx" in essential_packages, "siunitx required by style file but not in essential packages"

    def test_style_file_package_requirements_coverage(self):
        """Test that common LaTeX packages required by style file are in essential packages."""
        logger = MagicMock(spec=InstallLogger)
        handler = LaTeXHandler(logger)
        essential_packages = handler.get_essential_packages()

        # Common packages that rxiv_maker_style.cls likely requires
        common_requirements = [
            "amsmath",
            "amsfonts",
            "amssymb",
            "xcolor",
            "graphicx",
            "hyperref",
        ]

        for package in common_requirements:
            assert package in essential_packages, f"Common package {package} missing from essential packages"


class TestLaTeXErrorHandling:
    """Test LaTeX error handling scenarios."""

    @pytest.fixture
    def latex_handler(self):
        """Create LaTeX handler instance with mock logger."""
        logger = MagicMock(spec=InstallLogger)
        return LaTeXHandler(logger)

    @patch("subprocess.run")
    def test_verification_handles_permission_error(self, mock_run, latex_handler):
        """Test that verification handles permission errors gracefully."""
        mock_run.side_effect = PermissionError("Permission denied")

        result = latex_handler.verify_installation()
        assert result is False

    @patch("subprocess.run")
    def test_installation_handles_network_timeout(self, mock_run, latex_handler):
        """Test that package installation handles network timeouts."""
        mock_run.side_effect = subprocess.TimeoutExpired(["tlmgr"], 120)

        packages = ["siunitx"]
        result = latex_handler.install_packages(packages)

        assert result is False

    @patch("subprocess.run")
    def test_installation_logs_errors(self, mock_run, latex_handler):
        """Test that package installation logs errors properly."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Package 'nonexistent' not found")

        packages = ["nonexistent"]
        result = latex_handler.install_packages(packages)

        assert result is False
        # Verify logger was called with debug message
        latex_handler.logger.debug.assert_called()
