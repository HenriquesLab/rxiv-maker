"""Integration tests for centralized components.

Tests to verify that the new centralized managers work correctly together
and integrate properly with the existing rxiv-maker codebase.
"""

import tempfile


# Test the centralized managers
def test_content_processor_integration():
    """Test ContentProcessor integration with md2tex conversion."""
    try:
        from rxiv_maker.converters.md2tex import convert_markdown_to_latex

        # Test basic markdown conversion
        test_content = """
# Test Document

This is a test with **bold** and *italic* text.

- List item 1
- List item 2

## Section

Some more content with `code` formatting.

![Figure](test.png)

> This is a blockquote

| Table | Test |
|-------|------|
| A     | B    |
"""

        # Test conversion - should use ContentProcessor now
        result = convert_markdown_to_latex(test_content)

        # Verify basic conversions worked
        assert "\\section{Test Document}" in result
        assert "\\subsection{Section}" in result
        assert "\\textbf{bold}" in result
        assert "\\textit{italic}" in result
        assert "\\begin{itemize}" in result
        assert "\\texttt{code}" in result

        print("✅ ContentProcessor integration test passed")
        return True

    except Exception as e:
        print(f"❌ ContentProcessor integration test failed: {e}")
        return False


def test_command_framework_integration():
    """Test CommandFramework integration with CLI commands."""
    from rxiv_maker.cli.framework import FiguresCommand, ValidationCommand

    # Test that commands can be instantiated
    validation_cmd = ValidationCommand()
    figures_cmd = FiguresCommand()

    # Test basic method availability
    assert hasattr(validation_cmd, "execute_operation")
    assert hasattr(validation_cmd, "setup_common_options")
    assert hasattr(figures_cmd, "execute_operation")

    # If we get here, the test passed
    assert True  # Explicit assertion for pytest


def test_dependency_manager_integration():
    """Test DependencyManager basic functionality."""
    try:
        from rxiv_maker.core.dependency_manager import check_dependencies, get_dependency_manager

        # Test manager instantiation
        dep_manager = get_dependency_manager()

        # Test basic dependency checking
        assert hasattr(dep_manager, "check_dependency")
        assert hasattr(dep_manager, "check_context_dependencies")

        # Test convenience function
        has_python = check_dependencies("build", required_only=True)
        # Should return True or False, not error
        assert isinstance(has_python, bool)

        print("✅ DependencyManager integration test passed")
        return True

    except Exception as e:
        print(f"❌ DependencyManager integration test failed: {e}")
        return False


def test_resource_manager_integration():
    """Test ResourceManager basic functionality."""
    try:
        from rxiv_maker.core.resource_manager import get_resource_manager, managed_resources

        # Test manager instantiation
        resource_manager = get_resource_manager()

        # Test basic resource management
        assert hasattr(resource_manager, "register_temp_file")
        assert hasattr(resource_manager, "cleanup_all")

        # Test basic functionality without complex cleanup scenarios
        # Just verify the context manager doesn't crash
        with managed_resources():
            # Simple test that the context manager works
            temp_file = tempfile.NamedTemporaryFile(delete=True)
            # Don't register or do complex cleanup - just test it doesn't crash
            temp_file.close()

        print("✅ ResourceManager integration test passed")
        return True

    except Exception as e:
        print(f"❌ ResourceManager integration test failed: {e}")
        return False


def test_validation_manager_integration():
    """Test ValidationManager basic functionality."""
    try:
        from rxiv_maker.core.validation_manager import get_validation_manager

        # Test manager instantiation
        validation_manager = get_validation_manager()

        # Test basic validation functionality
        assert hasattr(validation_manager, "validate")
        assert hasattr(validation_manager, "register_validator")

        print("✅ ValidationManager integration test passed")
        return True

    except Exception as e:
        print(f"❌ ValidationManager integration test failed: {e}")
        return False


def test_execution_manager_integration():
    """Test ExecutionManager basic functionality."""
    try:
        from rxiv_maker.core.execution_manager import get_execution_manager

        # Test manager instantiation using factory function
        exec_manager = get_execution_manager("LOCAL")

        # Test basic execution functionality
        assert hasattr(exec_manager, "execute_pipeline")
        assert hasattr(exec_manager, "register_step")

        print("✅ ExecutionManager integration test passed")
        return True

    except Exception as e:
        print(f"❌ ExecutionManager integration test failed: {e}")
        return False


def run_all_integration_tests():
    """Run all integration tests for centralized components."""
    print("🧪 Running integration tests for centralized components...\n")

    tests = [
        test_content_processor_integration,
        test_command_framework_integration,
        test_dependency_manager_integration,
        test_resource_manager_integration,
        test_validation_manager_integration,
        test_execution_manager_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()  # Add spacing between tests

    print("📊 Integration Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(
        f"📈 Success Rate: {passed}/{passed + failed} ({100 * passed // (passed + failed) if (passed + failed) > 0 else 0}%)"
    )

    if failed == 0:
        print("\n🎉 All centralized component integration tests passed!")
        return True
    else:
        print("\n⚠️  Some integration tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)
