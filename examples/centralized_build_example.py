#!/usr/bin/env python3
"""Centralized Build Example for rxiv-maker.

This example demonstrates how to use all the centralized managers together
to build a manuscript with proper resource management, validation, and error recovery.

Example usage:
    python examples/centralized_build_example.py MANUSCRIPT/
    python examples/centralized_build_example.py --help
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add src to path for example
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rxiv_maker.core.dependency_manager import DependencyManager
from rxiv_maker.core.execution_manager import ExecutionMode, ExecutionStep, create_execution_manager
from rxiv_maker.core.logging_config import get_logger
from rxiv_maker.core.resource_manager import ResourceManager
from rxiv_maker.core.validation_manager import ValidationContext, ValidationManager

logger = get_logger()


class CentralizedBuildManager:
    """Demonstration of centralized build management using all centralized components.

    This replaces the scattered logic from the original BuildManager classes
    with a clean, centralized approach using:
    - ExecutionManager: Pipeline orchestration
    - ResourceManager: Automatic resource cleanup
    - ValidationManager: Centralized validation
    - DependencyManager: Unified dependency checking
    """

    def __init__(self, manuscript_path: Path, output_dir: Optional[Path] = None, mode: str = "local"):
        """Initialize centralized build manager.

        Args:
            manuscript_path: Path to manuscript directory
            output_dir: Output directory (defaults to manuscript_path/output)
            mode: Execution mode ("local", "docker", "podman")
        """
        self.manuscript_path = Path(manuscript_path)
        self.output_dir = output_dir or self.manuscript_path / "output"

        # Initialize centralized managers
        self.resource_manager = ResourceManager()
        self.validation_manager = ValidationManager()
        self.dependency_manager = DependencyManager()

        # Initialize execution manager
        self.execution_manager = create_execution_manager(
            mode=ExecutionMode(mode.lower()), working_dir=self.manuscript_path, output_dir=self.output_dir
        )

        logger.info(f"Centralized build manager initialized for {manuscript_path}")

    def build(self, validation_context: str = "build", skip_validation: bool = False) -> bool:
        """Build manuscript using centralized pipeline.

        Args:
            validation_context: Validation context to use
            skip_validation: Skip validation steps

        Returns:
            True if build successful, False otherwise
        """
        try:
            with self.resource_manager:  # Automatic resource cleanup
                # Step 1: Dependency checking
                self._add_dependency_step()

                # Step 2: Pre-build validation
                if not skip_validation:
                    self._add_validation_step(validation_context)

                # Step 3: Content processing steps
                self._add_content_processing_steps()

                # Step 4: Build execution
                self._add_build_execution_step()

                # Step 5: Post-build validation
                if not skip_validation:
                    self._add_post_build_validation_step()

                # Execute the pipeline
                logger.info("Starting centralized build pipeline...")
                result = self.execution_manager.setup_pipeline().execute()

                if result.success:
                    logger.info(f"✅ Build completed successfully in {result.total_duration:.2f}s")
                    logger.info(f"📁 Output available in: {self.output_dir}")
                    return True
                else:
                    logger.error(f"❌ Build failed: {result.error_message}")
                    return False

        except Exception as e:
            logger.error(f"❌ Build error: {e}")
            return False

    def _add_dependency_step(self):
        """Add dependency checking step to pipeline."""

        def check_dependencies(context: Dict[str, Any]) -> Dict[str, Any]:
            """Check all build dependencies."""
            logger.info("🔍 Checking dependencies...")

            # Use DependencyManager for unified dependency checking
            missing_deps = self.dependency_manager.check_dependencies(context=["build", "latex"], install_missing=True)

            if missing_deps:
                logger.warning(f"⚠️  Missing dependencies: {missing_deps}")
                # DependencyManager can attempt installation
                installed = self.dependency_manager.install_dependencies(missing_deps)
                if not installed:
                    raise RuntimeError(f"Failed to install dependencies: {missing_deps}")

            logger.info("✅ Dependencies satisfied")
            return {"dependencies_checked": True}

        step = ExecutionStep(
            id="check_dependencies",
            name="Check Build Dependencies",
            function=check_dependencies,
            required=True,
            timeout=300,  # 5 minutes
        )
        self.execution_manager.add_step(step)

    def _add_validation_step(self, context: str):
        """Add validation step to pipeline."""

        def validate_manuscript(context_data: Dict[str, Any]) -> Dict[str, Any]:
            """Validate manuscript using ValidationManager."""
            logger.info("🔍 Validating manuscript...")

            # Use ValidationManager for centralized validation
            validation_context = ValidationContext(context)
            result = self.validation_manager.validate_all(
                manuscript_path=self.manuscript_path, context=validation_context
            )

            if not result.is_valid:
                error_msg = f"Validation failed: {', '.join(result.errors)}"
                logger.error(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            if result.warnings:
                for warning in result.warnings:
                    logger.warning(f"⚠️  {warning}")

            logger.info("✅ Manuscript validation passed")
            return {"validation_result": result}

        step = ExecutionStep(
            id="validate_manuscript",
            name="Validate Manuscript",
            function=validate_manuscript,
            required=True,
            timeout=180,  # 3 minutes
        )
        self.execution_manager.add_step(step)

    def _add_content_processing_steps(self):
        """Add content processing steps to pipeline."""

        def process_markdown(context: Dict[str, Any]) -> Dict[str, Any]:
            """Process markdown to LaTeX."""
            logger.info("📝 Processing markdown content...")

            # Use ContentProcessor for centralized markdown processing
            from rxiv_maker.core.content_processor import ContentProcessor

            processor = ContentProcessor()

            # Process all markdown files
            markdown_files = list(self.manuscript_path.glob("**/*.md"))
            processed_files = []

            for md_file in markdown_files:
                if md_file.name.startswith("."):
                    continue  # Skip hidden files

                output_file = self.output_dir / f"{md_file.stem}.tex"
                self.output_dir.mkdir(parents=True, exist_ok=True)

                # Register temp file for cleanup
                self.resource_manager.register_temp_file(output_file)

                success = processor.process_file(md_file, output_file)
                if success:
                    processed_files.append(output_file)
                    logger.info(f"✅ Processed {md_file.name} → {output_file.name}")
                else:
                    logger.error(f"❌ Failed to process {md_file.name}")

            return {"processed_files": processed_files}

        step = ExecutionStep(
            id="process_markdown",
            name="Process Markdown to LaTeX",
            function=process_markdown,
            required=True,
            timeout=600,  # 10 minutes
        )
        self.execution_manager.add_step(step)

    def _add_build_execution_step(self):
        """Add build execution step to pipeline."""

        def execute_build(context: Dict[str, Any]) -> Dict[str, Any]:
            """Execute the actual build process."""
            logger.info("🔨 Executing build process...")

            # Create output directory with resource tracking
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.resource_manager.register_temp_directory(self.output_dir)

            # This is where actual build logic would go
            # For demo purposes, we'll create a simple output file
            output_file = self.output_dir / "manuscript.pdf"

            # Simulate build process
            time.sleep(1)  # Simulate work

            # Create mock PDF output
            output_file.write_text("Mock PDF content - build successful!")
            logger.info(f"✅ Build output created: {output_file}")

            return {"output_file": output_file, "build_success": True}

        step = ExecutionStep(
            id="execute_build",
            name="Execute Build Process",
            function=execute_build,
            required=True,
            timeout=900,  # 15 minutes
        )
        self.execution_manager.add_step(step)

    def _add_post_build_validation_step(self):
        """Add post-build validation step."""

        def validate_output(context: Dict[str, Any]) -> Dict[str, Any]:
            """Validate build output."""
            logger.info("🔍 Validating build output...")

            # Check if output file exists
            output_file = context.get("output_file")
            if not output_file or not output_file.exists():
                raise RuntimeError("Build output file not found")

            # Additional output validation could go here
            file_size = output_file.stat().st_size
            logger.info(f"✅ Output validation passed (size: {file_size} bytes)")

            return {"output_validated": True}

        step = ExecutionStep(
            id="validate_output",
            name="Validate Build Output",
            function=validate_output,
            required=True,
            timeout=60,  # 1 minute
        )
        self.execution_manager.add_step(step)


def main():
    """Main example function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Centralized Build Example for rxiv-maker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "manuscript_path", nargs="?", default="MANUSCRIPT", help="Path to manuscript directory (default: MANUSCRIPT)"
    )
    parser.add_argument(
        "--mode", choices=["local", "docker", "podman"], default="local", help="Execution mode (default: local)"
    )
    parser.add_argument("--output-dir", type=Path, help="Output directory (default: manuscript_path/output)")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation steps")
    parser.add_argument("--validation-context", default="build", help="Validation context to use (default: build)")

    args = parser.parse_args()

    # Initialize centralized build manager
    build_manager = CentralizedBuildManager(
        manuscript_path=Path(args.manuscript_path), output_dir=args.output_dir, mode=args.mode
    )

    # Execute build
    success = build_manager.build(validation_context=args.validation_context, skip_validation=args.skip_validation)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
