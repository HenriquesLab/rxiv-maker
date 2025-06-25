# Contributing to Rxiv-Maker

Welcome to Rxiv-Maker! We're thrilled that you're interested in contributing to our project. This guide will help you get started with contributing to Rxiv-Maker, whether you're fixing bugs, adding features, improving documentation, or helping in other ways.

## 🌟 Ways to Contribute

### 🐛 Bug Reports
- **Before submitting**: Search existing issues to avoid duplicates
- **Include**: Detailed description, steps to reproduce, expected vs actual behavior
- **Provide**: System information, error logs, minimal example if possible

### 💡 Feature Requests
- **Use cases**: Explain why this feature would be valuable
- **Scope**: Keep proposals focused and well-defined
- **Discussion**: Start with GitHub Discussions for complex features

### 📖 Documentation
- **Always welcome**: Fix typos, improve clarity, add examples
- **Types**: README updates, API docs, tutorials, troubleshooting guides
- **Standards**: Follow our documentation style guide

### 🔧 Code Contributions
- **Bug fixes**: Small, focused changes with tests
- **New features**: Discuss first via issues or discussions
- **Refactoring**: Improve code quality while maintaining functionality

## 🚀 Getting Started

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/rxiv-maker.git
   cd rxiv-maker
   git remote add upstream https://github.com/henriqueslab/rxiv-maker.git
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install development dependencies
   make setup
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify Setup**
   ```bash
   # Run tests
   pytest
   
   # Try building the example
   MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT make pdf
   ```

### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

2. **Make Your Changes**
   - Write clear, focused commits
   - Add tests for new functionality
   - Update documentation as needed
   - Follow code style guidelines

3. **Test Your Changes**
   ```bash
   # Run all tests
   pytest
   
   # Run specific tests
   pytest tests/unit/test_specific_module.py
   
   # Test with different manuscripts
   MANUSCRIPT_PATH=EXAMPLE_MANUSCRIPT make pdf
   ```

4. **Submit Your Contribution**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   git push origin feature/your-feature-name
   ```

## 📝 Pull Request Guidelines

### Before Submitting
- [ ] Tests pass locally (`pytest`)
- [ ] Code follows project style (`pre-commit run --all-files`)
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated for significant changes
- [ ] Pull request template filled out

### Pull Request Process
1. **Title**: Use conventional commit format (feat:, fix:, docs:, etc.)
2. **Description**: Explain what and why, link to relevant issues
3. **Testing**: Describe how you tested the changes
4. **Breaking Changes**: Clearly document any breaking changes

### Review Process
- **Maintainer Review**: All PRs reviewed by maintainers
- **CI Checks**: All automated checks must pass
- **Feedback**: Address review comments promptly
- **Merge**: Maintainers will merge when ready

## 🎯 Coding Standards

### Python Code Style
We use modern Python tooling for consistent code quality:

```bash
# All tools configured in pyproject.toml
pre-commit run --all-files  # Runs all checks
```

**Tools in use:**
- **Ruff**: Linting and formatting (replaces Black, isort, flake8)
- **MyPy**: Type checking
- **Pytest**: Testing framework

### Code Quality Guidelines
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Google-style docstrings for public functions
- **Error Handling**: Proper exception handling with meaningful messages
- **Testing**: Write tests for new functionality
- **Naming**: Use descriptive variable and function names

### Example Code Style
```python
from typing import Dict, List, Optional
import logging

def process_manuscript(
    manuscript_path: str,
    output_dir: str,
    config: Optional[Dict[str, str]] = None
) -> bool:
    """Process a manuscript and generate LaTeX output.
    
    Args:
        manuscript_path: Path to the manuscript directory
        output_dir: Directory where output files will be written
        config: Optional configuration overrides
        
    Returns:
        True if processing succeeded, False otherwise
        
    Raises:
        FileNotFoundError: If manuscript directory doesn't exist
        ValueError: If configuration is invalid
    """
    logger = logging.getLogger(__name__)
    
    if not Path(manuscript_path).exists():
        raise FileNotFoundError(f"Manuscript directory not found: {manuscript_path}")
    
    # Implementation details...
    logger.info(f"Successfully processed manuscript: {manuscript_path}")
    return True
