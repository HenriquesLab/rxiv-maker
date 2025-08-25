"""Security tests for cache utilities.

This module tests security hardening measures including:
- Path traversal prevention
- Symlink attack protection
- TOCTOU race condition mitigation
- Disk space exhaustion prevention
- Permission validation
"""

import os
from unittest.mock import patch

import pytest

from rxiv_maker.core.cache.secure_cache_utils import (
    SecurityError,
    _check_disk_space,
    _is_safe_path_component,
    _validate_path_within_base,
    get_secure_cache_dir,
    secure_migrate_cache_file,
    validate_cache_security,
)


class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""

    def test_reject_parent_directory_patterns(self):
        """Test that parent directory patterns are rejected."""
        dangerous_patterns = [
            "..",
            "../",
            "..\\",
            "test/../etc",
            "test/../../etc",
            "test\\..\\..\\etc",
            "~",
            "~/test",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]

        for pattern in dangerous_patterns:
            assert not _is_safe_path_component(pattern), f"Failed to reject: {pattern}"

    def test_reject_special_characters(self):
        """Test that special characters are rejected."""
        dangerous_chars = [
            "test\x00file",  # Null byte
            "test\nfile",  # Newline
            "test\rfile",  # Carriage return
            "test|command",  # Pipe
            "test>output",  # Redirect
            "test<input",  # Redirect
            "test&command",  # Command separator
            "test;command",  # Command separator
            "test`command`",  # Command substitution
            "test$(command)",  # Command substitution
        ]

        for pattern in dangerous_chars:
            assert not _is_safe_path_component(pattern), f"Failed to reject: {pattern}"

    def test_accept_safe_paths(self):
        """Test that safe paths are accepted."""
        safe_patterns = [
            "cache",
            "doi",
            "bibliography",
            "test_cache",
            "cache-2024",
            "cache.backup",
        ]

        for pattern in safe_patterns:
            assert _is_safe_path_component(pattern), f"Failed to accept: {pattern}"

    def test_get_cache_dir_with_traversal(self):
        """Test that get_secure_cache_dir rejects traversal attempts."""
        with pytest.raises(SecurityError):
            get_secure_cache_dir("../../../etc")

        with pytest.raises(SecurityError):
            get_secure_cache_dir("/etc/passwd")

        with pytest.raises(SecurityError):
            get_secure_cache_dir("~/.ssh")


