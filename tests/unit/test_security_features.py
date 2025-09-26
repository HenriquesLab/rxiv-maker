"""Security-focused unit tests for rxiv-maker."""

from pathlib import Path

import pytest

from rxiv_maker.converters.figure_processor import _validate_url_domain, validate_figure_path
from rxiv_maker.core.path_manager import PathManager, PathResolutionError


class TestPathManagerSecurity:
    """Test security features in PathManager."""

    def test_path_traversal_prevention(self):
        """Test that directory traversal attacks are prevented."""
        manager = PathManager(working_dir="/tmp/test")

        # Test various directory traversal patterns
        malicious_paths = [
            "../../../etc/passwd",
            "../../../../../../etc/shadow",
            "../secret.txt",
            "folder/../../../etc/hosts",
            "..\\..\\windows\\system32",  # Windows-style
        ]

        for path in malicious_paths:
            with pytest.raises(PathResolutionError, match="Path traversal not allowed"):
                manager.normalize_path(path)

    def test_absolute_paths_allowed_without_traversal(self):
        """Test that absolute paths without traversal are allowed."""
        manager = PathManager(working_dir="/tmp/test")

        valid_absolute_paths = [
            "/home/user/documents/file.txt",
            "/tmp/safe_file.txt",
            "/var/log/app.log",
        ]

        for path in valid_absolute_paths:
            # Should not raise exception
            result = manager.normalize_path(path)
            assert result.is_absolute()

    def test_relative_paths_stay_within_working_dir(self):
        """Test that relative paths cannot escape working directory."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            # Resolve both paths to handle macOS symlinks properly
            resolved_temp_dir = str(Path(temp_dir).resolve())
            manager = PathManager(working_dir=temp_dir)

            # Valid relative paths
            valid_paths = [
                "file.txt",
                "subdir/file.txt",
                "docs/readme.md",
            ]

            for path in valid_paths:
                result = manager.normalize_path(path)
                # Should be within working directory (resolve both paths for comparison)
                resolved_result = str(Path(result).resolve())
                assert resolved_result.startswith(resolved_temp_dir)

    def test_path_escaping_working_directory_blocked(self):
        """Test that paths escaping working directory are blocked."""
        # Create a real temporary directory for testing
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PathManager(working_dir=temp_dir)

            # This should fail because it would escape the working directory
            # when normalized and resolved
            escape_path = "subdir/../../outside.txt"

            # Note: This test may need adjustment based on actual path resolution
            # The key is ensuring the security check works correctly
            try:
                result = manager.normalize_path(escape_path)
                # If it doesn't raise an exception, ensure it's still within bounds
                assert str(result).startswith(temp_dir)
            except PathResolutionError:
                # This is acceptable - the security check blocked it
                pass


class TestFigureURLSecurity:
    """Test URL validation security features."""

    def test_trusted_domains_allowed(self):
        """Test that trusted domains are allowed."""
        trusted_urls = [
            "https://raw.githubusercontent.com/user/repo/main/image.png",
            "https://github.com/user/repo/blob/main/image.jpg",
            "https://imgur.com/abc123.png",
            "https://i.imgur.com/abc123.jpg",
            "https://upload.wikimedia.org/image.svg",
            "https://via.placeholder.com/300x200",
        ]

        for url in trusted_urls:
            assert _validate_url_domain(url), f"Trusted URL rejected: {url}"

    def test_untrusted_domains_blocked(self):
        """Test that untrusted domains are blocked."""
        untrusted_urls = [
            "https://evil.com/malicious.png",
            "https://attacker.net/image.jpg",
            "http://suspicious-site.org/pic.gif",
            "https://random-domain.xyz/figure.pdf",
            "https://malware.download/virus.exe",
        ]

        for url in untrusted_urls:
            assert not _validate_url_domain(url), f"Untrusted URL allowed: {url}"

    def test_malformed_urls_rejected(self):
        """Test that malformed URLs are rejected."""
        malformed_urls = [
            "not-a-url",
            "htp://broken.com/image.png",  # typo in protocol
            "https://",  # incomplete
            "",  # empty
            "javascript:alert('xss')",  # XSS attempt
        ]

        for url in malformed_urls:
            assert not _validate_url_domain(url), f"Malformed URL allowed: {url}"

    def test_figure_path_validation_with_urls(self):
        """Test figure path validation with URLs."""
        # Trusted URLs should be allowed
        trusted_figure_paths = [
            "https://raw.githubusercontent.com/user/repo/main/figure.png",
            "https://imgur.com/figure.jpg",
        ]

        for path in trusted_figure_paths:
            assert validate_figure_path(path), f"Trusted figure URL rejected: {path}"

        # Untrusted URLs should be blocked
        untrusted_figure_paths = [
            "https://evil.com/figure.png",
            "http://attacker.net/image.jpg",
        ]

        for path in untrusted_figure_paths:
            assert not validate_figure_path(path), f"Untrusted figure URL allowed: {path}"

    def test_local_figure_paths_still_work(self):
        """Test that local figure paths continue to work normally."""
        local_paths = [
            "FIGURES/figure1.png",
            "images/diagram.pdf",
            "chart.svg",
            "plot",  # extensionless
        ]

        for path in local_paths:
            assert validate_figure_path(path), f"Local figure path rejected: {path}"

    def test_www_prefix_handling(self):
        """Test that www. prefix is properly handled."""
        # Both should be treated the same
        assert _validate_url_domain("https://imgur.com/image.png")
        assert _validate_url_domain("https://www.imgur.com/image.png")

        # Both untrusted domains should be rejected
        assert not _validate_url_domain("https://evil.com/image.png")
        assert not _validate_url_domain("https://www.evil.com/image.png")


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_security_features_dont_break_normal_operation(self):
        """Ensure security features don't interfere with normal operation."""
        # Test normal path operations
        manager = PathManager(working_dir="/tmp/test")

        normal_paths = [
            "manuscript.md",
            "output/document.pdf",
            "FIGURES/plot.png",
        ]

        for path in normal_paths:
            result = manager.normalize_path(path)
            assert result is not None
            assert isinstance(result, Path)

        # Test normal figure validation
        normal_figures = [
            "figure.png",
            "plot.pdf",
            "diagram.svg",
            "chart",  # extensionless
        ]

        for figure in normal_figures:
            assert validate_figure_path(figure)
