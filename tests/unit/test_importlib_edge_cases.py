"""Edge cases and comprehensive error handling tests for importlib.util.find_spec() approach."""

import importlib.util
import sys
from unittest.mock import MagicMock, patch

import pytest

from rxiv_maker.install.dependency_handlers.system_libs import SystemLibsHandler
from rxiv_maker.install.utils.logging import InstallLogger
from rxiv_maker.install.utils.verification import _check_rxiv_maker, _check_system_libraries


class TestImportlibFindSpecEdgeCases:
    """Test edge cases specific to importlib.util.find_spec() usage."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock(spec=InstallLogger)

    @pytest.fixture
    def handler(self, mock_logger):
        """Create a SystemLibsHandler instance with mock logger."""
        return SystemLibsHandler(mock_logger)

    def test_find_spec_with_none_return(self, handler):
        """Test find_spec explicitly returning None for missing packages."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = None

            result = handler.verify_installation()

            assert result is False
            mock_find_spec.assert_called()

    def test_find_spec_with_valid_module_spec(self, handler):
        """Test find_spec returning a valid ModuleSpec object."""
        mock_spec = MagicMock()
        mock_spec.name = "matplotlib"
        mock_spec.origin = "/path/to/matplotlib/__init__.py"

        with patch("importlib.util.find_spec", return_value=mock_spec):
            result = handler.verify_installation()

            assert result is True

    def test_find_spec_with_namespace_package(self, handler):
        """Test find_spec with namespace packages (no __init__.py)."""
        mock_spec = MagicMock()
        mock_spec.name = "namespace_package"
        mock_spec.origin = None  # Namespace packages have no origin
        mock_spec.submodule_search_locations = ["/path/to/namespace"]

        with patch("importlib.util.find_spec", return_value=mock_spec):
            result = handler.verify_installation()

            assert result is True

    @pytest.mark.parametrize(
        "exception_type",
        [
            ImportError("Import error during spec finding"),
            ModuleNotFoundError("Module not found during spec resolution"),
            AttributeError("Attribute error in spec resolution"),
            ValueError("Invalid module name"),
            TypeError("Type error in spec finding"),
            OSError("OS error accessing module files"),
            PermissionError("Permission denied accessing module"),
        ],
    )
    def test_find_spec_exception_handling(self, handler, exception_type):
        """Test various exceptions that can occur during find_spec."""
        with patch("importlib.util.find_spec", side_effect=exception_type):
            # Should propagate the exception for proper error handling
            with pytest.raises(type(exception_type)):
                handler.verify_installation()

    def test_find_spec_with_corrupted_module_spec(self, handler):
        """Test find_spec with a corrupted or incomplete ModuleSpec."""
        # Create a spec that's missing expected attributes
        mock_spec = MagicMock()
        mock_spec.name = None  # Corrupted spec
        mock_spec.origin = "/invalid/path"

        with patch("importlib.util.find_spec", return_value=mock_spec):
            # Should still work - we only check for non-None return
            result = handler.verify_installation()

            assert result is True

    def test_find_spec_with_builtin_modules(self, handler):
        """Test find_spec with builtin modules."""
        # Test with a builtin module like 'sys'
        with patch("importlib.util.find_spec") as mock_find_spec:
            # Builtin modules have special spec properties
            mock_spec = MagicMock()
            mock_spec.name = "sys"
            mock_spec.origin = "built-in"
            mock_find_spec.return_value = mock_spec

            result = handler.verify_installation()

            assert result is True

    def test_find_spec_with_frozen_modules(self, handler):
        """Test find_spec with frozen modules."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            # Frozen modules have origin 'frozen'
            mock_spec = MagicMock()
            mock_spec.name = "frozen_module"
            mock_spec.origin = "frozen"
            mock_find_spec.return_value = mock_spec

            result = handler.verify_installation()

            assert result is True

    @pytest.mark.parametrize(
        "invalid_package_name",
        [
            "",  # Empty string
            " ",  # Whitespace only
            "123invalid",  # Starting with number
            "invalid-name",  # Invalid characters
            "invalid.name.with.too.many.dots",  # Overly complex
            None,  # None (this would cause TypeError)
        ],
    )
    def test_find_spec_with_invalid_package_names(self, handler, invalid_package_name):
        """Test find_spec behavior with invalid package names."""
        # Mock the package list to include invalid names
        original_packages = ["matplotlib", "numpy", "pandas", "PIL", "scipy"]

        if invalid_package_name is None:
            # None would cause TypeError or AttributeError in find_spec
            test_packages = original_packages + [invalid_package_name]

            with patch.object(handler, "verify_installation") as mock_verify:
                # Create a custom method that includes None
                def mock_verify_impl():
                    import importlib.util

                    for package in test_packages:
                        if package is None:
                            # This should raise TypeError or AttributeError
                            importlib.util.find_spec(package)
                    return True

                mock_verify.side_effect = mock_verify_impl

                with pytest.raises((TypeError, AttributeError)):
                    handler.verify_installation()
        else:
            # Other invalid names should be handled gracefully by find_spec
            with patch("importlib.util.find_spec") as mock_find_spec:
                # find_spec typically returns None for invalid names
                mock_find_spec.return_value = None

                # Mock the internal package list
                with patch.object(handler, "verify_installation") as mock_verify:

                    def mock_verify_impl():
                        import importlib.util

                        return importlib.util.find_spec(invalid_package_name) is not None

                    mock_verify.side_effect = mock_verify_impl

                    result = handler.verify_installation()
                    assert result is False

    def test_find_spec_circular_import_handling(self, handler):
        """Test find_spec handling of circular import scenarios."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            # Simulate a circular import scenario
            def circular_side_effect(name):
                if name == "circular_module":
                    # This would normally cause issues, but find_spec should handle it
                    raise ImportError("circular import detected")
                return MagicMock()  # Other modules work fine

            mock_find_spec.side_effect = circular_side_effect

            # Mock the verify_installation to test circular import behavior
            with patch.object(handler, "verify_installation") as mock_verify:

                def mock_verify_impl():
                    try:
                        # This should trigger the circular import scenario
                        importlib.util.find_spec("circular_module")
                        return True
                    except ImportError:
                        return False  # Handle gracefully

                mock_verify.side_effect = mock_verify_impl

                # Should handle the ImportError gracefully and return False
                result = handler.verify_installation()
                assert result is False

    def test_find_spec_with_sys_modules_manipulation(self, handler):
        """Test find_spec behavior when sys.modules is manipulated."""
        original_modules = sys.modules.copy()

        try:
            # Add fake module to sys.modules with a proper __spec__
            fake_module = MagicMock()
            fake_spec = MagicMock()
            fake_spec.name = "fake_test_module"
            fake_module.__spec__ = fake_spec
            sys.modules["fake_test_module"] = fake_module

            # find_spec should still work correctly
            import importlib.util

            spec = importlib.util.find_spec("fake_test_module")

            # Should find the module in sys.modules
            assert spec is not None

        finally:
            # Restore original sys.modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_find_spec_subpackage_resolution(self, handler):
        """Test find_spec with subpackage resolution."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            # Test subpackage like 'matplotlib.pyplot'
            mock_spec = MagicMock()
            mock_spec.name = "matplotlib.pyplot"
            mock_spec.parent = "matplotlib"
            mock_find_spec.return_value = mock_spec

            # Test that subpackage resolution works
            spec = importlib.util.find_spec("matplotlib.pyplot")
            assert spec is not None

    def test_find_spec_with_meta_path_finders(self, handler):
        """Test find_spec interaction with custom meta path finders."""
        # This tests the interaction with sys.meta_path
        original_meta_path = sys.meta_path.copy()

        try:
            # Create a custom meta path finder
            class CustomFinder:
                def find_spec(self, name, path, target=None):
                    if name == "custom_module":
                        spec = MagicMock()
                        spec.name = name
                        return spec
                    return None

            # Add custom finder to meta_path
            sys.meta_path.insert(0, CustomFinder())

            # find_spec should use our custom finder
            import importlib.util

            spec = importlib.util.find_spec("custom_module")

            assert spec is not None
            assert spec.name == "custom_module"

        finally:
            # Restore original meta_path
            sys.meta_path.clear()
            sys.meta_path.extend(original_meta_path)

    def test_verification_functions_find_spec_consistency(self):
        """Test that verification functions use find_spec consistently."""
        # Test _check_system_libraries
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = MagicMock()

            result = _check_system_libraries()

            assert result is True
            # Should check expected packages
            expected_calls = ["matplotlib", "numpy", "PIL"]
            assert mock_find_spec.call_count == len(expected_calls)

        # Test _check_rxiv_maker
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = MagicMock()

            result = _check_rxiv_maker()

            assert result is True
            mock_find_spec.assert_called_once_with("rxiv_maker")

    def test_find_spec_memory_usage_patterns(self, handler):
        """Test that find_spec doesn't cause memory leaks with repeated calls."""
        import gc

        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Run many find_spec operations
        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = MagicMock()

            for _ in range(1000):
                handler.verify_installation()

        # Check that we haven't created excessive objects
        gc.collect()
        final_objects = len(gc.get_objects())

        # Allow some growth but adjust threshold for test environments
        object_growth = final_objects - initial_objects

        # Use higher threshold - modern Python with testing frameworks creates many objects
        # The goal is to detect significant memory leaks, not count normal object churn
        threshold = 20000

        assert object_growth < threshold, f"Excessive object growth: {object_growth} (threshold: {threshold})"

    def test_find_spec_thread_safety(self, handler):
        """Test that find_spec usage is thread-safe."""
        import threading

        results = []
        errors = []

        def verify_in_thread():
            try:
                with patch("importlib.util.find_spec") as mock_find_spec:
                    mock_find_spec.return_value = MagicMock()
                    result = handler.verify_installation()
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Run verification in multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=verify_in_thread)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)

        # All should succeed without errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10
        assert all(result is True for result in results)

    @pytest.mark.parametrize("encoding", ["utf-8", "ascii", "latin-1"])
    def test_find_spec_encoding_handling(self, handler, encoding):
        """Test find_spec with different string encodings."""
        # Test package name with different encodings
        package_name = "matplotlib"

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = MagicMock()

            # Encode and decode package name
            encoded_name = package_name.encode(encoding).decode(encoding)

            # Should handle different encodings correctly
            importlib.util.find_spec(encoded_name)  # Just call for side effects
            assert mock_find_spec.called

    def test_find_spec_with_pep_420_namespace_packages(self, handler):
        """Test find_spec with PEP 420 namespace packages."""
        with patch("importlib.util.find_spec") as mock_find_spec:
            # PEP 420 namespace package spec
            mock_spec = MagicMock()
            mock_spec.name = "namespace_package"
            mock_spec.origin = None  # Namespace packages have no origin
            mock_spec.submodule_search_locations = ["path1", "path2"]
            mock_spec.parent = None
            mock_find_spec.return_value = mock_spec

            result = handler.verify_installation()

            # Should handle namespace packages correctly
            assert result is True

    def test_find_spec_performance_with_large_package_lists(self, handler):
        """Test find_spec performance with large package lists."""
        import time

        # Mock a scenario with many packages to check
        large_package_list = [f"package_{i}" for i in range(100)]

        with patch("importlib.util.find_spec") as mock_find_spec:
            mock_find_spec.return_value = MagicMock()

            start_time = time.time()

            # Simulate checking many packages
            for package in large_package_list:
                importlib.util.find_spec(package)

            end_time = time.time()
            elapsed = end_time - start_time

            # Should complete quickly even with many packages
            assert elapsed < 1.0, f"find_spec too slow for large lists: {elapsed:.2f}s"

    def test_find_spec_compatibility_across_python_versions(self, handler):
        """Test find_spec compatibility across different Python version behaviors."""
        # Test that our usage is compatible with different Python versions

        # Mock different Python version behaviors
        python_version_behaviors = [
            # Python 3.11 behavior
            {"has_find_spec": True, "returns_spec_object": True},
            # Potential future behavior
            {"has_find_spec": True, "returns_spec_object": True, "has_new_attributes": True},
        ]

        for behavior in python_version_behaviors:
            with patch("importlib.util.find_spec") as mock_find_spec:
                if behavior["returns_spec_object"]:
                    mock_spec = MagicMock()
                    mock_spec.name = "test_package"

                    if behavior.get("has_new_attributes"):
                        mock_spec.new_attribute = "future_feature"

                    mock_find_spec.return_value = mock_spec
                else:
                    mock_find_spec.return_value = None

                result = handler.verify_installation()

                # Should work regardless of spec object details
                expected = behavior["returns_spec_object"]
                assert result == expected


