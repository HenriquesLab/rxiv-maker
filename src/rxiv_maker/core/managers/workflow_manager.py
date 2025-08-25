"""Configurable workflow management system for rxiv-maker.

This module provides a powerful framework for defining and executing complex
multi-step workflows with dependencies, conditional execution, error recovery,
and comprehensive monitoring.
"""

import subprocess
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from ..error_recovery import RecoveryEnhancedMixin
from ..logging_config import get_logger
from .cache_manager import get_cache_manager
from .resource_manager import get_resource_manager, managed_resources
from .state_manager import get_state_manager

logger = get_logger()


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Individual step execution status."""

    PENDING = "pending"
    READY = "ready"  # Dependencies satisfied
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class ExecutionMode(Enum):
    """Workflow execution modes."""

    SEQUENTIAL = "sequential"  # Execute steps one by one
    PARALLEL = "parallel"  # Execute independent steps in parallel
    ADAPTIVE = "adaptive"  # Mix of sequential and parallel based on dependencies


@dataclass
class StepResult:
    """Result of step execution."""

    status: StepStatus
    output: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if step was successful."""
        return self.status == StepStatus.COMPLETED

    @property
    def failed(self) -> bool:
        """Check if step failed."""
        return self.status == StepStatus.FAILED


@dataclass
class StepConfig:
    """Configuration for workflow steps."""

    name: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[Callable[[], bool]] = None  # Conditional execution
    retry_count: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    parallel_group: Optional[str] = None  # Steps in same group can run in parallel
    critical: bool = False  # Workflow fails if critical step fails
    cleanup_on_failure: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowStep(ABC):
    """Abstract base class for workflow steps."""

    def __init__(self, config: StepConfig):
        """Initialize workflow step.

        Args:
            config: Step configuration
        """
        self.config = config
        self.result: Optional[StepResult] = None
        self._lock = threading.RLock()

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the workflow step.

        Args:
            context: Workflow execution context

        Returns:
            Step execution result
        """
        pass

    def should_execute(self, context: Dict[str, Any]) -> bool:
        """Check if step should be executed.

        Args:
            context: Workflow execution context

        Returns:
            True if step should execute
        """
        if self.config.condition:
            try:
                return self.config.condition()
            except Exception as e:
                logger.warning(f"Step condition evaluation failed for {self.config.name}: {e}")
                return False
        return True

    @abstractmethod
    def cleanup(self, context: Dict[str, Any]) -> None:
        """Cleanup after step execution (success or failure).

        Args:
            context: Workflow execution context
        """
        pass

    def get_dependencies(self) -> List[str]:
        """Get step dependencies.

        Returns:
            List of dependency step names
        """
        return self.config.dependencies.copy()


class FunctionStep(WorkflowStep):
    """Workflow step that wraps a function."""

    def __init__(self, config: StepConfig, function: Callable):
        """Initialize function step.

        Args:
            config: Step configuration
            function: Function to execute
        """
        super().__init__(config)
        self.function = function

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the wrapped function."""
        return self.function(context)


