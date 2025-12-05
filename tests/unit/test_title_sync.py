"""Unit tests for title synchronization functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from rxiv_maker.utils.title_sync import (
    AUTO_GENERATED_MARKER,
    extract_title_from_config,
    extract_title_from_main,
    remove_title_from_main,
    sync_titles,
    update_title_in_config,
    update_title_in_main,
)


@pytest.fixture
def temp_manuscript_dir():
    """Create a temporary manuscript directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manuscript_path = Path(tmpdir)
        yield manuscript_path


@pytest.fixture
def config_with_title(temp_manuscript_dir):
    """Create a config file with a title."""
    config_path = temp_manuscript_dir / "00_CONFIG.yml"
    config = {"title": "Test Manuscript Title"}
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def config_with_long_short_title(temp_manuscript_dir):
    """Create a config file with long and short titles."""
    config_path = temp_manuscript_dir / "00_CONFIG.yml"
    config = {"title": {"long": "A Very Long Test Manuscript Title", "short": "Test Title"}}
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


@pytest.fixture
def main_with_title(temp_manuscript_dir):
    """Create a main file with a title."""
    main_path = temp_manuscript_dir / "01_MAIN.md"
    content = """# Test Main Title

## Introduction
This is the introduction.
"""
    with open(main_path, "w") as f:
        f.write(content)
    return main_path


@pytest.fixture
def main_with_auto_title(temp_manuscript_dir):
    """Create a main file with an auto-generated title."""
    main_path = temp_manuscript_dir / "01_MAIN.md"
    content = f"""{AUTO_GENERATED_MARKER}
# Auto Generated Title

## Introduction
This is the introduction.
"""
    with open(main_path, "w") as f:
        f.write(content)
    return main_path


@pytest.fixture
def main_with_yaml_and_title(temp_manuscript_dir):
    """Create a main file with YAML front matter and title."""
    main_path = temp_manuscript_dir / "01_MAIN.md"
    content = """---
some_metadata: value
---

# Title After YAML

## Introduction
This is the introduction.
"""
    with open(main_path, "w") as f:
        f.write(content)
    return main_path


class TestExtractTitleFromConfig:
    """Tests for extracting title from config file."""

    def test_extract_simple_string_title(self, config_with_title):
        """Test extracting a simple string title."""
        title = extract_title_from_config(config_with_title)
        assert title == "Test Manuscript Title"

    def test_extract_dict_title_with_long(self, config_with_long_short_title):
        """Test extracting title from dict format (prefers long)."""
        title = extract_title_from_config(config_with_long_short_title)
        assert title == "A Very Long Test Manuscript Title"

    def test_extract_nonexistent_config(self, temp_manuscript_dir):
        """Test extracting from non-existent config."""
        config_path = temp_manuscript_dir / "nonexistent.yml"
        title = extract_title_from_config(config_path)
        assert title is None

    def test_extract_empty_config(self, temp_manuscript_dir):
        """Test extracting from empty config."""
        config_path = temp_manuscript_dir / "rxiv.yml"
        with open(config_path, "w") as f:
            f.write("")
        title = extract_title_from_config(config_path)
        assert title is None

    def test_extract_config_without_title(self, temp_manuscript_dir):
        """Test extracting from config without title field."""
        config_path = temp_manuscript_dir / "00_CONFIG.yml"
        config = {"authors": ["John Doe"]}
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        title = extract_title_from_config(config_path)
        assert title is None


class TestExtractTitleFromMain:
    """Tests for extracting title from main manuscript file."""

    def test_extract_simple_title(self, main_with_title):
        """Test extracting a simple title."""
        title, is_auto, line_num = extract_title_from_main(main_with_title)
        assert title == "Test Main Title"
        assert is_auto is False
        assert line_num == 1

    def test_extract_auto_generated_title(self, main_with_auto_title):
        """Test extracting an auto-generated title."""
        title, is_auto, line_num = extract_title_from_main(main_with_auto_title)
        assert title == "Auto Generated Title"
        assert is_auto is True
        assert line_num == 2

    def test_extract_title_after_yaml(self, main_with_yaml_and_title):
        """Test extracting title after YAML front matter."""
        title, is_auto, line_num = extract_title_from_main(main_with_yaml_and_title)
        assert title == "Title After YAML"
        assert is_auto is False
        assert line_num == 5

    def test_extract_from_nonexistent_file(self, temp_manuscript_dir):
        """Test extracting from non-existent file."""
        main_path = temp_manuscript_dir / "nonexistent.md"
        title, is_auto, line_num = extract_title_from_main(main_path)
        assert title is None
        assert is_auto is False
        assert line_num == -1

    def test_extract_from_file_without_title(self, temp_manuscript_dir):
        """Test extracting from file without level 1 heading."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        content = """## Introduction
