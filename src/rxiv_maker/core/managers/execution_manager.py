"""Centralized execution management for rxiv-maker.

This module provides a unified interface for executing complex multi-step operations
with consistent error handling, progress tracking, and resource management.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger
from ..path_manager import PathManager

logger = get_logger()


class ExecutionMode(Enum):
    """Execution mode options."""

    LOCAL = "local"
    DOCKER = "docker"
    PODMAN = "podman"


class StepStatus(Enum):
    """Execution step status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(Enum):
    """Step execution result."""

    SUCCESS = "success"
    FAILURE = "failure"
    SKIP = "skip"


@dataclass
class ExecutionStep:
    """Represents a single execution step in a pipeline."""

    id: str
    name: str
    description: str
    function: Callable[[Dict[str, Any]], StepResult]  # Enhanced: now takes context dict
    dependencies: List[str] = field(default_factory=list)
    required: bool = True
    timeout: Optional[int] = None
    retry_count: int = 0
    status: StepStatus = StepStatus.PENDING
    error_message: Optional[str] = None
    duration: float = 0.0
    result_data: Dict[str, Any] = field(default_factory=dict)  # Store step results
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Execution context containing shared state and configuration."""

    mode: ExecutionMode
    working_dir: Path
    output_dir: Path
    verbose: bool = False
    dry_run: bool = False
    force: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of executing a pipeline."""

    success: bool
    total_duration: float
    steps_completed: int
    steps_failed: int
    steps_skipped: int
    error_message: Optional[str] = None
    step_results: Dict[str, ExecutionStep] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressCallback:
    """Progress reporting interface."""

    def __init__(self, callback: Optional[Callable[[str, int, int], None]] = None):
        self.callback = callback

    def report(self, message: str, current: int, total: int) -> None:
        """Report progress."""
        if self.callback:
            self.callback(message, current, total)
        else:
            logger.info(f"[{current}/{total}] {message}")


