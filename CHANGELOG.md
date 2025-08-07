# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v1.4.16] - 2025-08-06

### Fixed
- **PDF Generation Pipeline**: Resolve critical script path resolution issues
  - Fix style directory not found by using absolute paths relative to project root
  - Fix copy_pdf.py script path resolution for proper PDF copying
  - Fix analyze_word_count.py script path for word count analysis 
  - Fix pdf_validator.py script path for PDF validation
  - Improve path resolution in pdf_utils.py to avoid nested directory issues
  - Resolves "file not found" errors when running PDF generation from VSCode extension or different working directories

### Changed
- **Citation**: Migrate from Zenodo to arXiv citation (2508.00836)
  - Update `acknowledge_rxiv_maker` feature to use arXiv preprint citation instead of outdated Zenodo reference
  - Change BibTeX entry from `@article` (Zenodo) to `@misc` (arXiv) format
  - Maintain same citation key (`saraiva_2025_rxivmaker`) for backward compatibility

## [v1.4.13] - 2025-08-04

### Fixed
- **🔒 SECURITY**: Fix xml2js prototype pollution vulnerability (CVE-2023-0842) in VSCode extension submodule
  - Updated xml2js dependency from 0.4.23 to 0.5.0 to address GHSA-776f-qx25-q3cc
  - Resolves medium severity prototype pollution vulnerability allowing external modification of object properties
- **CI/CD Pipeline**: Fix CI timeout issue in PyPI integration test
  - Added `@pytest.mark.timeout(300)` to prevent global 120s timeout from killing LaTeX compilation tests
  - Resolves GitHub Actions failures where PDF build tests were timing out prematurely
- Fix PDF detection and download issues in Colab notebook environment
- Fix GitHub Actions workflow configurations and Docker container setup

### Changed
- Update GitHub workflows and improve Colab notebook functionality 
- Update Colab notebook to use modern rxiv CLI commands and improve UX
- Update setup completion messages to use proper rxiv CLI syntax
- Improve CI/CD pipeline stability with better error handling and workflow orchestration

## [v1.4.12] - 2025-07-27

### Fixed
- **Build System**: Add logging cleanup before all sys.exit calls in build command
  - Ensures proper cleanup of log handles before process termination
  - Prevents file permission errors and resource leaks during build failures
- **CI/CD Pipeline**: Fix CI issues with Windows file permissions and module imports
  - Resolve Windows-specific file permission errors by adding proper logging cleanup
  - Fix 5 failing tests in CI pipeline through improved error handling
  - Fix missing imports in build manager tests for better cross-platform compatibility
- **Dependency Management**: Remove all references to cairo from codebase
  - Eliminates problematic cairo dependency that caused installation issues
  - Improves package compatibility across different operating systems

### Changed
- **GitHub Integration**: Add Claude Code GitHub Workflow for automated assistance
  - Provides AI-powered code review and automated development support
  - Enhances development workflow with intelligent suggestions and fixes
- **Performance**: Implement PR recommendations for improved debugging and performance
  - Better error reporting and diagnostic information for troubleshooting
  - Optimized build processes and enhanced logging capabilities
- **CI/CD Stability**: Stabilize CI/CD pipeline for reliable testing
  - Improved test execution reliability across different platforms
  - Enhanced error handling and recovery mechanisms

## [v1.4.11] - 2025-07-26

### Fixed
- **Windows Cross-Platform Compatibility**: Fixed Windows platform detector tests to handle path separators correctly
- **File Permission Issues**: Resolved log file cleanup permission errors on Windows systems
- **SVG Placeholder Generation**: Fixed path validation errors when creating SVG placeholders in temporary directories
- **Container Script Execution**: Improved Docker container script execution with better error handling

## [v1.4.10] - 2025-07-26

### Fixed
- **🚨 CRITICAL**: Fix PyPI deployment critical issues for Windows cross-platform compatibility
  - Addresses deployment failures preventing Windows users from installing via PyPI
  - Resolves platform-specific compatibility issues in package distribution
- **Windows Platform Support**: Fix Windows platform detector tests to handle path separators correctly
  - Ensures proper path handling across different operating systems (Windows vs Unix-like)
  - Fixes test failures related to file system path differences
