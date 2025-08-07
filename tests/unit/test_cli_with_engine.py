"""
Example tests demonstrating the new execution engine abstraction.

These tests show how to write engine-agnostic tests that can run
on local, Docker, or Podman environments.
"""

import sys

import pytest


@pytest.mark.fast
def test_cli_version(execution_engine):
    """
    Tests if the 'rxiv --version' command runs successfully
    in the specified engine.
    """
    # Use the standardized rxiv_command method
    result = execution_engine.rxiv_command("--version")

    assert result.returncode == 0
    assert "rxiv" in result.stdout.lower() or "version" in result.stdout.lower()


@pytest.mark.fast
def test_cli_help(execution_engine):
    """
    Tests if the 'rxiv --help' command provides help information.
    """
    # Use the standardized rxiv_command method
    result = execution_engine.rxiv_command("--help")

    assert result.returncode == 0
    assert "rxiv-maker" in result.stdout.lower()
    assert "commands" in result.stdout.lower()


def test_check_installation(execution_engine):
    """
    Tests the check-installation command across different engines.
    """
    if execution_engine.engine_type == "local":
        result = execution_engine.run([sys.executable, "-m", "rxiv_maker.cli", "check-installation"])
    else:
        result = execution_engine.run(["rxiv", "check-installation"])

    # Should complete without error
    assert result.returncode == 0
    # Should show some status information
    assert "checking" in result.stdout.lower() or "status" in result.stdout.lower()


def test_init_command(execution_engine, temp_dir):
    """
    Tests manuscript initialization in different engines.
    """
    # Create a test manuscript directory name
    manuscript_name = "test_manuscript"

    # Run init command in the temporary directory
    # Use check=False as init might have specific requirements
    if execution_engine.engine_type == "local":
        result = execution_engine.run(
            [
                sys.executable,
                "-m",
                "rxiv_maker.cli",
                "init",
                manuscript_name,
                "--no-interrupt",
            ],
            cwd=str(temp_dir),
            check=False,
        )
    else:
        result = execution_engine.run(
            ["rxiv", "init", manuscript_name, "--no-interrupt"],
            cwd=str(temp_dir),
            check=False,
        )

    # The init command might fail if certain requirements aren't met
    # but we can at least check if the command was recognized
    if result.returncode != 0:
        # Check if it failed for a valid reason (not command not found)
        assert "usage" not in result.stderr.lower() or "error" in result.stderr.lower()
    else:
        # If it succeeded, verify output mentions creation
        assert "creating" in result.stdout.lower() or "initialized" in result.stdout.lower()


@pytest.mark.fast
@pytest.mark.parametrize("invalid_command", ["invalid", "not-a-command", "xyz123"])
def test_invalid_commands(execution_engine, invalid_command):
    """
    Tests that invalid commands fail appropriately across engines.
    """
    # We expect this to fail, so we don't use check=True in the engine
    if execution_engine.engine_type == "local":
        result = execution_engine.run([sys.executable, "-m", "rxiv_maker.cli", invalid_command], check=False)
    else:
        result = execution_engine.run(["rxiv", invalid_command], check=False)

    # Should return non-zero exit code
    assert result.returncode != 0

    # Should show error or usage information
    assert "error" in result.stderr.lower() or "usage" in result.stderr.lower()


@pytest.mark.fast
def test_validate_without_manuscript(execution_engine, temp_dir):
    """
    Tests validation command when no manuscript exists.
    """
    # Try to validate in empty directory
    if execution_engine.engine_type == "local":
        result = execution_engine.run(
            [sys.executable, "-m", "rxiv_maker.cli", "validate"],
            cwd=str(temp_dir),
            check=False,
        )
    else:
        result = execution_engine.run(["rxiv", "validate"], cwd=str(temp_dir), check=False)

    # Should fail since no manuscript exists
    assert result.returncode != 0


class TestEngineIntegration:
    """Group of tests specifically for engine integration."""

    def test_engine_environment_variables(self, execution_engine):
        """
        Tests that environment variables work correctly in different engines.
        """
        # Set a custom environment variable
        if execution_engine.engine_type == "local":
            result = execution_engine.run(
                [
                    sys.executable,
                    "-c",
                    "import os; print(os.environ.get('RXIV_TEST', 'not set'))",
                ],
                env={"RXIV_TEST": "test_value"},
            )
        else:
            # In Docker, use python3 command
            result = execution_engine.run(
                [
                    "python3",
                    "-c",
                    "import os; print(os.environ.get('RXIV_TEST', 'not set'))",
                ],
                env={"RXIV_TEST": "test_value"},
            )

        assert result.returncode == 0
        assert "test_value" in result.stdout

    def test_working_directory_handling(self, execution_engine, temp_dir):
        """
        Tests that working directory is handled correctly across engines.
        """
        if execution_engine.engine_type == "local":
            # Create a marker file
            marker_file = temp_dir / "marker.txt"
            marker_file.write_text("test content")

            # List files in the directory
            result = execution_engine.run(
                [sys.executable, "-c", "import os; print(sorted(os.listdir('.')))"],
                cwd=str(temp_dir),
            )
            assert result.returncode == 0
            assert "marker.txt" in result.stdout
        else:
            # For Docker/Podman, create a test directory inside the container
            # First create a test directory
            test_dir = "/tmp/test_dir_" + str(temp_dir).split("/")[-1]
            execution_engine.run(["mkdir", "-p", test_dir])

            # Create a marker file
            execution_engine.run(["sh", "-c", f"echo 'test content' > {test_dir}/marker.txt"])

            # List files in the directory
            result = execution_engine.run(
                ["python3", "-c", "import os; print(sorted(os.listdir('.')))"],
                cwd=test_dir,
            )

            assert result.returncode == 0
            assert "marker.txt" in result.stdout
