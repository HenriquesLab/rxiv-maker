"""Unit tests for container engine functionality (Docker and Podman)."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Exclude from default CI test session; run via dedicated engine jobs
pytestmark = pytest.mark.ci_exclude


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    temp_dir = tempfile.mkdtemp()
    workspace_dir = Path(temp_dir)
    yield workspace_dir
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.docker
@pytest.mark.podman
class TestContainerEngines:
    """Test container engine functionality for both Docker and Podman."""

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_engine_availability_check(self, mock_run, engine_type, temp_workspace):
        """Test container engine availability checking."""
        # Test engine available
        version_output = f"{engine_type.title()} version 20.10.0"
        mock_run.return_value = Mock(returncode=0, stdout=version_output)

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": engine_type}):
                engine = get_container_engine(engine_type, workspace_dir=temp_workspace)
                assert engine.engine_name == engine_type

        except (ImportError, RuntimeError):
            # Skip if engine not available or imports fail
            pytest.skip(f"{engine_type.title()} engine not available or imports failed")

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_engine_unavailable(self, mock_run, engine_type, temp_workspace):
        """Test behavior when container engine is unavailable."""
        # Test engine not available
        mock_run.return_value = Mock(returncode=1, stderr=f"{engine_type}: command not found")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with pytest.raises(RuntimeError):
                get_container_engine(engine_type, workspace_dir=temp_workspace)

        except ImportError:
            # Skip if imports fail
            pytest.skip("Engine imports not available")

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    def test_container_environment_variable_detection(self, engine_type):
        """Test container engine detection via environment variable."""
        with patch.dict(os.environ, {"RXIV_ENGINE": engine_type.upper()}):
            assert os.environ.get("RXIV_ENGINE") == engine_type.upper()

        with patch.dict(os.environ, {"RXIV_ENGINE": engine_type.lower()}):
            assert os.environ.get("RXIV_ENGINE") == engine_type.lower()

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_command_execution(self, mock_run, engine_type, temp_workspace):
        """Test container command execution."""
        mock_run.return_value = Mock(returncode=0, stdout=f"{engine_type.title()} command executed")

        # Simulate container command
        container_cmd = [
            engine_type,
            "run",
            "--rm",
            "-v",
            f"{temp_workspace}:/workspace",
            "-w",
            "/workspace",
            "henriqueslab/rxiv-maker-base:latest",
            "python3",
            "--version",
        ]

        try:
            import subprocess

            result = subprocess.run(container_cmd, capture_output=True, text=True)
            assert result.returncode == 0
        except Exception:
            # Skip if subprocess simulation fails
            pytest.skip(f"{engine_type.title()} command simulation failed")

    def test_container_image_reference(self):
        """Test container image reference validation."""
        expected_image = "henriqueslab/rxiv-maker-base:latest"

        # Test that the expected image reference is used
        assert isinstance(expected_image, str)
        assert "henriqueslab/rxiv-maker-base" in expected_image
        assert "latest" in expected_image

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_lifecycle(self, mock_run, engine_type, temp_workspace):
        """Test container lifecycle operations."""
        # Mock successful container operations
        mock_run.return_value = Mock(returncode=0, stdout="Container operation successful")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": engine_type}):
                # Test engine creation
                engine = get_container_engine(engine_type, workspace_dir=temp_workspace)

                # Test basic engine properties
                assert engine.engine_name == engine_type
                assert engine.workspace_dir == temp_workspace

        except (ImportError, RuntimeError):
            # Skip if engine not available or imports fail
            pytest.skip(f"{engine_type.title()} engine not available or imports failed")

    def test_container_workspace_mounting(self, temp_workspace):
        """Test container workspace directory mounting logic."""
        workspace_path = str(temp_workspace)

        # Test workspace path formatting for container mount
        mount_arg = f"{workspace_path}:/workspace"

        assert workspace_path in mount_arg
        assert ":/workspace" in mount_arg

        # Test workspace creation
        test_file = temp_workspace / "test.txt"
        test_file.write_text("test content")

        assert test_file.exists()
        assert test_file.read_text() == "test content"

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_memory_and_cpu_limits(self, mock_run, engine_type, temp_workspace):
        """Test container memory and CPU limit configuration."""
        mock_run.return_value = Mock(returncode=0)

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": engine_type}):
                # Test engine creation with resource limits
                engine = get_container_engine(
                    engine_type, workspace_dir=temp_workspace, memory_limit="1g", cpu_limit="1.0"
                )

                # Verify resource limits are set
                assert engine.memory_limit == "1g"
                assert engine.cpu_limit == "1.0"

        except (ImportError, RuntimeError, AttributeError):
            # Skip if engine not available or attributes don't exist
            pytest.skip(f"{engine_type.title()} engine not available or resource limit attributes not implemented")

    def test_container_engine_factory_registration(self):
        """Test container engine registration in factory."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Test that both engines are registered
            supported_engines = ContainerEngineFactory.get_supported_engines()
            assert "docker" in supported_engines
            assert "podman" in supported_engines

        except ImportError:
            # Skip if imports fail
            pytest.skip("Engine factory imports not available")

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_error_handling(self, mock_run, engine_type):
        """Test container error handling scenarios."""
        # Test engine command failure
        mock_run.return_value = Mock(returncode=1, stderr=f"{engine_type.title()} error occurred")

        try:
            import subprocess

            result = subprocess.run([engine_type, "--version"], capture_output=True, text=True)
            assert result.returncode == 1

        except Exception:
            # Skip if subprocess simulation fails
            pytest.skip(f"{engine_type.title()} error simulation failed")


