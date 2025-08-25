"""Integration tests for LaTeX dependency handling."""

from unittest.mock import MagicMock, patch

import pytest

from rxiv_maker.engines.operations.build_manager import BuildManager
from rxiv_maker.install.dependency_handlers.latex import LaTeXHandler
from rxiv_maker.install.utils.logging import InstallLogger


class TestLaTeXDependencyIntegration:
    """Integration tests for LaTeX dependency handling in real build scenarios."""

    def setup_test_manuscript(self, temp_dir, name="test_manuscript"):
        """Set up a test manuscript with LaTeX style requirements."""
        manuscript_dir = temp_dir / name
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        # Create config file
        config_content = """title: "Test Manuscript"
authors:
  - name: "Test Author"
    email: "test@example.com"
abstract: "Test abstract"
"""
        (manuscript_dir / "00_CONFIG.yml").write_text(config_content)

        # Create main manuscript with siunitx usage
        main_content = """# Test Manuscript

This manuscript uses siunitx for units: \\SI{10}{\\meter}.

## Methods

We measured values in \\si{\\meter\\per\\second}.
"""
        (manuscript_dir / "01_MAIN.md").write_text(main_content)

        # Create bibliography
        bib_content = """@article{test2024,
  title={Test Article},
  author={Test Author},
  journal={Test Journal},
  year={2024}
}"""
        (manuscript_dir / "03_REFERENCES.bib").write_text(bib_content)

        return manuscript_dir

    def setup_mock_style_files(self, temp_dir):
        """Set up mock style files with siunitx requirement."""
        style_dir = temp_dir / "style"
        style_dir.mkdir()

        # Create style file that requires siunitx
        cls_content = """\\NeedsTeXFormat{LaTeX2e}
\\ProvidesClass{rxiv_maker_style}[2025/01/01 Test style]
\\LoadClass{article}

% Essential packages
\\RequirePackage{amsmath}
\\RequirePackage{amsfonts}
\\RequirePackage{amssymb}
\\RequirePackage{xcolor}
\\RequirePackage{graphicx}
\\RequirePackage{hyperref}
\\RequirePackage{siunitx}  % This is the critical package

% Document setup
\\setcounter{secnumdepth}{0}
"""
        (style_dir / "rxiv_maker_style.cls").write_text(cls_content)

        # Create bibliography style
        bst_content = """% Test bibliography style
ENTRY
  { address
    author
    title
    journal
    year
  }
  {}
  { label }
"""
        (style_dir / "rxiv_maker_style.bst").write_text(bst_content)

        return style_dir

    @pytest.mark.integration
    def test_build_with_missing_siunitx_package(self, tmp_path):
        """Test build failure when siunitx package is missing."""
        manuscript_dir = self.setup_test_manuscript(tmp_path)
        output_dir = tmp_path / "output"
        style_dir = self.setup_mock_style_files(tmp_path)

        # Create build manager
        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # Override style directory to use our mock
        build_manager.style_dir = style_dir

        # Copy style files first
        assert build_manager.copy_style_files() is True

        # Verify style files were copied and contain siunitx requirement
        copied_cls = output_dir / "rxiv_maker_style.cls"
        assert copied_cls.exists()
        cls_content = copied_cls.read_text()
        assert "\\RequirePackage{siunitx}" in cls_content

    @pytest.mark.integration
    def test_latex_handler_includes_required_packages(self):
        """Test that LaTeX handler includes all packages required by style file."""
        logger = MagicMock(spec=InstallLogger)
        handler = LaTeXHandler(logger)

        essential_packages = handler.get_essential_packages()

        # Verify critical packages for rxiv_maker_style.cls
        required_packages = [
            "siunitx",  # For units and measurements
            "amsmath",  # Mathematical typesetting
            "amsfonts",  # Mathematical fonts
            "amssymb",  # Mathematical symbols
            "xcolor",  # Color support
            "graphicx",  # Graphics inclusion
            "hyperref",  # Hyperlinks and PDF features
        ]

        for package in required_packages:
            assert package in essential_packages, f"Required package {package} missing from essential packages"

    @pytest.mark.integration
    def test_style_file_and_package_consistency(self, tmp_path):
        """Test consistency between style file requirements and essential packages."""
        # Set up style files
        style_dir = self.setup_mock_style_files(tmp_path)
        cls_file = style_dir / "rxiv_maker_style.cls"

        # Read style file content
        cls_content = cls_file.read_text()

        # Extract required packages from style file
        import re

        required_packages = re.findall(r"\\RequirePackage\{([^}]+)\}", cls_content)

        # Get essential packages from handler
        logger = MagicMock(spec=InstallLogger)
        handler = LaTeXHandler(logger)
        essential_packages = handler.get_essential_packages()

        # Verify all required packages are in essential packages
        missing_packages = []
        for package in required_packages:
            if package not in essential_packages:
                missing_packages.append(package)

        assert not missing_packages, f"Style file requires packages not in essential list: {missing_packages}"

    @pytest.mark.integration
    def test_build_manager_style_file_integration(self, tmp_path):
        """Test full integration of BuildManager with style file copying."""
        manuscript_dir = self.setup_test_manuscript(tmp_path)
        output_dir = tmp_path / "output"
        style_dir = self.setup_mock_style_files(tmp_path)

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # Override style directory
        build_manager.style_dir = style_dir

        # Test the full workflow
        assert build_manager.copy_style_files() is True

        # Verify all expected files are copied
        assert (output_dir / "rxiv_maker_style.cls").exists()
        assert (output_dir / "rxiv_maker_style.bst").exists()

        # Verify content integrity
        copied_cls = (output_dir / "rxiv_maker_style.cls").read_text()
        original_cls = (style_dir / "rxiv_maker_style.cls").read_text()
        assert copied_cls == original_cls

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_latex_package_installation_workflow(self, mock_run, tmp_path):
        """Test the workflow of detecting and installing missing LaTeX packages."""
        logger = MagicMock(spec=InstallLogger)
        handler = LaTeXHandler(logger)

        # Mock successful installation
        mock_run.return_value = MagicMock(returncode=0)

        # Test installing essential packages
        essential_packages = handler.get_essential_packages()
        result = handler.install_packages(essential_packages)

        assert result is True
        # Verify tlmgr was called for each package
        assert mock_run.call_count == len(essential_packages)

        # Verify siunitx was included in the installation calls
        install_calls = [call[0][0] for call in mock_run.call_args_list]
        siunitx_calls = [call for call in install_calls if "siunitx" in call]
        assert len(siunitx_calls) > 0, "siunitx package was not included in installation calls"

    @pytest.mark.integration
    def test_error_message_for_missing_style_files(self, tmp_path):
        """Test error handling when style files are missing."""
        manuscript_dir = self.setup_test_manuscript(tmp_path)
        output_dir = tmp_path / "output"

        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir), output_dir=str(output_dir), skip_validation=True
        )

        # Set style_dir to non-existent directory
        build_manager.style_dir = tmp_path / "nonexistent_style"

        # Should handle gracefully
        result = build_manager.copy_style_files()
        assert result is True  # Returns True but logs warning

    @pytest.mark.integration
    def test_build_manager_path_resolution_integration(self, tmp_path):
        """Test BuildManager path resolution in different scenarios."""
        manuscript_dir = self.setup_test_manuscript(tmp_path)
        output_dir = tmp_path / "output"

        # Test with trailing slash (regression test for issue #100)
        build_manager = BuildManager(
            manuscript_path=str(manuscript_dir) + "/",  # Note trailing slash
            output_dir=str(output_dir),
            skip_validation=True,
        )

        # Should handle trailing slash correctly
        assert build_manager.manuscript_dir == manuscript_dir
        assert build_manager.style_dir is not None

    @pytest.mark.integration
    def test_siunitx_usage_detection_in_manuscript(self, tmp_path):
        """Test detection of siunitx usage in manuscript content."""
        manuscript_dir = self.setup_test_manuscript(tmp_path)

        # Read manuscript content
        main_content = (manuscript_dir / "01_MAIN.md").read_text()

        # Should contain siunitx-style commands
        assert "\\SI{" in main_content or "\\si{" in main_content

        # This simulates what would happen during LaTeX compilation
        # where siunitx package would be required