This is just a section, no title.
"""
        with open(main_path, "w") as f:
            f.write(content)

        title, is_auto, line_num = extract_title_from_main(main_path)
        assert title is None
        assert is_auto is False
        assert line_num == -1


class TestUpdateTitleInConfig:
    """Tests for updating title in config file."""

    def test_update_existing_config(self, config_with_title):
        """Test updating title in existing config."""
        success = update_title_in_config(config_with_title, "New Title")
        assert success is True

        # Verify the update
        with open(config_with_title) as f:
            config = yaml.safe_load(f)
        assert config["title"] == "New Title"

    def test_update_creates_new_config(self, temp_manuscript_dir):
        """Test updating creates new config if it doesn't exist."""
        config_path = temp_manuscript_dir / "00_CONFIG.yml"
        success = update_title_in_config(config_path, "Created Title")
        assert success is True

        # Verify the creation
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["title"] == "Created Title"


class TestUpdateTitleInMain:
    """Tests for updating title in main manuscript file."""

    def test_add_title_to_empty_file(self, temp_manuscript_dir):
        """Test adding title to empty file."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("")

        success = update_title_in_main(main_path, "New Title", is_auto_generated=True)
        assert success is True

        # Verify the title was added
        with open(main_path) as f:
            content = f.read()
        assert AUTO_GENERATED_MARKER in content
        assert "# New Title" in content

    def test_replace_existing_title(self, main_with_title):
        """Test replacing existing title."""
        success = update_title_in_main(main_with_title, "Replaced Title", is_auto_generated=False)
        assert success is True

        # Verify the replacement
        with open(main_with_title) as f:
            content = f.read()
        assert "# Replaced Title" in content
        assert "Test Main Title" not in content

    def test_replace_auto_generated_title(self, main_with_auto_title):
        """Test replacing auto-generated title."""
        success = update_title_in_main(main_with_auto_title, "Updated Auto Title", is_auto_generated=True)
        assert success is True

        # Verify the replacement
        with open(main_with_auto_title) as f:
            content = f.read()
        assert "# Updated Auto Title" in content
        assert AUTO_GENERATED_MARKER in content

    def test_add_title_after_yaml(self, temp_manuscript_dir):
        """Test adding title after YAML front matter."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        content = """---
metadata: value
---

