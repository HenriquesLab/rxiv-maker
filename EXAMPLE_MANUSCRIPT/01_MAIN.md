# Rxiv-Maker: an automated template engine for streamlined scientific publications
<!-- note that this title is not rendered in the PDF, instead the one in the YAML metadata is used -->

## Abstract
Preprint servers accelerate research dissemination, but authors still face complex manuscript preparation without professional typesetting support. Rxiv-Maker enables researchers to create documents using a framework that converts Markdown into publication-standard PDFs through intelligent optimisation. The framework automatically translates markdown text into LaTeX without requiring researchers to write LaTeX code directly. This tool transforms simple documents into dynamic, version-controlled files that integrate seamlessly with modern development workflows and collaborative practices. Rxiv-Maker executes Python and R scripts for on-the-fly figure generation with intelligent caching, ensuring visualisations stay current with data and analyses whilst minimising compilation time. Local-first architecture with comprehensive validation systems and built-in citation management ensures reliable, reproducible builds across platforms, while the conversion process handles mathematical equations and formatting with professional quality. Rxiv-Maker simplifies scientific publishing through developer-friendly tools, promoting clear and open scientific communication. This manuscript showcases Rxiv-Maker's capabilities, serving as a testament to its elegance in action.

## Main

<!-- Introduction -->

Preprint servers like arXiv, bioRxiv, and medRxiv have become central to research communication [@beck2020;@levchenk2024;@Fraser2020_preprint_growth]. As submission rates climb (@sfig:arxiv_growth, @sfig:preprint_trends), researchers now handle tasks once managed by journal production teams [@Vale2015_preprints;@Tenant2016_academic_publishing]. Most manuscript preparation workflows use proprietary formats that work poorly with version control systems, making collaborative research more difficult [@lin2020].

Computational research faces particular challenges because algorithms, analysis methods, and processing pipelines change frequently. In computational biology, researchers struggle to keep manuscripts synchronised with evolving analysis code, leading to publications that don't accurately describe the methods used. 

Bioimage analysis shows these problems clearly: collaborative frameworks [@biaflows2024] and containerised analysis environments [@dl4miceverywhere2024] highlight how important reproducible computational workflows are for scientific publishing.

Rxiv-Maker helps address these challenges by providing a developer-centric framework for reproducible preprint preparation through local-first execution. It generates publication-standard PDFs through intelligent LaTeX processing with sophisticated caching and validation systems. The framework integrates seamlessly with Git workflows and modern development practices whilst maintaining optimal performance through local execution.

Manuscript preparation becomes a transparent, efficient process that provides researchers with professional typesetting capabilities through familiar command-line interfaces. A companion Visual Studio Code extension offers enhanced editing features including syntax highlighting and automated citation management. Researchers can leverage standard development tools and workflows whilst maintaining rigorous version control and reproducibility guarantees. This approach bridges traditional authoring workflows with contemporary best practices in computational research through developer-friendly tooling.

