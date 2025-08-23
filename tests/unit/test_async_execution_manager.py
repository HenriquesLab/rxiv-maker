"""Comprehensive tests for AsyncLocalExecutionManager."""

import asyncio
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from rxiv_maker.core.managers.execution_manager import (
    AsyncLocalExecutionManager,
    ExecutionContext,
    ExecutionMode,
    StepResult,
)


class TestAsyncExecutionManager:
    """Test AsyncLocalExecutionManager functionality."""

    @pytest.mark.asyncio
    async def test_async_step_creation(self):
        """Test adding async steps to pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            async def test_function(context):
                return StepResult.SUCCESS

            manager.add_async_step(
                step_id="test_step", name="Test Step", description="Test async step", async_function=test_function
            )

            assert len(manager.steps) == 1
            assert "test_step" in manager.step_index
            assert manager.async_steps["test_step"] is True

    @pytest.mark.asyncio
    async def test_mixed_sync_async_steps(self):
        """Test mixing sync and async steps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)
            execution_order = []

            async def async_step(context):
                await asyncio.sleep(0.01)
                execution_order.append("async")
                return StepResult.SUCCESS

            def sync_step(context):
                execution_order.append("sync")
                return StepResult.SUCCESS

            manager.add_async_step("async_step", "Async Step", "Async step", async_step)
            manager.add_async_step("sync_step", "Sync Step", "Sync step", sync_step)

            result = await manager.setup_pipeline().execute_async()

            assert result.success is True
            assert result.steps_completed == 2
            assert len(execution_order) == 2
            assert manager.async_steps["async_step"] is True
            assert manager.async_steps["sync_step"] is False

    @pytest.mark.asyncio
    async def test_concurrent_execution_waves(self):
        """Test that independent steps execute concurrently."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)
            execution_times = {}

            async def timed_step(context, step_id):
                start = time.time()
                await asyncio.sleep(0.05)  # 50ms delay
                execution_times[step_id] = time.time() - start
                return StepResult.SUCCESS

            # Add 3 independent steps
            for i in range(3):

                async def step_func(context, step_num=i):
                    return await timed_step(context, f"step_{step_num}")

                manager.add_async_step(f"step_{i}", f"Step {i}", f"Step {i}", step_func)

            start_time = time.time()
            result = await manager.setup_pipeline().execute_async()
            total_time = time.time() - start_time

            assert result.success is True
            assert result.steps_completed == 3
            # Should complete in roughly 50ms (concurrent) not 150ms (sequential)
            assert total_time < 0.1  # Should be much less than 3 * 50ms

    @pytest.mark.asyncio
    async def test_dependency_wave_organization(self):
        """Test that dependencies are properly organized into waves."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            async def step_function(context):
                return StepResult.SUCCESS

            # Create dependency chain: A -> B -> C, plus independent D
            manager.add_async_step("step_a", "Step A", "Step A", step_function)
            manager.add_async_step("step_b", "Step B", "Step B", step_function, dependencies=["step_a"])
            manager.add_async_step("step_c", "Step C", "Step C", step_function, dependencies=["step_b"])
            manager.add_async_step("step_d", "Step D", "Step D", step_function)  # Independent

            waves = manager._build_execution_waves()

            # Should have 3 waves: [A, D], [B], [C]
            assert len(waves) == 3

            # First wave should have A and D (independent)
            wave_0_ids = {step.id for step in waves[0]}
            assert wave_0_ids == {"step_a", "step_d"}

            # Second wave should have B (depends on A)
            wave_1_ids = {step.id for step in waves[1]}
            assert wave_1_ids == {"step_b"}

            # Third wave should have C (depends on B)
            wave_2_ids = {step.id for step in waves[2]}
            assert wave_2_ids == {"step_c"}

    @pytest.mark.asyncio
    async def test_context_sharing_async(self):
        """Test context sharing between async steps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            async def producer_step(context):
                await asyncio.sleep(0.01)
                context["shared_state"]["produced_data"] = "test_value"
                return StepResult.SUCCESS

            async def consumer_step(context):
                await asyncio.sleep(0.01)
                shared_value = context["shared_state"].get("produced_data")
                context["shared_state"]["consumed_data"] = f"processed_{shared_value}"
                return StepResult.SUCCESS

            manager.add_async_step("producer", "Producer", "Produces data", producer_step)
            manager.add_async_step("consumer", "Consumer", "Consumes data", consumer_step, dependencies=["producer"])

            result = await manager.setup_pipeline().execute_async()

            assert result.success is True
            assert context.shared_state["produced_data"] == "test_value"
            assert context.shared_state["consumed_data"] == "processed_test_value"

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test error handling in async execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            async def failing_step(context):
                await asyncio.sleep(0.01)
                raise RuntimeError("Async step failed")

            async def success_step(context):
                await asyncio.sleep(0.01)
                return StepResult.SUCCESS

            manager.add_async_step("failing", "Failing Step", "Step that fails", failing_step, required=True)
            manager.add_async_step("success", "Success Step", "Step that succeeds", success_step)

            result = await manager.setup_pipeline().execute_async()

            assert result.success is False
            assert result.steps_failed == 1
            assert "failing" in result.error_message

    @pytest.mark.asyncio
    async def test_async_timeout_handling(self):
        """Test timeout handling for async steps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            async def slow_step(context):
                await asyncio.sleep(1.0)  # Sleep longer than timeout
                return StepResult.SUCCESS

            manager.add_async_step(
                "slow_step",
                "Slow Step",
                "Step that times out",
                slow_step,
                timeout=0.1,  # 100ms timeout
            )

            start_time = time.time()
            result = await manager.setup_pipeline().execute_async()
            duration = time.time() - start_time

            assert result.success is False
            assert result.steps_failed == 1
            assert duration < 0.5  # Should timeout quickly, not wait full second

    @pytest.mark.asyncio
    async def test_performance_improvement(self):
        """Test that async execution provides performance improvement."""
        num_io_operations = 4
        io_delay = 0.05  # 50ms per operation

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            # Add multiple I/O-bound operations
            for i in range(num_io_operations):

                async def io_operation(context, step_num=i):
                    await asyncio.sleep(io_delay)
                    return StepResult.SUCCESS

                manager.add_async_step(f"io_step_{i}", f"I/O Step {i}", f"I/O operation {i}", io_operation)

            start_time = time.time()
            result = await manager.setup_pipeline().execute_async()
            async_duration = time.time() - start_time

            # Calculate expected sequential time
            expected_sequential_time = num_io_operations * io_delay
            speedup = expected_sequential_time / async_duration

            assert result.success is True
            assert result.steps_completed == num_io_operations
            assert speedup > 2.0  # Should be significantly faster than sequential
            assert async_duration < expected_sequential_time * 0.7  # At least 30% faster

    @pytest.mark.asyncio
    async def test_wave_metadata(self):
        """Test that execution wave metadata is properly recorded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            context = ExecutionContext(mode=ExecutionMode.LOCAL, working_dir=temp_path, output_dir=temp_path / "output")

            manager = AsyncLocalExecutionManager(context)

            async def step_function(context):
                return StepResult.SUCCESS

            # Create steps with complex dependencies
            manager.add_async_step("a", "Step A", "Step A", step_function)
            manager.add_async_step("b", "Step B", "Step B", step_function)
            manager.add_async_step("c", "Step C", "Step C", step_function, dependencies=["a", "b"])
            manager.add_async_step("d", "Step D", "Step D", step_function, dependencies=["c"])

            result = await manager.setup_pipeline().execute_async()

            assert result.success is True
            assert "execution_waves" in result.metadata
            assert result.metadata["execution_waves"] == 3  # [A,B], [C], [D]


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
