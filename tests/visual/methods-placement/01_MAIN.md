## Introduction

This is a test manuscript to verify the **methods_placement** configuration option in rxiv-maker v1.12.1.

The four placement options are:
1. **after_intro** (1) - Methods after Introduction (classic paper style)
2. **after_results** (2) - Methods after Results, before Discussion
3. **after_discussion** (3) - Methods after Discussion, before Bibliography
4. **after_bibliography** (4) - Methods after Bibliography (Nature Methods style - **default**)

This manuscript has Methods authored between Introduction and Results. The placement in the final PDF depends on the `methods_placement` configuration setting.

## Methods

This is the Methods section. When using `methods_placement: "inline"`, this section should appear in the PDF exactly where it appears in this markdown file.

**Key Points:**
- Methods section is written between Introduction and Results
- Should appear in the same position in the generated PDF
- This is the default behavior (most flexible for authors)

**Test verification:**
1. Check that Methods appears after Introduction
2. Check that Methods appears before Results
3. Verify section ordering: Introduction → Methods → Results → Discussion

## Results

This is the Results section. It should appear after the Methods section when using inline placement.

If the Methods section appears before this Results section, the inline placement is working correctly.

## Discussion

This is the Discussion section. When using inline placement, Methods should appear before Results, not here.

If you see the Methods section between Introduction and Results (as authored), the test passes.

## Conclusions

The inline methods placement option allows authors maximum flexibility in organizing their manuscript structure. This is the default behavior in rxiv-maker v1.11.1.
