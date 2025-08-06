"""Word count analysis command for Rxiv-Maker.

This module provides word count analysis functionality that can be run independently
after manuscript generation to provide statistics about the document.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to allow imports when run as a script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from rxiv_maker.converters.md2tex import extract_content_sections
    from rxiv_maker.utils import find_manuscript_md
else:
    from ..converters.md2tex import extract_content_sections
    from ..utils import find_manuscript_md


def count_words_in_text(text):
    """Count words in text, excluding LaTeX commands."""
    import re

    # Remove LaTeX commands (backslash followed by word characters)
    text_no_latex = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)
    text_no_latex = re.sub(r"\\[a-zA-Z]+", "", text_no_latex)
    # Remove remaining LaTeX markup
    text_no_latex = re.sub(r"[{}\\]", " ", text_no_latex)
    # Split by whitespace and count non-empty words
    words = [word.strip() for word in text_no_latex.split() if word.strip()]
    return len(words)


def analyze_section_word_counts(content_sections):
    """Analyze word counts for each section and provide warnings."""
    section_guidelines = {
        "abstract": {"ideal": 150, "max_warning": 250, "description": "Abstract"},
        "main": {"ideal": 1500, "max_warning": 3000, "description": "Main content"},
        "methods": {"ideal": 1000, "max_warning": 3000, "description": "Methods"},
        "results": {"ideal": 800, "max_warning": 2000, "description": "Results"},
        "discussion": {"ideal": 600, "max_warning": 1500, "description": "Discussion"},
        "conclusion": {"ideal": 200, "max_warning": 500, "description": "Conclusion"},
        "funding": {"ideal": 50, "max_warning": 150, "description": "Funding"},
        "acknowledgements": {
            "ideal": 100,
            "max_warning": 300,
            "description": "Acknowledgements",
        },
    }

    print("\n📊 WORD COUNT ANALYSIS:")
    print("=" * 50)

    total_words = 0
    for section_key, content in content_sections.items():
        if content.strip():
            word_count = count_words_in_text(content)
            total_words += word_count

            # Get guidelines for this section
            guidelines = section_guidelines.get(section_key, {})
            section_name = guidelines.get("description", section_key.replace("_", " ").title())
            ideal = guidelines.get("ideal")
            max_warning = guidelines.get("max_warning")

            # Format output
            status = "✓"
            warning = ""

            if max_warning and word_count > max_warning:
                status = "⚠️"
                warning = f" (exceeds typical {max_warning} word limit)"
            elif ideal and word_count > ideal * 1.5:
                status = "⚠️"
                warning = f" (consider typical ~{ideal} words)"

            print(f"{status} {section_name:<15}: {word_count:>4} words{warning}")

    print("-" * 50)
    print(f"📝 Total article words: {total_words}")

    # Overall article length guidance
    if total_words > 8000:
        print("⚠️  Article is quite long (>8000 words) - consider condensing for most journals")
    elif total_words > 5000:
        print("ℹ️  Article length is substantial - check target journal word limits")
    elif total_words < 2000:
        print("ℹ️  Article is relatively short - ensure adequate detail for publication")

    print("=" * 50)


def analyze_manuscript_word_count(manuscript_path: str | None = None) -> int:
    """Analyze word counts from manuscript markdown.

    Args:
        manuscript_path: Path to manuscript markdown file (auto-detected if
            not provided)

    Returns:
        0 if successful, 1 if error
    """
    try:
        # Find the manuscript markdown file
        if manuscript_path:
            manuscript_md = Path(manuscript_path)
            if not manuscript_md.exists():
                print(f"Error: Manuscript file not found: {manuscript_md}")
                return 1
        else:
            manuscript_md = find_manuscript_md()
            if not manuscript_md:
                print("Error: Could not find manuscript markdown file")
                return 1

        # Extract content sections from markdown
        content_sections = extract_content_sections(str(manuscript_md))

        # Analyze word counts and provide warnings
        analyze_section_word_counts(content_sections)

        return 0

    except Exception as e:
        import traceback

        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(analyze_manuscript_word_count())