class CommandStep(WorkflowStep):
    """Workflow step that executes a shell command."""

    def __init__(self, config: StepConfig, command: str, shell: bool = True):
        """Initialize command step.

        Args:
            config: Step configuration
            command: Shell command to execute
            shell: Whether to use shell
        """
        super().__init__(config)
        self.command = command
        self.shell = shell

    def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the shell command."""
        try:
            result = subprocess.run(
                self.command, shell=self.shell, capture_output=True, text=True, timeout=self.config.timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Command failed with code {result.returncode}: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Command timed out after {self.config.timeout} seconds") from e


@dataclass
class WorkflowConfig:
    """Configuration for workflows."""

    name: str
    description: str = ""
    execution_mode: ExecutionMode = ExecutionMode.ADAPTIVE
    max_parallel_steps: int = 4
    overall_timeout: Optional[float] = None
    continue_on_failure: bool = False  # Continue with non-dependent steps if one fails
    save_state: bool = True  # Save workflow state for recovery
    enable_caching: bool = True  # Cache step results
    metadata: Dict[str, Any] = field(default_factory=dict)


class Workflow:
    """Configurable multi-step workflow orchestrator.

    Features:
    - Dependency-based step ordering
    - Parallel execution of independent steps
    - Conditional step execution
    - Retry mechanisms with exponential backoff
    - Comprehensive error handling and recovery
    - Progress tracking and state management
    - Caching of step results
    - Resource management integration
    """

    def __init__(self, config: WorkflowConfig):
        """Initialize workflow.

        Args:
            config: Workflow configuration
        """
        self.config = config
        self.steps: Dict[str, WorkflowStep] = {}
        self.results: Dict[str, StepResult] = {}
        self.context: Dict[str, Any] = {}

        self.status = WorkflowStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        self._lock = threading.RLock()
        self._execution_graph: Optional[Dict[str, Set[str]]] = None

        # Integration with other managers
        self.state_manager = get_state_manager()
        self.resource_manager = get_resource_manager()
        self.cache_manager = get_cache_manager()

        logger.debug(f"Workflow initialized: {config.name}")

    def add_step(self, step: WorkflowStep) -> None:
        """Add step to workflow.

        Args:
            step: Workflow step to add
        """
        with self._lock:
            self.steps[step.config.name] = step
            self._execution_graph = None  # Reset graph cache

        logger.debug(f"Added step to workflow {self.config.name}: {step.config.name}")

    def add_function_step(
        self, name: str, function: Callable, dependencies: Optional[List[str]] = None, **kwargs
    ) -> None:
        """Add a function-based step to workflow.

        Args:
            name: Step name
            function: Function to execute
            dependencies: Step dependencies
            **kwargs: Additional step configuration
        """
        config = StepConfig(name=name, dependencies=dependencies or [], **kwargs)
        step = FunctionStep(config, function)
        self.add_step(step)

    def add_command_step(self, name: str, command: str, dependencies: Optional[List[str]] = None, **kwargs) -> None:
        """Add a command-based step to workflow.

        Args:
            name: Step name
            command: Shell command to execute
            dependencies: Step dependencies
            **kwargs: Additional step configuration
        """
        config = StepConfig(name=name, dependencies=dependencies or [], **kwargs)
        step = CommandStep(config, command)
        self.add_step(step)

    def set_context(self, key: str, value: Any) -> None:
        """Set workflow context value.

        Args:
            key: Context key
            value: Context value
        """
        with self._lock:
            self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get workflow context value.

        Args:
            key: Context key
            default: Default value

        Returns:
            Context value or default
        """
        return self.context.get(key, default)

    def execute(self, initial_context: Optional[Dict[str, Any]] = None) -> bool:
        """Execute the workflow.

        Args:
            initial_context: Initial context values

        Returns:
            True if workflow completed successfully
        """
        with self._lock:
            if self.status == WorkflowStatus.RUNNING:
                logger.warning(f"Workflow {self.config.name} is already running")
                return False

            self.status = WorkflowStatus.RUNNING
            self.start_time = time.time()

            if initial_context:
                self.context.update(initial_context)

        logger.info(f"Starting workflow: {self.config.name}")

        try:
            with managed_resources():
                # Build execution plan
                execution_plan = self._build_execution_plan()

                if not execution_plan:
                    raise RuntimeError("No executable steps found")

                # Execute steps according to plan
                if self.config.execution_mode == ExecutionMode.SEQUENTIAL:
                    success = self._execute_sequential(execution_plan)
                elif self.config.execution_mode == ExecutionMode.PARALLEL:
                    success = self._execute_parallel(execution_plan)
                else:  # ADAPTIVE
                    success = self._execute_adaptive(execution_plan)

                # Update final status
                with self._lock:
                    self.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
                    self.end_time = time.time()

                duration = self.end_time - (self.start_time or 0)
                logger.info(f"Workflow {self.config.name} {'completed' if success else 'failed'} ({duration:.1f}s)")

                return success

        except Exception as e:
            with self._lock:
                self.status = WorkflowStatus.FAILED
                self.end_time = time.time()

            logger.error(f"Workflow {self.config.name} failed: {e}")
            return False

    def _build_execution_plan(self) -> List[List[str]]:
        """Build execution plan with dependency resolution.

        Returns:
            List of execution phases, each containing step names that can run in parallel
        """
        # Topological sort with parallel grouping
        in_degree = {}
        graph = {}

        # Initialize graph
        for step_name, step in self.steps.items():
            if not step.should_execute(self.context):
                continue

            in_degree[step_name] = 0
            graph[step_name] = []

        # Build dependency graph
        for step_name, step in self.steps.items():
            if step_name not in in_degree:
                continue

            for dep in step.get_dependencies():
                if dep in graph:
                    graph[dep].append(step_name)
                    in_degree[step_name] += 1
                else:
                    logger.warning(f"Dependency {dep} not found for step {step_name}")

        # Topological sort
        execution_plan = []
        ready_queue = [name for name, degree in in_degree.items() if degree == 0]

        while ready_queue:
            # Current phase - all steps in ready_queue can run in parallel
            current_phase = ready_queue[:]
            execution_plan.append(current_phase)
            ready_queue.clear()

            # Update in_degree for next phase
            for step_name in current_phase:
                for dependent in graph[step_name]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        ready_queue.append(dependent)

        # Check for circular dependencies
        remaining_steps = [name for name, degree in in_degree.items() if degree > 0]
        if remaining_steps:
            raise RuntimeError(f"Circular dependencies detected: {remaining_steps}")

        return execution_plan

    def _execute_sequential(self, execution_plan: List[List[str]]) -> bool:
        """Execute workflow sequentially.

        Args:
            execution_plan: Execution plan

        Returns:
            True if all steps succeeded
        """
        for phase in execution_plan:
            for step_name in phase:
                if not self._execute_step(step_name):
                    step = self.steps[step_name]
                    if step.config.critical or not self.config.continue_on_failure:
                        return False

        return True

    def _execute_parallel(self, execution_plan: List[List[str]]) -> bool:
        """Execute workflow with maximum parallelism.

        Args:
            execution_plan: Execution plan

        Returns:
            True if all steps succeeded
        """
        for phase in execution_plan:
            if len(phase) == 1:
                # Single step - execute directly
                step_name = phase[0]
                if not self._execute_step(step_name):
                    step = self.steps[step_name]
                    if step.config.critical or not self.config.continue_on_failure:
                        return False
            else:
                # Multiple steps - execute in parallel
                success = self._execute_parallel_phase(phase)
                if not success and not self.config.continue_on_failure:
                    return False

        return True

    def _execute_adaptive(self, execution_plan: List[List[str]]) -> bool:
        """Execute workflow adaptively (mix of sequential and parallel).

        Args:
            execution_plan: Execution plan

        Returns:
            True if all steps succeeded
        """
        for phase in execution_plan:
            if len(phase) <= self.config.max_parallel_steps:
                # Execute phase in parallel
                success = self._execute_parallel_phase(phase)
                if not success and not self.config.continue_on_failure:
                    return False
            else:
                # Too many steps - execute sequentially
                for step_name in phase:
                    if not self._execute_step(step_name):
                        step = self.steps[step_name]
                        if step.config.critical or not self.config.continue_on_failure:
                            return False

        return True

    def _execute_parallel_phase(self, step_names: List[str]) -> bool:
        """Execute a phase of steps in parallel.

        Args:
            step_names: Names of steps to execute

        Returns:
            True if all steps succeeded
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_parallel_steps) as executor:
            futures = {executor.submit(self._execute_step, name): name for name in step_names}

            results = {}
            for future in concurrent.futures.as_completed(futures):
                step_name = futures[future]
                try:
                    results[step_name] = future.result()
                except Exception as e:
                    logger.error(f"Step {step_name} raised exception: {e}")
                    results[step_name] = False

        # Check results
        failed_steps = [name for name, success in results.items() if not success]

        if failed_steps:
            # Check if any failed step is critical
            for step_name in failed_steps:
                step = self.steps[step_name]
                if step.config.critical:
                    return False

        return len(failed_steps) == 0 or self.config.continue_on_failure

    def _execute_step(self, step_name: str) -> bool:
        """Execute a single workflow step.

        Args:
            step_name: Name of step to execute

        Returns:
            True if step succeeded
        """
        step = self.steps[step_name]

        # Check cache if enabled
        cache_key = f"workflow_{self.config.name}_step_{step_name}"
        if self.config.enable_caching:
            cache = self.cache_manager.get_cache("build")
            if cache and cache.exists(cache_key):
                cached_result = cache.get(cache_key)
                if cached_result and cached_result.success:
                    logger.debug(f"Using cached result for step: {step_name}")
                    self.results[step_name] = cached_result
                    return True

        logger.info(f"Executing step: {step_name}")
        start_time = time.time()

        retries = 0
        max_retries = step.config.retry_count

        while retries <= max_retries:
            try:
                # Execute step
                output = step.execute(self.context)

                # Create successful result
                duration = time.time() - start_time
                result = StepResult(status=StepStatus.COMPLETED, output=output, duration=duration, retries=retries)

                self.results[step_name] = result

                # Cache result if enabled
                if self.config.enable_caching:
                    cache = self.cache_manager.get_cache("build")
                    if cache:
                        cache.set(cache_key, result)

                logger.debug(f"Step {step_name} completed ({duration:.1f}s)")
                return True

            except Exception as e:
                retries += 1

                if retries <= max_retries:
                    logger.warning(f"Step {step_name} failed (attempt {retries}), retrying: {e}")
                    if step.config.retry_delay > 0:
                        time.sleep(step.config.retry_delay * retries)  # Exponential backoff
                else:
                    # Final failure
                    duration = time.time() - start_time
                    result = StepResult(status=StepStatus.FAILED, error=e, duration=duration, retries=retries - 1)

                    self.results[step_name] = result

                    logger.error(f"Step {step_name} failed after {retries - 1} retries: {e}")

                    # Cleanup on failure
                    if step.config.cleanup_on_failure:
                        try:
                            step.cleanup(self.context)
                        except Exception as cleanup_error:
                            logger.warning(f"Cleanup failed for step {step_name}: {cleanup_error}")

                    return False

        return False

    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """Get result of a step.

        Args:
            step_name: Step name

        Returns:
            Step result or None if not executed
        """
        return self.results.get(step_name)

    def get_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics.

        Returns:
            Dictionary with execution statistics
        """
        total_steps = len(self.steps)
        completed_steps = sum(1 for r in self.results.values() if r.success)
        failed_steps = sum(1 for r in self.results.values() if r.failed)

        total_duration = 0.0
        if self.start_time and self.end_time:
            total_duration = self.end_time - self.start_time

        return {
            "workflow_name": self.config.name,
            "status": self.status.value,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "success_rate": completed_steps / total_steps if total_steps > 0 else 0.0,
            "total_duration": total_duration,
            "step_durations": {name: result.duration for name, result in self.results.items()},
            "retries": {name: result.retries for name, result in self.results.items() if result.retries > 0},
        }