- **Test Execution**: Fix Windows test execution by removing unsupported --forked flag
  - Removes pytest-forked flag that was causing test failures on Windows systems
  - Improves cross-platform test reliability and execution consistency

## [v1.4.9] - 2025-07-26

### Fixed
- **Critical CI/CD Pipeline Issues**: Comprehensive fixes to improve build reliability and stability
  - Resolve Docker build shell escaping failures in Dockerfile with proper command formatting
  - Improve cross-platform Windows dependency handling in setup-environment GitHub Action
  - Enhance test execution error handling and exit code capture for better failure detection
  - Add UTF-8 encoding consistency across all GitHub workflows to prevent encoding issues
  - Disable Docker provenance/SBOM generation to prevent cache conflicts and build failures
  - Optimize multi-architecture build performance with streamlined Docker configurations
  - Fixed Docker base image build failures by adding missing system dependencies
  - Resolved package conflicts in Docker build by replacing libmariadb-dev with proper dependencies
  - Address root causes of workflow failures that were impacting CI/CD pipeline stability

### Changed
- **Project Optimization and Cleanup**: Comprehensive codebase organization and maintenance improvements
  - Removed obsolete test files and temporary artifacts (14 deleted files)
  - Optimized Docker base image with streamlined dependency management and reduced layer count
  - Updated figure generation pipeline with improved error handling and API integration
  - Enhanced package management scripts with better validation and error handling
  - Consolidated testing framework with removal of deprecated Docker integration tests
  - Updated submodule configurations for package managers (Homebrew, Scoop, VSCode extension)
  - Improved GitHub Actions workflows with better organization and efficiency
  - Updated documentation and CLI reference materials
  - Cleaned up file permissions and standardized project structure

## [v1.4.5] - 2025-07-19

### Fixed
- **🚨 CRITICAL FIX: LaTeX Template Files Missing from PyPI Package**
  - Fixed hatchling build configuration to properly include LaTeX template files (`template.tex` and `rxiv_maker_style.cls`) in wheel distribution
  - Added `[tool.hatch.build.targets.wheel.force-include]` configuration to ensure template files are packaged
  - Users can now successfully generate PDFs after installing from PyPI without "template not found" errors
  - Added comprehensive integration tests (`test_pypi_package_integration.py`) to prevent this issue in future releases
  - This resolves the critical issue where pip-installed packages could not build PDFs due to missing LaTeX templates

## [v1.4.0] - 2025-07-18

### Changed

#### 🔧 Package Installation Improvements
- **Removed Automatic System Dependencies**: Pip install now only installs Python dependencies for better compatibility
  - No more automatic LaTeX, Node.js, or R installation during `pip install rxiv-maker`
  - Manual system dependency installation available via `rxiv-install-deps` command
  - Follows Python packaging best practices and avoids unexpected system modifications
  - Faster and more reliable pip installation process

#### 🧪 Test Suite Optimization
- **Performance Improvements**: Optimized slow validation tests for better CI/CD performance
  - Added `--no-doi` flag to skip DOI validation in tests for 43% speed improvement
  - Replaced `make validate` calls with direct CLI calls in test suite
  - Added `@pytest.mark.slow` markers for performance tracking
  - Reduced test execution time from 2.88s to 1.64s for validation workflow tests

#### 🧹 Code Quality and Maintenance
- **Test Infrastructure Cleanup**: Removed inappropriate Docker-based installation tests
  - Deleted entire `tests/install/` directory containing obsolete Docker installation tests
  - Updated pyproject.toml to remove 'install' test marker
  - Preserved legitimate Docker engine mode functionality
  - Maintained test coverage while improving execution speed

### Fixed

#### 🔧 Test Suite Stability
- **CLI Test Fixes**: Resolved 15 failing tests across multiple test modules
  - Fixed CLI help text assertions (rxiv-maker vs Rxiv-Maker, pdf vs build commands)
  - Resolved config get existing key test failures due to singleton config pollution
  - Fixed build command test failures (method name updates from .build() to .run_full_build())
  - Corrected documentation generation FileNotFoundError (path updates from src/py/ to src/rxiv_maker/)
  - Added missing pytest imports and updated exit code expectations

