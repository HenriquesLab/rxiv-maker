"""Tests for custom command processor.

This module tests the custom markdown command processing functionality,
including blindtext commands and the extensible framework for future commands.
"""

from rxiv_maker.converters.custom_command_processor import (
    COMMAND_PROCESSORS,
    _process_blindtext_commands,
    get_supported_commands,
    process_custom_commands,
    register_command_processor,
)


class TestBlindtextCommands:
    """Test blindtext command processing."""

    def test_basic_blindtext_conversion(self):
        """Test basic blindtext command conversion."""
        input_text = "Before text\n\n{{blindtext}}\n\nAfter text"
        expected = "Before text\n\n\\blindtext\n\nAfter text"
        result = _process_blindtext_commands(input_text)
        assert result == expected

    def test_capitalized_blindtext_conversion(self):
        """Test capitalized Blindtext command conversion."""
        input_text = "Before text\n\n{{Blindtext}}\n\nAfter text"
        expected = "Before text\n\n\\Blindtext\n\nAfter text"
        result = _process_blindtext_commands(input_text)
        assert result == expected

    def test_multiple_blindtext_commands(self):
        """Test multiple blindtext commands in same text."""
        input_text = """
        # Title

        {{blindtext}}

        ## Section

        {{Blindtext}}

        More content.

        {{blindtext}}
        """
        result = _process_blindtext_commands(input_text)
        assert "\\blindtext" in result
        assert "\\Blindtext" in result
        assert result.count("\\blindtext") == 2  # Two lowercase instances
        assert result.count("\\Blindtext") == 1  # One capitalized instance

    def test_blindtext_with_whitespace(self):
        """Test blindtext commands with whitespace inside braces."""
        input_text = "{{ blindtext }}"
        expected = "\\blindtext"
        result = _process_blindtext_commands(input_text)
        assert result == expected

    def test_blindtext_case_sensitive(self):
        """Test that blindtext commands are case sensitive."""
        input_text = "{{BLINDTEXT}} {{blindTEXT}} {{BlindText}}"
        # Only exact matches should be converted
        result = _process_blindtext_commands(input_text)
        assert "\\BLINDTEXT" not in result
        assert "\\blindTEXT" not in result
        assert "\\BlindText" not in result
        assert "{{BLINDTEXT}}" in result
        assert "{{blindTEXT}}" in result
        assert "{{BlindText}}" in result

    def test_blindtext_in_complex_markdown(self):
        """Test blindtext commands within complex markdown structure."""
        input_text = """
        # Title

        This is **bold** and *italic* text.

        {{blindtext}}

        - List item 1
        - List item 2

        {{Blindtext}}

        | Table | Header |
        |-------|--------|
        | Cell  | Cell   |

        `{{blindtext}}` should not be converted in code.
        """
        # Note: _process_blindtext_commands doesn't handle code protection
        # That's handled by the main process_custom_commands function
        result = _process_blindtext_commands(input_text)
        # Should convert ALL commands since this function doesn't do code protection
        assert result.count("\\blindtext") == 2  # Both instances converted
        assert result.count("\\Blindtext") == 1
        # The backticks version will also be converted by this function
        assert "`\\blindtext`" in result


class TestCustomCommandProcessor:
    """Test the main custom command processor."""

    def test_process_custom_commands_blindtext(self):
        """Test that process_custom_commands handles blindtext correctly."""
        input_text = "{{blindtext}} and {{Blindtext}}"
        expected = "\\blindtext and \\Blindtext"
        result = process_custom_commands(input_text)
        assert result == expected

    def test_code_protection_fenced(self):
        """Test that fenced code blocks are protected from command processing."""
        input_text = """
        Regular text with {{blindtext}}.

        ```
        This {{blindtext}} should not be converted.
        {{Blindtext}} also should not be converted.
        ```

        More {{blindtext}} to convert.
        """
        result = process_custom_commands(input_text)

        # Count occurrences
        blindtext_count = result.count("\\blindtext")
        blindtext_upper_count = result.count("\\Blindtext")
        preserved_count = result.count("{{blindtext}}") + result.count("{{Blindtext}}")

        # Should convert 2 commands outside code blocks
        assert blindtext_count == 2
        assert blindtext_upper_count == 0  # Only lowercase instances in this test
        # Should preserve 2 commands inside code blocks
        assert preserved_count == 2

    def test_code_protection_inline(self):
        """Test that inline code is protected from command processing."""
        input_text = "Convert {{blindtext}} but not `{{blindtext}}` in code."
        result = process_custom_commands(input_text)

        assert "\\blindtext" in result
        assert "`{{blindtext}}`" in result
        assert result.count("\\blindtext") == 1

    def test_mixed_code_and_commands(self):
        """Test complex mixing of code blocks and commands."""
        input_text = """
        # Title

        {{blindtext}}

        ```python
        def test():
            # This {{blindtext}} is in code
            return "{{Blindtext}}"
        ```

        Back to regular text {{Blindtext}}.

        Inline `{{blindtext}}` is protected.
        """
        result = process_custom_commands(input_text)

        # Should convert 2 commands (1 blindtext + 1 Blindtext outside code)
        total_conversions = result.count("\\blindtext") + result.count("\\Blindtext")
        assert total_conversions == 2

        # Should preserve commands in code
        code_preserved = result.count("{{blindtext}}") + result.count("{{Blindtext}}")
        assert code_preserved >= 2  # At least 2 in fenced + inline code

    def test_empty_and_whitespace_input(self):
        """Test handling of empty and whitespace-only input."""
        assert process_custom_commands("") == ""
        assert process_custom_commands("   \n\n  ") == "   \n\n  "
        assert process_custom_commands("{{blindtext}}") == "\\blindtext"