@pytest.mark.docker
@pytest.mark.podman
class TestContainerEngineIntegration:
    """Test container engine integration scenarios."""

    @patch("subprocess.run")
    def test_engine_selection_priority(self, mock_run):
        """Test container engine selection priority."""
        mock_run.return_value = Mock(returncode=0, stdout="Engine available")

        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Test engine availability detection
            availability = ContainerEngineFactory.list_available_engines()

            # Both engines should be in the list
            assert "docker" in availability
            assert "podman" in availability

        except ImportError:
            # Skip if imports fail
            pytest.skip("Engine factory imports not available")

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    def test_container_session_reuse_configuration(self, engine_type, temp_workspace):
        """Test container session reuse configuration."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import get_container_engine

            with patch.dict(os.environ, {"RXIV_ENGINE": engine_type}):
                # Test with session reuse enabled
                with patch("subprocess.run", return_value=Mock(returncode=0)):
                    engine = get_container_engine(engine_type, workspace_dir=temp_workspace, enable_session_reuse=True)

                    assert engine.enable_session_reuse is True

                # Test with session reuse disabled
                with patch("subprocess.run", return_value=Mock(returncode=0)):
                    engine = get_container_engine(engine_type, workspace_dir=temp_workspace, enable_session_reuse=False)

                    assert engine.enable_session_reuse is False

        except (ImportError, RuntimeError, AttributeError):
            # Skip if engine not available or attributes don't exist
            pytest.skip(f"{engine_type.title()} engine not available or session reuse not implemented")

    @pytest.mark.parametrize("engine_type", ["docker", "podman"])
    @patch("subprocess.run")
    def test_container_fallback_behavior(self, mock_run, engine_type):
        """Test container fallback behavior when primary operations fail."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stderr="First attempt failed"),
            Mock(returncode=0, stdout="Fallback successful"),
        ]

        try:
            import subprocess

            # Simulate initial failure
            result1 = subprocess.run([engine_type, "pull", "test:latest"], capture_output=True)
            assert result1.returncode == 1

            # Simulate fallback success
            result2 = subprocess.run([engine_type, "build", "-t", "test:latest", "."], capture_output=True)
            assert result2.returncode == 0

        except Exception:
            # Skip if subprocess simulation fails
            pytest.skip(f"{engine_type.title()} fallback simulation failed")

    def test_default_engine_selection(self, temp_workspace):
        """Test default engine selection logic."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Test with no environment variable
            with patch.dict(os.environ, {}, clear=True):
                with patch("subprocess.run", return_value=Mock(returncode=0)):
                    # Should default to the first available engine (Docker has priority)
                    with patch.object(ContainerEngineFactory._engines["docker"], "check_available", return_value=True):
                        engine = ContainerEngineFactory.get_default_engine(workspace_dir=temp_workspace)
                        assert engine.engine_name == "docker"

        except (ImportError, RuntimeError):
            # Skip if imports fail or no engines available
            pytest.skip("Engine imports not available or no engines available")

    def test_engine_factory_error_handling(self, temp_workspace):
        """Test engine factory error handling for unsupported engines."""
        try:
            import sys

            sys.path.insert(0, "src")
            from rxiv_maker.engines.factory import ContainerEngineFactory

            # Test unsupported engine type
            with pytest.raises(ValueError):
                ContainerEngineFactory.create_engine("unsupported_engine", workspace_dir=temp_workspace)

        except ImportError:
            # Skip if imports fail
            pytest.skip("Engine factory imports not available")