class WorkflowManager(RecoveryEnhancedMixin):
    """Central manager for workflow definitions and execution.

    Features:
    - Workflow template library
    - Execution history and analytics
    - Workflow composition and reuse
    - Integration with state and resource management
    """

    def __init__(self):
        """Initialize workflow manager."""
        super().__init__()
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, Callable[[], Workflow]] = {}
        self.execution_history: List[Dict[str, Any]] = []

        self._register_builtin_workflows()

        logger.debug("WorkflowManager initialized")

    def _register_builtin_workflows(self) -> None:
        """Register built-in workflow templates."""

        # Register standard build workflow template
        def create_build_workflow() -> Workflow:
            config = WorkflowConfig(
                name="build",
                description="Standard manuscript build workflow",
                execution_mode=ExecutionMode.ADAPTIVE,
                max_parallel_steps=3,
                continue_on_failure=False,
            )

            workflow = Workflow(config)

            # Add standard build steps
            workflow.add_function_step(
                "validate",
                lambda ctx: self._validate_manuscript(ctx),
                description="Validate manuscript structure and content",
            )

            workflow.add_function_step(
                "generate_figures",
                lambda ctx: self._generate_figures(ctx),
                dependencies=["validate"],
                description="Generate figures from scripts",
            )

            workflow.add_function_step(
                "process_content",
                lambda ctx: self._process_content(ctx),
                dependencies=["validate"],
                description="Convert markdown to LaTeX",
            )

            workflow.add_function_step(
                "compile_latex",
                lambda ctx: self._compile_latex(ctx),
                dependencies=["generate_figures", "process_content"],
                description="Compile LaTeX to PDF",
            )

            return workflow

        self.register_template("build", create_build_workflow)

    def register_template(self, name: str, factory: Callable[[], Workflow]) -> None:
        """Register workflow template.

        Args:
            name: Template name
            factory: Function that creates workflow instance
        """
        self.templates[name] = factory
        logger.debug(f"Registered workflow template: {name}")

    def create_workflow(self, template_name: str) -> Optional[Workflow]:
        """Create workflow from template.

        Args:
            template_name: Name of template

        Returns:
            Created workflow or None if template not found
        """
        if template_name in self.templates:
            return self.templates[template_name]()
        return None

    def execute_workflow(self, workflow: Workflow, context: Optional[Dict[str, Any]] = None) -> bool:
        """Execute workflow and record history.

        Args:
            workflow: Workflow to execute
            context: Initial context

        Returns:
            True if workflow succeeded
        """
        success = workflow.execute(context)

        # Record execution history
        stats = workflow.get_statistics()
        self.execution_history.append(stats)

        return success

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history.

        Returns:
            List of execution statistics
        """
        return self.execution_history.copy()

    # Built-in workflow step implementations

    def _validate_manuscript(self, context: Dict[str, Any]) -> bool:
        """Validate manuscript step implementation."""
        # This would integrate with ValidationManager
        logger.info("Validating manuscript...")
        return True

    def _generate_figures(self, context: Dict[str, Any]) -> bool:
        """Generate figures step implementation."""
        # This would integrate with FigureGenerator
        logger.info("Generating figures...")
        return True

    def _process_content(self, context: Dict[str, Any]) -> bool:
        """Process content step implementation."""
        # This would integrate with ContentProcessor
        logger.info("Processing content...")
        return True

    def _compile_latex(self, context: Dict[str, Any]) -> bool:
        """Compile LaTeX step implementation."""
        # This would integrate with LaTeX compilation
        logger.info("Compiling LaTeX...")
        return True


# Global workflow manager instance
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """Get the global workflow manager instance.

    Returns:
        Global workflow manager
    """
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()
    return _workflow_manager


# Convenience functions
def create_simple_workflow(name: str, steps: List[Callable]) -> Workflow:
    """Create a simple sequential workflow from functions.

    Args:
        name: Workflow name
        steps: List of functions to execute

    Returns:
        Created workflow
    """
    config = WorkflowConfig(name=name, execution_mode=ExecutionMode.SEQUENTIAL)
    workflow = Workflow(config)

    for i, step_func in enumerate(steps):
        step_name = f"step_{i + 1}"
        workflow.add_function_step(step_name, step_func)

    return workflow


# Export public API
__all__ = [
    "WorkflowManager",
    "Workflow",
    "WorkflowStep",
    "FunctionStep",
    "CommandStep",
    "WorkflowConfig",
    "StepConfig",
    "WorkflowStatus",
    "StepStatus",
    "ExecutionMode",
    "StepResult",
    "get_workflow_manager",
    "create_simple_workflow",
]
