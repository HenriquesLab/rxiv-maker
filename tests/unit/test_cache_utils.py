"""Tests for cache utilities."""

from pathlib import Path
from unittest.mock import patch

import pytest

from rxiv_maker.core.cache.cache_utils import (
    cleanup_legacy_cache_dir,
    cleanup_legacy_rxiv_cache_dir,
    get_cache_dir,
    get_legacy_cache_dir,
    get_legacy_rxiv_cache_dir,
    migrate_all_rxiv_caches,
    migrate_cache_file,
    migrate_rxiv_cache_directory,
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

    def test_get_legacy_rxiv_cache_dir(self):
        """Test legacy rxiv cache directory."""
        legacy_dir = get_legacy_rxiv_cache_dir()
        assert legacy_dir == Path(".rxiv_cache")

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

    def test_migrate_rxiv_cache_directory_success(self, tmp_path, monkeypatch):
        """Test successful .rxiv_cache directory migration."""
        monkeypatch.chdir(tmp_path)

        # Create .rxiv_cache directory with subdirectories and files
        rxiv_cache = tmp_path / ".rxiv_cache"
        rxiv_cache.mkdir()

        # Create doi subdirectory with a file
        doi_dir = rxiv_cache / "doi"
        doi_dir.mkdir()
        (doi_dir / "doi_cache.json").write_text('{"test": "data"}')

        # Create bibliography subdirectory with a file
        bib_dir = rxiv_cache / "bibliography"
        bib_dir.mkdir()
        (bib_dir / "bib_cache.json").write_text('{"bib": "data"}')

        # Create a file directly in .rxiv_cache
        (rxiv_cache / "other_file.json").write_text('{"other": "data"}')

        # Mock get_cache_dir to return a temporary location
        with patch("rxiv_maker.core.cache.cache_utils.get_cache_dir") as mock_get_cache_dir:
            mock_get_cache_dir.side_effect = lambda subfolder=None: (
                tmp_path / "new_cache" / subfolder if subfolder else tmp_path / "new_cache"
            )

            result = migrate_rxiv_cache_directory()

            assert result is True

            # Check that files were migrated
            assert (tmp_path / "new_cache" / "doi" / "doi_cache.json").exists()
            assert (tmp_path / "new_cache" / "bibliography" / "bib_cache.json").exists()
            assert (tmp_path / "new_cache" / "other_file.json").exists()

    def test_migrate_rxiv_cache_directory_no_cache(self, tmp_path, monkeypatch):
        """Test migration when no .rxiv_cache directory exists."""
        monkeypatch.chdir(tmp_path)

        result = migrate_rxiv_cache_directory()
        assert result is False

    def test_migrate_all_rxiv_caches(self, tmp_path, monkeypatch):
        """Test migration of multiple .rxiv_cache directories."""
        monkeypatch.chdir(tmp_path)

        # Create .rxiv_cache in current directory
        rxiv_cache1 = tmp_path / ".rxiv_cache"
        rxiv_cache1.mkdir()
        (rxiv_cache1 / "test1.json").write_text('{"test": "1"}')

        # Create subdirectory with .rxiv_cache
        subdir = tmp_path / "MANUSCRIPT"
        subdir.mkdir()
        rxiv_cache2 = subdir / ".rxiv_cache"
        rxiv_cache2.mkdir()
        (rxiv_cache2 / "test2.json").write_text('{"test": "2"}')

        # Mock get_cache_dir to return a temporary location
        with patch("rxiv_maker.core.cache.cache_utils.get_cache_dir") as mock_get_cache_dir:
            mock_get_cache_dir.return_value = tmp_path / "new_cache"

            with patch("rxiv_maker.core.cache.cache_utils.migrate_rxiv_cache_directory") as mock_migrate:
                mock_migrate.return_value = True

                # Pass explicit search paths to avoid finding real cache directories
                result = migrate_all_rxiv_caches(search_paths=[tmp_path])

                # Should have been called twice (once for each .rxiv_cache found)
                assert result == 2
                assert mock_migrate.call_count == 2

    def test_cleanup_legacy_rxiv_cache_dir(self, tmp_path, monkeypatch):
        """Test cleanup of empty legacy .rxiv_cache directory."""
        monkeypatch.chdir(tmp_path)

        # Create empty .rxiv_cache directory
        rxiv_cache = tmp_path / ".rxiv_cache"
        rxiv_cache.mkdir()

        cleanup_legacy_rxiv_cache_dir()

        assert not rxiv_cache.exists()

    def test_cleanup_legacy_rxiv_cache_dir_not_empty(self, tmp_path, monkeypatch):
        """Test cleanup leaves non-empty legacy .rxiv_cache directory."""
        monkeypatch.chdir(tmp_path)

        # Create .rxiv_cache directory with file
        rxiv_cache = tmp_path / ".rxiv_cache"
        rxiv_cache.mkdir()
        (rxiv_cache / "file.txt").write_text("test")

        cleanup_legacy_rxiv_cache_dir()

        assert rxiv_cache.exists()
        assert (rxiv_cache / "file.txt").exists()


if __name__ == "__main__":
    pytest.main([__file__])
