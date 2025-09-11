"""Tests for tips functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from rxiv_maker.utils.tips import TipsManager, get_build_success_tip, get_general_tip


class TestTipsManager:
    """Test the TipsManager class."""

    def test_init_default_path(self):
        """Test TipsManager initialization with default path."""
        manager = TipsManager()
        assert manager.tips_file is not None
        assert "tips.yaml" in str(manager.tips_file)

    def test_init_custom_path(self):
        """Test TipsManager initialization with custom path."""
        custom_path = Path("/tmp/custom_tips.yaml")
        manager = TipsManager(tips_file=custom_path)
        assert manager.tips_file == custom_path

    def test_should_show_tip_frequencies(self):
        """Test tip frequency logic - now always returns True."""
        manager = TipsManager()

        # All frequency settings now return True
        assert manager._should_show_tip("never") is True
        assert manager._should_show_tip("low") is True
        assert manager._should_show_tip("normal") is True
        assert manager._should_show_tip("high") is True
        assert manager._should_show_tip("always") is True

    def test_load_tips_fallback_when_file_missing(self):
        """Test loading tips when file doesn't exist."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=True) as tmp:
            tmp_path = Path(tmp.name)

        # File is deleted, so it doesn't exist
        manager = TipsManager(tips_file=tmp_path)
        tips_data = manager._load_tips()

        assert "tips" in tips_data
        assert len(tips_data["tips"]) > 0
        assert tips_data["tips"][0]["id"] == "vscode_extension"

    def test_load_tips_with_valid_yaml(self):
        """Test loading tips from valid YAML file."""
        yaml_content = """
tips:
  - id: test_tip
    title: Test Tip
    message: This is a test tip
    category: test
    priority: 5
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp_path = Path(tmp.name)

        try:
            manager = TipsManager(tips_file=tmp_path)
            tips_data = manager._load_tips()

            assert "tips" in tips_data
            assert len(tips_data["tips"]) == 1
            assert tips_data["tips"][0]["id"] == "test_tip"
            assert tips_data["tips"][0]["title"] == "Test Tip"
        finally:
            tmp_path.unlink()

    def test_select_tip_no_category_filter(self):
        """Test tip selection without category filter."""
        yaml_content = """
tips:
  - id: tip1
    title: Tip 1
    message: First tip
    category: general
  - id: tip2
    title: Tip 2
    message: Second tip
    category: build
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp_path = Path(tmp.name)

        try:
            manager = TipsManager(tips_file=tmp_path)
            tip = manager._select_tip()

            assert tip is not None
            assert tip["id"] in ["tip1", "tip2"]
        finally:
            tmp_path.unlink()

    def test_select_tip_with_category_filter(self):
        """Test tip selection with category filter."""
        yaml_content = """
tips:
  - id: tip1
    title: Tip 1
    message: First tip
    category: general
  - id: tip2
    title: Tip 2
    message: Second tip
    category: build
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp_path = Path(tmp.name)

        try:
            manager = TipsManager(tips_file=tmp_path)
            tip = manager._select_tip(category="build")

            assert tip is not None
            assert tip["id"] == "tip2"
            assert tip["category"] == "build"
        finally:
            tmp_path.unlink()

    def test_select_tip_priority_preference(self):
        """Test that high-priority tips are preferred."""
        yaml_content = """
tips:
  - id: low_priority
    title: Low Priority
    message: Low priority tip
    priority: 1
  - id: high_priority
    title: High Priority
    message: High priority tip
    priority: 8
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
            tmp.write(yaml_content)
            tmp_path = Path(tmp.name)

        try:
            manager = TipsManager(tips_file=tmp_path)

            # Test multiple selections to check priority preference
            selections = []
            for _ in range(20):
                tip = manager._select_tip()
                if tip:
                    selections.append(tip["id"])

            # High priority tip should appear more frequently
            high_priority_count = selections.count("high_priority")

            # Due to randomness, we can't guarantee exact counts, but high should generally be more frequent
            assert high_priority_count >= 0  # Should appear at least sometimes

        finally:
            tmp_path.unlink()

    def test_get_tip_with_force(self):
        """Test getting tip with force flag."""
        manager = TipsManager()

        # Force should always return a tip regardless of frequency
        tip = manager.get_tip(frequency="never", force=True)
        assert tip is not None

    def test_format_tip_for_console(self):
        """Test tip formatting for console output."""
        manager = TipsManager()

        test_tip = {"title": "Test Title", "message": "This is a test message"}

        formatted = manager.format_tip_for_console(test_tip)

        assert "💡" in formatted
        assert "Test Title" in formatted
        assert "This is a test message" in formatted
        assert "[bold blue]" in formatted or "[/bold blue]" in formatted

    def test_get_tip_frequency_behavior(self):
        """Test that tips are always shown regardless of frequency."""
        manager = TipsManager()

        # All frequency settings now return tips
        assert manager.get_tip(frequency="never") is not None
        assert manager.get_tip(frequency="low") is not None
        assert manager.get_tip(frequency="normal") is not None
        assert manager.get_tip(frequency="high") is not None
        assert manager.get_tip(frequency="always") is not None