class TestCommandRegistry:
    """Test the command processor registry system."""

    def test_default_supported_commands(self):
        """Test that blindtext is in the default supported commands."""
        commands = get_supported_commands()
        assert "blindtext" in commands

    def test_register_new_processor(self):
        """Test registering a new command processor."""

        def dummy_processor(text):
            return text.replace("{{test}}", "\\test")

        # Save original state
        original_processors = COMMAND_PROCESSORS.copy()

        try:
            register_command_processor("test", dummy_processor)

            # Check it was registered
            commands = get_supported_commands()
            assert "test" in commands
            assert COMMAND_PROCESSORS["test"] == dummy_processor

        finally:
            # Restore original state
            COMMAND_PROCESSORS.clear()
            COMMAND_PROCESSORS.update(original_processors)

    def test_processor_registry_isolation(self):
        """Test that processor registration doesn't affect existing processors."""

        def dummy_processor(text):
            return text

        original_processors = COMMAND_PROCESSORS.copy()
        original_commands = get_supported_commands()

        try:
            register_command_processor("dummy", dummy_processor)

            # Original commands should still be there
            new_commands = get_supported_commands()
            for cmd in original_commands:
                assert cmd in new_commands

        finally:
            COMMAND_PROCESSORS.clear()
            COMMAND_PROCESSORS.update(original_processors)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_commands(self):
        """Test handling of malformed command syntax."""
        input_text = """
        {blindtext}
        {{{blindtext}}}
        {{blindtext
        blindtext}}
        {{blindtext_typo}}
        """
        # Should not crash and should not convert malformed commands
        result = process_custom_commands(input_text)
        # Single braces should be preserved
        assert "{blindtext}" in result  # Single braces preserved
        # Triple braces contain valid {{blindtext}} so it gets partially converted
        assert "{\\blindtext}" in result  # Triple braces become {\blindtext}
        # Split commands should be preserved
        assert "{{blindtext\n        blindtext}}" in result  # Split command preserved
        # Typos should be preserved
        assert "{{blindtext_typo}}" in result  # Typo preserved

    def test_nested_braces_in_commands(self):
        """Test commands with nested braces (shouldn't convert)."""
        input_text = "{{blind{text}}} {{blind}text}}"
        result = process_custom_commands(input_text)
        # These are malformed and shouldn't convert
        assert "\\blind" not in result

    def test_commands_in_various_contexts(self):
        """Test commands in different markdown contexts."""
        input_text = """
        > {{blindtext}} in blockquote

        - {{blindtext}} in list

        1. {{blindtext}} in numbered list

        [{{blindtext}}](link) - in link text

        **{{blindtext}}** - in bold

        *{{blindtext}}* - in italic
        """
        result = process_custom_commands(input_text)

        # All should be converted (6 total)
        assert result.count("\\blindtext") == 6
        assert "{{blindtext}}" not in result


class TestIntegrationWithMd2tex:
    """Test integration with the main markdown processing pipeline."""

    def test_custom_commands_in_md2tex_pipeline(self):
        """Test that custom commands work in the full markdown pipeline."""
        # Test with a simpler input that won't trigger special processing
        input_markdown = "This is {{blindtext}} and {{Blindtext}} in text."

        # Import here to avoid circular imports during testing
        from rxiv_maker.converters.md2tex import convert_markdown_to_latex

        result = convert_markdown_to_latex(input_markdown)

        # Should contain converted commands
        assert "\\blindtext" in result
        assert "\\Blindtext" in result

        # Should not contain original markdown commands
        assert "{{blindtext}}" not in result
        assert "{{Blindtext}}" not in result