#### 📦 Package Publishing
- **PyPI Release**: Successfully published v1.4.0 to PyPI with comprehensive testing
  - Built and published both wheel and source distributions
  - Created git release tag v1.4.0
  - Verified installation and CLI functionality from PyPI
  - All core features working correctly in production environment

### Performance

#### ⚡ Test Execution Speed
- **43% Faster Validation Tests**: Optimized validation workflow for CI/CD environments
  - Intelligent DOI validation skipping in test environments
  - Direct CLI calls instead of subprocess overhead
  - Better resource utilization in automated testing

## [v1.3.0] - 2025-07-14

### Added

#### 🔍 Change Tracking System
- **Complete Change Tracking Workflow**: New `track_changes.py` command with latexdiff integration for visual change highlighting
  - Compare current manuscript against any previous git tag version
  - Generate PDFs with underlined additions, struck-through deletions, and modified text markup
  - Multi-pass LaTeX compilation with proper bibliography integration and cross-references
  - Custom filename generation following standard convention with "_changes_vs_TAG" suffix
  - Supports both local and Docker execution modes
- **Makefile Integration**: New `make pdf-track-changes TAG=v1.0.0` command for streamlined workflow
- **Academic Workflow Support**: Comprehensive documentation with use cases for peer review, preprint updates, and collaborative writing
- **CI/CD Integration**: GitHub Actions and GitLab CI examples for automated change tracking
- **Advanced Features**: Handles figures, tables, equations, citations, and complex LaTeX structures

#### 🐳 Docker-Accelerated Google Colab Notebook
- **New Colab Notebook**: `notebooks/rxiv_maker_colab_docker.ipynb` with udocker integration for containerized execution
  - **Massive Speed Improvement**: ~4 minutes setup vs ~20 minutes for manual dependency installation
  - **Container Integration**: Uses `henriqueslab/rxiv-maker-base:latest` image with all dependencies pre-installed
  - **Volume Mounting**: Seamless file access between Google Colab and container environment
  - **Pre-configured Environment**: Complete LaTeX distribution, Python 3.11, R, Node.js, and Mermaid CLI
  - **Improved Reliability**: Isolated execution environment with consistent results across platforms
  - **User-Friendly Interface**: Maintains existing ezinput UI while leveraging containerization benefits

#### 🏗️ Docker Engine Mode Infrastructure
- **Complete Containerization**: RXIV_ENGINE=DOCKER mode for all operations requiring only Docker and Make
- **Docker Image Management**: Comprehensive build system in `src/docker/` with automated image building
- **GitHub Actions Acceleration**: 5x faster CI/CD workflows using pre-compiled Docker images
- **Platform Detection**: Automatic AMD64/ARM64 architecture compatibility with performance optimizations
- **Safe Build Wrapper**: Resource monitoring, timeout management, and system protection via `build-safe.sh`
- **Transparent Execution**: Volume mounting for seamless file access between host and container
- **Cross-Platform Consistency**: Identical build environments across Windows, macOS, and Linux

#### 🌐 Cross-Platform Compatibility
- **Universal Support**: Complete Windows, macOS, and Linux compatibility with automatic platform detection
- **Platform-Specific Commands**: Adaptive file operations (rmdir/del vs rm) and shell handling
- **Multiple Python Managers**: Support for uv, venv, and system Python with intelligent selection
- **Cross-Platform Testing**: Comprehensive CI/CD validation workflows across all platforms
- **Path Handling**: Correct path separators and shell compatibility fixes
- **Environment Setup**: Platform-agnostic environment setup with `setup_environment.py`

#### 📚 Enhanced Documentation
- **Docker-First Approach**: Restructured documentation prioritizing containerized workflows
- **Comprehensive Guides**: New installation guide with four setup methods (Colab, Docker, Local, GitHub Actions)
- **Workflow Documentation**: Enhanced GitHub Actions guide emphasizing 5x faster builds
- **Command Reference**: Docker and local mode examples with comprehensive usage patterns
- **Troubleshooting**: Enhanced debugging guides and common issue resolution

### Changed

