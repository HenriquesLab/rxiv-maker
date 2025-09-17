## Supplementary Tables

| **Format** | **Input Extension** | **Processing Method** | **Output Formats** | **Quality** | **Use Case** |
|---------|-----------------|------------------|----------------|---------|----------|
| **Mermaid Diagrams** | `.mmd` | Mermaid CLI | SVG, PNG, PDF | Vector/Raster | Flowcharts, architectures |
| **Python and R Figures** | `.py`, `.R` | Script execution | PNG, PDF, SVG | Publication | Data visualisation |
| **Static Images** | `.png`, `.jpg`, `.svg` | Direct inclusion | Same format | Original | Photographs, logos |
| **LaTeX Graphics** | `.tex`, `.tikz` | LaTeX compilation | PDF | Vector | Mathematical diagrams |
| **Data Files** | `.csv`, `.json`, `.xlsx` | Python and R processing | Via scripts | Computed | Raw data integration |

{#stable:figure-formats} **Supported Figure Generation Methods.** Comprehensive overview of the framework's figure processing capabilities, demonstrating support for both static and dynamic content generation with emphasis on reproducible computational graphics.

| **Tool** | **Type** | **Markdown** | **Primary Use Case** | **Key Strengths** | **Open Source** |
|----------|----------|--------------|-------------------|-------------------|-----------------|
| **Rxiv-Maker** | Pipeline | Excellent | Reproducible preprints | Local-first execution, intelligent caching, rich CLI | Yes |
| **Overleaf** [@Overleaf2024] | Web Editor | Limited | Collaborative LaTeX | Real-time collaboration, rich templates, cloud-based | Freemium |
| **Quarto** [@Quarto2024] | Publisher | Native | Multi-format publishing | Polyglot support, multiple outputs, scientific focus | Yes |
| **Manubot** [@himmelstein2019] | Collaborative | Native | Version-controlled writing | Automated citations, transparent collaboration, Git-based | Yes |
| **Pandoc** [@pandoc2020] | Converter | Excellent | Format conversion | Universal format support, extensible filters | Yes |
| **Typst** [@Typst2024] | Typesetter | Good | Modern typesetting | Fast compilation, modern syntax, growing ecosystem | Yes |
| **Bookdown** [@Xie2016_bookdown] | Publisher | R Markdown | Academic books | Cross-references, multiple formats | Yes |
| **Direct LaTeX** | Typesetter | None | Traditional publishing | Full control, established workflows, mature ecosystem | Yes |

{#stable:tool-comparison} **Comprehensive Comparison of Manuscript Preparation Tools.** This comparison positions each tool within the scientific publishing ecosystem based on current capabilities and primary strengths. Rxiv-Maker specialises in reproducible preprint workflows with local-first execution, automated figure generation, and developer-centric features. Overleaf is a popular collaborative LaTeX platform, whilst Quarto excels at multi-format computational publishing. The comparison reflects that different tools address distinct workflow requirements: collaborative editing (Overleaf), multi-format output (Quarto), version-controlled writing (Manubot), and reproducible preprint generation (Rxiv-Maker).

| **Deployment Method** | **Environment** | **Dependencies** | **Collaboration** | **Ease of Use** | **Reproducibility** |
|-------------------|-------------|-------------|--------------|-------------|----------------|
| **Local Installation** | Local machine | Python + LaTeX | Git-based | High | Excellent |
| **Docker (Separate)** | Container | Docker only | Git-based | Medium | Excellent |
| **Manual LaTeX** | Local machine | Full LaTeX suite | Git-based | Low | Variable |

{#stable:deployment-options} **Rxiv-Maker Deployment Strategies.** Comparison of available compilation methods, with local installation as the primary recommended approach and containerised execution available through the separate docker-rxiv-maker repository for specialised deployment needs.

| **Markdown Element** | **LaTeX Equivalent** | **Description** |
|------------------|------------------|-------------|
| *Basic Text Formatting* | | |
| `**bold text**` | `\textbf{bold text}` | Bold formatting for emphasis |
| `*italic text*` | `\textit{italic text}` | Italic formatting for emphasis |
| `~subscript~` | `\textsubscript{subscript}` | Subscript formatting (H~2~O, CO~2~) |
| `^superscript^` | `\textsuperscript{superscript}` | Superscript formatting (E=mc^2^, x^n^) |
| *Document Structure* | | |
| `# Header 1` | `\section{Header 1}` | Top-level section heading |
| `## Header 2` | `\subsection{Header 2}` | Second-level section heading |
| `### Header 3` | `\subsubsection{Header 3}` | Third-level section heading |
| *Lists* | | |
| `- list item` | `\begin{itemize}\item...\end{itemize}` | Unordered list |
| `1. list item` | `\begin{enumerate}\item...\end{enumerate}` | Ordered list |
| *Links and URLs* | | |
| `[link text](url)` | `\href{url}{link text}` | Hyperlink with custom text |
| `https://example.com` | `\url{https://example.com}` | Bare URL |
| *Citations* | | |
| `@citation` | `\cite{citation}` | Single citation reference |
| `[@cite1;@cite2]` | `\cite{cite1,cite2}` | Multiple citation references |
| **Cross-References** | | |
| `@fig:label` | `\ref{fig:label}` | Figure cross-reference |
| `@sfig:label` | `\ref{sfig:label}` | Supplementary figure cross-reference |
| `@table:label` | `\ref{table:label}` | Table cross-reference |
| `@stable:label` | `\ref{stable:label}` | Supplementary table cross-reference |
| `@eq:label` | `\eqref{eq:label}` | Equation cross-reference |
| `@snote:label` | `\sidenote{label}` | Supplement note cross-reference |
| *Tables and Figures* | | |
| Markdown table | `\begin{table}...\end{table}` | Table with automatic formatting |
| Image with caption | `\begin{figure}...\end{figure}` | Figure with separate caption |
| *Document Control* | | |
| `<!-- comment -->` | `% comment` | Comments (converted to LaTeX style) |
| `<newpage>` | `\newpage` | Manual page break control |
| `<clearpage>` | `\clearpage` | Page break with float clearing |

{#stable:markdown-syntax} **Rxiv-Maker Markdown Syntax Overview.** Comprehensive mapping of markdown elements to their LaTeX equivalents, demonstrating the automated translation system that enables researchers to write in familiar markdown syntax whilst producing professional LaTeX output.

<newpage>

## Supplementary Notes

{#snote:figure-generation} **Programmatic Figure Generation and Computational Reproducibility**

Rxiv-Maker's figure generation capabilities demonstrate automated processing pipelines maintaining transparent connections between source data and final visualisations whilst ensuring computational reproducibility. The system supports two primary methodologies: Mermaid diagram processing and Python/R-based data visualisation, each addressing distinct requirements within scientific publishing workflows.

Mermaid diagram processing leverages the Mermaid CLI to convert text-based specifications into publication-ready graphics. This approach enables version-controlled diagram creation where complex flowcharts, system architectures, and conceptual models are specified using intuitive syntax and automatically rendered into multiple output formats. The system generates SVG, PNG, and PDF variants accommodating different compilation requirements whilst maintaining vector quality. This automation eliminates manual effort for diagram creation and updates, ensuring modifications are immediately reflected in the final document.

Script-based figure generation represents computational reproducibility where analytical scripts execute during compilation to generate figures directly from source data. This integration ensures visualisations remain synchronised with underlying datasets and analytical methods, eliminating outdated or inconsistent graphics. The system executes image generation scripts within the compilation environment, automatically detecting generated files and incorporating them into document structure. This approach transforms figures from static illustrations into dynamic, reproducible computational artefacts enhancing scientific rigour.

{#snote:mathematical-formulas} **Mathematical Formula Support and LaTeX Integration**

Rxiv-Maker integrates mathematical notation by translating markdown-style expressions into publication-ready LaTeX mathematics. This enables researchers to author complex mathematical content using familiar syntax whilst benefiting from LaTeX's superior typesetting capabilities.

Inline mathematical expressions use dollar sign delimiters (`$...$`), enabling formulas such as $E = mc^2$ or $\alpha = \frac{\beta}{\gamma}$ to be embedded within text. The conversion system preserves expressions during markdown-to-LaTeX transformation, ensuring mathematical notation maintains proper formatting and spacing.

Display equations utilise double dollar delimiters (`$$...$$`) for prominent mathematical expressions requiring centred presentation. Complex equations such as the Schrödinger equation:

$$i\hbar\frac{\partial}{\partial t}\Psi(\mathbf{r},t) = \hat{H}\Psi(\mathbf{r},t)$$

or the Navier-Stokes equations:

$$\rho\left(\frac{\partial \mathbf{v}}{\partial t} + \mathbf{v} \cdot \nabla \mathbf{v}\right) = -\nabla p + \mu \nabla^2 \mathbf{v} + \mathbf{f}$$

demonstrate the framework's capability to handle sophisticated mathematical typography, including Greek letters, partial derivatives, vector notation, and complex fraction structures.

The system supports LaTeX's mathematical environments by directly including LaTeX code blocks. This hybrid approach enables simple markdown syntax for straightforward expressions whilst retaining access to LaTeX's full capabilities for complex multi-line derivations.

Mathematical expressions within figure captions, table entries, and cross-references are automatically processed, ensuring consistent typography throughout documents. The framework's content protection system preserves mathematical expressions during multi-stage conversion, preventing unwanted modifications.

Statistical notation commonly required in manuscripts is supported, including confidence intervals $\mu \pm \sigma$, probability distributions $P(X \leq x)$, and significance levels $p < 0.05$. Complex expressions involving summations $\sum_{i=1}^{n} x_i$, integrals $\int_{-\infty}^{\infty} f(x) dx$, and matrix operations $\mathbf{A}^{-1}\mathbf{b} = \mathbf{x}$ are rendered with appropriate spacing.

{#snote:caching-validation} **Intelligent Caching and Validation Systems**

Rxiv-Maker implements sophisticated caching mechanisms that significantly accelerate manuscript compilation through content-based change detection and selective regeneration. The caching system operates at multiple levels: file-level checksums track modifications to source documents, whilst content-based hashing monitors changes within executable code blocks and figure generation scripts.

The figure caching system maintains checksums for Python, R, and Mermaid source files, comparing current content against cached versions to determine whether regeneration is necessary. This approach eliminates redundant computation whilst ensuring figures remain synchronised with their source code. Cache invalidation occurs automatically when dependencies change, maintaining consistency without manual intervention.

The comprehensive validation framework provides multi-layered quality assurance through LaTeX error parsing with contextual error messages, figure validation that verifies file existence and format compatibility, and citation validation with DOI resolution through CrossRef and DataCite APIs. The system generates detailed diagnostic reports that guide users through error resolution, significantly reducing debugging complexity.

Dependency validation ensures all required components (LaTeX distributions, Python packages, R libraries, Node.js modules) are properly installed and configured before manuscript processing begins. The validation system provides automated installation suggestions for missing dependencies, streamlining setup procedures across different computing environments.

{#snote:latex-injection} **Direct LaTeX Integration and Advanced Typesetting**

While Rxiv-Maker's markdown-to-LaTeX conversion handles the majority of scientific publishing requirements, the framework provides direct LaTeX injection capabilities through `{{tex: ...}}` blocks for sophisticated typesetting scenarios that exceed markdown's capabilities. This approach offers researchers an "escape hatch" to access LaTeX's full typesetting power when needed, while maintaining the simplicity of markdown for routine content.

Direct LaTeX injection is particularly valuable for complex tables with custom formatting, advanced mathematical layouts, specialized scientific notation, and publication-quality data presentation that requires precise control over spacing, alignment, and typography. The following example demonstrates a measurement data table utilizing LaTeX's professional table formatting capabilities:

{{tex:
\begin{stable}[h!]
\centering
\begin{tabular}{|l|c|c|r|}
\hline
\textbf{Sample} & \textbf{Temperature} & \textbf{Pressure} & \textbf{Yield} \\
 & \textbf{(K)} & \textbf{(MPa)} & \textbf{(\%)} \\
\hline
Control & $298.15 \pm 0.05$ & $0.101 \pm 0.001$ & $85.3 \pm 2.1$ \\
Sample A & $373.15 \pm 0.10$ & $0.250 \pm 0.005$ & $92.7 \pm 1.8$ \\
Sample B & $423.15 \pm 0.15$ & $0.500 \pm 0.010$ & $96.1 \pm 1.4$ \\
Sample C & $473.15 \pm 0.20$ & $1.000 \pm 0.020$ & $88.9 \pm 2.3$ \\
\hline
\multicolumn{3}{|l|}{Mean $\pm$ Standard Deviation} & $90.8 \pm 4.5$ \\
\hline
\end{tabular}
\caption{\textbf{Example Measurement Results with Statistical Analysis.} The data shown is purely illustrative and does not represent actual experimental results.}
\label{stable:experimental-results}
\end{stable}
}}

This example showcases LaTeX features including professional table borders (`\hline`), custom column alignment specifications (`|l|c|c|r|`), multi-column headers, mathematical expressions with proper spacing, and scientific notation with uncertainties. Such precise formatting control enables researchers to meet the exacting typographical standards required for high-impact scientific publications while maintaining computational reproducibility through the framework's local execution environment.

<newpage>

## Supplementary Figures 

![](FIGURES/SFigure__arxiv_growth.pdf)
{#sfig:arxiv_growth width="100%"} **The growth of preprint submissions on the arXiv server from 1991 to 2025.** The data, sourced from arXiv's public statistics, is plotted using a Python script integrated into our Rxiv-Maker pipeline. This demonstrates the system's capacity for reproducible, data-driven figure generation directly within the publication workflow.

![](FIGURES/SFigure__preprint_trends.pdf)
{#sfig:preprint_trends width="100%"} **Preprint Submission Trends Across Multiple Servers (2018-2025).** The figure displays the annual number of preprints indexed by PubMed from major repositories, including arXiv, bioRxiv, and medRxiv. Data was collected from publicly available sources [@PubMedByYear2025] and visualised using a reproducible R script within the Rxiv-Maker pipeline. This approach ensures that the figure remains synchronised with the latest available data and supports transparent, data-driven scientific reporting.

![](FIGURES/SFigure__architecture.pdf)
{#sfig:architecture width="90%"} **Detailed System Architecture and Processing Layers.** Comprehensive technical diagram showing the complete Rxiv-Maker architecture, including input layer organisation, processing engine components (parsers, converters, generators), compilation infrastructure, output generation, and deployment methodology integration. This figure illustrates the modular design that enables independent development and testing of system components across different deployment environments.

![](FIGURES/SFigure__vscode_extension.png)
{#sfig:vscode_extension width="100%"} **Visual Studio Code Extension Syntax Highlighting Demonstration.** Screenshot showing the comprehensive syntax highlighting capabilities of the Rxiv-Maker VS Code extension. 