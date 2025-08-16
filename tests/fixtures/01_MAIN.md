---
title:
  long: "Testing Guillaume's Figure Issues"
  short: "Guillaume Test"
authors:
  - name: "Guillaume Jacquemet"
    affiliation: "University of Testing"
    orcid: "0000-0000-0000-0000"
keywords: ["figure", "positioning", "testing", "ready files"]
acknowledge_rxiv_maker: false
---

# Abstract

This manuscript tests Guillaume's specific figure handling issues and validates the fixes.

## Introduction

This introduction section should appear as "Introduction" not "Main" in the PDF, testing Guillaume's Issue #3.

As shown in (@fig:Fig1 A), panel references should not have spaces. Compare (@fig:Fig1 A) with (@fig:Fig1 B) and (@fig:Fig2 C) for details.

<!-- Guillaume Issue #2: Ready file detection -->
![Ready Figure 1](FIGURES/Fig1.png)
{#fig:Fig1} **Figure 1: Testing ready file detection.** This figure tests whether ready files are properly detected and use direct paths instead of subdirectory format.

<!-- Guillaume Issue #4: Full-page positioning -->
![](FIGURES/Fig2.png)
{#fig:Fig2 width="\textwidth" tex_position="p"} **Figure 2: Full-page positioning test.** This figure should appear on a dedicated page using figure[p] environment, not figure*[p] two-column layout.

## Methods

Regular figure with normal positioning:

![Regular Figure](FIGURES/Fig3.png)
{#fig:Fig3 width="0.8"} **Figure 3: Regular figure.** This figure uses standard positioning and should work normally.

Two-column spanning figure (should use figure*):

![](FIGURES/Fig4.png)
{#fig:Fig4 width="\textwidth"} **Figure 4: Two-column spanning.** This figure should use figure* environment for two-column layout.

## Results

Mixed panel references to test Guillaume Issue #1:
- Panel A: (@fig:Fig1 A) - should render as Fig. 1A
- Panel B: (@fig:Fig1 B) - should render as Fig. 1B  
- Panel C: (@fig:Fig2 C) - should render as Fig. 2C

## Conclusion

This manuscript validates all Guillaume's fixes are working correctly.