<!-- Example 1: Standard single-column figure positioning -->
<!-- tex_position="t" places the figure at the top of the page (recommended default) -->
<!-- width not specified defaults to \linewidth (full column width) -->
![](FIGURES/Figure__system_diagram.pdf)
{#fig:system_diagram tex_position="t"} **The Rxiv-Maker System Diagram.** The system integrates Markdown content, YAML metadata, Python and R scripts, and bibliography files through a processing engine. This engine leverages local execution, virtual environments, and LaTeX to produce a publication-ready scientific article, demonstrating a fully automated and reproducible pipeline.

<!-- Example 2: Full-width two-column spanning figure -->
<!-- width="\textwidth" makes the figure span both columns (use figure* environment) -->
<!-- tex_position="t" maintains top placement preference -->  
<!-- This combination is perfect for detailed workflow diagrams that need maximum width -->
![](FIGURES/Figure__workflow.pdf)
{#fig:workflow width="\textwidth" tex_position="t" caption_width="\textwidth"} **Rxiv-Maker Workflow: User Input vs. Automated Processing.** The framework clearly separates user responsibilities (content creation and configuration) from automated processes (parsing, conversion, compilation, and output generation). Users only need to write content and set preferences. At the same time, the system handles all technical aspects of manuscript preparation automatically, ensuring a streamlined workflow from markdown input to publication-ready PDF output.

<!-- For comprehensive figure positioning guidance, see docs/guides/figures-guide.md -->
<!-- This covers positioning attributes, width control, panel references, and troubleshooting -->

The framework enables programmatic generation of figures and tables using Python and R scripting with visualisation libraries including Matplotlib [@Hunter2007_matplotlib] and Seaborn [@Waskom2021_seaborn].

{{py:exec
import pandas as pd
from datetime import datetime
from pathlib import Path
from data_updater import update_all_data_files

# Update data files and load arXiv statistics
update_all_data_files()
df = pd.read_csv("DATA/arxiv_monthly_submissions.csv")
df['year_month'] = pd.to_datetime(df['year_month'])

# Calculate key statistics for the manuscript
data_start_year = int(df['year_month'].dt.year.min())
total_submissions = int(df['submissions'].sum())
total_submissions_millions = round(total_submissions / 1_000_000, 2)
years_span = int(df['year_month'].dt.year.max() - df['year_month'].dt.year.min() + 1)
compilation_date = datetime.now().strftime("%B %d, %Y")
last_updated = datetime.fromtimestamp(Path("DATA/arxiv_monthly_submissions.csv").stat().st_mtime).strftime("%B %Y")

print(f"Loaded {len(df)} months of arXiv data spanning {years_span} years")
}}

Both data can be analysed and figures generated directly from source datasets during compilation, establishing transparent connections between raw data, processing pipelines, and final visualisations. The framework's intelligent caching system tracks content changes in data files and analysis scripts through checksum comparisons, regenerating figures only when source materials have been modified. This approach significantly reduces compilation time whilst ensuring visualisations remain synchronised with underlying data.

The framework also allows for manuscripts to include executable python code that is run during compilation. For example, python code within this manuscript automatically fetches the latest data from web sources including arXiv monthly submissions and preprint server statistics. For example, @sfig:arxiv_growth showcases {{py:get total_submissions_millions}} million arXiv submissions spanning {{py:get years_span}} years starting from {{py:get data_start_year}}. These statistics were computed live during manuscript compilation on {{py:get compilation_date}} with data last updated {{py:get last_updated}}. This numerical data is inserted automatically and dynamically by python code into manuscript through special py:get commands.

This executable manuscript approach eliminates the manual copy-and-paste workflow that traditionally introduces errors when transferring results between analysis and documentation [@perkel2022]. When datasets are updated or algorithms refined, affected figures are automatically regenerated, ensuring consistency and eliminating outdated visualisations. The system integrates Mermaid.js [@Mermaid2023_documentation] for generating technical diagrams from text-based syntax, with the complete range of supported methods detailed in @stable:figure-formats. The comprehensive markdown syntax capabilities are documented in @stable:markdown-syntax.

This approach reframes manuscripts as executable outputs of the research process rather than static documentation. Built upon the HenriquesLab bioRxiv template [@HenriquesLab2015_template], Rxiv-Maker extends capabilities through automated processing pipelines. The architecture, detailed in @fig:system_diagram and @fig:workflow, provides automated build processes through local execution with virtual environment isolation (technical details described in @snote:figure-generation).

Academic authors use various tools depending on their research needs and technical requirements. Traditional LaTeX environments like Overleaf democratise professional typesetting through accessible web interfaces, but struggle with version control and computational content integration. 

Multi-format publishing platforms including Quarto, R Markdown, and Bookdown excel at producing multiple output formats with statistical integration, though they introduce complexity for simple documents and variable LaTeX typesetting quality. Collaborative writing frameworks such as Manubot enable transparent, version-controlled scholarly communication with automated citation management [@himmelstein2019], yet offer limited computational reproducibility features. 

Web-first computational systems like MyST and Jupyter Book prioritise interactive content and browser-native experiences, but compromise PDF output quality and offline accessibility. Modern typesetting engines like Typst provide cleaner syntax and faster compilation, though ecosystem maturity and adoption remain barriers.

Rxiv-Maker occupies a specialised niche at the intersection of developer workflows, academic publishing, and computational reproducibility. This developer-centric approach requires technical setup but delivers automated, reproducible PDF preprint generation particularly suited to computational research where datasets evolve and algorithmic documentation is essential. The framework trades initial complexity for long-term automation benefits, enabling deeper specialisation for manuscripts involving dynamic content and processing pipelines. A comprehensive comparison is provided in @stable:tool-comparison.

<!-- Results -->

Rxiv-Maker simplifies manuscript creation by building reproducibility directly into the writing process. Writers work in familiar Markdown, which the system converts to LaTeX and compiles into publication-ready PDFs with proper formatting, pagination, and high-quality figures.


For users requiring containerised environments, the separate docker-rxiv-maker repository provides Docker-based execution. This alternative is valuable for collaborative research across platforms or institutional settings with specific software restrictions [@Boettiger2015_docker_reproducibility].

The system automatically saves all generated files, creating a complete record from source materials to the finished document. The local execution model provides immediate feedback through fast compilation cycles and intelligent caching that skips unchanged content.

The separate docker-rxiv-maker repository supports containerised execution for specialised deployment needs. Available deployment strategies are compared in @stable:deployment-options.

When working with figures, the system handles both static images and dynamic content with intelligent optimisation. Python or R scripts placed in designated folders are executed during compilation with sophisticated caching that monitors file modifications and dependencies. The system pulls in data, runs analyses, and generates visualisations whilst skipping unchanged components to accelerate build cycles [@Jupyter2016_notebook]. Mermaid.js diagrams are rendered from text-based specifications into publication-ready vector graphics, with fallback mechanisms ensuring reliability across different network conditions. This approach creates manuscripts that serve as complete, verifiable records of research where readers can trace every figure and result back to its source code and data, whilst maintaining optimal performance through intelligent caching.

The framework provides a sophisticated developer experience through a modern command-line interface featuring rich formatting, progress indicators, and coloured output that significantly enhances usability. This interface includes intelligent shell completion for Bash and Zsh environments, reducing command entry errors and improving workflow efficiency. Automatic update notifications ensure users benefit from the latest features and security improvements without manual intervention.

Core workflow automation extends beyond PDF generation through specialised commands: `rxiv setup` handles automated dependency installation across platforms, `rxiv clean` maintains workspace hygiene, and `rxiv track-changes` provides visual comparison between manuscript versions for collaborative review. The comprehensive validation system delivers detailed error reporting with contextual LaTeX error parsing, systematic figure validation, and thorough citation checking with DOI resolution. Intelligent caching with content-based change detection dramatically accelerates rebuild cycles by selectively regenerating only modified components (@snote:caching-validation).

The Visual Studio Code extension provides editing features including real-time syntax highlighting, autocompletion for bibliographic citations from BibTeX files, and cross-reference management. The extension reduces cognitive load and minimises syntax errors while maintaining consistent formatting.

<!-- Discussion and conclusions section -->

Rxiv-Maker combines plain-text authoring with local execution environments to address consistency and reproducibility challenges in scientific publishing. Following literate programming principles [@Knuth1984_literate_programming], it creates documents that blend narrative text with executable code while hiding typesetting complexity. Git integration provides transparent attribution, conflict-free merging, and complete revision histories [@Ram2013_git_science;@Perez-Riverol2016_github_bioinformatics], supporting collaborative practices needed for open science.

Preprint servers have transferred quality control and typesetting responsibilities from journals to individual authors, creating both opportunities and challenges for scientific communication. Rxiv-Maker provides automated safeguards that help researchers produce publication-quality work without extensive typesetting knowledge, making professional publishing tools available through GitHub-based infrastructure.

The focus on PDF output via LaTeX optimises preprint workflows for scientific publishing requirements. We plan to extend format support by integrating universal converters such as Pandoc [@pandoc2020], while preserving typographic control and reproducibility standards. 

The Visual Studio Code extension addresses adoption barriers by providing familiar development environments that bridge text editing with version control workflows. Future development will prioritise deeper integration with computational environments and quality assessment tools, building upon established collaborative frameworks [@biaflows2024] and container-based approaches that enhance reproducibility [@dl4miceverywhere2024]. 

The system supports scientific publishing through organised project structure separating content, configuration, and computational elements. All manuscript content, metadata, and bibliographic references are version-controlled, ensuring transparency.

The markdown-to-LaTeX conversion pipeline handles complex academic syntax including figures, tables, citations, and mathematical expressions while preserving semantic meaning and typographical quality. The system uses a multi-pass approach that protects literal content during transformation, ensuring intricate scientific expressions render accurately. For advanced typesetting requirements that exceed markdown capabilities, the framework provides direct LaTeX injection through specialised code blocks, enabling access to LaTeX's full typesetting capabilities (@snote:latex-injection).

The framework supports subscript and superscript notation essential for chemical formulas, allowing expressions such as $\text{H}_2\text{O}$, $\text{CO}_2$, $\text{Ca}^{2+}$, $\text{SO}_4^{2-}$, and $E=mc^2$, as well as temperature notation like 25°C.

The system's mathematical typesetting capabilities extend to numbered equations, which are essential for scientific manuscripts. For instance, the fundamental equation relating mass and energy can be expressed as:

$$E = mc^2$${#eq:einstein}

The framework also supports more complex mathematical formulations, such as the standard deviation calculation commonly used in data analysis:

$$\sigma = \sqrt{\frac{1}{N-1} \sum_{i=1}^{N} (x_i - \bar{x})^2}$${#eq:std_dev}

Additionally, the system handles chemical equilibrium expressions, which are crucial in biochemical and chemical research:

$$K_{eq} = \frac{[\text{Products}]}{[\text{Reactants}]} = \frac{[\text{Ca}^{\text{2+}}][\text{SO}_4^{\text{2-}}]}{[\text{CaSO}_4]}$${#eq:equilibrium}

These numbered equations (@eq:einstein, @eq:std_dev, and @eq:equilibrium) demonstrate the framework's capability to handle diverse mathematical notation while maintaining proper cross-referencing throughout the manuscript. This functionality ensures that complex scientific concepts can be presented with the precision and clarity required for academic publication.

Rxiv-Maker is optimised for reproducible PDF preprint generation within the scientific authoring ecosystem. While platforms such as Overleaf and Quarto offer multi-format capabilities, Rxiv-Maker provides focused, developer-centric workflows that integrate with version control and local execution environments.

The framework provides practical training in version control, local development workflows, and computational reproducibility, which are skills fundamental to modern scientific practice. Researchers learn technical skills including Git proficiency, markdown authoring, and build automation. The system is designed to be accessible without extensive programming backgrounds, featuring comprehensive documentation and intuitive workflows that reduce barriers and foster skill development.

The technical architecture provides efficient local execution through intelligent caching and selective content regeneration. The framework supports high-resolution graphics and advanced figure layouts while maintaining optimal document organisation and cross-referencing functionality.

Computational research faces a growing disconnect between advanced analytical methods and traditional publishing workflows. Rxiv-Maker addresses this by treating manuscripts as executable code rather than static documents, bringing collaborative development practices from software engineering to scientific communication. This enables transparent, verifiable publications suitable for both immediate sharing and long-term preservation.

The framework's impact extends beyond technical capabilities to foster a culture of computational literacy and transparent science. As preprint servers continue to reshape academic publishing, tools like Rxiv-Maker become essential infrastructure for maintaining quality and reproducibility in researcher-led publication processes. The framework serves as both a practical solution for immediate publishing needs and a foundation for advancing open science principles across diverse research domains.

## Methods

This section describes the Rxiv-Maker framework technically, showing how the system generates structured documentation from source code and plain text. System architecture is detailed in @sfig:architecture.

### Processing Pipeline
Rxiv-Maker processes manuscripts through a five-stage pipeline that converts source files into publication-ready PDFs using local execution with intelligent optimisations. The pipeline ensures computational reproducibility through these stages:

1. **Environment Setup**: Automated dependency resolution with local virtual environments and pinned package versions, enhanced by intelligent caching systems
2. **Content Generation**: Conditional execution of Python/R scripts and Mermaid diagram compilation based on content-based change detection and modification timestamps
3. **Markdown Processing**: Multi-pass conversion with intelligent content protection preserving mathematical expressions, code blocks, and LaTeX commands
4. **Asset Aggregation**: Systematic collection and validation of figures, tables, and bibliographic references with comprehensive integrity checking and error reporting
5. **LaTeX Compilation**: Optimised `pdflatex` sequences with automatic cross-reference resolution, citation processing, and detailed error parsing

The local-first architecture includes sophisticated caching mechanisms that track content changes at the file and block level, significantly reducing build times for iterative manuscript development.

### Markdown-to-LaTeX Conversion
Manuscript conversion is handled by a Python processing engine that manages complex academic syntax requirements through "rxiv-markdown". This multi-pass conversion system uses content protection strategies to preserve computational elements such as code blocks and mathematical notation. It converts specialised academic elements including dynamic citations (`@smith2023`), programmatic figures, statistical tables, and supplementary notes before applying standard markdown formatting. 

The system supports notation essential for scientific disciplines: subscript and superscript syntax for chemical formulas such as $\text{H}_2\text{O}$ and $\text{CO}_2$, mathematical expressions including Einstein's mass-energy equivalence (@eq:einstein), chemical notation such as $\text{Ca}^{2+}$ and $\text{SO}_4^{2-}$ (@eq:equilibrium), temperature specifications like 25°C, and statistical calculations including standard deviation (@eq:std_dev). The framework supports complex mathematical expressions typical of computational workflows:

$$\frac{\partial}{\partial t} \mathbf{u} + (\mathbf{u} \cdot \nabla) \mathbf{u} = -\frac{1}{\rho} \nabla p + \nu \nabla^2 \mathbf{u}$${#eq:navier_stokes}

This approach provides accessible alternatives for common formulas while ensuring complex equations like the Navier-Stokes equation (@eq:navier_stokes) are rendered with professional quality. Mathematical formula support is detailed in @snote:mathematical-formulas. 

### Programmatic Content and Environments
The framework generates figures, statistical analyses, and algorithmic diagrams as reproducible outputs linked to source data and processing pipelines. The build pipeline executes Python, R, and Mermaid scripts with sophisticated content-based caching that tracks file checksums and dependencies to avoid redundant computation while maintaining complete traceability between datasets, algorithms, and visualisations (@snote:figure-generation). 

Rxiv-Maker implements robust local environment management with automated dependency resolution and validation. Dependencies are rigorously pinned through virtual environments with comprehensive version tracking, ensuring consistent execution across different computing platforms and time periods. The system includes automated setup procedures for LaTeX, Python, and R dependencies, with intelligent detection of missing components and guided installation procedures. The framework ensures consistent execution across different computing platforms and time periods through rigorous dependency management and virtual environment isolation.

### Deployment Architecture and Platform Considerations
The framework prioritizes local execution as its primary deployment strategy, providing optimal performance and universal architecture compatibility across AMD64 and ARM64 systems. Local installation eliminates container overhead while offering direct access to native resources required for diagram generation, enabling faster iteration cycles and comprehensive debugging capabilities.

The local-first architecture includes intelligent dependency management with virtual environments, automated validation systems, and content-based caching for optimal performance. This approach ensures reproducible builds while maintaining the flexibility and speed that researchers need for iterative manuscript development.

For specialised use cases requiring containerised environments, the separate docker-rxiv-maker repository offers Docker-based execution. The modular architecture enables researchers to select deployment strategies appropriate to their technical constraints while maintaining reproducibility guarantees.

### Visual Studio Code Extension
A dedicated Visual Studio Code extension (available as a separate project at vscode-rxiv-maker) provides an integrated development environment optimised for rxiv-maker manuscript preparation. The extension leverages the Language Server Protocol to deliver real-time syntax highlighting for academic markdown syntax, intelligent autocompletion for bibliographic citations from BibTeX files, and context-aware suggestions for cross-references to figures, tables, equations, and supplementary materials.

The extension integrates seamlessly with the core framework through file system monitoring and automated workspace detection, automatically recognising rxiv-maker project structures and activating appropriate editing features. Schema validation for YAML configuration files ensures project metadata adheres to reproducibility specifications, whilst integrated terminal access enables direct execution of framework commands. This companion extension provides researchers with an accessible, feature-rich editing experience that maintains reproducibility guarantees whilst reducing technical barriers to adoption.

### Quality Assurance
Framework reliability is ensured through comprehensive multi-level validation protocols and user-facing quality checks. Unit tests validate individual components, integration tests verify end-to-end pipelines, and platform tests validate deployment environment behaviour across different operating systems. Pre-commit pipelines enforce code formatting, linting, and type checking, ensuring code quality throughout development.

User-facing validation includes sophisticated LaTeX error parsing with contextual error messages, comprehensive figure validation that checks for missing files and format compatibility, and citation validation with DOI resolution through CrossRef APIs. The framework provides detailed error reporting with suggestions for resolution, significantly reducing debugging time for users. Automated dependency checking ensures all required components are properly installed and configured before manuscript processing begins.

## Data availability
arXiv monthly submission data used in this article is available at [https://arxiv.org/stats/monthly_submissions](https://arxiv.org/stats/monthly_submissions). Preprint submissions data across different hosting platforms is available at [https://github.com/esperr/pubmed-by-year](https://github.com/esperr/pubmed-by-year). The source code and data for the figures in this article are available at [https://github.com/HenriquesLab/rxiv-maker](https://github.com/HenriquesLab/rxiv-maker).

## Code availability
The Rxiv-Maker computational framework is available at [https://github.com/HenriquesLab/rxiv-maker](https://github.com/HenriquesLab/rxiv-maker). The framework includes comprehensive documentation, example manuscripts, and automated testing suites to ensure reliability across different deployment environments.

The companion Visual Studio Code extension is maintained as a separate project at [https://github.com/HenriquesLab/vscode-rxiv-maker](https://github.com/HenriquesLab/vscode-rxiv-maker). This extension provides researchers with an integrated development environment featuring syntax highlighting, intelligent autocompletion for citations and cross-references, schema validation for configuration files, and seamless integration with the main framework's build processes.

For users requiring containerised execution, the docker-rxiv-maker repository provides Docker-based deployment at [https://github.com/HenriquesLab/docker-rxiv-maker](https://github.com/HenriquesLab/docker-rxiv-maker). All repositories are released under an MIT License, enabling free use, modification, and distribution for both academic and commercial applications.

## Author contributions
Both Bruno M. Saraiva, Guillaume Jacquemet, and Ricardo Henriques conceived the project and designed the framework. All authors contributed to writing and reviewing the manuscript.

## Acknowledgements
The authors thank Jeffrey Perkel for feedback that helped improve the manuscript. B.S. and R.H. acknowledge support from the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation programme (grant agreement No. 101001332) (to R.H.) and funding from the European Union through the Horizon Europe program (AI4LIFE project with grant agreement 101057970-AI4LIFE and RT-SuperES project with grant agreement 101099654-RTSuperES to R.H.). Funded by the European Union. However, the views and opinions expressed are those of the authors only and do not necessarily reflect those of the European Union. Neither the European Union nor the granting authority can be held responsible for them. This work was also supported by a European Molecular Biology Organization (EMBO) installation grant (EMBO-2020-IG-4734 to R.H.), a Chan Zuckerberg Initiative Visual Proteomics Grant (vpi-0000000044 with https://doi.org/10.37921/743590vtudfp to R.H.), and a Chan Zuckerberg Initiative Essential Open Source Software for Science (EOSS6-0000000260). This study was supported by the Academy of Finland (no. 338537 to G.J.), the Sigrid Juselius Foundation (to G.J.), the Cancer Society of Finland (Syöpäjärjestöt, to G.J.), and the Solutions for Health strategic funding to Åbo Akademi University (to G.J.). This research was supported by the InFLAMES Flagship Program of the Academy of Finland (decision no. 337531).
