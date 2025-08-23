"""Tests for the check_installation command functionality."""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from rxiv_maker.cli.commands.check_installation import check_installation


class TestCheckInstallationCommand:
    """Test the check_installation command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_basic_check_all_components_installed(self, mock_console, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0
        mock_verify.assert_called_once_with(verbose=False)

        # Check that success message was printed
        print_calls = mock_console_instance.print.call_args_list
        success_call = any("All critical components are working!" in str(call) for call in print_calls)
        assert success_call

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_basic_check_missing_components(self, mock_console, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0

        # Check that warning message was printed
        print_calls = mock_console_instance.print.call_args_list
        warning_call = any("2 critical components missing" in str(call) for call in print_calls)
        assert warning_call

        # Check that fix suggestion was shown
        fix_suggestion = any("Run with --fix to attempt repairs" in str(call) for call in print_calls)
        assert fix_suggestion

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_r_component_optional(self, mock_console, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0

        # Should show success since R is optional
        print_calls = mock_console_instance.print.call_args_list
        success_call = any("All critical components are working!" in str(call) for call in print_calls)
        assert success_call

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.diagnose_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_detailed_flag(self, mock_console, mock_diagnose, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation, ["--detailed"])

        assert result.exit_code == 0
        mock_diagnose.assert_called_once()

        # Check that detailed information was shown
        print_calls = mock_console_instance.print.call_args_list
        version_call = any("Version: 3.11.5" in str(call) for call in print_calls)
        assert version_call

        issue_call = any("pdflatex not found in PATH" in str(call) for call in print_calls)
        assert issue_call

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.diagnose_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_json_output(self, mock_console, mock_diagnose, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation, ["--json"])

        assert result.exit_code == 0
        mock_verify.assert_called_once_with(verbose=False)
        mock_diagnose.assert_called_once()

        # Check that JSON was printed
        print_calls = mock_console_instance.print.call_args_list
        assert len(print_calls) > 0

        # The last call should be the JSON output
        json_call = print_calls[-1]
        json_str = str(json_call)

        # Should contain JSON structure elements
        assert "status" in json_str or "components" in json_str

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.core.managers.install_manager.InstallManager")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_fix_flag_success(self, mock_console, mock_install_manager, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation, ["--fix"])

        assert result.exit_code == 0
        mock_manager_instance.repair.assert_called_once()

        # Check that repair messages were shown
        print_calls = mock_console_instance.print.call_args_list
        repair_start = any("Starting repair process" in str(call) for call in print_calls)
        repair_success = any("Repair completed successfully" in str(call) for call in print_calls)
        recheck = any("Re-checking installation" in str(call) for call in print_calls)

        assert repair_start
        assert repair_success
        assert recheck

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.core.managers.install_manager.InstallManager")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_fix_flag_failure(self, mock_console, mock_install_manager, mock_verify):
        """Test fix flag with failed repair."""
        # Mock verification shows missing components
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": False,
            "system_libs": True,
            "rxiv_maker": True,
        }

        # Mock failed repair
        mock_manager_instance = MagicMock()
        mock_manager_instance.repair.return_value = False
        mock_install_manager.return_value = mock_manager_instance

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation, ["--fix"])

        assert result.exit_code == 0
        mock_manager_instance.repair.assert_called_once()

        # Check that failure messages were shown
        print_calls = mock_console_instance.print.call_args_list
        repair_failed = any("Repair failed" in str(call) for call in print_calls)
        log_location = any("~/.rxiv-maker/logs/" in str(call) for call in print_calls)

        assert repair_failed
        assert log_location

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.core.managers.install_manager.InstallManager")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_fix_flag_exception(self, mock_console, mock_install_manager, mock_verify):
        """Test fix flag with exception during repair."""
        # Mock verification shows missing components
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "system_libs": True,
            "rxiv_maker": True,
        }

        # Mock exception during repair
        mock_install_manager.side_effect = Exception("Repair error")

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation, ["--fix"])

        assert result.exit_code == 0

        # Check that error message was shown
        print_calls = mock_console_instance.print.call_args_list
        error_call = any("Error during repair: Repair error" in str(call) for call in print_calls)
        assert error_call

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_next_steps_all_installed(self, mock_console, mock_verify):
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

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0

        # Check next steps for complete installation
        print_calls = mock_console_instance.print.call_args_list
        complete_install = any("Your installation is complete" in str(call) for call in print_calls)
        try_init = any("rxiv init my-paper" in str(call) for call in print_calls)
        try_pdf = any("rxiv pdf my-paper" in str(call) for call in print_calls)

        assert complete_install
        assert try_init
        assert try_pdf

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_next_steps_missing_components(self, mock_console, mock_verify):
        """Test next steps when components are missing."""
        # Mock missing components
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": False,
            "system_libs": True,
            "rxiv_maker": True,
        }

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0

        # Check next steps for incomplete installation
        print_calls = mock_console_instance.print.call_args_list
        fix_deps = any("To fix missing dependencies" in str(call) for call in print_calls)
        check_fix = any("rxiv check-installation --fix" in str(call) for call in print_calls)

        assert fix_deps
        assert check_fix

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_table_display(self, mock_console, mock_verify):
        """Test that basic results show table with correct formatting."""
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": True,
        }

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0

        # Check that table was created
        print_calls = mock_console_instance.print.call_args_list
        table_call = any("Table" in str(call) or "Installation Status" in str(call) for call in print_calls)
        assert table_call


class TestCheckInstallationHelperFunctions:
    """Test helper functions in check_installation command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.diagnose_installation")
    def test_json_output_structure(self, mock_diagnose, mock_verify):
        """Test JSON output structure."""
        mock_verify.return_value = {
            "python": True,
            "latex": False,
            "nodejs": True,
        }

        mock_diagnose.return_value = {
            "python": {"version": "3.11.5"},
            "latex": {"issues": ["not found"]},
        }

        from rxiv_maker.cli.commands.check_installation import _output_json_results

        # Capture console output
        mock_console = MagicMock()

        _output_json_results(mock_console)

        # Check that JSON was printed
        mock_console.print.assert_called_once()
        json_output = mock_console.print.call_args[0][0]

        # Parse and validate JSON
        parsed = json.loads(json_output)

        assert "status" in parsed
        assert "components" in parsed
        assert "diagnosis" in parsed
        assert "summary" in parsed

        assert parsed["status"] == "incomplete"  # latex is False
        assert parsed["summary"]["total"] == 3
        assert parsed["summary"]["installed"] == 2
        assert parsed["summary"]["missing"] == 1

    def test_show_basic_results_table_structure(self):
        """Test basic results table structure."""

        from rxiv_maker.cli.commands.check_installation import _show_basic_results

        mock_console = MagicMock()
        results = {
            "python": True,
            "latex": False,
            "system_libs": True,
        }

        _show_basic_results(mock_console, results)

        # Check that table was printed
        mock_console.print.assert_called_once()
        table_call = mock_console.print.call_args[0][0]

        # Should be a Table object
        from rich.table import Table

        assert isinstance(table_call, Table)

    @patch("rxiv_maker.cli.commands.check_installation.diagnose_installation")
    def test_show_detailed_results(self, mock_diagnose):
        """Test detailed results display."""
        mock_diagnose.return_value = {
            "python": {
                "version": "3.11.5",
                "path": "/usr/bin/python3",
            },
            "latex": {
                "issues": ["pdflatex not found", "bibtex missing"],
            },
        }

        from rxiv_maker.cli.commands.check_installation import _show_detailed_results

        mock_console = MagicMock()
        results = {
            "python": True,
            "latex": False,
        }

        _show_detailed_results(mock_console, results)

        # Check that diagnostic info was printed
        print_calls = mock_console.print.call_args_list

        # Should have component status
        python_status = any("Python:" in str(call) and "✅ Installed" in str(call) for call in print_calls)
        latex_status = any("Latex:" in str(call) and "❌ Missing" in str(call) for call in print_calls)

        # Should have detailed info
        version_info = any("Version: 3.11.5" in str(call) for call in print_calls)
        path_info = any("Path: /usr/bin/python3" in str(call) for call in print_calls)
        issue_info = any("pdflatex not found" in str(call) for call in print_calls)

        assert python_status
        assert latex_status
        assert version_info
        assert path_info
        assert issue_info


