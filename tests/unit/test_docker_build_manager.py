"""Comprehensive tests for Docker Build Manager."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from rxiv_maker.docker.build_manager import (
    DockerBuildManager,
    DockerBuildMode,
)


class TestDockerBuildMode:
    """Test DockerBuildMode configuration constants."""

    def test_build_mode_constants(self):
        """Test that build mode constants are properly defined."""
        assert DockerBuildMode.ACCELERATED == "accelerated"
        assert DockerBuildMode.SAFE == "safe"
        assert DockerBuildMode.BALANCED == "balanced"


class TestDockerBuildManagerInit:
    """Test DockerBuildManager initialization."""

    @patch("rxiv_maker.docker.build_manager.DockerBuildManager._find_dockerfile")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    @patch("rxiv_maker.docker.build_manager.platform_detector")
    def test_init_default_values(self, mock_platform, mock_resource_manager, mock_optimizer, mock_find_dockerfile):
        """Test initialization with default values."""
        mock_find_dockerfile.return_value = Path("Dockerfile")
        mock_optimizer.return_value = MagicMock()
        mock_resource_manager.return_value = MagicMock()

        manager = DockerBuildManager()

        assert manager.mode == DockerBuildMode.BALANCED
        assert manager.image_name == "henriqueslab/rxiv-maker-base:latest"
        assert manager.max_build_time == 7200
        assert manager.use_proxy is True
        assert manager.use_buildkit is True
        assert manager.enable_verification is True

    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_init_custom_values(self, mock_resource_manager, mock_optimizer):
        """Test initialization with custom values."""
        dockerfile_path = Path("/custom/Dockerfile")
        build_context = Path("/custom/context")

        manager = DockerBuildManager(
            mode=DockerBuildMode.ACCELERATED,
            image_name="custom:latest",
            dockerfile_path=dockerfile_path,
            build_context=build_context,
            max_build_time=3600,
            use_proxy=False,
            use_buildkit=False,
            enable_verification=False,
        )

        assert manager.mode == DockerBuildMode.ACCELERATED
        assert manager.image_name == "custom:latest"
        assert manager.dockerfile_path == dockerfile_path
        assert manager.build_context == build_context
        assert manager.max_build_time == 3600
        assert manager.use_proxy is False
        assert manager.use_buildkit is False
        assert manager.enable_verification is False


class TestDockerBuildManagerDockerfileSearch:
    """Test Dockerfile finding functionality."""

    @patch("pathlib.Path.exists")
    def test_find_dockerfile_in_common_locations(self, mock_exists):
        """Test finding Dockerfile in common locations."""
        # Mock that the first path exists
        mock_exists.side_effect = [True, False, False, False] * 2  # Called twice due to resolve()

        with (
            patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer"),
            patch("rxiv_maker.docker.build_manager.DockerResourceManager"),
        ):
            manager = DockerBuildManager()
            dockerfile_path = manager._find_dockerfile()

            assert dockerfile_path.name == "Dockerfile"

    @patch("pathlib.Path.exists")
    def test_find_dockerfile_fallback(self, mock_exists):
        """Test Dockerfile fallback when none found."""
        # Mock that no paths exist
        mock_exists.return_value = False

        with (
            patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer"),
            patch("rxiv_maker.docker.build_manager.DockerResourceManager"),
        ):
            manager = DockerBuildManager()
            dockerfile_path = manager._find_dockerfile()

            assert str(dockerfile_path).endswith("src/docker/images/base/Dockerfile")


class TestDockerBuildManagerPrerequisites:
    """Test DockerBuildManager prerequisite checking."""

    @patch("subprocess.run")
    @patch("shutil.disk_usage")
    @patch("pathlib.Path.exists")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_check_prerequisites_docker_available(
        self, mock_resource_manager, mock_optimizer, mock_exists, mock_disk_usage, mock_run
    ):
        """Test prerequisite check when Docker is available."""
        # Mock dockerfile exists
        mock_exists.return_value = True

        # Mock successful docker commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Docker version 20.10.0"),  # docker --version
            MagicMock(returncode=0, stdout="Docker info"),  # docker info
            MagicMock(returncode=0, stdout="buildx version"),  # docker buildx version
            MagicMock(returncode=0, stdout=""),  # docker ps --filter
        ]

        # Mock disk usage (10GB available) - create a proper stat object
        mock_stat = MagicMock()
        mock_stat.free = 10_000_000_000  # 10GB
        mock_disk_usage.return_value = mock_stat

        # Mock optimizer memory check
        mock_optimizer_instance = MagicMock()
        mock_optimizer_instance._get_available_memory_gb.return_value = 8.0
        mock_optimizer.return_value = mock_optimizer_instance

        # Mock dockerfile path exists
        with patch.object(Path, "exists", return_value=True):
            manager = DockerBuildManager()
            result = manager.check_prerequisites()

        assert result["docker_available"] is True
        assert result["buildkit_available"] is True
        assert result["disk_space_sufficient"] is True

    @patch("subprocess.run")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_check_prerequisites_docker_not_available(self, mock_resource_manager, mock_optimizer, mock_run):
        """Test prerequisite check when Docker is not available."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

        manager = DockerBuildManager()
        result = manager.check_prerequisites()

        assert result["docker_available"] is False
        assert len(result["errors"]) > 0