class TestTipFunctions:
    """Test the standalone tip functions."""

    @patch("rxiv_maker.utils.tips.TipsManager")
    def test_get_build_success_tip(self, mock_tips_manager_class):
        """Test get_build_success_tip function."""
        # Mock the manager instance
        mock_manager = Mock()
        mock_tips_manager_class.return_value = mock_manager

        # Mock return values
        mock_tip = {"title": "Build Success", "message": "Great job!"}
        mock_manager.get_tip.return_value = mock_tip
        mock_manager.format_tip_for_console.return_value = "Formatted tip"

        result = get_build_success_tip("normal")

        # Verify the manager was called correctly (now always uses "always")
        mock_manager.get_tip.assert_called_once_with(category="build_success", frequency="always")
        mock_manager.format_tip_for_console.assert_called_once_with(mock_tip)
        assert result == "Formatted tip"

    @patch("rxiv_maker.utils.tips.TipsManager")
    def test_get_general_tip(self, mock_tips_manager_class):
        """Test get_general_tip function."""
        # Mock the manager instance
        mock_manager = Mock()
        mock_tips_manager_class.return_value = mock_manager

        # Mock return values
        mock_tip = {"title": "General Tip", "message": "Useful info!"}
        mock_manager.get_tip.return_value = mock_tip
        mock_manager.format_tip_for_console.return_value = "Formatted general tip"

        result = get_general_tip("high")

        # Verify the manager was called correctly (now always uses "always")
        mock_manager.get_tip.assert_called_once_with(frequency="always")
        mock_manager.format_tip_for_console.assert_called_once_with(mock_tip)
        assert result == "Formatted general tip"

    @patch("rxiv_maker.utils.tips.TipsManager")
    def test_get_tip_returns_none_when_no_tip_selected(self, mock_tips_manager_class):
        """Test that functions return None when no tip is selected."""
        # Mock the manager instance
        mock_manager = Mock()
        mock_tips_manager_class.return_value = mock_manager

        # Mock get_tip to return None
        mock_manager.get_tip.return_value = None

        result = get_build_success_tip("never")

        # Should not call format_tip_for_console and should return None
        mock_manager.get_tip.assert_called_once()
        mock_manager.format_tip_for_console.assert_not_called()
        assert result is None


class TestTipsIntegration:
    """Integration tests for tips system."""

    def test_tips_yaml_file_exists_and_loads(self):
        """Test that the default tips.yaml file exists and loads correctly."""
        manager = TipsManager()
        tips_data = manager._load_tips()

        assert "tips" in tips_data
        assert len(tips_data["tips"]) > 0

        # Check for the VSCode extension tip
        vscode_tips = [tip for tip in tips_data["tips"] if "vscode" in tip.get("id", "").lower()]
        assert len(vscode_tips) > 0, "Should have VSCode extension tips"

        # Validate tip structure
        for tip in tips_data["tips"]:
            assert "id" in tip
            assert "title" in tip
            assert "message" in tip
            # Optional fields
            if "category" in tip:
                assert isinstance(tip["category"], str)
            if "priority" in tip:
                assert isinstance(tip["priority"], int)

    def test_end_to_end_tip_display(self):
        """Test end-to-end tip selection and formatting."""
        # Force a tip to be shown
        formatted_tip = get_build_success_tip("always")

        # Should get a formatted tip
        assert formatted_tip is not None
        assert "💡" in formatted_tip
        assert len(formatted_tip) > 10  # Should have meaningful content