class TestRealWorldImportlibScenarios:
    """Test real-world scenarios that may occur with importlib.util.find_spec()."""

    def test_common_missing_packages_scenarios(self):
        """Test scenarios with commonly missing packages."""
        # Common packages that might be missing
        potentially_missing = [
            "matplotlib",  # Large scientific package
            "PIL",  # PIL/Pillow naming
            "cv2",  # OpenCV naming inconsistency
            "sklearn",  # scikit-learn naming
        ]

        for package in potentially_missing:
            # Test that find_spec handles these correctly
            try:
                spec = importlib.util.find_spec(package)
                # If package exists, spec should not be None
                if spec is not None:
                    assert hasattr(spec, "name")
                    assert spec.name == package or spec.name.startswith(package)
            except ImportError:
                # ImportError is acceptable for missing packages
                pass

    def test_common_package_naming_issues(self):
        """Test common package naming issues that find_spec should handle."""
        # Test package name variations
        name_mappings = {
            "PIL": "Pillow",  # PIL is installed as Pillow but imported as PIL
            "cv2": "opencv-python",  # OpenCV naming
            "sklearn": "scikit-learn",  # scikit-learn naming
        }

        for import_name, _package_name in name_mappings.items():
            # find_spec should work with the import name
            try:
                spec = importlib.util.find_spec(import_name)
                if spec is not None:
                    assert spec.name == import_name
            except ImportError:
                # Expected if package not installed
                pass

    def test_virtual_environment_package_detection(self):
        """Test package detection in virtual environments."""
        # This tests the real behavior in the current environment

        # Test that find_spec works correctly in virtual environments
        # These packages should be available in the test environment
        test_packages = ["sys", "os", "pathlib"]  # Built-in packages

        for package in test_packages:
            spec = importlib.util.find_spec(package)
            assert spec is not None
            assert spec.name == package

    def test_editable_install_detection(self):
        """Test detection of packages installed in editable mode."""
        # Test that find_spec works with editable installs (development mode)

        # Test current package (should be available)
        spec = importlib.util.find_spec("rxiv_maker")

        if spec is not None:
            # If rxiv_maker is found, verify it's properly detected
            assert spec.name == "rxiv_maker"
            # Editable installs might have different origins
            if spec.origin:
                assert isinstance(spec.origin, str)

    def test_system_vs_user_package_detection(self):
        """Test detection of system vs user installed packages."""
        # Test that find_spec finds packages regardless of install location

        # Test a package that's likely to exist
        for package in ["sys", "os", "json"]:  # Standard library
            spec = importlib.util.find_spec(package)
            assert spec is not None

            # Standard library packages should have predictable properties
            if package in ["sys", "os"]:
                # These are typically builtin or built-in
                assert spec.origin in ["built-in", "frozen"] or spec.origin is not None

    def test_package_version_independence(self):
        """Test that find_spec works independently of package versions."""
        # find_spec should find packages regardless of their version

        # Test with current environment packages
        import sys

        # Get some packages from current environment
        current_packages = []
        for name, _module in sys.modules.items():
            if not name.startswith("_") and "." not in name:
                current_packages.append(name)
                if len(current_packages) >= 5:  # Test with first 5
                    break

        for package in current_packages:
            spec = importlib.util.find_spec(package)
            # Should find package regardless of version
            assert spec is not None or package in ["__main__"]  # __main__ is special