## Introduction
Content here.
"""
        with open(main_path, "w") as f:
            f.write(content)

        success = update_title_in_main(main_path, "Title After YAML", is_auto_generated=True)
        assert success is True

        # Verify title was added after YAML
        with open(main_path) as f:
            lines = f.readlines()

        # Find the auto-generated marker
        marker_found = False
        title_found = False
        for i, line in enumerate(lines):
            if AUTO_GENERATED_MARKER in line:
                marker_found = True
                # Title should be on next line
                if i + 1 < len(lines) and "# Title After YAML" in lines[i + 1]:
                    title_found = True
                break

        assert marker_found
        assert title_found


class TestRemoveTitleFromMain:
    """Tests for removing auto-generated title from main file."""

    def test_remove_auto_generated_title(self, main_with_auto_title):
        """Test removing auto-generated title."""
        success = remove_title_from_main(main_with_auto_title)
        assert success is True

        # Verify removal
        with open(main_with_auto_title) as f:
            content = f.read()
        assert AUTO_GENERATED_MARKER not in content
        assert "# Auto Generated Title" not in content
        assert "## Introduction" in content  # Other content should remain

    def test_remove_from_file_without_auto_title(self, main_with_title):
        """Test removing from file without auto-generated title (no-op)."""
        original_content = main_with_title.read_text()
        success = remove_title_from_main(main_with_title)
        assert success is True

        # Content should be unchanged
        assert main_with_title.read_text() == original_content


class TestSyncTitles:
    """Tests for the main title synchronization function."""

    def test_sync_from_config_to_main(self, temp_manuscript_dir, config_with_title):
        """Test syncing title from config to main when only config has title."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("## Introduction\nContent here.\n")

        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is True
        assert result.action == "synced_to_main"
        assert result.title == "Test Manuscript Title"

        # Verify title was added to main
        title, is_auto, _ = extract_title_from_main(main_path)
        assert title == "Test Manuscript Title"
        assert is_auto is True

    def test_sync_from_main_to_config(self, temp_manuscript_dir, main_with_title):
        """Test syncing title from main to config when only main has title."""
        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is True
        assert result.action == "synced_to_config"
        assert result.title == "Test Main Title"

        # Verify title was added to config
        config_path = temp_manuscript_dir / "00_CONFIG.yml"
        title = extract_title_from_config(config_path)
        assert title == "Test Main Title"

    def test_sync_matching_titles(self, temp_manuscript_dir, config_with_title):
        """Test sync when both have matching titles."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("# Test Manuscript Title\n\n## Introduction\n")

        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is True
        assert result.action == "no_change"

    def test_sync_mismatched_manual_titles(self, temp_manuscript_dir, config_with_title, main_with_title):
        """Test sync when both have different manual titles (error case)."""
        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is False
        assert result.action == "mismatch"
        assert "Test Manuscript Title" in result.message
        assert "Test Main Title" in result.message

    def test_sync_updates_outdated_auto_title(self, temp_manuscript_dir, config_with_title, main_with_auto_title):
        """Test sync updates outdated auto-generated title."""
        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is True
        assert result.action == "synced_to_main"
        assert result.title == "Test Manuscript Title"

        # Verify title was updated
        main_path = temp_manuscript_dir / "01_MAIN.md"
        title, is_auto, _ = extract_title_from_main(main_path)
        assert title == "Test Manuscript Title"
        assert is_auto is True

    def test_sync_no_titles(self, temp_manuscript_dir):
        """Test sync when neither config nor main has title."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        config_path = temp_manuscript_dir / "00_CONFIG.yml"

        with open(main_path, "w") as f:
            f.write("## Introduction\nContent.\n")
        with open(config_path, "w") as f:
            yaml.dump({}, f)

        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is True
        assert result.action == "no_change"

    def test_sync_with_auto_sync_disabled(self, temp_manuscript_dir, config_with_title):
        """Test sync with auto_sync disabled (validation mode)."""
        main_path = temp_manuscript_dir / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("## Introduction\n")

        result = sync_titles(temp_manuscript_dir, auto_sync=False)

        assert result.success is True
        assert result.action == "no_change"

        # Main should not have been modified
        title, _, _ = extract_title_from_main(main_path)
        assert title is None

    def test_sync_case_insensitive_match(self, temp_manuscript_dir):
        """Test sync considers titles matching in different cases as same."""
        config_path = temp_manuscript_dir / "00_CONFIG.yml"
        main_path = temp_manuscript_dir / "01_MAIN.md"

        # Config has lowercase
        with open(config_path, "w") as f:
            yaml.dump({"title": "test title"}, f)

        # Main has titlecase
        with open(main_path, "w") as f:
            f.write("# Test Title\n\n## Introduction\n")

        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        # Should be considered matching (case-insensitive)
        assert result.success is True
        assert result.action == "no_change"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_removes_leading_newlines_when_adding_title(self, temp_manuscript_dir):
        """Test that leading newlines are removed when adding title."""
        config_path = temp_manuscript_dir / "00_CONFIG.yml"
        main_path = temp_manuscript_dir / "01_MAIN.md"

        # Create config
        with open(config_path, "w") as f:
            yaml.dump({"title": "Test Title"}, f)

        # Create main with leading newlines
        with open(main_path, "w") as f:
            f.write("\n\n## Introduction\nContent.\n")

        # Sync should remove leading newlines
        result = sync_titles(temp_manuscript_dir, auto_sync=True)
        assert result.success is True
        assert result.action == "synced_to_main"

        # Verify no leading newlines
        with open(main_path, "r") as f:
            content = f.read()

        assert content.startswith("<!-- Title auto-synced")
        assert not content.startswith("\n")

    def test_handle_nonexistent_manuscript_dir(self):
        """Test handling non-existent manuscript directory."""
        nonexistent_path = Path("/nonexistent/path")
        result = sync_titles(nonexistent_path, auto_sync=True)

        # Should handle gracefully
        assert result.success is True
        assert result.action == "no_change"

    def test_handle_malformed_config(self, temp_manuscript_dir):
        """Test handling malformed config file."""
        config_path = temp_manuscript_dir / "00_CONFIG.yml"
        with open(config_path, "w") as f:
            f.write("invalid: yaml: content:\n  - broken")

        main_path = temp_manuscript_dir / "01_MAIN.md"
        with open(main_path, "w") as f:
            f.write("# Test\n")

        # Should handle gracefully without crashing
        _ = sync_titles(temp_manuscript_dir, auto_sync=True)
        # Exact outcome depends on implementation, but should not crash

    def test_unicode_in_title(self, temp_manuscript_dir):
        """Test handling unicode characters in title."""
        config_path = temp_manuscript_dir / "rxiv.yml"
        main_path = temp_manuscript_dir / "01_MAIN.md"

        unicode_title = "Test Title with Unicode: α β γ 中文"

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump({"title": unicode_title}, f, allow_unicode=True)

        with open(main_path, "w", encoding="utf-8") as f:
            f.write("## Introduction\n")

        result = sync_titles(temp_manuscript_dir, auto_sync=True)

        assert result.success is True
        assert result.action == "synced_to_main"

        # Verify unicode was preserved
        title, _, _ = extract_title_from_main(main_path)
        assert title == unicode_title
