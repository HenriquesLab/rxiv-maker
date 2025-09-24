# Visual Test Manuscripts

This directory contains manuscript examples specifically designed for **visual and functional testing** of Rxiv-Maker features. These are not meant to be user-facing examples, but rather comprehensive test cases for ensuring specific functionality works correctly.

## Structure

### `figure-positioning/`
Comprehensive manuscript for testing figure positioning functionality including:
- All figure positioning parameters (`tex_position="t"`, `"b"`, `"h"`, `"H"`, `"p"`, etc.)
- Width specifications (linewidth, textwidth, percentages, decimals)
- Two-column spanning figures
- Ready vs generated figure handling
- Panel reference formatting
- Python code execution commands
- Blindtext placeholder commands

This manuscript was created to address and test fixes for issues reported by users, particularly Guillaume's figure positioning problems.

## Usage

These manuscripts are integrated into the test suite via:
- `tests/e2e/test_visual_manuscripts.py` - End-to-end testing of visual features
- `tests/regression/test_guillaume_issues.py` - Regression testing for specific reported issues

To manually test visual features:
```bash
# Test figure positioning
cd tests/visual/figure-positioning
rxiv pdf .

# Or from project root
rxiv pdf tests/visual/figure-positioning
```

## When to Add New Visual Tests

Add new manuscripts to this directory when you need to:
- Test complex visual layouts or positioning
- Create comprehensive examples of specific features
- Reproduce and test fixes for reported visual issues
- Validate end-to-end workflows with realistic content

## Related Documentation

- [User Guide](../../docs/user_guide.md) - For user-facing examples
- [Figures Guide](../../docs/figures-guide.md) - Figure usage documentation
- [Developer Guide]() - Development workflows