class TestCheckInstallationCommandEdgeCases:
    """Test edge cases for check_installation command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    def test_empty_results(self, mock_console, mock_verify):
        """Test handling of empty verification results."""
        mock_verify.return_value = {}

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        result = self.runner.invoke(check_installation)

        assert result.exit_code == 0
        # Should complete without crashing

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.Console")
    @patch("rxiv_maker.core.managers.install_manager.InstallManager")
    def test_combined_flags(self, mock_install_manager, mock_console, mock_verify):
        """Test combining multiple flags."""
        mock_verify.return_value = {
            "python": True,
            "latex": False,
        }

        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        # Mock the InstallManager to prevent actual installation
        mock_manager_instance = MagicMock()
        mock_install_manager.return_value = mock_manager_instance
        mock_manager_instance.repair.return_value = True

        # Test --detailed --fix together (should prioritize --json if present)
        result = self.runner.invoke(check_installation, ["--detailed", "--fix"])

        assert result.exit_code == 0
        # Verify that repair was called when --fix flag is used
        mock_manager_instance.repair.assert_called_once()

    @patch("rxiv_maker.cli.commands.check_installation.verify_installation")
    @patch("rxiv_maker.cli.commands.check_installation.diagnose_installation")
    def test_json_output_with_complete_status(self, mock_diagnose, mock_verify):
        """Test JSON output when all components are installed."""
        mock_verify.return_value = {
            "python": True,
            "latex": True,
            "nodejs": True,
        }

        mock_diagnose.return_value = {}

        from rxiv_maker.cli.commands.check_installation import _output_json_results

        mock_console = MagicMock()

        _output_json_results(mock_console)

        # Check that JSON was printed with complete status
        json_output = mock_console.print.call_args[0][0]
        parsed = json.loads(json_output)

        assert parsed["status"] == "complete"  # All components True
        assert parsed["summary"]["missing"] == 0