class TestSymlinkProtection:
    """Test symlink attack protection."""

    def test_validate_path_within_base(self, tmp_path):
        """Test path validation within base directory."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()

        # Valid paths
        valid_path = base_dir / "subdir" / "file.txt"
        assert _validate_path_within_base(valid_path, base_dir)

        # Invalid paths
        outside_path = tmp_path / "outside" / "file.txt"
        assert not _validate_path_within_base(outside_path, base_dir)

        # Parent directory path
        parent_path = base_dir / ".." / "outside"
        assert not _validate_path_within_base(parent_path, base_dir)

    def test_refuse_symlink_migration(self, tmp_path):
        """Test that symlinks are not migrated."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create a regular file
        regular_file = source_dir / "regular.txt"
        regular_file.write_text("content")

        # Create a symlink
        symlink_file = source_dir / "symlink.txt"
        target_file = tmp_path / "target.txt"
        target_file.write_text("target content")
        symlink_file.symlink_to(target_file)

        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        # Regular file should migrate
        dest_regular = dest_dir / "regular.txt"
        assert secure_migrate_cache_file(regular_file, dest_regular)
        assert dest_regular.exists()
        assert dest_regular.read_text() == "content"

        # Symlink should not migrate
        dest_symlink = dest_dir / "symlink.txt"
        assert not secure_migrate_cache_file(symlink_file, dest_symlink)
        assert not dest_symlink.exists()

    @pytest.mark.skipif(os.name == "nt", reason="Symlink tests may fail on Windows")
    def test_detect_unsafe_symlinks(self, tmp_path):
        """Test detection of unsafe symlinks in cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create safe symlink (within cache)
        safe_target = cache_dir / "target.txt"
        safe_target.write_text("safe")
        safe_link = cache_dir / "safe_link.txt"
        safe_link.symlink_to(safe_target)

        # Create unsafe symlink (outside cache)
        unsafe_target = tmp_path / "outside.txt"
        unsafe_target.write_text("unsafe")
        unsafe_link = cache_dir / "unsafe_link.txt"
        unsafe_link.symlink_to(unsafe_target)

        # Mock get_secure_cache_dir to return our test directory
        with patch("rxiv_maker.core.cache.secure_cache_utils.get_secure_cache_dir", return_value=cache_dir):
            results = validate_cache_security()

            # Should detect symlinks
            assert len(results["symlinks_found"]) == 2

            # Should identify unsafe symlink
            unsafe_links = [link for link in results["symlinks_found"] if not link["safe"]]
            assert len(unsafe_links) == 1
            assert not results["secure"]


class TestAtomicOperations:
    """Test atomic operation implementation."""

    def test_atomic_file_write(self, tmp_path):
        """Test that file writes are atomic."""
        from rxiv_maker.core.cache.secure_cache_utils import _atomic_write

        target_file = tmp_path / "target.txt"
        content = b"test content"

        # Write atomically
        _atomic_write(content, target_file)

        assert target_file.exists()
        assert target_file.read_bytes() == content

        # Check permissions (Unix only)
        if os.name != "nt":
            stat_info = target_file.stat()
            mode = stat_info.st_mode & 0o777
            assert mode == 0o644

    def test_atomic_write_failure_cleanup(self, tmp_path):
        """Test that temporary files are cleaned up on failure."""
        from rxiv_maker.core.cache.secure_cache_utils import _atomic_write

        target_file = tmp_path / "target.txt"

        # Make parent directory read-only to cause failure
        tmp_path.chmod(0o555)

        try:
            with pytest.raises((OSError, PermissionError)):
                _atomic_write(b"content", target_file)
        finally:
            # Restore permissions
            tmp_path.chmod(0o755)

        # Check no temporary files left
        temp_files = list(tmp_path.glob(".target_*.tmp"))
        assert len(temp_files) == 0


class TestDiskSpaceProtection:
    """Test disk space exhaustion prevention."""

    def test_check_disk_space(self, tmp_path):
        """Test disk space checking."""
        has_space, available_mb = _check_disk_space(tmp_path, 1)

        # Should have at least 1MB available in temp directory
        assert has_space
        assert available_mb > 1

    def test_reject_large_files(self, tmp_path):
        """Test that excessively large files are rejected."""
        source_file = tmp_path / "large.bin"
        dest_file = tmp_path / "dest.bin"

        # Create a small file first
        source_file.write_bytes(b"small content")

        # Test the size limit by temporarily lowering it
        from rxiv_maker.core.cache import secure_cache_utils

        # Backup original limit
        original_limit = secure_cache_utils.MAX_FILE_SIZE_MB

        try:
            # Set a very small limit to trigger the rejection
            secure_cache_utils.MAX_FILE_SIZE_MB = 0.000001  # 1 byte

            # Should reject migration due to size
            result = secure_migrate_cache_file(source_file, dest_file)
            assert not result
            assert not dest_file.exists()

        finally:
            # Restore original limit
            secure_cache_utils.MAX_FILE_SIZE_MB = original_limit

    def test_insufficient_space_handling(self, tmp_path):
        """Test handling of insufficient disk space."""
        with patch("rxiv_maker.core.cache.secure_cache_utils._check_disk_space", return_value=(False, 10)):
            with pytest.raises(IOError, match="Insufficient disk space"):
                get_secure_cache_dir("test")


class TestPermissionValidation:
    """Test permission validation and enforcement."""

    @pytest.mark.skipif(os.name == "nt", reason="Permission tests don't apply to Windows")
    def test_directory_permissions(self, tmp_path):
        """Test that directories are created with secure permissions."""
        cache_dir = tmp_path / "cache"

        with patch("platformdirs.user_cache_dir", return_value=str(cache_dir)):
            result_dir = get_secure_cache_dir("test")

            # Check permissions
            stat_info = result_dir.parent.stat()
            mode = stat_info.st_mode & 0o777
            assert mode == 0o755

    def test_detect_insecure_permissions(self, tmp_path):
        """Test detection of insecure permissions."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(mode=0o755)  # Start with secure permissions

        if os.name != "nt":  # Only test on Unix-like systems
            # Explicitly set insecure permissions
            cache_dir.chmod(0o777)

            # Verify permissions were actually set
            stat_info = cache_dir.stat()
            current_mode = stat_info.st_mode & 0o777

            # Only run the test if we successfully set insecure permissions
            if current_mode & 0o022:  # Has world/group write permissions
                with patch("rxiv_maker.core.cache.secure_cache_utils.get_secure_cache_dir", return_value=cache_dir):
                    results = validate_cache_security()

                    assert not results["permissions_ok"]
                    assert not results["secure"]
                    assert any("insecure permissions" in issue for issue in results["issues"])
            else:
                # Permissions weren't set as expected (maybe due to umask), skip the test
                pytest.skip("Unable to create directory with insecure permissions (umask or filesystem restrictions)")
        else:
            # On Windows, just verify the function doesn't crash
            with patch("rxiv_maker.core.cache.secure_cache_utils.get_secure_cache_dir", return_value=cache_dir):
                results = validate_cache_security()
                assert "permissions_ok" in results