#### 🔧 Enhanced Build System
- **Python Module Architecture**: Centralized build management with `build_manager.py` for orchestrating complete build process
- **Improved Error Handling**: Better logging infrastructure with warning and error logs in `output/` directory
- **Multi-Pass LaTeX Compilation**: Proper bibliography integration and cross-reference resolution
- **Figure System Transformation**: Descriptive naming conventions (Figure__system_diagram vs Figure_1) with enhanced generation
- **Streamlined Makefile**: Simplified commands with Python delegation for better maintainability
- **Build Process Order**: PDF validation before word count analysis for logical workflow

#### 💻 Code Quality Modernization
- **Type Annotations**: Updated to modern Python typing (dict/list vs Dict/List) across entire codebase
- **Pre-commit Hooks**: Comprehensive code quality checks with ruff, mypy, and automated formatting
- **Linting Integration**: Resolved 215+ linting issues with automated formatting and type safety
- **Test Coverage**: Enhanced testing infrastructure with 434 tests passing
- **Documentation Generation**: Improved API documentation with lazydocs integration
- **Code Organization**: Better module structure with focused, type-safe components

#### ⚡ Performance Optimizations
- **Caching Strategies**: Aggressive caching for Python dependencies, virtual environments, and LaTeX outputs
- **Parallel Processing**: Optimized CI/CD workflows with concurrent execution and matrix builds
- **Dependency Management**: Modern package management with uv for faster installations
- **Build Speed**: Reduced compilation times through intelligent change detection and selective rebuilds
- **Memory Optimization**: Efficient resource usage for large manuscripts and complex builds

### Fixed

#### 📝 Citation and Bibliography
- **Citation Rendering**: Fixed citations displaying as question marks (?) instead of proper numbers
- **BibTeX Integration**: Enhanced BibTeX processing with proper path checking and multi-pass compilation
- **Reference Resolution**: Corrected cross-reference and citation processing in build pipeline
- **Bibliography Path Handling**: Fixed file path resolution in test environments and track changes
- **Cross-Reference Validation**: Improved handling of figure, table, and equation references

#### 🖥️ Cross-Platform Issues
- **Windows Compatibility**: Unicode encoding fixes in `cleanup.py` and `utils/__init__.py` with ASCII fallbacks
- **Path Management**: Corrected path separators and file operations across platforms
- **Shell Compatibility**: Fixed bash vs sh compatibility issues in GitHub Actions and Makefiles
- **Tool Installation**: Resolved platform-specific dependency installation with proper PATH handling
- **Environment Variables**: Fixed environment variable handling across different shells and platforms

#### 🐳 Docker Integration
- **Container Permissions**: Fixed file access and workspace permissions for GitHub Actions
- **Volume Mounting**: Corrected path mapping between host and container environments
- **Environment Variables**: Proper variable passing to containers with MANUSCRIPT_PATH and RXIV_ENGINE
- **Image Configuration**: Optimized Dockerfile with proper dependencies and global tool availability
- **Build Context**: Fixed Docker build context and resource allocation issues

#### 🛠️ Build System Stability
- **Error Handling**: Improved error reporting and graceful failure handling throughout build process
- **File Operations**: Fixed recursive file detection with rglob() and proper path handling
- **Test Stability**: Resolved test failures in track changes and figure generation
- **Figure Generation**: Fixed nested directory creation and output paths in figure scripts
- **Executable Permissions**: Fixed executable permissions for files with shebangs

### Performance

#### 🚀 GitHub Actions Optimization
- **5x Faster Builds**: Pre-compiled Docker images reduce build time from ~10 minutes to ~3-5 minutes
- **Parallel Execution**: Concurrent workflow steps and matrix builds for optimal resource utilization
- **Intelligent Caching**: Comprehensive caching strategies for dependencies, virtual environments, and LaTeX outputs
- **Resource Optimization**: Efficient memory and CPU usage with Docker containerization
- **Build Acceleration**: Docker base image with all system dependencies pre-installed

#### 💻 Local Development
- **Faster Setup**: Streamlined installation process across platforms with improved dependency management
- **Incremental Builds**: Smart change detection and selective rebuilds for faster iteration
- **Dependency Caching**: Reduced repeated installations and downloads with intelligent caching
- **Build Optimization**: Efficient compilation and validation processes with parallel figure generation
- **Development Workflow**: Enhanced developer experience with better error reporting and debugging