class ExecutionManager(RecoveryEnhancedMixin, ABC):
    """Abstract base class for execution management.

    Provides consistent interface for complex multi-step operations with:
    - Pipeline execution with dependencies
    - Progress tracking and reporting
    - Error handling and recovery
    - Resource management integration
    - Context and state management
    """

    def __init__(
        self,
        context: ExecutionContext,
        path_manager: Optional[PathManager] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        """Initialize execution manager.

        Args:
            context: Execution context with configuration
            path_manager: Path manager for file operations
            progress_callback: Optional progress reporting callback
        """
        super().__init__()
        self.context = context
        self.path_manager = path_manager or PathManager(
            manuscript_path=None, output_dir=str(context.output_dir), working_dir=str(context.working_dir)
        )
        self.progress = ProgressCallback(progress_callback)

        # Pipeline state
        self.steps: List[ExecutionStep] = []
        self.step_index: Dict[str, ExecutionStep] = {}
        self.execution_start_time: Optional[float] = None

        # Error handling
        self.continue_on_error = False
        self.recovery_strategies: Dict[str, Callable[[ExecutionStep], StepResult]] = {}

        logger.debug(f"ExecutionManager initialized with mode: {context.mode}")

    @abstractmethod
    def setup_pipeline(self) -> "ExecutionManager":
        """Setup the execution pipeline.

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def execute(self) -> ExecutionResult:
        """Execute the pipeline.

        Returns:
            ExecutionResult with success status and details
        """
        pass

    def add_step(
        self,
        step_id: str,
        name: str,
        description: str,
        function: Callable[[Dict[str, Any]], StepResult],
        dependencies: Optional[List[str]] = None,
        required: bool = True,
        timeout: Optional[int] = None,
    ) -> "ExecutionManager":
        """Add a step to the execution pipeline.

        Args:
            step_id: Unique identifier for the step
            name: Human-readable name for the step
            description: Description of what the step does
            function: Function to execute (takes context dict, returns StepResult)
            dependencies: List of step IDs this step depends on
            required: Whether this step is required for pipeline success
            timeout: Timeout in seconds for step execution

        Returns:
            Self for method chaining
        """
        if step_id in self.step_index:
            raise ValueError(f"Step {step_id} already exists in pipeline")

        step = ExecutionStep(
            id=step_id,
            name=name,
            description=description,
            function=function,
            dependencies=dependencies or [],
            required=required,
            timeout=timeout,
        )

        self.steps.append(step)
        self.step_index[step_id] = step

        logger.debug(f"Added step {step_id}: {name}")
        return self

    def add_simple_step(
        self,
        step_id: str,
        name: str,
        description: str,
        function: Callable[[], StepResult],
        dependencies: Optional[List[str]] = None,
        required: bool = True,
        timeout: Optional[int] = None,
    ) -> "ExecutionManager":
        """Add a simple step with backward compatibility.

        This method provides backward compatibility for functions that don't
        need the context parameter.

        Args:
            step_id: Unique identifier for the step
            name: Human-readable name for the step
            description: Description of what the step does
            function: Simple function to execute (no parameters, returns StepResult)
            dependencies: List of step IDs this step depends on
            required: Whether this step is required for pipeline success
            timeout: Timeout in seconds for step execution

        Returns:
            Self for method chaining
        """

        def wrapper(context: Dict[str, Any]) -> StepResult:
            """Wrapper to adapt simple function to context-aware signature."""
            return function()

        return self.add_step(
            step_id=step_id,
            name=name,
            description=description,
            function=wrapper,
            dependencies=dependencies,
            required=required,
            timeout=timeout,
        )

    def _resolve_dependencies(self) -> List[ExecutionStep]:
        """Resolve step dependencies and return execution order.

        Returns:
            List of steps in dependency-resolved order

        Raises:
            ValueError: If circular dependencies detected
        """
        ordered_steps = []
        completed_steps = set()
        remaining_steps = set(self.step_index.keys())

        while remaining_steps:
            # Find steps that can run (all dependencies completed)
            ready_steps = []
            for step_id in remaining_steps:
                step = self.step_index[step_id]
                if all(dep in completed_steps for dep in step.dependencies):
                    ready_steps.append(step)

            if not ready_steps:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected among steps: {remaining_steps}")

            # Add ready steps to execution order
            ordered_steps.extend(ready_steps)

            # Mark as completed for dependency resolution
            for step in ready_steps:
                completed_steps.add(step.id)
                remaining_steps.remove(step.id)

        return ordered_steps

    def _execute_step(self, step: ExecutionStep, context: Dict[str, Any]) -> StepResult:
        """Execute a single step.

        Args:
            step: Step to execute
            context: Execution context with shared state

        Returns:
            StepResult indicating success/failure
        """
        step.status = StepStatus.IN_PROGRESS
        start_time = time.time()

        try:
            logger.info(
                f"ℹ️ [{len([s for s in self.steps if s.status == StepStatus.COMPLETED]) + 1}/{len(self.steps)}] {step.description}"
            )

            # Execute the step function with enhanced context
            if step.timeout:
                # Simple timeout implementation (could be enhanced with threading)
                result = step.function(context)
            else:
                result = step.function(context)

            # Handle different return types for backward compatibility
            if isinstance(result, StepResult):
                step_result = result
            elif isinstance(result, dict):
                # Store dict results in step data
                step.result_data.update(result)
                step_result = StepResult.SUCCESS
            elif result is None:
                step_result = StepResult.SUCCESS
            else:
                # Store other results
                step.result_data["result"] = result
                step_result = StepResult.SUCCESS

            if step_result == StepResult.SUCCESS:
                step.status = StepStatus.COMPLETED
                logger.debug(f"Step {step.id} completed successfully")
            else:
                step.status = StepStatus.FAILED
                logger.error(f"Step {step.id} failed")

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            logger.error(f"❌ Step {step.id} failed with exception: {e}")
            step_result = StepResult.FAILURE

        step.duration = time.time() - start_time
        return step_result


class LocalExecutionManager(ExecutionManager):
    """Local execution manager for running steps in the current process."""

    def setup_pipeline(self) -> "LocalExecutionManager":
        """Setup the local execution pipeline.

        Returns:
            Self for method chaining
        """
        logger.debug("Setting up local execution pipeline")
        # Local setup is minimal - just validate steps
        if not self.steps:
            logger.warning("No steps configured for execution")
        return self

    def execute(self) -> ExecutionResult:
        """Execute the pipeline locally.

        Returns:
            ExecutionResult with execution statistics
        """
        if not self.steps:
            logger.warning("No steps to execute")
            return ExecutionResult(success=True, total_duration=0.0, steps_completed=0, steps_failed=0, steps_skipped=0)

        self.execution_start_time = time.time()
        total_steps = len(self.steps)
        completed_count = 0
        failed_count = 0
        skipped_count = 0
        failed_step_ids = []

        logger.info(f"ℹ️ Starting execution pipeline with {total_steps} steps")

        try:
            # Resolve dependencies
            ordered_steps = self._resolve_dependencies()

            # Prepare execution context with shared state
            execution_context = {
                "shared_state": self.context.shared_state,
                "step_results": {},
                "working_dir": self.context.working_dir,
                "output_dir": self.context.output_dir,
                "verbose": self.context.verbose,
                "dry_run": self.context.dry_run,
                "metadata": self.context.metadata,
            }

            # Execute steps in dependency order
            for step in ordered_steps:
                if step.status == StepStatus.SKIPPED:
                    skipped_count += 1
                    continue

                result = self._execute_step(step, execution_context)

                if result == StepResult.SUCCESS:
                    completed_count += 1
                    execution_context["step_results"][step.id] = step
                    self.progress.report(f"Completed {step.name}", completed_count, total_steps)
                else:
                    failed_count += 1
                    failed_step_ids.append(step.id)

                    if step.required:
                        logger.error(f"❌ Required step {step.id} failed, stopping pipeline")
                        # Mark remaining required steps as skipped
                        remaining_steps = ordered_steps[ordered_steps.index(step) + 1 :]
                        for remaining_step in remaining_steps:
                            remaining_step.status = StepStatus.SKIPPED
                            skipped_count += 1
                        break

            # Calculate final results
            total_duration = time.time() - self.execution_start_time
            success = failed_count == 0

            # Create result dictionary
            step_results = {step.id: step for step in self.steps}

            error_message = None
            if failed_step_ids:
                error_message = f"Pipeline failed. Failed steps: {', '.join(failed_step_ids)}"

            logger.info(
                f"ℹ️ Pipeline execution completed: {completed_count} completed, {failed_count} failed, {skipped_count} skipped ({total_duration:.1f}s)"
            )

            return ExecutionResult(
                success=success,
                total_duration=total_duration,
                steps_completed=completed_count,
                steps_failed=failed_count,
                steps_skipped=skipped_count,
                error_message=error_message,
                step_results=step_results,
            )

        except Exception as e:
            total_duration = time.time() - self.execution_start_time if self.execution_start_time else 0
            logger.error(f"❌ Pipeline execution failed with exception: {e}")

            return ExecutionResult(
                success=False,
                total_duration=total_duration,
                steps_completed=completed_count,
                steps_failed=failed_count + 1,
                steps_skipped=total_steps - completed_count - failed_count - 1,
                error_message=f"Pipeline execution failed: {str(e)}",
                step_results={step.id: step for step in self.steps},
            )


class ContainerExecutionManager(ExecutionManager):
    """Container-based execution manager using Docker/Podman."""

    def __init__(self, context: ExecutionContext, engine_type: str = "docker", **kwargs):
        """Initialize container execution manager.

        Args:
            context: Execution context
            engine_type: Container engine ("docker" or "podman")
            **kwargs: Additional arguments
        """
        super().__init__(context, **kwargs)
        self.engine_type = engine_type

        # Import container engine and global manager
        from ..global_container_manager import get_global_container_manager

        # Use global container manager for shared engine instances
        global_manager = get_global_container_manager()
        self.engine = global_manager.get_container_engine(engine_type=engine_type)

        logger.debug(f"ContainerExecutionManager initialized with {engine_type}")

    def setup_pipeline(self) -> "ContainerExecutionManager":
        """Setup the container execution pipeline.

        Returns:
            Self for method chaining
        """
        logger.debug(f"Setting up {self.engine_type} execution pipeline")

        # Verify container engine is available
        if not self.engine.is_available():
            raise RuntimeError(f"{self.engine_type} is not available")

        # Additional container setup can go here
        return self

    def execute(self) -> ExecutionResult:
        """Execute the pipeline in containers.

        Returns:
            ExecutionResult with execution statistics
        """
        logger.info(f"ℹ️ Starting {self.engine_type} execution pipeline")

        # For now, delegate to local execution
        # Container-specific execution logic would be implemented here
        local_manager = LocalExecutionManager(self.context, self.path_manager, self.progress.callback)
        local_manager.steps = self.steps
        local_manager.step_index = self.step_index

        return local_manager.execute()


class AsyncLocalExecutionManager(LocalExecutionManager):
    """Async version of LocalExecutionManager with concurrent step execution.

    Provides significant performance improvements for I/O-intensive operations
    by executing independent pipeline steps concurrently.
    """

    def __init__(self, *args, **kwargs):
        """Initialize async execution manager."""
        super().__init__(*args, **kwargs)
        self.async_steps: Dict[str, bool] = {}  # Track which steps are async

    def add_async_step(
        self,
        step_id: str,
        name: str,
        description: str,
        async_function: Callable[[Dict[str, Any]], Any],  # Can be sync or async
        dependencies: Optional[List[str]] = None,
        required: bool = True,
        timeout: Optional[int] = None,
    ) -> "AsyncLocalExecutionManager":
        """Add an async step to the pipeline.

        Args:
            step_id: Unique identifier for the step
            name: Human-readable name
            description: Step description
            async_function: Async function to execute (or sync function)
            dependencies: List of step IDs this step depends on
            required: Whether step is required for pipeline success
            timeout: Timeout in seconds

        Returns:
            Self for method chaining
        """
        import asyncio

        # Detect if function is async
        is_async = asyncio.iscoroutinefunction(async_function)
        self.async_steps[step_id] = is_async

        # Add step using parent method
        self.add_step(
            step_id=step_id,
            name=name,
            description=description,
            function=async_function,
            dependencies=dependencies or [],
            required=required,
            timeout=timeout,
        )

        return self

    def _build_execution_waves(self) -> List[List[ExecutionStep]]:
        """Build waves of steps that can execute concurrently.

        Returns:
            List of waves, where each wave contains steps with no dependencies
            on each other that can run concurrently.
        """
        remaining_steps = set(self.step_index.keys())
        completed_steps = set()
        waves = []

        while remaining_steps:
            # Find steps that can run (all dependencies completed)
            ready_steps = []
            for step_id in remaining_steps:
                step = self.step_index[step_id]
                if all(dep in completed_steps for dep in step.dependencies):
                    ready_steps.append(step)

            if not ready_steps:
                # Circular dependency or missing dependency
                raise ValueError(f"Circular dependency detected or missing dependencies. Remaining: {remaining_steps}")

            waves.append(ready_steps)

            # Mark these steps as completed for dependency resolution
            for step in ready_steps:
                remaining_steps.remove(step.id)
                completed_steps.add(step.id)

        return waves

    async def _execute_step_async(self, step: ExecutionStep, context: Dict[str, Any]) -> StepResult:
        """Execute a single step asynchronously.

        Args:
            step: Step to execute
            context: Execution context dictionary

        Returns:
            StepResult indicating success/failure
        """
        import asyncio

        step.status = StepStatus.IN_PROGRESS
        start_time = time.time()

        try:
            # Check if this is an async function
            if self.async_steps.get(step.id, False):
                # Execute async function directly
                if step.timeout:
                    result = await asyncio.wait_for(step.function(context), timeout=step.timeout)
                else:
                    result = await step.function(context)
            else:
                # Execute sync function in thread pool
                if step.timeout:
                    result = await asyncio.wait_for(asyncio.to_thread(step.function, context), timeout=step.timeout)
                else:
                    result = await asyncio.to_thread(step.function, context)

            # Handle different return types
            if isinstance(result, StepResult):
                step_result = result
            elif isinstance(result, dict):
                step.result_data.update(result)
                step_result = StepResult.SUCCESS
            elif result is None:
                step_result = StepResult.SUCCESS
            else:
                # Store any other result
                step.result_data["result"] = result
                step_result = StepResult.SUCCESS

            if step_result == StepResult.SUCCESS:
                step.status = StepStatus.COMPLETED
                logger.info(f"✅ Step {step.id} completed successfully")
            else:
                step.status = StepStatus.FAILED
                logger.error(f"❌ Step {step.id} failed")

        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error_message = f"Step {step.id} timed out after {step.timeout} seconds"
            logger.error(f"⏰ Step {step.id} timed out")
            step_result = StepResult.FAILURE

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error_message = str(e)
            logger.error(f"❌ Step {step.id} failed with exception: {e}")
            step_result = StepResult.FAILURE

        step.duration = time.time() - start_time
        return step_result

    async def _execute_wave_concurrently(
        self, wave_steps: List[ExecutionStep], context: Dict[str, Any]
    ) -> List[StepResult]:
        """Execute a wave of steps concurrently.

        Args:
            wave_steps: List of steps to execute concurrently
            context: Shared execution context

        Returns:
            List of step results in same order as input steps
        """
        import asyncio

        logger.info(f"🚀 Executing wave of {len(wave_steps)} concurrent steps: {[s.name for s in wave_steps]}")

        # Create tasks for concurrent execution
        tasks = []
        for step in wave_steps:
            task = asyncio.create_task(self._execute_step_async(step, context), name=f"step_{step.id}")
            tasks.append(task)

        # Execute all steps concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        step_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Task raised an exception
                step = wave_steps[i]
                step.status = StepStatus.FAILED
                step.error_message = str(result)
                logger.error(f"❌ Step {step.id} failed with exception: {result}")
                step_results.append(StepResult.FAILURE)
            else:
                step_results.append(result)

        return step_results

    async def execute_async(self) -> ExecutionResult:
        """Execute the pipeline asynchronously with concurrent step execution.

        Returns:
            ExecutionResult with execution statistics and results
        """
        if not self.steps:
            logger.warning("No steps to execute")
            return ExecutionResult(success=True, total_duration=0.0, steps_completed=0, steps_failed=0, steps_skipped=0)

        self.execution_start_time = time.time()
        total_steps = len(self.steps)
        completed_count = 0
        failed_count = 0
        skipped_count = 0
        failed_step_ids = []

        logger.info(f"🚀 Starting async execution pipeline with {total_steps} steps")

        try:
            # Build execution waves for concurrent execution
            execution_waves = self._build_execution_waves()
            logger.info(f"📊 Pipeline organized into {len(execution_waves)} execution waves")

            # Prepare execution context with shared state
            execution_context = {
                "shared_state": self.context.shared_state,
                "step_results": {},
                "working_dir": self.context.working_dir,
                "output_dir": self.context.output_dir,
                "verbose": self.context.verbose,
                "dry_run": self.context.dry_run,
                "metadata": self.context.metadata,
            }

            # Execute waves sequentially, steps within waves concurrently
            for wave_idx, wave_steps in enumerate(execution_waves):
                logger.info(f"🌊 Executing wave {wave_idx + 1}/{len(execution_waves)} with {len(wave_steps)} steps")

                # Execute this wave concurrently
                wave_results = await self._execute_wave_concurrently(wave_steps, execution_context)

                # Process wave results
                wave_failures = []
                for step, result in zip(wave_steps, wave_results, strict=False):
                    if result == StepResult.SUCCESS:
                        completed_count += 1
                        execution_context["step_results"][step.id] = step
                        self.progress.report(f"Completed {step.name}", completed_count, total_steps)
                    else:
                        failed_count += 1
                        failed_step_ids.append(step.id)
                        wave_failures.append(step.id)

                        if step.required:
                            logger.error(f"❌ Required step {step.id} failed, stopping pipeline")
                            # Mark dependent steps as skipped
                            remaining_steps = []
                            for remaining_wave in execution_waves[wave_idx + 1 :]:
                                remaining_steps.extend(remaining_wave)

                            for remaining_step in remaining_steps:
                                remaining_step.status = StepStatus.SKIPPED
                                skipped_count += 1

                            break

                # If any required step failed, stop execution
                if wave_failures and any(self.step_index[step_id].required for step_id in wave_failures):
                    break

            # Calculate final results
            total_duration = time.time() - self.execution_start_time
            success = failed_count == 0

            # Create result dictionary
            step_results = {step.id: step for step in self.steps}

            error_message = None
            if failed_step_ids:
                error_message = f"Pipeline failed. Failed steps: {', '.join(failed_step_ids)}"

            logger.info(
                f"🏁 Async pipeline execution completed: {completed_count} completed, {failed_count} failed, {skipped_count} skipped ({total_duration:.1f}s)"
            )

            return ExecutionResult(
                success=success,
                total_duration=total_duration,
                steps_completed=completed_count,
                steps_failed=failed_count,
                steps_skipped=skipped_count,
                error_message=error_message,
                step_results=step_results,
                metadata={"execution_waves": len(execution_waves)},
            )

        except Exception as e:
            total_duration = time.time() - self.execution_start_time if self.execution_start_time else 0
            logger.error(f"❌ Pipeline execution failed with exception: {e}")

            return ExecutionResult(
                success=False,
                total_duration=total_duration,
                steps_completed=completed_count,
                steps_failed=failed_count + 1,
                steps_skipped=total_steps - completed_count - failed_count - 1,
                error_message=f"Pipeline execution failed: {str(e)}",
                step_results={step.id: step for step in self.steps},
            )


def create_execution_manager(
    mode: Union[ExecutionMode, str], working_dir: Optional[Path] = None, output_dir: Optional[Path] = None, **kwargs
) -> ExecutionManager:
    """Factory function to create appropriate execution manager.

    Args:
        mode: Execution mode (LOCAL, DOCKER, PODMAN or string)
        working_dir: Working directory for execution
        output_dir: Output directory for results
        **kwargs: Additional arguments for manager initialization

    Returns:
        Configured ExecutionManager instance
    """
    # Convert string mode to enum
    if isinstance(mode, str):
        mode = ExecutionMode(mode.lower())

    # Set default directories
    if working_dir is None:
        working_dir = Path.cwd()
    if output_dir is None:
        output_dir = working_dir / "output"

    # Create execution context
    context = ExecutionContext(
        mode=mode,
        working_dir=working_dir,
        output_dir=output_dir,
        **{k: v for k, v in kwargs.items() if k in ExecutionContext.__dataclass_fields__},
    )

    if mode == ExecutionMode.LOCAL:
        return LocalExecutionManager(context, **kwargs)
    else:
        engine_type = "docker" if mode == ExecutionMode.DOCKER else "podman"
        return ContainerExecutionManager(context, engine_type=engine_type, **kwargs)
