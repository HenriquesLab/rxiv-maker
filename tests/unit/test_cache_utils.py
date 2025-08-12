"""Tests for cache utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.utils.cache_utils import (
    cleanup_legacy_cache_dir,
    get_cache_dir,
    get_legacy_cache_dir,
    migrate_cache_file,
)


class TestCacheUtils:
    """Test cache utilities."""

    def test_get_cache_dir_basic(self):
        """Test basic cache directory retrieval."""
        cache_dir = get_cache_dir()
        # Cache directory should exist and contain "rxiv-maker" in its path
        assert cache_dir.exists()
        assert "rxiv-maker" in str(cache_dir)

    def test_get_cache_dir_with_subfolder(self):
        """Test cache directory with subfolder."""
        cache_dir = get_cache_dir("doi")
        assert cache_dir.name == "doi"
        # Parent directory should contain "rxiv-maker" in its path
        assert "rxiv-maker" in str(cache_dir.parent)
        assert cache_dir.exists()

    @patch("platformdirs.user_cache_dir")
    def test_get_cache_dir_platform_specific(self, mock_user_cache_dir):
        """Test platform-specific cache directory."""
        mock_user_cache_dir.return_value = "/tmp/test-cache"

        cache_dir = get_cache_dir()

        mock_user_cache_dir.assert_called_once_with("rxiv-maker")
        # Use Path to handle platform-specific path separators
        assert cache_dir == Path("/tmp/test-cache")

    def test_get_legacy_cache_dir(self):
        """Test legacy cache directory."""
        legacy_dir = get_legacy_cache_dir()
        assert legacy_dir == Path(".cache")

    def test_migrate_cache_file_success(self, tmp_path):
        """Test successful cache file migration."""
        # Create source file
        source_file = tmp_path / "source.json"
        source_file.write_text('{"test": "data"}')

        # Create target location
        target_dir = tmp_path / "target"
        target_file = target_dir / "cache.json"

        # Migrate
        result = migrate_cache_file(source_file, target_file)

        assert result is True
        assert not source_file.exists()
        assert target_file.exists()
        assert target_file.read_text() == '{"test": "data"}'

    def test_migrate_cache_file_no_source(self, tmp_path):
        """Test migration with non-existent source file."""
        source_file = tmp_path / "nonexistent.json"
        target_file = tmp_path / "target.json"

        result = migrate_cache_file(source_file, target_file)

        assert result is False
        assert not target_file.exists()

    def test_migrate_cache_file_target_exists(self, tmp_path):
        """Test migration when target file already exists."""
        # Create source and target files
        source_file = tmp_path / "source.json"
        source_file.write_text('{"source": "data"}')

        target_file = tmp_path / "target.json"
        target_file.write_text('{"target": "data"}')

        # Migration should fail without force
        result = migrate_cache_file(source_file, target_file, force=False)
        assert result is False
        assert source_file.exists()
        assert target_file.read_text() == '{"target": "data"}'

        # Migration should succeed with force
        result = migrate_cache_file(source_file, target_file, force=True)
        assert result is True
        assert not source_file.exists()
        assert target_file.read_text() == '{"source": "data"}'

    def test_cleanup_legacy_cache_dir(self, tmp_path, monkeypatch):
        """Test cleanup of empty legacy cache directory."""
        monkeypatch.chdir(tmp_path)

        # Create empty legacy cache directory
        legacy_dir = tmp_path / ".cache"
        legacy_dir.mkdir()

        cleanup_legacy_cache_dir()

        assert not legacy_dir.exists()

    def test_cleanup_legacy_cache_dir_not_empty(self, tmp_path, monkeypatch):
        """Test cleanup leaves non-empty legacy cache directory."""
        monkeypatch.chdir(tmp_path)

        # Create legacy cache directory with file
        legacy_dir = tmp_path / ".cache"
        legacy_dir.mkdir()
        (legacy_dir / "file.txt").write_text("test")

        cleanup_legacy_cache_dir()

        assert legacy_dir.exists()
        assert (legacy_dir / "file.txt").exists()

    def test_cleanup_legacy_cache_dir_nonexistent(self, tmp_path, monkeypatch):
        """Test cleanup with non-existent legacy directory."""
        monkeypatch.chdir(tmp_path)

        # Should not raise error
        cleanup_legacy_cache_dir()


if __name__ == "__main__":
    pytest.main([__file__])
