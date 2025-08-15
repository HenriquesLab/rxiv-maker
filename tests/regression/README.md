# Guillaume Issues Regression Tests

This document describes the regression tests created to address specific issues raised by Guillaume.

## Issues Covered

### Issue #96: CLI Path Resolution Problems
**Problem**: Manuscript file lookup issues - the system was looking for `01_MAIN.md` in the parent folder instead of the manuscript folder.

**Tests**:
- `TestPathResolution.test_manuscript_file_lookup_in_correct_directory`
- `TestPathResolution.test_manuscript_file_lookup_with_environment_variable`
- `TestPathResolution.test_figure_path_resolution`
- `TestPathResolution.test_working_directory_independence`

### Issue #97: Google Colab Argument Parsing Issues
**Problem**: CLI argument parsing failures in Google Colab with error "Got unexpected extra argument (paper)".

**Tests**:
- `TestCLIArgumentParsing.test_clean_command_with_unexpected_argument`
- `TestCLIArgumentParsing.test_clean_command_argument_validation`
- `TestCLIArgumentParsing.test_pdf_command_argument_parsing`

### PR #98: Widget Authors Cleared When Adding Affiliations
**Problem**: In the Jupyter widget interface, authors were being cleared when users added affiliations.

**Tests**:
- `TestWidgetAuthorBehavior.test_author_widget_preservation_on_affiliation_add`
- `TestWidgetAuthorBehavior.test_widget_state_consistency`
- `TestWidgetInteractionsWithPlaywright.*` (all Playwright-based widget tests)

## Test Categories

### 1. CLI Argument Parsing Tests
Tests CLI command argument handling to ensure compatibility with Google Colab.

### 2. Path Resolution Tests
Tests file and directory path resolution to ensure correct manuscript file discovery.

### 3. Widget Behavior Tests
Tests Jupyter widget behavior using both mocking and Playwright for browser automation.

### 4. Google Colab Integration Tests
Tests specific Google Colab environment compatibility.

### 5. Error Message Quality Tests
Tests that error messages are helpful and actionable for debugging.

### 6. Playwright Widget Tests
Browser automation tests that simulate real widget interactions in a Colab-like environment.

## Running the Tests

### Run All Guillaume Issue Tests
```bash
uv run python -m pytest tests/regression/test_guillaume_issues.py -v
```

### Run Specific Test Categories
```bash
# CLI argument parsing tests
uv run python -m pytest tests/regression/test_guillaume_issues.py::TestCLIArgumentParsing -v

# Path resolution tests
uv run python -m pytest tests/regression/test_guillaume_issues.py::TestPathResolution -v

# Widget behavior tests (no Playwright)
uv run python -m pytest tests/regression/test_guillaume_issues.py::TestWidgetAuthorBehavior -v

# Playwright widget tests (requires browser)
uv run python -m pytest tests/regression/test_guillaume_issues.py::TestWidgetInteractionsWithPlaywright -v
```

### Skip Playwright Tests (if browsers not available)
```bash
uv run python -m pytest tests/regression/test_guillaume_issues.py -v -m "not playwright"
```

## Playwright Tests

The Playwright tests simulate real browser interactions to test widget behavior:

1. **Widget Loading**: Tests that widgets load properly in a Colab-like environment
2. **State Persistence**: Tests that widget state persists across interactions
3. **IPython Compatibility**: Tests compatibility with IPython/Jupyter widgets
4. **Environment Detection**: Tests Google Colab environment detection

These tests create HTML pages that simulate the widget interface and use browser automation to verify:
- Authors are not cleared when adding affiliations
- Widget state is preserved during interactions
- The interface works correctly in different environments

## Prerequisites

### For Standard Tests
- Python 3.11+
- pytest
- All rxiv-maker dependencies

### For Playwright Tests
- Playwright Python package
- Playwright browsers (automatically installed)

Install with:
```bash
uv add playwright pytest-playwright
uv run playwright install
```

## Test Structure

Each test class focuses on a specific aspect of Guillaume's reported issues:

- **TestCLIArgumentParsing**: CLI command argument handling
- **TestPathResolution**: File and directory path resolution
- **TestWidgetAuthorBehavior**: Widget state management (mocked)
- **TestGoogleColabIntegration**: Colab-specific environment handling
- **TestErrorMessageQuality**: Error message clarity and helpfulness
- **TestWidgetInteractionsWithPlaywright**: Real browser widget testing

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Guillaume regression tests
  run: |
    uv run python -m pytest tests/regression/test_guillaume_issues.py -v
```

For environments without browser support, skip Playwright tests:
```yaml
- name: Run Guillaume regression tests (no browser)
  run: |
    uv run python -m pytest tests/regression/test_guillaume_issues.py -v -m "not playwright"
```
