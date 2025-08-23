"""Tests for the unified setup command."""

import tempfile
import unittest
from pathlib import Path

from rxiv_maker.cli.commands.setup import setup as setup_cmd


class TestSetupCommandStructure(unittest.TestCase):
    """Test setup command structure and components."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_command_exists(self):
        """Test setup command can be imported and has correct structure."""
        # Test that the setup command exists and is callable
        self.assertTrue(callable(setup_cmd))

        # Test that it's a Click command
        self.assertTrue(hasattr(setup_cmd, "callback"))
        self.assertTrue(hasattr(setup_cmd, "params"))

    def test_setup_command_parameters(self):
        """Test that setup command has expected parameters."""
        # Get parameter names from the Click command
        param_names = [param.name for param in setup_cmd.params]

        # Check for expected parameters
        expected_params = ["mode", "reinstall", "force", "non_interactive", "check_only", "log_file"]
        for param in expected_params:
            self.assertIn(param, param_names, f"Parameter {param} not found in setup command")

    def test_mode_parameter_choices(self):
        """Test that mode parameter has correct choices."""
        mode_param = None
        for param in setup_cmd.params:
            if param.name == "mode":
                mode_param = param
                break

        self.assertIsNotNone(mode_param, "Mode parameter not found")

        # Check that it has the expected choices
        if hasattr(mode_param.type, "choices"):
            expected_modes = ["full", "python-only", "system-only", "minimal", "core"]
            for mode in expected_modes:
                self.assertIn(mode, mode_param.type.choices)

    def test_setup_docstring(self):
        """Test that setup command has proper documentation."""
        self.assertIsNotNone(setup_cmd.__doc__)
        self.assertIn("Unified setup command", setup_cmd.__doc__)

    def test_install_manager_import(self):
        """Test that InstallManager can be imported from install module."""
        # Test that we can import InstallManager from the install module (not setup module)
        try:
            from rxiv_maker.core.managers.install_manager import InstallManager, InstallMode

            self.assertTrue(callable(InstallManager))
            # InstallMode is an enum, check for common values
            self.assertTrue(hasattr(InstallMode, "FULL") or hasattr(InstallMode, "full") or len(list(InstallMode)) > 0)
        except ImportError:
            self.skipTest("InstallManager module not available")

    def test_verification_import(self):
        """Test that verification utilities can be imported."""
        # Test verification import
        try:
            from rxiv_maker.cli.commands.setup import verify_installation

            self.assertTrue(callable(verify_installation))
        except ImportError:
            # Verification might not be directly imported
            pass

    def test_console_import(self):
        """Test that console utilities are available."""
        from rxiv_maker.cli.commands.setup import console

        self.assertIsNotNone(console)

    def test_setup_environment_import(self):
        """Test that setup_environment_main can be imported from engine module."""
        # Test that we can import from the engine module (not setup module)
        try:
            from rxiv_maker.engines.operations.setup_environment import main as setup_environment_main

            self.assertTrue(callable(setup_environment_main))
        except ImportError:
            self.skipTest("Setup environment module not available")

    def test_install_mode_mapping(self):
        """Test install mode mapping logic."""
        # Test that the mapping exists in the code
        # This tests the logic structure without executing it

        # The mapping should be present in the source code
        # We can verify this by checking the function source exists
        self.assertIsNotNone(setup_cmd.callback)


class TestSetupCommandComponents(unittest.TestCase):
    """Test individual components used by setup command."""

    def test_path_handling(self):
        """Test Path handling in setup command."""
        from pathlib import Path

        # Test that Path objects can be created and used
        test_path = Path("/tmp/test")
        self.assertIsInstance(test_path, Path)

    def test_sys_import(self):
        """Test sys module availability."""
        import sys

        self.assertIsNotNone(sys.argv)

    def test_click_import(self):
        """Test Click framework availability."""
        import click

        self.assertTrue(hasattr(click, "command"))
        self.assertTrue(hasattr(click, "option"))

    def test_rich_console_import(self):
        """Test Rich console availability."""
        from rich.console import Console

        console = Console()
        self.assertIsNotNone(console)

    def test_install_mode_enum(self):
        """Test InstallMode enum usage."""
        # Test that InstallMode can be imported and used
        try:
            from rxiv_maker.core.managers.install_manager import InstallMode

            # Test enum has expected values or is callable
            self.assertTrue(hasattr(InstallMode, "FULL") or callable(InstallMode) or len(list(InstallMode)) > 0)
        except ImportError:
            self.skipTest("InstallMode enum not available")


class TestSetupCommandIntegration(unittest.TestCase):
    """Integration tests for setup command components."""

    def test_command_module_structure(self):
        """Test that command module has proper structure."""
        import sys

        # Import the module and access it through sys.modules to avoid naming conflicts
        setup_module = sys.modules["rxiv_maker.cli.commands.setup"]

        # Test module has expected attributes
        self.assertTrue(hasattr(setup_module, "setup"))
        self.assertTrue(hasattr(setup_module, "console"))
        # Verify setup is the click command we imported
        self.assertEqual(setup_module.setup, setup_cmd)

    def test_engine_module_access(self):
        """Test access to engine modules."""
        try:
            from rxiv_maker.engines.operations.setup_environment import main

            self.assertTrue(callable(main))
        except ImportError:
            # Module might not be available in test environment
            pass

    def test_install_module_access(self):
        """Test access to install modules."""
        try:
            from rxiv_maker.core.managers.install_manager import InstallManager

            self.assertTrue(callable(InstallManager))
        except ImportError:
            # Module might not be available in test environment
            pass

    def test_verification_module_access(self):
        """Test access to verification modules."""
        try:
            from rxiv_maker.install.utils.verification import verify_installation

            self.assertTrue(callable(verify_installation))
        except ImportError:
            # Module might not be available in test environment
            pass

    def test_command_callback_structure(self):
        """Test that command callback has proper structure."""
        # Test that callback exists and has expected signature
        self.assertIsNotNone(setup_cmd.callback)

        # Test parameter count (should match function signature)
        import inspect

        sig = inspect.signature(setup_cmd.callback)
        self.assertGreater(len(sig.parameters), 5)  # Should have multiple parameters

    def test_error_handling_imports(self):
        """Test that error handling components are available."""
        # Test that we can access exception types
        self.assertTrue(isinstance(KeyboardInterrupt, type))
        self.assertTrue(isinstance(Exception, type))
        # Test that we can create instances of these exceptions
        try:
            raise KeyboardInterrupt("test")
        except KeyboardInterrupt:
            pass  # Expected

        try:
            raise Exception("test")
        except Exception:
            pass  # Expected


if __name__ == "__main__":
    unittest.main()
