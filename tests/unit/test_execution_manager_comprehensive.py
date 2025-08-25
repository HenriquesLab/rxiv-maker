"""Comprehensive tests for ExecutionManager centralized component.

This test suite validates all aspects of the ExecutionManager including:
- Pipeline creation and execution
- Enhanced context-aware step functions
- Error handling and recovery
- Context management and data passing
- Performance characteristics
- Integration with other components
"""

import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the components we're testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.core.managers.execution_manager import (
    ContainerExecutionManager,
    ExecutionContext,
    ExecutionMode,
    ExecutionStep,
    LocalExecutionManager,
    ProgressCallback,
    StepResult,
    StepStatus,
    create_execution_manager,
)


class TestExecutionContext:
    """Test ExecutionContext data structure."""

    def test_execution_context_creation(self):
        """Test basic ExecutionContext creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "output"

            context = ExecutionContext(
                mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=output_path, verbose=True, dry_run=False
            )

            assert context.mode == ExecutionMode.LOCAL
            assert context.working_dir == temp_path
            assert context.output_dir == output_path
            assert context.verbose is True
            assert context.dry_run is False
            assert isinstance(context.metadata, dict)
            assert isinstance(context.shared_state, dict)

    def test_execution_context_defaults(self):
        """Test ExecutionContext with default values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path)

            assert context.verbose is False
            assert context.dry_run is False
            assert context.force is False
            assert len(context.metadata) == 0
            assert len(context.shared_state) == 0


class TestExecutionStep:
    """Test ExecutionStep functionality."""

    def test_execution_step_creation(self):
        """Test creating ExecutionStep instances."""

        def dummy_function(context):
            return StepResult.SUCCESS

        step = ExecutionStep(
            id="test_step",
            name="Test Step",
            description="A test step for validation",
            function=dummy_function,
            dependencies=["other_step"],
            required=True,
            timeout=300,
        )

        assert step.id == "test_step"
        assert step.name == "Test Step"
        assert step.description == "A test step for validation"
        assert step.function == dummy_function
        assert step.dependencies == ["other_step"]
        assert step.required is True
        assert step.timeout == 300
        assert step.status == StepStatus.PENDING

    def test_execution_step_execution(self):
        """Test executing a step and updating status."""

        def test_function(context):
            return StepResult.SUCCESS

        step = ExecutionStep(
            id="exec_test", name="Execution Test", description="Test step execution", function=test_function
        )

        # Initially pending
        assert step.status == StepStatus.PENDING

        # Mock execution (status updates happen in ExecutionManager)
        result = step.function({})
        assert result == StepResult.SUCCESS


class TestProgressCallback:
    """Test progress reporting functionality."""

    def test_progress_callback_creation(self):
        """Test creating progress callback."""
        callback_calls = []

        def test_callback(message, current, total):
            callback_calls.append((message, current, total))

        progress = ProgressCallback(test_callback)
        progress.report("Test message", 1, 10)

        assert len(callback_calls) == 1
        assert callback_calls[0] == ("Test message", 1, 10)

    def test_progress_callback_no_callback(self):
        """Test progress callback with no function."""
        progress = ProgressCallback(None)
        # Should not raise an exception
        progress.report("Test message", 1, 10)


