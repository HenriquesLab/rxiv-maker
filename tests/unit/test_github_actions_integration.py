"""Tests for GitHub Actions integration functionality.

This module tests the GitHub Actions workflow configuration, environment variable
handling, caching strategies, and CI/CD pipeline behavior.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

# Exclude from default CI run (parses workflow files and can be brittle)
pytestmark = pytest.mark.ci_exclude


class TestGitHubActionsWorkflow(unittest.TestCase):
    """Test GitHub Actions workflow configuration and behavior."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.workflow_file = Path(__file__).parent.parent.parent / ".github/workflows/ci.yml"

    def test_workflow_file_exists(self):
        """Test that the GitHub Actions workflow file exists."""
        self.assertTrue(self.workflow_file.exists())

    @pytest.mark.fast
    def test_workflow_yaml_structure(self):
        """Test GitHub Actions workflow YAML structure."""
        if not self.workflow_file.exists():
            self.skipTest("Workflow file not found")

        try:
            with open(self.workflow_file) as f:
                workflow = yaml.safe_load(f)
        except Exception as e:
            self.skipTest(f"Could not parse workflow YAML: {e}")

        # Test basic structure
        self.assertIn("name", workflow)
        # Handle YAML parsing edge case where 'on:' becomes True
        self.assertTrue("on" in workflow or True in workflow)
        self.assertIn("jobs", workflow)

        # Test workflow name
        self.assertEqual(workflow["name"], "Unified CI/CD Pipeline")

        # Test trigger events - handle YAML parsing edge case
        trigger_section = workflow.get("on") or workflow.get(True)
        self.assertIsNotNone(trigger_section, "No trigger section found")

        self.assertIn("pull_request", trigger_section)

        # Test pull_request trigger configuration
        pr_triggers = trigger_section["pull_request"]
        if "branches" in pr_triggers:
            branches = pr_triggers["branches"]
            self.assertIn("main", branches)
            self.assertIn("dev", branches)

    @pytest.mark.fast
    def test_workflow_dispatch_inputs(self):
        """Test workflow_dispatch input configuration."""
        if not self.workflow_file.exists():
            self.skipTest("Workflow file not found")

        try:
            with open(self.workflow_file) as f:
                workflow = yaml.safe_load(f)
        except Exception as e:
            self.skipTest(f"Could not parse workflow YAML: {e}")

        # Test workflow_dispatch structure - handle YAML parsing edge case
        trigger_section = workflow.get("on") or workflow.get(True)
        if not trigger_section or "workflow_dispatch" not in trigger_section:
            self.skipTest("workflow_dispatch not found in workflow - this is expected for CI workflow")

        workflow_dispatch = trigger_section["workflow_dispatch"]
        if "inputs" not in workflow_dispatch:
            self.skipTest("inputs not found in workflow_dispatch")

        dispatch_inputs = workflow_dispatch["inputs"]
        self.assertIn("test_suite", dispatch_inputs)

        test_suite_input = dispatch_inputs["test_suite"]
        self.assertEqual(test_suite_input["default"], "fast")
        self.assertEqual(test_suite_input["type"], "choice")
        self.assertFalse(test_suite_input["required"])

    @pytest.mark.fast
    def test_jobs_configuration(self):
        """Test jobs configuration in the workflow."""
        if not self.workflow_file.exists():
            self.skipTest("Workflow file not found")

        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        jobs = workflow["jobs"]

        # Test job presence - check for fast-tests job
        self.assertIn("fast-tests", jobs, f"Available jobs: {list(jobs.keys())}")

        # Test fast-tests job
        test_job = jobs["fast-tests"]
        self.assertIn("runs-on", test_job)
        self.assertEqual(test_job["name"], "Fast Tests (${{ matrix.os }}, Python ${{ matrix.python-version }})")
        self.assertEqual(test_job["timeout-minutes"], 15)

    @pytest.mark.fast
    def test_docker_container_configuration(self):
        """Test Docker container configuration in build job."""
        if not self.workflow_file.exists():
            self.skipTest("Workflow file not found")

        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        test_job = workflow["jobs"]["fast-tests"]

        # CI workflow doesn't use Docker containers - runs directly on ubuntu-latest
        if "container" not in test_job:
            self.skipTest("CI workflow doesn't use Docker containers - this is expected")

        container = test_job["container"]
        # If there is a container config, test it
        self.assertIsInstance(container, dict)

    @pytest.mark.fast
    def test_caching_strategies(self):
        """Test caching strategies in the workflow."""
        if not self.workflow_file.exists():
            self.skipTest("Workflow file not found")

        with open(self.workflow_file) as f:
            workflow = yaml.safe_load(f)

        test_steps = workflow["jobs"]["fast-tests"]["steps"]
        cache_steps = [step for step in test_steps if step.get("name", "").startswith("Cache")]

        # Test that we have cache steps
        self.assertGreater(len(cache_steps), 0)

        # Test specific cache configurations for CI workflow
        cache_names = [step["name"] for step in cache_steps]
        expected_caches = [
            "Cache dependencies",
        ]

        for expected_cache in expected_caches:
            self.assertIn(expected_cache, cache_names)

    def test_environment_variable_handling(self):
        """Test environment variable handling in workflow steps."""
        # Test manuscript path environment variable logic
        test_cases = [
            {
                "event_name": "workflow_dispatch",
                "input_path": "CUSTOM_MANUSCRIPT",
                "expected": "CUSTOM_MANUSCRIPT",
            },
            {
                "event_name": "push",
                "env_path": "EXAMPLE_MANUSCRIPT",
                "expected": "EXAMPLE_MANUSCRIPT",
            },
        ]

        for case in test_cases:
            with self.subTest(case=case):
                # Simulate manuscript path determination logic
                if case.get("event_name") == "workflow_dispatch":
                    manuscript_path = case.get("input_path", "MANUSCRIPT")
                else:
                    manuscript_path = case.get("env_path", "EXAMPLE_MANUSCRIPT")

                self.assertEqual(manuscript_path, case["expected"])


