"""Tests for title synchronization validation in SyntaxValidator."""

import tempfile
from pathlib import Path

import pytest
import yaml

from rxiv_maker.validators.syntax_validator import SyntaxValidator


@pytest.fixture
def temp_manuscript_with_mismatch():
    """Create a temporary manuscript with mismatched titles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manuscript_path = Path(tmpdir)

        # Create config with one title
        config_path = manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump({"title": "Config Title"}, f)

        # Create main with different title
        main_path = manuscript_path / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("# Main Title\n\n## Introduction\nContent.\n")

        yield manuscript_path


@pytest.fixture
def temp_manuscript_with_match():
    """Create a temporary manuscript with matching titles."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manuscript_path = Path(tmpdir)

        # Create config
        config_path = manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump({"title": "Same Title"}, f)

        # Create main with same title
        main_path = manuscript_path / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("# Same Title\n\n## Introduction\nContent.\n")

        yield manuscript_path


@pytest.fixture
def temp_manuscript_with_auto_title():
    """Create a temporary manuscript with auto-generated title."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manuscript_path = Path(tmpdir)

        # Create config
        config_path = manuscript_path / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            yaml.dump({"title": "Config Title"}, f)

        # Create main with auto-generated title (different from config)
        main_path = manuscript_path / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write(
                "<!-- Title auto-synced from config (00_CONFIG.yml) by rxiv-maker -->\n"
                "# Old Auto Title\n\n"
                "## Introduction\nContent.\n"
            )

        yield manuscript_path


class TestTitleSyncValidation:
    """Tests for title sync validation in SyntaxValidator."""

    def test_validator_detects_title_mismatch(self, temp_manuscript_with_mismatch):
        """Test that validator detects title mismatch."""
        validator = SyntaxValidator(str(temp_manuscript_with_mismatch))
        result = validator.validate()

        # Should have at least one error
        assert len(result.errors) > 0

        # Check that there's a title_mismatch error
        title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
        assert len(title_errors) == 1

        error = title_errors[0]
        assert "Config Title" in error.message or (error.context and "Config Title" in error.context)
        assert "Main Title" in error.message or (error.context and "Main Title" in error.context)

    def test_validator_passes_with_matching_titles(self, temp_manuscript_with_match):
        """Test that validator passes when titles match."""
        validator = SyntaxValidator(str(temp_manuscript_with_match))
        result = validator.validate()

        # Should not have title_mismatch errors
        title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
        assert len(title_errors) == 0

    def test_validator_passes_with_auto_generated_title(self, temp_manuscript_with_auto_title):
        """Test that validator doesn't flag auto-generated titles as mismatch."""
        validator = SyntaxValidator(str(temp_manuscript_with_auto_title))
        result = validator.validate()

        # Should not have title_mismatch errors (auto-generated titles are ok)
        title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
        assert len(title_errors) == 0

    def test_validator_handles_missing_config(self):
        """Test validator handles missing config gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_path = Path(tmpdir)

            # Create main without config
            main_path = manuscript_path / "01_MAIN.md"
            with open(main_path, "w") as f:
                f.write("# Title\n\n## Introduction\n")

            validator = SyntaxValidator(str(manuscript_path))
            result = validator.validate()

            # Should not crash or have title_mismatch errors
            title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
            assert len(title_errors) == 0

    def test_validator_handles_missing_main(self):
        """Test validator handles missing main file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manuscript_path = Path(tmpdir)

            # Create config without main
            config_path = manuscript_path / "00_CONFIG.yml"
            with open(config_path, "w") as f:
                yaml.dump({"title": "Title"}, f)

            validator = SyntaxValidator(str(manuscript_path))
            result = validator.validate()

            # Should not crash or have title_mismatch errors
            title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
            assert len(title_errors) == 0


class TestValidationErrorDetails:
    """Tests for validation error message details."""

    def test_error_includes_line_number(self, temp_manuscript_with_mismatch):
        """Test that error includes line number of title in main."""
        validator = SyntaxValidator(str(temp_manuscript_with_mismatch))
        result = validator.validate()

        title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
        assert len(title_errors) == 1

        error = title_errors[0]
        assert error.line_number is not None
        assert error.line_number == 1  # Title is on first line

    def test_error_includes_helpful_suggestion(self, temp_manuscript_with_mismatch):
        """Test that error includes helpful suggestion."""
        validator = SyntaxValidator(str(temp_manuscript_with_mismatch))
        result = validator.validate()

        title_errors = [e for e in result.errors if e.error_code == "title_mismatch"]
        assert len(title_errors) == 1

        error = title_errors[0]
        assert error.suggestion is not None
        # Should mention updating one or the other
        assert "00_CONFIG.yml" in error.suggestion or "01_MAIN.md" in error.suggestion