```

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/              # Unit tests for individual modules
├── integration/       # Integration tests for workflows
├── fixtures/          # Test data and fixtures
└── conftest.py       # Pytest configuration
```

### Writing Tests
```python
import pytest
from pathlib import Path
from rxiv_maker.processors import MarkdownProcessor

class TestMarkdownProcessor:
    def test_process_basic_markdown(self):
        """Test basic markdown processing."""
        processor = MarkdownProcessor()
        result = processor.process("# Hello World")
        assert "Hello World" in result
    
    @pytest.mark.parametrize("input_text,expected", [
        ("# Title", "\\section{Title}"),
        ("## Subtitle", "\\subsection{Subtitle}"),
    ])
    def test_heading_conversion(self, input_text, expected):
        """Test heading conversion with multiple cases."""
        processor = MarkdownProcessor()
        result = processor.process(input_text)
        assert expected in result
```

### Test Categories
- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test end-to-end workflows
- **Regression Tests**: Prevent previously fixed bugs from returning
- **Performance Tests**: Ensure changes don't degrade performance

## 📚 Documentation Standards

### Documentation Types
1. **Code Documentation**: Inline comments and docstrings
2. **API Documentation**: Auto-generated from docstrings
3. **User Guides**: Step-by-step tutorials and how-tos
4. **Reference**: Complete feature documentation

### Writing Guidelines
- **Clear and Concise**: Use simple language, avoid jargon
- **Examples**: Include practical examples
- **Structure**: Use consistent formatting and organization
- **Accuracy**: Keep documentation synchronized with code

### Markdown Style
```markdown
# Use sentence case for headings

## Code Examples
Always include language specification:

```python
def example_function():
    """Example with proper formatting."""
    return "formatted result"
```

## Lists
- Use bullet points for unordered lists
- Use numbers for sequential steps
- Keep items parallel in structure

## Links
- Use [descriptive text](URL) format
- Prefer relative links for internal documentation
```

## 🏷️ Issue and PR Labels

### Issue Labels
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

### PR Labels
- `breaking change`: Introduces breaking changes
- `feature`: Adds new functionality
- `bugfix`: Fixes a bug
- `docs`: Documentation only changes
- `refactor`: Code refactoring
- `tests`: Adding or updating tests

## 🚀 Release Process

### Versioning
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow
1. **Update CHANGELOG.md**: Document all changes
2. **Version Bump**: Update version in relevant files
3. **Create Release**: GitHub release with notes
4. **PyPI Upload**: Automated via GitHub Actions

## 🎯 Project Priorities

### Current Focus Areas
1. **Stability**: Robust error handling and testing
2. **User Experience**: Better documentation and examples
3. **Performance**: Faster builds and processing
4. **Platform Support**: Cross-platform compatibility

### Long-term Goals
- Enhanced template system
- Real-time preview capabilities
- Plugin architecture
- Web-based editor interface

## ❓ Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Email**: Contact maintainers for sensitive issues

### Response Times
- **Bug Reports**: 2-3 business days
- **Feature Requests**: 1 week
- **Pull Reviews**: 3-5 business days
- **Security Issues**: 24 hours

## 🙏 Recognition

### Contributors
All contributors are recognized in:
- GitHub contributors page
- CHANGELOG.md for significant contributions
- Special mentions in release notes

### Code of Conduct
This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## 📞 Contact

- **Maintainers**: See [CODEOWNERS](.github/CODEOWNERS)
- **Security Issues**: See [SECURITY.md](SECURITY.md)
- **General Questions**: Use GitHub Discussions

Thank you for contributing to Rxiv-Maker! Your efforts make scientific publishing more accessible and efficient for researchers worldwide. 🚀