class TestInputValidation:
    """Test comprehensive input validation."""

    def test_empty_input_rejection(self):
        """Test that empty inputs are rejected."""
        assert not _is_safe_path_component("")
        assert not _is_safe_path_component(None)

    def test_path_normalization(self):
        """Test that paths are properly normalized."""
        with patch("platformdirs.user_cache_dir", return_value="/tmp/cache"):
            # These should all resolve to the same safe path
            paths = [
                "test",
                "./test",
                "test/",
                "test/.",
            ]

            for path in paths:
                if _is_safe_path_component(path):
                    result = get_secure_cache_dir(path)
                    assert "test" in str(result)


class TestSecurityValidation:
    """Test security validation functionality."""

    def test_comprehensive_validation(self, tmp_path):
        """Test comprehensive security validation."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Add some test content
        (cache_dir / "test.txt").write_text("test")

        with patch("rxiv_maker.core.cache.secure_cache_utils.get_secure_cache_dir", return_value=cache_dir):
            results = validate_cache_security()

            assert "cache_dir" in results
            assert "secure" in results
            assert "issues" in results
            assert "warnings" in results
            assert "permissions_ok" in results
            assert "symlinks_found" in results
            assert "disk_space_ok" in results
            assert "size_within_limits" in results

    def test_size_limit_enforcement(self, tmp_path):
        """Test that cache size limits are enforced."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Mock a large cache
        with patch("rxiv_maker.core.cache.secure_cache_utils.get_secure_cache_dir", return_value=cache_dir):
            # Create mock files that appear large
            for i in range(10):
                (cache_dir / f"file{i}.bin").write_bytes(b"x" * 1000)

            with patch("rxiv_maker.core.cache.secure_cache_utils.MAX_CACHE_SIZE_MB", 0.001):  # 1KB limit
                results = validate_cache_security()

                assert not results["size_within_limits"]
                assert any("exceeds size limit" in warning for warning in results["warnings"])


class TestRaceConditionPrevention:
    """Test TOCTOU race condition prevention."""

    def test_atomic_migration(self, tmp_path):
        """Test that migration is atomic."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("content")

        dest_file = tmp_path / "dest.txt"

        # Migration should be atomic (file either exists completely or not at all)
        result = secure_migrate_cache_file(source_file, dest_file)

        assert result
        assert dest_file.exists()
        assert dest_file.read_text() == "content"
        assert not source_file.exists()  # Original removed only after success

    def test_concurrent_access_safety(self, tmp_path):
        """Test safety under concurrent access."""
        import threading

        source_dir = tmp_path / "source"
        source_dir.mkdir()

        # Create test files
        for i in range(10):
            (source_dir / f"file{i}.txt").write_text(f"content{i}")

        dest_dir = tmp_path / "dest"
        dest_dir.mkdir()

        errors = []

        def migrate_file(index):
            try:
                source = source_dir / f"file{index}.txt"
                dest = dest_dir / f"file{index}.txt"
                secure_migrate_cache_file(source, dest)
            except Exception as e:
                errors.append(e)

        # Run migrations concurrently
        threads = []
        for i in range(10):
            t = threading.Thread(target=migrate_file, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All files should be migrated without errors
        assert len(errors) == 0
        assert len(list(dest_dir.glob("*.txt"))) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
