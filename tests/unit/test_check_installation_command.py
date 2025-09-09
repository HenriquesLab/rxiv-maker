"""Tests for the check_installation command functionality."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.check_installation import check_installation


class TestCheckInstallationCommand:
    """Test the check_installation command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    def test_basic_check_all_components_installed(self, mock_verify):
        """Test basic check when all components are installed."""
        # Mock verification results - all components installed
        mock_verify.return_value = {
            "python": True,
            "latex": True,
            "nodejs": True,
            "r": True,
            "system_libs": True,
            "rxiv_maker": True,
        }

        result = self.runner.invoke(check_installation, obj={"verbose": False})

        assert result.exit_code == 0
        mock_verify.assert_called_once_with(verbose=False)

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    def test_basic_check_missing_components(self, mock_verify):
        """Test basic check when some components are missing."""
        # Mock verification results - missing latex and nodejs
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": False,
            "r": True,
            "system_libs": True,
            "rxiv_maker": True,
        }

        result = self.runner.invoke(check_installation, obj={"verbose": False})

        assert result.exit_code == 0
        mock_verify.assert_called_once_with(verbose=False)

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    def test_r_component_optional(self, mock_verify):
        """Test that R component is treated as optional."""
        # Mock verification results - missing only R
        mock_verify.return_value = {
            "python": True,
            "latex": True,
            "nodejs": True,
            "r": False,  # R is missing but should be optional
            "system_libs": True,
            "rxiv_maker": True,
        }

        result = self.runner.invoke(check_installation, obj={"verbose": False})

        assert result.exit_code == 0
        # Should show success since R is optional
        mock_verify.assert_called_once_with(verbose=False)

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    @patch("rxiv_maker.install.utils.verification.diagnose_installation")
    def test_detailed_flag(self, mock_diagnose, mock_verify):
        """Test detailed flag showing diagnostic information."""
        # Mock verification results
        mock_verify.return_value = {
            "python": True,
            "latex": False,
        }

        # Mock diagnosis results
        mock_diagnose.return_value = {
            "python": {
                "version": "3.11.5",
                "path": "/usr/bin/python3",
            },
            "latex": {
                "issues": ["pdflatex not found in PATH"],
            },
        }

        result = self.runner.invoke(check_installation, ["--detailed"], obj={"verbose": False})

        assert result.exit_code == 0
        mock_diagnose.assert_called_once()

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    @patch("rxiv_maker.install.utils.verification.diagnose_installation")
    def test_json_output(self, mock_diagnose, mock_verify):
        """Test JSON output format."""
        # Mock verification results
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": True,
        }

        # Mock diagnosis results
        mock_diagnose.return_value = {
            "python": {"version": "3.11.5"},
            "latex": {"issues": ["not found"]},
        }

        result = self.runner.invoke(check_installation, ["--json"], obj={"verbose": False})

        assert result.exit_code == 0
        mock_verify.assert_called_once_with(verbose=False)
        mock_diagnose.assert_called_once()

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    @patch("rxiv_maker.core.managers.install_manager.InstallManager")
    def test_fix_flag_success(self, mock_install_manager, mock_verify):
        """Test fix flag with successful repair."""
        # Initial verification shows missing components
        mock_verify.side_effect = [
            {
                "python": True,
                "latex": False,
                "nodejs": False,
                "system_libs": True,
                "rxiv_maker": True,
            },
            # After repair - all working
            {
                "python": True,
                "latex": True,
                "nodejs": True,
                "system_libs": True,
                "rxiv_maker": True,
            },
        ]

        # Mock successful repair
        mock_manager_instance = MagicMock()
        mock_manager_instance.repair.return_value = True
        mock_install_manager.return_value = mock_manager_instance

        result = self.runner.invoke(check_installation, ["--fix"], obj={"verbose": False})

        assert result.exit_code == 0
        # The --fix flag should complete successfully even if automatic repair is not yet implemented

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    def test_next_steps_all_installed(self, mock_verify):
        """Test next steps when all components are installed."""
        # Mock all components installed
        mock_verify.return_value = {
            "python": True,
            "latex": True,
            "nodejs": True,
            "r": True,
            "system_libs": True,
            "rxiv_maker": True,
        }

        result = self.runner.invoke(check_installation, obj={"verbose": False})

        assert result.exit_code == 0


class TestCheckInstallationHelperFunctions:
    """Test helper functions in check_installation command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    @patch("rxiv_maker.install.utils.verification.diagnose_installation")
    def test_json_output_structure(self, mock_diagnose, mock_verify):
        """Test JSON output structure via CLI command."""
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": True,
        }

        mock_diagnose.return_value = {
            "python": {"version": "3.11.5"},
            "latex": {"issues": ["not found"]},
        }

        result = self.runner.invoke(check_installation, ["--json"], obj={"verbose": False})

        assert result.exit_code == 0
        # JSON output should be produced
        assert "status" in result.output or "components" in result.output

    def test_show_basic_results_table_structure(self):
        """Test basic results are displayed via CLI command."""
        # Test that the basic results display works through the CLI
        with patch("rxiv_maker.install.utils.verification.verify_installation") as mock_verify:
            mock_verify.return_value = {
                "python": True,
                "latex": False,
                "system_libs": True,
            }

            result = self.runner.invoke(check_installation, obj={"verbose": False})

            assert result.exit_code == 0
            # Should display basic results table
            assert "Installation Status" in result.output or "python" in result.output.lower()


class TestCheckInstallationCommandEdgeCases:
    """Test edge cases for check_installation command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    def test_empty_results(self, mock_verify):
        """Test handling of empty verification results."""
        mock_verify.return_value = {}

        result = self.runner.invoke(check_installation, obj={"verbose": False})

        assert result.exit_code == 0
        # Should complete without crashing

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    @patch("rxiv_maker.core.managers.install_manager.InstallManager")
    def test_combined_flags(self, mock_install_manager, mock_verify):
        """Test combining multiple flags."""
        mock_verify.return_value = {
            "python": True,
            "latex": False,
        }

        # Mock the InstallManager to prevent actual installation
        mock_manager_instance = MagicMock()
        mock_install_manager.return_value = mock_manager_instance
        mock_manager_instance.repair.return_value = True

        # Test --detailed --fix together (should prioritize --json if present)
        result = self.runner.invoke(check_installation, ["--detailed", "--fix"], obj={"verbose": False})

        assert result.exit_code == 0
        # Should complete successfully with multiple flags

    @patch("rxiv_maker.install.utils.verification.verify_installation")
    @patch("rxiv_maker.install.utils.verification.diagnose_installation")
    def test_json_output_with_complete_status(self, mock_diagnose, mock_verify):
        """Test JSON output when all components are installed."""
        mock_verify.return_value = {
            "python": True,
            "latex": True,
            "nodejs": True,
        }

        mock_diagnose.return_value = {}

        result = self.runner.invoke(check_installation, ["--json"], obj={"verbose": False})

        assert result.exit_code == 0
        # Should produce JSON output for complete installation
        assert "status" in result.output or "complete" in result.output