## [v1.2.0] - 2025-07-08

### Added
- **Visual Studio Code Extension Integration**: Enhanced documentation and support for the companion VS Code extension
  - Detailed installation instructions and feature descriptions
  - Integration with rxiv-markdown language support
  - Improved user experience for scientific manuscript preparation
- **Rxiv-Markdown Language Support**: Updated documentation to reflect the introduction of rxiv-markdown
  - Enhanced clarity on processing pipeline
  - Better integration with VS Code extension ecosystem
- **Enhanced Testing Infrastructure**: Added lazydocs dependency for improved documentation generation
  - Updated DOI validation tests for better CrossRef integration
  - Improved test coverage and reliability

### Changed
- **Documentation Improvements**: Comprehensive updates to README and example manuscripts
  - Enhanced Visual Studio Code extension descriptions
  - Clearer processing pipeline documentation
  - Improved accessibility for scientific manuscript preparation
- **Text Formatting Enhancements**: Refactored text formatting logic for better handling of nested braces
  - Updated unit tests for edge cases
  - Improved robustness of markdown processing

### Fixed
- **Reference Management**: Updated references and citations in manuscript files for accuracy and consistency
- **Dependency Management**: Added crossref-commons dependency in pyproject.toml for better DOI validation

## [v1.1.1] - 2025-07-02

### Added
- **Enhanced DOI Validation System**: Comprehensive DOI validation with multi-registrar support
  - CrossRef, DataCite, and JOSS API integration
  - Support for 10+ DOI registrar types (Zenodo, OSF, bioRxiv, arXiv, etc.)
  - Intelligent registrar detection with specific guidance for each DOI type
  - Parallel API calls for improved validation performance
  - Intelligent caching system with 30-day expiration and automatic cleanup
- **New Bibliography Management Commands**:
  - `add_bibliography.py` - Add and manage bibliography entries
  - `fix_bibliography.py` - Automatically fix common bibliography issues
- **Streamlined Validation Output**: Concise output showing only warnings and errors
- **Enhanced Citation Validator**: Configurable DOI validation integration
- **Comprehensive Testing**: Unit and integration tests for DOI validation workflow

### Fixed
- **Critical DOI Validation Fix**: Fixed CrossRef API integration that was causing all DOIs to fail validation
- Resolved false positive DOI warnings (reduced from 17 to 0 for valid manuscripts)
- Improved network error handling and resilience for API calls
- Fixed misleading error messages about DataCite when it was already being checked

### Changed
- **Streamlined Validation Output**: Removed verbose statistics clutter from default validation
- Default validation now shows only essential warnings and errors
- Detailed statistics available with `--verbose` flag
- Updated Makefile validation targets for cleaner output
- Enhanced error messages with actionable suggestions based on DOI type

### Performance
- Parallel API calls to multiple DOI registrars for faster validation
- Intelligent caching reduces repeated API calls
- Improved validation speed for manuscripts with many DOIs

---

### Previous Changes

### Added
- Enhanced Makefile with improved MANUSCRIPT_PATH handling and FIGURES directory setup instructions
- Mermaid CLI support with `--no-sandbox` argument for GitHub Actions compatibility
- Automatic FIGURES directory creation when missing
- Clean step integration in build process

### Fixed
- Fixed issue with passing CLI options to figure generation commands
- Fixed typos in environment variable handling
- Resolved image generation issues on GitHub Actions
- Fixed wrapper script handling for Mermaid CLI

### Changed
- Moved Mermaid CLI options to environment variables for better configuration
- Updated GitHub Actions workflow to reflect Makefile changes
- Improved error handling in figure generation pipeline

## [v1.1.0] - 2025-07-02

### Added
- **R Script Support**: Added support for R scripts in figure generation pipeline
- R environment integration in GitHub Actions
- Safe fail mechanisms for R figure generation
- SVG output format support for R plots
- Updated documentation to reflect R script capabilities

### Fixed
- Fixed Python path handling in image generation
- Resolved GitHub Actions formatting issues
- Fixed Makefile tentative issues with figure generation

### Changed
- Enhanced figure generation to support both Python and R scripts
- Updated README to include R script information
- Improved build process robustness