class TestDockerBuildManagerCommands:
    """Test Docker build command generation."""

    @patch("subprocess.run")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_get_build_command_accelerated(self, mock_resource_manager, mock_optimizer, mock_run):
        """Test accelerated build command generation."""
        # Mock buildx availability
        mock_run.return_value = MagicMock(returncode=0)

        # Mock optimizer
        mock_optimizer_instance = MagicMock()
        mock_optimizer_instance.get_optimal_build_args.return_value = {
            "DOCKER_DEFAULT_PLATFORM": "linux/amd64",
            "BUILDKIT_PROGRESS": "plain",
        }
        mock_optimizer.return_value = mock_optimizer_instance

        manager = DockerBuildManager(mode=DockerBuildMode.ACCELERATED)
        command = manager._get_build_command()

        assert "docker" in command[0]
        assert "--cache-from" in command or "--cache-to" in command

    @patch("subprocess.run")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_get_build_command_safe(self, mock_resource_manager, mock_optimizer, mock_run):
        """Test safe build command generation."""
        # Mock buildx not available
        mock_run.return_value = MagicMock(returncode=1)

        # Mock optimizer
        mock_optimizer_instance = MagicMock()
        mock_optimizer_instance.get_optimal_build_args.return_value = {}
        mock_optimizer.return_value = mock_optimizer_instance

        # Mock resource manager
        mock_resource_manager_instance = MagicMock()
        mock_resource_manager_instance.get_optimal_container_limits.return_value = {"memory": "2g", "cpus": "2"}
        mock_resource_manager.return_value = mock_resource_manager_instance

        manager = DockerBuildManager(mode=DockerBuildMode.SAFE)
        command = manager._get_build_command()

        assert "docker" in command[0]
        assert "--no-cache" in command


class TestDockerBuildManagerLogging:
    """Test Docker build logging functionality."""

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("time.strftime")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_setup_build_logging(self, mock_resource_manager, mock_optimizer, mock_strftime, mock_file, mock_mkdir):
        """Test build logging setup."""
        mock_strftime.return_value = "20231201-120000"

        manager = DockerBuildManager()
        log_file = manager._setup_build_logging()

        assert "docker-build-20231201-120000.log" in str(log_file)
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once()


class TestDockerBuildManagerExecution:
    """Test DockerBuildManager build execution."""

    @patch("subprocess.Popen")
    @patch("rxiv_maker.docker.build_manager.DockerBuildOptimizer")
    @patch("rxiv_maker.docker.build_manager.DockerResourceManager")
    def test_execute_build_safe_success(self, mock_resource_manager, mock_optimizer, mock_popen):
        """Test safe build execution success."""
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Build successful", None)
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        with (
            patch("rxiv_maker.docker.build_manager.DockerBuildManager._setup_build_logging") as mock_setup_log,
            patch("builtins.open", mock_open()),
        ):
            mock_setup_log.return_value = Path("/tmp/test.log")

            manager = DockerBuildManager(mode=DockerBuildMode.SAFE)
            success, message = manager._execute_build_safe(["docker", "build", "."])

            assert success is True
            assert message == ""


if __name__ == "__main__":
    pytest.main([__file__])
