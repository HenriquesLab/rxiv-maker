# Comprehensive Figure Positioning and Blindtext Examples

## Abstract

This manuscript demonstrates comprehensive figure positioning options in Rxiv-Maker, including all `tex_position` parameters, width specifications, two-column spanning figures, and the new blindtext command support. It serves as a complete reference for users implementing complex figure layouts and placeholder text generation.

## Introduction

Modern scientific publishing requires precise control over figure placement and document structure. This example manuscript demonstrates every figure positioning option available in Rxiv-Maker, from basic single-column figures to complex two-column spanning layouts.

{{blindtext}}

The examples in this document cover Guillaume's reported issues that have been resolved, including:
- Ready figure loading from single `FIGURES/` directory
- Dedicated page positioning with `tex_position="p"`
- Full-width figure handling with proper caption formatting
- Panel reference formatting without unwanted spaces

## Figure Positioning Examples

### Basic Positioning Options

#### Example 1: Top Position (Recommended Default)
This figure uses `tex_position="t"` to place the figure at the top of the page:

![](FIGURES/ReadyFig.png)
{#fig:ready_top tex_position="t"} **Ready Figure with Top Positioning.** This demonstrates a ready figure loaded directly from the FIGURES/ directory without requiring subdirectory duplication. The figure is positioned at the top of the page using `tex_position="t"`.

{{Blindtext}}

#### Example 2: Bottom Position
This figure uses `tex_position="b"` to place the figure at the bottom of the page:

![](FIGURES/Figure__positioning_test.png)
{#fig:generated_bottom tex_position="b"} **Generated Figure with Bottom Positioning.** This demonstrates a generated figure that uses the subdirectory structure (Figure__positioning_test/Figure__positioning_test.png). The figure is positioned at the bottom using `tex_position="b"`.

{{Blindtext}}

#### Example 3: Here Position
This figure uses `tex_position="h"` to place the figure approximately where it appears in the text:

![](FIGURES/ReadyFig.png)
{#fig:ready_here tex_position="h"} **Figure with Here Positioning.** Using `tex_position="h"` attempts to place the figure at the current position in the text, though LaTeX may adjust based on space constraints.

{{Blindtext}}

#### Example 4: Force Here Position
This figure uses `tex_position="H"` to force exact placement (requires float package):

![](FIGURES/ReadyFig.png)
{#fig:ready_force_here tex_position="!ht" width="0.8"} **Figure with Force Here Positioning.** Using `tex_position="H"` forces the figure to appear exactly at this position. Note the reduced width of 0.8 linewidth.

{{Blindtext}}

### Dedicated Page Examples (Guillaume's Fixed Issue)

#### Example 5: Dedicated Page with Full Width
This addresses Guillaume's issue where `tex_position="p"` with `width="\textwidth"` was incorrectly using two-column layout:

{{Blindtext}}

![](FIGURES/Figure__positioning_test.png)
{#fig:dedicated_fullwidth tex_position="p" width="\textwidth"} **Dedicated Page Figure.** Uses `tex_position="p"` with `width="\textwidth"` to create dedicated page. Guillaume's reported issue.

{{Blindtext}}

#### Example 6: Dedicated Page with Custom Width (0.8)
This addresses Guillaume's scaling issue where `tex_position="p"` failed with non-textwidth values:

{{Blindtext}}

![](FIGURES/ReadyFig.png)
{#fig:dedicated_custom_80 tex_position="p" width="0.8"} **Dedicated Page Figure with 0.8 Width.** This demonstrates that `tex_position="p"` now works correctly with custom widths like 0.8 linewidth, resolving Guillaume's reported scaling issues.

{{Blindtext}}

#### Example 7: Dedicated Page with Percentage Width
Testing percentage width with dedicated page positioning:

{{Blindtext}}

![](FIGURES/Figure__positioning_test.png)
{#fig:dedicated_percentage tex_position="p" width="90%"} **Dedicated Page Figure with 90% Width.** Using percentage widths (converted to decimal linewidth values) with dedicated page positioning.

{{Blindtext}}

### Two-Column Spanning Figures

#### Example 8: Auto-Detected Two-Column Spanning
This figure automatically uses two-column spanning due to `width="\textwidth"` without explicit positioning:

{{Blindtext}}

![](FIGURES/Figure__positioning_test.png)
{#fig:twocol_auto width="\textwidth"} **Auto-Detected Two-Column Spanning Figure.** When `width="\textwidth"` is specified without `tex_position="p"`, the figure automatically spans both columns using the `figure*` environment with enhanced caption formatting.

{{Blindtext}}

#### Example 9: Explicit Two-Column Spanning with Top Position
This figure explicitly spans two columns with top positioning preference:

{{Blindtext}}

![](FIGURES/Figure__positioning_test.png)
{#fig:twocol_explicit tex_position="t" width="\textwidth"} **Explicit Two-Column Figure with Top Position.** Using `tex_position="t"` with `width="\textwidth"` creates a two-column spanning figure positioned at the top of the page.

{{Blindtext}}

### Panel Reference Examples (Guillaume's Fixed Issue)

The following demonstrates the fixed panel referencing that removes unwanted spaces:

As shown in (@fig:ready_top A), panel references now work correctly. Compare with (@fig:generated_bottom B) and (@fig:dedicated_fullwidth C). Notice that there are no spaces between the figure number and panel letter: (@fig:twocol_auto A), (@fig:twocol_explicit B).

For supplementary figures, the same fix would apply to panel references when supplementary figures are present in the manuscript.

### Advanced Positioning Combinations

#### Example 10: Force Top with Override
Using `tex_position="!t"` to override LaTeX's spacing rules:

{{Blindtext}}

![](FIGURES/ReadyFig.png)
{#fig:force_top tex_position="!t" width="0.7"} **Force Top Position Override.** The `!t` parameter overrides LaTeX's float placement preferences and forces top placement even when spacing might be suboptimal.

{{Blindtext}}

#### Example 11: Top or Here Preference
Using `tex_position="ht"` for flexible positioning:

{{Blindtext}}

![](FIGURES/ReadyFig.png)
{#fig:top_or_here tex_position="!ht" width="0.9"} **Top or Here Flexible Positioning.** The `ht` parameter allows LaTeX to choose between top or here positioning based on what works best for the page layout.

{{Blindtext}}

## Blindtext Command Examples

The new blindtext commands provide convenient placeholder text generation:

### Basic Blindtext
{{blindtext}}

### Paragraph Blindtext
{{Blindtext}}

These commands are particularly useful during manuscript preparation when you need placeholder content to test layouts and formatting.

## Python Execution Examples

The new Python execution feature allows dynamic content generation directly in markdown:

### Inline Python Calculations

Simple mathematical calculations can be embedded inline: The result of $2^8$ is {py: 2**8}, and the sum of the first 10 integers is {py: sum(range(1, 11))}.

### Block Python Code with Output

Complex calculations can be performed in code blocks:

{{py:
# Statistical analysis example
import statistics
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
mean_val = statistics.mean(data)
std_val = statistics.stdev(data)
print(f"Dataset: {data}")
print(f"Mean: {mean_val:.2f}")
print(f"Standard Deviation: {std_val:.2f}")
}}

### Variable Persistence

Variables persist between code blocks, enabling complex workflows:

{{py:
# Set up experimental parameters
sample_size = 100
trials = 5
success_rate = 0.85
print(f"Experimental setup: {sample_size} samples, {trials} trials, {success_rate} success rate")
}}

The expected number of successes is {py: sample_size * success_rate} across all trials.

### Data Processing Example

{{py:
# Process some experimental data
results = []
for trial in range(trials):
    expected_successes = int(sample_size * success_rate)
    results.append(expected_successes)

print(f"Trial results: {results}")
print(f"Total successes across all trials: {sum(results)}")
print(f"Average successes per trial: {sum(results)/len(results):.1f}")
}}

### Mathematical Operations

Complex mathematical expressions: {py: (2**10 + 3**5) / (4 + 1)} and scientific notation: {py: 1.23e-4 * 1000}.

### List Processing

{{py:
# Generate a list of squares
squares = [x**2 for x in range(1, 6)]
print(f"Squares of 1-5: {squares}")

# Find prime numbers up to 20
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [n for n in range(2, 21) if is_prime(n)]
print(f"Prime numbers 2-20: {primes}")
}}

### Security Features

Python execution includes comprehensive security restrictions to prevent dangerous operations. Attempts to import restricted modules or use dangerous functions are blocked:

{{py:
# This will be blocked for security
import os
}}

Similarly, file system access and other potentially dangerous operations are prevented through sandboxing and whitelist-based security validation.

## Technical Implementation Notes

### Ready vs Generated Figures

This example demonstrates both figure loading methods:

1. **Ready Figures**: `ReadyFig.png` is stored directly in `FIGURES/` and loaded without subdirectory structure
2. **Generated Figures**: `Figure__positioning_test.py` creates figures in the `FIGURES/Figure__positioning_test/` subdirectory

### Positioning Logic Summary

The figure positioning system now correctly handles:

- **Dedicated Page (`tex_position="p"`)**: Always uses regular `figure` environment regardless of width
- **Two-Column Spanning**: Auto-detected for `width="\textwidth"` when not using dedicated page positioning  
- **Custom Widths**: Properly converted from percentages and decimal values
- **Caption Formatting**: Enhanced formatting for two-column figures with long captions

### Command Processing

The blindtext commands are processed early in the markdown pipeline:
- `{{blindtext}}` → `\blindtext`
- `{{Blindtext}}` → `\Blindtext`

Future planned commands include:
- `{{py: code}}` → Execute Python code and insert output
- `{py: code}` → Execute Python code inline

## Conclusions

This comprehensive example demonstrates that all of Guillaume's reported figure positioning issues have been resolved:

1. Ready figures load from single `FIGURES/` location without subdirectory duplication
2. Panel references render without unwanted spaces: (@fig:ready_top A) instead of (Fig. 1 A)  
3. `tex_position="p"` correctly creates dedicated pages with any width specification
4. Two-column spanning works automatically for full-width figures
5. New blindtext commands provide convenient placeholder text generation

The figure positioning system now provides complete control over layout while maintaining backward compatibility and following LaTeX best practices.

{{blindtext}}