## [v1.0.2] - 2025-07-02

### Added
- **Automatic Python Figure Generation**: Implemented automatic execution of Python scripts in FIGURES directory
- Troubleshooting guide for missing figure files
- Enhanced testing for mathematical expression handling

### Fixed
- Fixed mathematical expression handling in code spans
- Resolved image path issues in figure processing
- Fixed GitHub Actions compatibility issues
- Improved automatic figure generation implementation

### Changed
- Enhanced figure processing pipeline
- Updated figure path handling for better reliability
- Improved error reporting for figure generation

## [v1.0.1] - 2025-06-30

### Added
- Enhanced validation system with improved error reporting
- Citation section with clickable preprint image in README
- Configuration system improvements
- VSCode syntax highlighting for citations

### Fixed
- Fixed mathematical expression handling in code spans
- Improved abstract clarity and GitHub links in README
- Fixed table reference format validation
- Enhanced GitHub Actions error handling

### Changed
- Modernized type annotations throughout codebase
- Updated ORCID information
- Reset manuscript to clean template state
- Improved documentation structure

## [v1.0.0] - 2025-06-26

### Added
- **Core Features**: Complete manuscript generation system
- Markdown to LaTeX conversion with 20+ enhanced features
- Automated figure generation (Python scripts, Mermaid diagrams)
- Scientific cross-references (`@fig:`, `@table:`, `@eq:`, `@snote:`)
- Citation management (`@citation`, `[@cite1;@cite2]`)
- Subscript/superscript support (`~sub~`, `^super^`)
- Professional LaTeX templates and bibliography management
- Comprehensive validation system
- GitHub Actions integration for cloud PDF generation
- Google Colab notebook support
- arXiv submission package generation

### Technical Features
- Content protection system for complex elements
- Multi-stage processing pipeline
- Automatic word count analysis
- Pre-commit hooks and code quality tools
- Comprehensive testing suite (unit and integration)
- Docker support (later removed in favor of native execution)

### Documentation
- Complete user guide and API documentation
- Platform-specific setup guides (Windows/macOS/Linux)
- Tutorials for Google Colab and GitHub Actions
- Architecture documentation

## [v0.0.3] - 2025-06-25

### Added
- Enhanced GitHub Actions workflow with proper permissions
- Automatic version management with versioneer
- Improved test coverage and validation
- Better error handling and logging

### Fixed
- Fixed GitHub Actions permissions for forked repositories
- Resolved LaTeX compilation issues
- Fixed table formatting and supplementary section organization

## [v0.0.2] - 2025-06-20

### Added
- Table header formatting with markdown to LaTeX conversion
- Supplementary note processing functionality
- Improved markdown conversion pipeline
- Enhanced test coverage

### Fixed
- Fixed table width and markdown formatting issues
- Resolved LaTeX compilation problems
- Fixed markdown inside backticks to preserve literal formatting

### Changed
- Refactored md2tex.py into focused, type-safe modules
- Improved markdown to LaTeX conversion reliability

## [v0.0.1] - 2025-06-13

### Added
- Initial project setup and core architecture
- Basic Markdown to LaTeX conversion
- Figure generation utilities
- Docker setup and management scripts
- Testing framework
- Project renaming from Article-Forge to RXiv-Forge (later Rxiv-Maker)

### Features
- Basic manuscript processing
- Figure generation from scripts
- LaTeX template system
- Word count analysis
- Flowchart generation with Mermaid

### Documentation
- Initial README and setup instructions
- Basic user documentation
- Docker installation guides

---

## Project History

**Rxiv-Maker** started as "Article-Forge" in June 2025, developed to bridge the gap between easy scientific writing in Markdown and professional LaTeX output. The project has evolved through several major iterations:

- **June 2025**: Initial development as Article-Forge
- **June 2025**: Renamed to RXiv-Forge, then standardized to Rxiv-Maker
- **June-July 2025**: Rapid development with 250+ commits
- **July 2025**: Major feature additions including R script support

The project emphasizes reproducible science workflows, automated figure generation, and professional typesetting while maintaining accessibility through familiar Markdown syntax.

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details on how to submit improvements, bug fixes, and new features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.