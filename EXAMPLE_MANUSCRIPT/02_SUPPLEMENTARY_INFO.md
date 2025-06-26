## Supplementary Tables

| **Format** | **Input Extension** | **Processing Method** | **Output Formats** | **Quality** | **Use Case** |
|---------|-----------------|------------------|----------------|---------|----------|
| **Mermaid Diagrams** | `.mmd` | Mermaid CLI | SVG, PNG, PDF | Vector/Raster | Flowcharts, architectures |
| **Python Figures** | `.py` | Script execution | PNG, PDF, SVG | Publication | Data visualisation |
| **Static Images** | `.png`, `.jpg`, `.svg` | Direct inclusion | Same format | Original | Photographs, logos |
| **LaTeX Graphics** | `.tex`, `.tikz` | LaTeX compilation | PDF | Vector | Mathematical diagrams |
| **Data Files** | `.csv`, `.json`, `.xlsx` | Python processing | Via scripts | Computed | Raw data integration |

{#stable:figure-formats} **Supported Figure Generation Methods.** Comprehensive overview of the framework's figure processing capabilities, demonstrating support for both static and dynamic content generation with emphasis on reproducible computational graphics.

| **Tool** | **Type** | **Markdown** | **Primary Use Case** | **Key Strengths** | **Open Source** |
|----------|----------|--------------|-------------------|-------------------|-----------------|
| **Rxiv-Maker** | Pipeline | Excellent | Preprint servers | GitHub Actions integration, automated workflows | Yes |
| **Overleaf** [@Overleaf2024] | Web Editor | Limited | Academic publishing | Real-time collaboration, rich templates | Freemium |
| **Quarto** [@Quarto2024] | Publisher | Native | Multi-format publishing | Polyglot support, multiple outputs | Yes |
| **Pandoc** [@MacFarlane2022] | Converter | Excellent | Format conversion | Universal format support, extensible | Yes |
| **MyST-Parser** [@Laursen2021_myst] | Extension | Native | Technical documentation | Sphinx ecosystem, rich directives | Yes |
| **Jupyter Book** [@ExecutableBooks2020] | Publisher | Native | Educational content | Interactive content, executable books | Yes |
| **Typst** [@Typst2024] | Typesetter | Good | Modern typesetting | Fast compilation, modern syntax | Yes |
| **Bookdown** [@Xie2016_bookdown] | Publisher | R Markdown | Academic books | Cross-references, multiple formats | Yes |
| **Direct LaTeX** | Typesetter | Limited | Traditional publishing | Ultimate control, established workflows | Yes |

{#stable:tool-comparison} **Comprehensive Comparison of Manuscript Preparation Tools.** This comparison provides an exhaustive overview of available tools for scientific manuscript preparation, positioning each within the broader ecosystem of academic publishing workflows. Rxiv-Maker is designed as a specialized solution optimizing for preprint server submissions, complementing rather than replacing established tools like Overleaf for general LaTeX collaboration or Quarto for multi-format publishing. The comparison highlights that different tools excel in distinct contexts: Overleaf dominates collaborative LaTeX editing, Quarto excels at multi-format computational publishing, and Rxiv-Maker streamlines the specific workflow of preparing reproducible preprints for submission to arXiv, bioRxiv, and medRxiv.

| **Deployment Method** | **Environment** | **Dependencies** | **Collaboration** | **Ease of Use** | **Reproducibility** |
|-------------------|-------------|-------------|--------------|-------------|----------------|
| **GitHub Actions** | Cloud CI/CD | None (cloud) | Automatic | Very High | Perfect |
| **Google Colab** | Web browser | None (cloud) | Shared notebooks | Very High | High |
| **Local Python** | Local machine | Python + LaTeX | Git-based | Medium | Good |
| **Manual LaTeX** | Local machine | Full LaTeX suite | Git-based | Low | Variable |

{#stable:deployment-options} **Rxiv-Maker Deployment Strategies.** Comparison of available compilation methods, highlighting the flexibility of the framework in accommodating different user preferences and technical environments whilst maintaining consistent output quality.

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

The technical architecture underlying Rxiv-Maker's figure generation capabilities demonstrates how automated processing pipelines can maintain transparent connections between source data and final visualisations whilst ensuring computational reproducibility. The system supports two primary methodologies for figure creation: Mermaid diagram processing and Python-based data visualisation, each addressing distinct requirements within the scientific publishing workflow.

Mermaid diagram processing leverages the Mermaid CLI to convert text-based diagram specifications into publication-ready graphics. This approach enables version-controlled diagram creation where complex flowcharts, system architectures, and conceptual models can be specified using intuitive syntax and automatically rendered into multiple output formats. The system generates SVG, PNG, and PDF variants to accommodate different compilation requirements whilst maintaining vector quality where appropriate. This automation eliminates the manual effort traditionally required for diagram creation and updates, whilst ensuring that modifications to diagram specifications are immediately reflected in the final document.

Python figure generation represents a more sophisticated approach to computational reproducibility, where analytical scripts are executed during document compilation to generate figures directly from source data. This integration ensures that visualisations remain synchronised with the underlying datasets and analytical methods, eliminating the possibility of outdated or inconsistent graphics persisting in the manuscript. The system executes Python scripts within the compilation environment, automatically detecting generated image files and incorporating them into the document structure. This approach transforms figures from static illustrations into dynamic, reproducible computational artefacts that enhance the scientific rigour of the publication.

{#snote:mathematical-formulas} **Mathematical Formula Support and LaTeX Integration**

The Rxiv-Maker framework seamlessly integrates mathematical notation by automatically translating markdown-style mathematical expressions into publication-ready LaTeX mathematics. This capability enables researchers to author complex mathematical content using familiar syntax whilst benefiting from LaTeX's superior mathematical typesetting capabilities.

Inline mathematical expressions are supported through dollar sign delimiters (`$...$`), enabling simple formulas such as $E = mc^2$ or $\alpha = \frac{\beta}{\gamma}$ to be embedded within narrative text. The conversion system automatically preserves these expressions during the markdown-to-LaTeX transformation, ensuring that mathematical notation maintains proper formatting and spacing according to established typographical conventions.

Display equations utilise double dollar sign delimiters (`$$...$$`) for prominent mathematical expressions that require centered presentation. Complex equations such as the Schrödinger equation:

$$i\hbar\frac{\partial}{\partial t}\Psi(\mathbf{r},t) = \hat{H}\Psi(\mathbf{r},t)$$

or the Navier-Stokes equations:

$$\rho\left(\frac{\partial \mathbf{v}}{\partial t} + \mathbf{v} \cdot \nabla \mathbf{v}\right) = -\nabla p + \mu \nabla^2 \mathbf{v} + \mathbf{f}$$

demonstrate the framework's capability to handle sophisticated mathematical typography, including Greek letters, partial derivatives, vector notation, and complex fraction structures.

The system also supports LaTeX's advanced mathematical environments by directly including LaTeX code blocks. This hybrid approach enables authors to utilise simple markdown syntax for straightforward expressions whilst retaining access to LaTeX's full mathematical typesetting capabilities for complex multi-line derivations:

The framework supports Maxwell's equations and complex mathematical expressions in various formats for flexible scientific notation.

Mathematical expressions within figure captions, table entries, and cross-references are automatically processed, ensuring consistent mathematical typography throughout the document. The framework's content protection system ensures that mathematical expressions are preserved during the multi-stage conversion pipeline, preventing unwanted modifications to delicate mathematical syntax.

Statistical notation commonly required in scientific manuscripts is fully supported, including confidence intervals $\mu \pm \sigma$, probability distributions $P(X \leq x)$, and statistical tests with significance levels $p < 0.05$. Complex expressions involving summations $\sum_{i=1}^{n} x_i$, integrals $\int_{-\infty}^{\infty} f(x) dx$, and matrix operations $\mathbf{A}^{-1}\mathbf{b} = \mathbf{x}$ are rendered with appropriate spacing and sizing.

<newpage>

## Supplementary Figures 

![](FIGURES/SFigure_2.svg)
{#sfig:arxiv-growth width="100%"} **The growth of preprint submissions on the arXiv server from 1991 to 2025.** The data, sourced from arXiv's public statistics, is plotted using a Python script integrated into our Rxiv-Maker pipeline. This demonstrates the system's capacity for reproducible, data-driven figure generation directly within the publication workflow.

![](FIGURES/SFigure_1.svg)
{#sfig:architecture width="80%"} **Detailed System Architecture and Processing Layers.** Comprehensive technical diagram showing the complete Rxiv-Maker architecture, including input layer organisation, processing engine components (parsers, converters, generators), compilation infrastructure, output generation, and deployment methodology integration. This figure illustrates the modular design that enables independent development and testing of system components.


