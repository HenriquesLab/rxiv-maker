"""Test that dependency manager uses correct Python package import names.

This test ensures that the dependency manager checks for packages using their
actual Python import names (e.g., 'yaml') rather than their PyPI package names
(e.g., 'PyYAML').

Regression test for: https://github.com/HenriquesLab/rxiv-maker/issues/XXX
Where Homebrew installations were showing false positives for missing dependencies
because the dependency manager was checking for 'pyyaml' instead of 'yaml'.
"""

import pytest

from rxiv_maker.core.managers.dependency_manager import DependencyType, get_dependency_manager


@pytest.mark.unit
class TestDependencyPackageNames:
    """Test dependency package naming conventions."""

    def test_yaml_package_uses_correct_import_name(self):
        """Test that YAML package is checked with correct import name 'yaml'."""
        dm = get_dependency_manager()

        # Should have 'yaml' registered (the import name)
        assert "yaml" in dm.dependencies
        assert dm.dependencies["yaml"].type == DependencyType.PYTHON_PACKAGE

        # Should NOT have 'pyyaml' registered (that's the PyPI name, not import name)
        assert "pyyaml" not in dm.dependencies

    def test_jinja2_not_required(self):
        """Test that jinja2 is not a required dependency.

        jinja2 was previously listed as required but is not actually used
        in the codebase or declared in pyproject.toml.
        """
        dm = get_dependency_manager()

        # jinja2 should not be in required dependencies since it's not used
        assert "jinja2" not in dm.dependencies

    def test_all_python_packages_use_import_names(self):
        """Verify all Python packages use import names, not PyPI names."""
        dm = get_dependency_manager()

        # Get all Python package dependencies
        python_packages = {
            name: spec for name, spec in dm.dependencies.items() if spec.type == DependencyType.PYTHON_PACKAGE
        }

        # Common PyPI name vs import name mismatches
        pypi_names = ["pyyaml", "pillow", "beautifulsoup4", "python-dotenv"]

        for pypi_name in pypi_names:
            assert pypi_name not in python_packages, (
                f"Found PyPI name '{pypi_name}' instead of import name in dependencies"
            )

        # Verify correct import names are used for common packages
        expected_import_names = ["yaml", "click", "rich"]
        for import_name in expected_import_names:
            if import_name in python_packages:
                # If registered, verify it can actually be imported
                # (This is what PythonPackageChecker does)
                try:
                    __import__(import_name)
                    imported = True
                except ImportError:
                    imported = False

                # If it's registered, it should be importable
                # (unless it's optional and not installed)
                if python_packages[import_name].required:
                    assert imported, f"Required dependency '{import_name}' is registered but cannot be imported"

    def test_dependency_checker_can_verify_yaml(self):
        """Test that the dependency checker can successfully verify PyYAML installation."""
        dm = get_dependency_manager()

        # Check the yaml dependency
        result = dm.check_dependency("yaml")

        # Should be able to check it (whether installed or not)
        assert result is not None
        assert result.spec.name == "yaml"

        # If yaml is installed (it should be for this test suite), status should be AVAILABLE
        from rxiv_maker.core.managers.dependency_manager import DependencyStatus

        # yaml should be installed for the test suite
        assert result.status == DependencyStatus.AVAILABLE, "yaml package should be available for test suite"