class TestLocalExecutionManager:
    """Test LocalExecutionManager functionality."""

    def test_local_execution_manager_creation(self):
        """Test creating LocalExecutionManager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)
            assert manager.context.mode == ExecutionMode.LOCAL
            assert len(manager.steps) == 0

    def test_local_execution_manager_setup_pipeline(self):
        """Test pipeline setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)
            result = manager.setup_pipeline()

            # Should return self for chaining
            assert result is manager

    def test_add_step_enhanced_api(self):
        """Test adding steps using enhanced API."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)

            def test_function(context):
                return StepResult.SUCCESS

            manager.add_step(step_id="test_step", name="Test Step", description="Test step", function=test_function)

            assert len(manager.steps) == 1
            assert "test_step" in manager.step_index
            assert manager.step_index["test_step"].name == "Test Step"

    def test_step_dependency_resolution(self):
        """Test that steps are executed in dependency order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)
            execution_order = []

            def step_a(context):
                execution_order.append("A")
                return StepResult.SUCCESS

            def step_b(context):
                execution_order.append("B")
                return StepResult.SUCCESS

            def step_c(context):
                execution_order.append("C")
                return StepResult.SUCCESS

            # Add steps in reverse order, but with dependencies
            manager.add_step("step_c", "Step C", "Step C", step_c, dependencies=["step_b"])
            manager.add_step("step_b", "Step B", "Step B", step_b, dependencies=["step_a"])
            manager.add_step("step_a", "Step A", "Step A", step_a)

            # Execute pipeline
            result = manager.setup_pipeline().execute()

            # Should execute in dependency order: A, B, C
            assert execution_order == ["A", "B", "C"]
            assert result.success is True

    def test_step_error_handling(self):
        """Test error handling in step execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)

            def failing_function(context):
                raise RuntimeError("Test error")

            manager.add_step(
                step_id="failing_step",
                name="Failing Step",
                description="Step that fails",
                function=failing_function,
                required=True,
            )

            result = manager.setup_pipeline().execute()

            # Should fail and report error
            assert result.success is False
            assert result.steps_failed == 1
            assert result.error_message is not None
            assert "Failed steps: failing_step" in result.error_message

    def test_context_sharing_between_steps(self):
        """Test that steps can share data through context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)

            def producer_step(context):
                context["shared_state"]["shared_data"] = "test_value"
                return StepResult.SUCCESS

            def consumer_step(context):
                shared_value = context["shared_state"].get("shared_data")
                context["consumed_value"] = shared_value
                return StepResult.SUCCESS

            manager.add_step("producer", "Producer", "Produces data", producer_step)
            manager.add_step("consumer", "Consumer", "Consumes data", consumer_step, dependencies=["producer"])

            result = manager.setup_pipeline().execute()

            assert result.success is True
            assert manager.context.shared_state["shared_data"] == "test_value"

    def test_backward_compatibility_api(self):
        """Test backward compatibility with simple step API."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)

            def simple_function():
                return StepResult.SUCCESS

            manager.add_simple_step(
                step_id="simple_step", name="Simple Step", description="Step using old API", function=simple_function
            )

            result = manager.setup_pipeline().execute()
            assert result.success is True


class TestExecutionManagerFactory:
    """Test the execution manager factory function."""

    def test_create_local_execution_manager(self):
        """Test creating local execution manager via factory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            manager = create_execution_manager(mode=ExecutionMode.LOCAL, working_dir=temp_path)

            assert isinstance(manager, LocalExecutionManager)
            assert manager.context.mode == ExecutionMode.LOCAL
            assert manager.context.working_dir == temp_path

    def test_create_execution_manager_string_mode(self):
        """Test creating execution manager with string mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            manager = create_execution_manager(mode="local", working_dir=temp_path)

            assert isinstance(manager, LocalExecutionManager)
            assert manager.context.mode == ExecutionMode.LOCAL

    def test_create_container_execution_manager(self):
        """Test creating container execution manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock the global container manager to avoid actual container engine initialization
            with patch("rxiv_maker.core.global_container_manager.get_global_container_manager") as mock_global_manager:
                mock_manager = MagicMock()
                mock_engine = MagicMock()
                mock_manager.get_container_engine.return_value = mock_engine
                mock_global_manager.return_value = mock_manager

                manager = create_execution_manager(mode=ExecutionMode.DOCKER, working_dir=temp_path)

                assert isinstance(manager, ContainerExecutionManager)
                assert manager.context.mode == ExecutionMode.DOCKER


class TestExecutionManagerPerformance:
    """Test performance characteristics of ExecutionManager."""

    def test_large_pipeline_performance(self):
        """Test performance with large number of steps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)

            # Add 100 simple steps
            for i in range(100):

                def step_function(context, step_num=i):
                    context[f"step_{step_num}"] = step_num
                    return StepResult.SUCCESS

                manager.add_step(step_id=f"step_{i}", name=f"Step {i}", description=f"Step {i}", function=step_function)

            start_time = time.time()
            result = manager.setup_pipeline().execute()
            end_time = time.time()

            assert result.success is True
            assert result.steps_completed == 100
            assert end_time - start_time < 5.0  # Should complete in under 5 seconds

    def test_memory_usage_with_large_context(self):
        """Test memory usage with large context data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)

            def memory_intensive_step(context):
                # Add large data to context
                large_data = "x" * 1000000  # 1MB string
                context["shared_state"]["large_data"] = large_data
                return StepResult.SUCCESS

            manager.add_step(
                step_id="memory_step",
                name="Memory Step",
                description="Memory intensive step",
                function=memory_intensive_step,
            )

            result = manager.setup_pipeline().execute()

            assert result.success is True
            # Context should contain the large data
            assert len(manager.context.shared_state.get("large_data", "")) == 1000000


class TestExecutionManagerIntegration:
    """Test ExecutionManager integration with other components."""

    def test_integration_with_resource_manager(self):
        """Test ExecutionManager working with ResourceManager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            from rxiv_maker.core.managers.resource_manager import get_resource_manager

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = LocalExecutionManager(context)
            rm = get_resource_manager()

            def resource_using_step(context):
                # Create resources during step execution
                temp_file = rm.create_temp_file(suffix=".test")
                temp_file.write_text("test content")
                context["temp_file_path"] = str(temp_file)
                return StepResult.SUCCESS

            manager.add_step(
                step_id="resource_step",
                name="Resource Step",
                description="Step using resources",
                function=resource_using_step,
            )

            with rm.managed_execution():
                result = manager.setup_pipeline().execute()

                assert result.success is True
                # Temp file should exist during execution
                temp_file_path = context.shared_state.get("temp_file_path")
                if temp_file_path:
                    assert Path(temp_file_path).exists()

    def test_progress_reporting(self):
        """Test progress reporting during execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            progress_reports = []

            def progress_callback(message, current, total):
                progress_reports.append((message, current, total))

            manager = LocalExecutionManager(context, progress_callback=progress_callback)

            # Add multiple steps
            for i in range(3):

                def step_function(context, step_num=i):
                    time.sleep(0.1)  # Small delay
                    return StepResult.SUCCESS

                manager.add_step(step_id=f"step_{i}", name=f"Step {i}", description=f"Step {i}", function=step_function)

            result = manager.setup_pipeline().execute()

            assert result.success is True
            assert len(progress_reports) > 0  # Should have progress reports


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