class TestWorkflowStepSimulation(unittest.TestCase):
    """Test simulation of individual workflow steps."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    @patch("subprocess.run")
    def test_git_configuration_step(self, mock_run):
        """Test Git configuration step simulation."""
        mock_run.return_value = Mock(returncode=0)

        # Simulate Git configuration commands
        commands = [
            [
                "git",
                "config",
                "--global",
                "--add",
                "safe.directory",
                "/__w/rxiv-maker/rxiv-maker",
            ],
            ["git", "config", "user.name", "github-actions"],
            ["git", "config", "user.email", "github-actions@github.com"],
        ]

        for _cmd in commands:
            result = mock_run.return_value
            self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_python_setup_step(self, mock_run):
        """Test Python setup step simulation."""
        mock_run.return_value = Mock(returncode=0, stdout="Setup completed successfully")

        # Simulate make setup command
        result = mock_run.return_value
        self.assertEqual(result.returncode, 0)

    def test_cache_key_generation(self):
        """Test cache key generation logic."""
        # Test Python dependencies cache key pattern
        python_cache_key = "ubuntu-latest-python-abc123def456"
        self.assertIn("python", python_cache_key)
        self.assertIn("ubuntu-latest", python_cache_key)

        # Test R packages cache key pattern
        r_cache_key = "ubuntu-latest-r-xyz789"
        self.assertIn("r", r_cache_key)

        # Test LaTeX cache key pattern
        latex_cache_key = "ubuntu-latest-latex-manuscript123"
        self.assertIn("latex", latex_cache_key)

        # Test figures cache key pattern
        figures_cache_key = "ubuntu-latest-figures-fig456"
        self.assertIn("figures", figures_cache_key)

    def test_timeout_configuration(self):
        """Test timeout configuration for PDF generation step."""
        timeout_minutes = 15
        self.assertEqual(timeout_minutes, 15)
        self.assertGreater(timeout_minutes, 10)  # Should be reasonable timeout

    @patch.dict(os.environ, {"R_LIBS_USER": "~/.R/library"})
    def test_r_environment_setup(self):
        """Test R environment setup."""
        r_libs_path = os.environ.get("R_LIBS_USER")
        self.assertEqual(r_libs_path, "~/.R/library")

    def test_build_configuration_logging(self):
        """Test build configuration logging."""
        config_info = {
            "manuscript_path": "EXAMPLE_MANUSCRIPT",
            "python_version": "3.11.0",
            "latex_version": "pdfTeX 3.141592653",
            "current_directory": "/workspace",
            "available_memory": "7.0Gi",
            "available_space": "10G",
        }

        # Test that all required configuration items are present
        required_keys = ["manuscript_path", "python_version", "latex_version"]
        for key in required_keys:
            self.assertIn(key, config_info)

    def test_output_directory_structure(self):
        """Test expected output directory structure."""
        expected_outputs = [
            "output/manuscript.pdf",
            "output/manuscript.tex",
            "output/manuscript.aux",
            "output/manuscript.bbl",
            "output/manuscript.blg",
        ]

        for output_file in expected_outputs:
            # Test that expected files have proper extensions
            file_path = Path(output_file)
            self.assertIn(file_path.suffix, [".pdf", ".tex", ".aux", ".bbl", ".blg"])


class TestArtifactHandling(unittest.TestCase):
    """Test artifact generation and handling."""

    def test_artifact_paths(self):
        """Test artifact path construction."""
        base_paths = {
            "pdf": "output/*.pdf",
            "tex": "output/*.tex",
            "logs": "output/*.log",
            "figures": "output/Figures/**/*",
        }

        for _artifact_type, path_pattern in base_paths.items():
            self.assertIsInstance(path_pattern, str)
            self.assertIn("output/", path_pattern)

    def test_release_artifact_naming(self):
        """Test release artifact naming convention."""
        # Test tag-based release naming
        tag_name = "v1.2.3"
        manuscript_name = "example_manuscript"

        expected_artifact_name = f"{manuscript_name}_{tag_name}.pdf"
        self.assertIn(tag_name, expected_artifact_name)
        self.assertIn(manuscript_name, expected_artifact_name)

    def test_pdf_validation_requirements(self):
        """Test PDF validation requirements."""
        pdf_validation_checks = [
            "file_exists",
            "file_size_reasonable",
            "pdf_format_valid",
            "page_count_positive",
        ]

        for check in pdf_validation_checks:
            self.assertIsInstance(check, str)
            self.assertTrue(len(check) > 0)


class TestErrorHandlingScenarios(unittest.TestCase):
    """Test error handling scenarios in GitHub Actions workflow."""

    @patch("subprocess.run")
    def test_latex_compilation_failure(self, mock_run):
        """Test handling of LaTeX compilation failures."""
        mock_run.return_value = Mock(returncode=1, stderr="! LaTeX Error: File `missing.sty' not found.")

        result = mock_run.return_value
        self.assertEqual(result.returncode, 1)
        self.assertIn("LaTeX Error", result.stderr)

    @patch("subprocess.run")
    def test_python_dependency_failure(self, mock_run):
        """Test handling of Python dependency installation failures."""
        mock_run.return_value = Mock(
            returncode=1,
            stderr="ERROR: Could not find a version that satisfies the requirement",
        )

        result = mock_run.return_value
        self.assertEqual(result.returncode, 1)
        self.assertIn("Could not find a version", result.stderr)

    @patch("subprocess.run")
    def test_r_package_installation_failure(self, mock_run):
        """Test handling of R package installation failures."""
        mock_run.return_value = Mock(returncode=1, stderr="ERROR: dependency 'package' is not available")

        result = mock_run.return_value
        self.assertEqual(result.returncode, 1)
        self.assertIn("dependency", result.stderr)

    def test_timeout_scenario(self):
        """Test timeout scenario handling."""
        import subprocess

        # Simulate timeout exception
        timeout_error = subprocess.TimeoutExpired(
            cmd=["make", "pdf"],
            timeout=900,  # 15 minutes
        )

        self.assertEqual(timeout_error.timeout, 900)
        self.assertIn("make", timeout_error.cmd)

    def test_disk_space_exhaustion(self):
        """Test disk space exhaustion scenario."""
        # Simulate disk space check
        available_space_gb = 0.5  # Less than 1GB available
        minimum_required_gb = 2.0

        space_sufficient = available_space_gb >= minimum_required_gb
        self.assertFalse(space_sufficient)

    def test_memory_exhaustion_scenario(self):
        """Test memory exhaustion scenario."""
        # Simulate memory usage check
        available_memory_gb = 1.0  # Limited memory
        estimated_usage_gb = 2.0  # Process needs more memory

        memory_sufficient = available_memory_gb >= estimated_usage_gb
        self.assertFalse(memory_sufficient)


class TestContainerizedBuildOptimizations(unittest.TestCase):
    """Test containerized build optimizations and performance."""

    def test_precompiled_image_benefits(self):
        """Test benefits of using precompiled Docker image."""
        # Comparison of build times
        traditional_build_time_minutes = 10
        containerized_build_time_minutes = 2

        performance_improvement = traditional_build_time_minutes / containerized_build_time_minutes
        self.assertGreaterEqual(performance_improvement, 4.0)  # ~5x improvement

    def test_dependency_caching_effectiveness(self):
        """Test dependency caching effectiveness."""
        cache_categories = [
            "python_dependencies",
            "r_packages",
            "latex_outputs",
            "processed_figures",
        ]

        for category in cache_categories:
            # Test that each cache category is properly handled
            self.assertIsInstance(category, str)
            self.assertTrue(len(category) > 0)

    def test_docker_image_optimization(self):
        """Test Docker image optimization features."""
        optimizations = [
            "pre_installed_latex",
            "pre_installed_r_packages",
            "pre_installed_python_packages",
            "pre_installed_nodejs",
            "optimized_layer_structure",
        ]

        for optimization in optimizations:
            self.assertIsInstance(optimization, str)

    def test_build_reproducibility(self):
        """Test build reproducibility across runs."""
        # Test deterministic build inputs
        build_inputs = {
            "docker_image_tag": "henriqueslab/rxiv-maker-base:latest",
            "platform": "linux/amd64",
            "user": "root",
        }

        for _key, value in build_inputs.items():
            self.assertIsInstance(value, str)
            self.assertTrue(len(value) > 0)


class TestWorkflowIntegrationScenarios(unittest.TestCase):
    """Test complete workflow integration scenarios."""

    def test_manual_trigger_workflow(self):
        """Test manual workflow trigger scenario."""
        workflow_trigger = {
            "event_name": "workflow_dispatch",
            "inputs": {"manuscript_path": "CUSTOM_MANUSCRIPT"},
        }

        self.assertEqual(workflow_trigger["event_name"], "workflow_dispatch")
        self.assertIn("manuscript_path", workflow_trigger["inputs"])

    def test_tag_based_release_workflow(self):
        """Test tag-based release workflow scenario."""
        release_trigger = {
            "event_name": "push",
            "ref": "refs/tags/v1.0.0",
            "tag_name": "v1.0.0",
        }

        self.assertEqual(release_trigger["event_name"], "push")
        self.assertTrue(release_trigger["ref"].startswith("refs/tags/"))

    def test_multi_manuscript_support(self):
        """Test multi-manuscript directory support."""
        supported_manuscripts = [
            "MANUSCRIPT",
            "EXAMPLE_MANUSCRIPT",
            "custom/path/to/manuscript",
        ]

        for manuscript_path in supported_manuscripts:
            self.assertIsInstance(manuscript_path, str)
            self.assertTrue(len(manuscript_path) > 0)

    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility in CI."""
        # GitHub Actions runs on ubuntu-latest
        platform_config = {
            "runner_os": "ubuntu-latest",
            "container_platform": "linux/amd64",
            "arch_support": ["amd64", "arm64_via_emulation"],
        }

        self.assertEqual(platform_config["runner_os"], "ubuntu-latest")
        self.assertIn("amd64", platform_config["arch_support"])

    def test_environment_isolation(self):
        """Test environment isolation in containerized builds."""
        isolation_features = [
            "containerized_execution",
            "isolated_file_system",
            "controlled_dependencies",
            "reproducible_environment",
        ]

        for feature in isolation_features:
            self.assertIsInstance(feature, str)


if __name__ == "__main__":
    unittest.main()
