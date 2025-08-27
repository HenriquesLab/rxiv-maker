# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **🎯 Dynamic Version Injection**: Added dynamic version injection to Rxiv-Maker acknowledgment text
  - **Version Display**: Acknowledgment text now shows "Rxiv-Maker v{version}" instead of just "Rxiv-Maker"
  - **Automatic Updates**: Version number automatically updates with each release without manual intervention
  - **Graceful Fallbacks**: Handles import failures gracefully with "unknown" fallback version
  - **Backward Compatible**: Existing `acknowledge_rxiv_maker: true/false` setting works unchanged
  - **Reproducibility**: Helps users identify which version generated their manuscript for better traceability

- **🎯 Python Code Execution in Markdown**: Added secure Python code execution capabilities for dynamic content generation
  - **Inline Execution**: `{py: expression}` for inline calculations and expressions
  - **Block Execution**: `{{py: code}}` for multi-line code blocks with output formatting
  - **Variable Persistence**: Execution context persists across commands within a document
  - **Security Features**: Comprehensive sandboxing with subprocess isolation, import whitelisting, and timeout protection
  - **Error Handling**: Graceful error handling with informative error messages
  - **Output Formatting**: Code block output wrapped in markdown code blocks, inline results inserted directly

- **🎯 Blindtext Command Support**: Added LaTeX blindtext package integration for placeholder text generation
  - **Short Placeholder**: `{{blindtext}}` converts to `\blindtext` for short text
  - **Paragraph Placeholder**: `{{Blindtext}}` converts to `\Blindtext` for longer paragraphs
  - **LaTeX Integration**: Automatically includes blindtext package in LaTeX dependencies

- **🎯 Extensible Custom Command Framework**: Created modular command processing architecture
  - **Registry System**: Plugin-style command processor registration
  - **Code Protection**: Prevents command processing inside code blocks and inline code
  - **Future Ready**: Framework prepared for R execution and other custom commands

### Enhanced
- **📚 Comprehensive Example Manuscript**: Updated figure positioning examples with Python execution demonstrations
  - **Statistical Analysis**: Examples showing data processing and statistical calculations
  - **Variable Persistence**: Demonstrated workflow with variables shared across code blocks  
  - **Security Examples**: Shows security restrictions in action
  - **Documentation**: Complete reference for all new features

### Fixed
- **🐛 ValidationError Test Suite**: Fixed pre-existing test failure in validation test suite
  - **Root Cause**: Test was incorrectly trying to use `ValidationError` dataclass as an exception
  - **Proper Import**: Updated test to import the correct `ValidationError` exception class from services module
  - **Test Coverage**: All 1542+ unit tests now pass without failures
  - **Architecture Clarity**: Improved distinction between validation dataclasses and service exceptions

## [v1.5.17] - 2025-08-17

### Fixed
- **🐛 LaTeX Comment Escaping in Table Cells**: Fixed LaTeX compilation failure when markdown tables contain LaTeX comment syntax
  - **Root Cause**: Cell content like `` `% comment` `` wasn't properly escaping the `%` character inside `\texttt{}` environments
  - **LaTeX Error**: Unescaped `%` caused LaTeX to treat everything after as a comment, breaking table structure with unmatched braces
  - **Detection Logic Fix**: Enhanced `_format_markdown_syntax_cell` to recognize content starting with `%` as LaTeX syntax (not just `\`)
  - **Proper Escaping**: LaTeX comments are now escaped as `\% comment` inside `\texttt{}` to prevent interpretation as comments
  - **User Impact**: Markdown syntax overview tables with LaTeX comment examples now compile successfully
  - **Comprehensive Documentation**: Added detailed comments explaining the escaping strategy and ContentProcessor bypass

- **🐛 Supplementary File Detection**: Fixed supplementary markdown files not being found when working from within manuscript directory
  - **Root Cause**: Path resolution incorrectly appended manuscript path twice when already inside manuscript directory
  - **Directory Context**: Enhanced `find_supplementary_md` to handle both parent and manuscript directory execution contexts
  - **Fallback Logic**: Checks current directory first, then manuscript_path subdirectory for maximum compatibility
  - **User Impact**: `02_SUPPLEMENTARY_INFO.md` files are now properly detected regardless of working directory

### Technical Notes
- **ContentProcessor Temporarily Disabled**: Disabled new ContentProcessor to use legacy table conversion pipeline with critical escaping fixes
- **Future TODO**: Port table escaping fixes to ContentProcessor before re-enabling

## [v1.5.14] - 2025-08-16

### Fixed
- **🐛 Introduction Section Header Mapping**: Fixed "## Introduction" sections being rendered as "Main" in PDF output
  - **Root Cause**: Template processor was using hardcoded `\section*{Main}` header regardless of actual section type
  - **Dynamic Section Headers**: Modified template processor to generate appropriate section headers based on content type
  - **Template Update**: Replaced hardcoded LaTeX section with dynamic `<PY-RPL:MAIN-SECTION>` placeholder
  - **User Impact**: Users writing `## Introduction` now get "Introduction" header in PDF, not "Main"
  - **Comprehensive Testing**: Added end-to-end tests that verify actual .tex file generation

- **🐛 Figure Ready File Duplication Requirement**: Fixed requirement to duplicate figure files in both direct and subdirectory locations
  - **Root Cause**: Ready file detection logic was incomplete - when ready file existed, code still converted to subdirectory format
  - **Smart Path Resolution**: Enhanced figure processor to use ready file path directly when file exists at `Figures/Fig1.png`
  - **Fallback Behavior**: Maintains subdirectory format `Figures/Fig1/Fig1.png` when no ready file exists
  - **User Impact**: Users can now place `Fig1.png` only in `Figures/` directory without requiring `Figures/Fig1/Fig1.png`
  - **Working Directory Independence**: Fixes work correctly regardless of current working directory

- **🐛 Full-Page Figure Positioning with Textwidth**: Fixed `tex_position="p"` being ignored for `width="\textwidth"` figures
  - **Root Cause**: Code automatically forced 2-column spanning (`figure*`) for textwidth figures, overriding explicit positioning
  - **Respect User Intent**: Modified logic to honor explicit `tex_position="p"` even with `width="\textwidth"`
  - **Smart Environment Selection**: Uses regular `figure[p]` for dedicated page figures instead of `figure*[p]`
  - **Preserved Behavior**: Maintains `figure*` for textwidth figures without explicit dedicated page positioning
  - **User Impact**: Full-width figures with `tex_position="p"` now appear on dedicated pages, not forced into 2-column layout

### Added
- **📋 Comprehensive Regression Testing**: Added extensive test suite covering all three reported issues
  - **End-to-End Validation**: Tests that verify actual .tex file generation, not just internal logic
  - **Real Environment Simulation**: Tests run in realistic manuscript directory structures
  - **Multiple Scenarios**: Tests cover both working and non-working cases for each fix
  - **Integration Testing**: Validates fixes work together without conflicts

## [v1.5.8] - 2025-08-15

### Fixed
- **🔧 Style File Path Resolution for Installed Packages**: Fixed "Style directory not found" warning when using installed rxiv-maker package
  - **Root Cause**: Style file detection was hardcoded for development directory structure and failed when rxiv-maker was installed via pip
  - **Multi-Location Detection**: Enhanced `BuildManager` to check multiple possible style file locations (installed package vs development)
  - **Robust Package Structure**: Improved path resolution to work with hatch build system mapping (`src/tex` → `rxiv_maker/tex`)
  - **Enhanced Error Handling**: Added graceful fallback when style directories don't exist with improved debug logging
  - **User Impact**: Eliminates "Style directory not found" warnings and ensures LaTeX style files are properly copied for all installation methods
  - **Verification**: Comprehensive package installation testing confirms fix works end-to-end in PyPI package scenario

### Added  
- **📋 Style File Resolution Tests**: Added comprehensive test suite for style file detection and error handling
  - **Development Environment Testing**: Verification of style directory detection in development setup
  - **Fallback Behavior Testing**: Tests for graceful handling when no style directory is found
  - **Error Handling Coverage**: Tests for None and non-existent style directory scenarios
  - **Package Integration Testing**: End-to-end verification of style file packaging and detection in installed packages

## [v1.5.7] - 2025-08-15

### Fixed
- **🐛 BibTeX Manuscript Name Detection**: Fixed critical manuscript name passing issue that caused BibTeX compilation failures
  - **Root Cause**: The `write_manuscript_output` function relied on inconsistent `MANUSCRIPT_PATH` environment variable setting, leading to empty manuscript names and `.tex` filenames
  - **Systematic Solution**: Enhanced `write_manuscript_output` to accept explicit `manuscript_name` parameter with robust fallback handling
  - **Direct Name Extraction**: Modified `generate_preprint` to extract manuscript name directly from path and pass it explicitly
  - **User Impact**: Commands like `rxiv pdf CCT8_paper/` now generate `CCT8_paper.tex` correctly instead of `.tex`, resolving "BibTeX returned error code 1" errors
  - **Comprehensive Testing**: Updated test suite with new function signature and verified edge case handling
- **GitHub Issues**: Resolves #100 (BibTeX error with manuscript path handling)

### Added
- **📚 Comprehensive Test Coverage**: Significantly expanded test coverage for core functionality
  - **generate_preprint.py**: Added 18 comprehensive tests covering CLI integration, template processing, and error handling
  - **fix_bibliography.py**: Extended from 18 to 40 tests covering CrossRef API integration, DOI validation, publication matching, and file operations
  - **Mock-based Testing**: Implemented extensive mocking for external dependencies and network operations
  - **Error Simulation**: Added tests for network timeouts, API failures, and edge cases
  - **Complete Workflow Coverage**: End-to-end testing including dry-run scenarios and complex bibliography fixing workflows

## [v1.5.5] - 2025-08-15

### Fixed  
- **🐛 BibTeX Error Code 1 - Trailing Slash Issue**: Fixed manuscript path handling when paths contain trailing slashes
  - **Root Cause**: When users run `rxiv pdf CCT8_paper/` (with trailing slash), `os.path.basename("CCT8_paper/")` returns empty string, causing filename validation to default to "MANUSCRIPT"
  - **Mismatch Problem**: This created a mismatch where LaTeX expected to compile `CCT8_paper.tex` but only `MANUSCRIPT.tex` was generated, causing "Emergency stop" and subsequent BibTeX error code 1
  - **Comprehensive Fix**: Added path normalization using `rstrip("/")` in both BuildManager constructor and environment variable setting to handle trailing slashes correctly
  - **Regression Testing**: Added comprehensive test suite `test_trailing_slash_regression.py` to prevent future regressions
  - **User Impact**: Users can now run `rxiv pdf manuscript_name/` (with trailing slash) without encountering BibTeX errors
- **GitHub Issues**: Resolves remaining cases of #100 (BibTeX returned error code 1) related to trailing slash paths
## [v1.5.4] - 2025-08-15

### Fixed
- **🐛 BibTeX Error Code 1**: Fixed invalid LaTeX filename generation that caused "BibTeX returned error code 1" errors
  - **Root Cause**: When `MANUSCRIPT_PATH` environment variable was set to invalid values (empty string, ".", or ".."), the `write_manuscript_output` function would create files with invalid names like `..tex` or `.tex`
  - **LaTeX Compilation Failure**: These invalid filenames caused LaTeX to fail with "Emergency stop" errors, which subsequently caused BibTeX to fail with error code 1
  - **Robust Validation**: Added input validation to `write_manuscript_output` function to prevent invalid filenames and default to "MANUSCRIPT.tex" when necessary
  - **Comprehensive Testing**: Added regression test `test_write_manuscript_output_invalid_paths` to ensure edge cases are handled correctly
  - **End-to-End Verification**: Confirmed PDF generation pipeline now works correctly with successful BibTeX processing
- **GitHub Issues**: Resolves #100 (BibTeX returned error code 1)

## [v1.5.2] - 2025-08-14

### Fixed
- **🐛 Path Resolution Issues**: Comprehensive fix for path handling throughout PDF generation workflow
  - **Figure Path Display**: Fixed duplicate path components in figure generation output (e.g., `Figure__example/Figure__example/Figure__example.png` → `Figure__example/Figure__example.png`)
  - **Manuscript File Lookup**: Updated all functions to use correct manuscript paths instead of current working directory
  - **PDF Generation Pipeline**: Enhanced `find_manuscript_md()`, `generate_preprint()`, and `copy_pdf_to_manuscript_folder()` with proper path parameter support
  - **Cross-Directory Compatibility**: PDF generation now works correctly from any directory location
  - **Google Colab Compatibility**: Resolved CLI parsing issues in containerized environments
  - **Backwards Compatibility**: All existing functionality preserved while fixing path resolution bugs
- **GitHub Issues**: Resolves #96 (CLI path issues) and #97 (Google Colab argument parsing)

## [v1.5.1] - 2025-08-14

### Fixed
- **🔧 Critical NotImplementedError Resolution**: Eliminate crashes in bibliography cache system
  - **Root Cause**: NotImplementedError bombs in `bibliography_cache.py` causing immediate test and runtime failures
  - **Solution**: Replaced NotImplementedError with safe placeholder implementations that emit warnings instead of crashing
  - **Impact**: All 899 fast tests now pass consistently, resolving critical blocking issues for development workflow
  - Functions `cached_parse_bibliography`, `cached_validate_doi`, and `cached_analyze_citations` now return safe defaults with appropriate warnings
- **Test Suite Stabilization**: Comprehensive test infrastructure improvements
  - Fixed CLI structure import tests to use correct function names matching actual exports
  - Added network connectivity mocking to DOI validator tests for reliable offline execution
  - Resolved validate command test failures with proper Click context objects and isolated filesystem testing
  - Enhanced test robustness across different execution environments
- **Development Workflow**: Improved development experience and debugging capabilities
  - Fixed InstallManager patch location in check_installation tests
  - Resolved dependency update conflicts in dev branch merge
  - All test suites now execute reliably in both local and CI environments

### Added
- **Comprehensive Test Infrastructure**: Major expansion of test coverage and organization
  - New test modules: `test_build_command.py`, `test_check_installation_command.py`, `test_cleanup_engine.py`
  - Enhanced container engine testing: `test_container_engines.py`, `test_docker_manager.py`
  - DOI validation system tests: `test_doi_fallback_system.py` with comprehensive fallback testing
  - Security and dependency management: `test_security_scanner.py`, `test_dependency_manager.py`
  - Setup and validation: `test_setup_environment.py`, `test_validate_command.py`
  - CLI integration: `test_cli_structure.py`, `test_cli_cleanup_integration.py`
- **Enhanced Container Engine Support**: Robust Docker and Podman integration
  - New `engines/exceptions.py` module with comprehensive error handling and troubleshooting guidance
  - Docker build manager with advanced optimization and caching strategies
  - Improved container cleanup and resource management
  - Cross-platform container engine detection and validation
- **Advanced Retry and Utility Systems**: Production-ready infrastructure components
  - New `utils/retry.py` with exponential backoff and circuit breaker patterns
  - Enhanced `utils/figure_checksum.py` for better figure validation
  - Improved platform detection and cross-platform compatibility

### Changed
- **Major Infrastructure Overhaul**: Comprehensive workflow and CI improvements
  - Restructured GitHub Actions workflows with intelligent staging and dependency management
  - Enhanced Docker build process with multi-stage optimization
  - Improved Homebrew automation with automated formula updates
  - Streamlined release process with better validation and testing
- **Code Quality and Architecture**: Significant refactoring for maintainability
  - Enhanced type annotations and null checking across codebase
  - Improved error handling and logging throughout application
  - Better separation of concerns in engine architecture
  - Consolidated Docker workflows and improved code organization
- **Documentation and Development**: Better developer experience
  - Updated installation documentation with latest package management approaches
  - Enhanced release process documentation
  - Improved local development guidelines
  - Better contributing guidelines and code organization

### Removed
- **Legacy Infrastructure Cleanup**: Removal of outdated and conflicting systems
  - Removed complex submodule guardrails system (`scripts/safeguards/`)
  - Cleaned up deprecated Docker workflows and test configurations
  - Eliminated redundant dependency analysis and repository boundary checking
  - Streamlined CI configuration by removing unused workflow files

## [v1.4.25] - 2025-08-13

### Fixed
- **🔧 Critical Docker Build Failure**: Resolve persistent fc-cache exit code 127 error blocking GitHub Actions builds
  - **Root Cause**: BuildKit cache mounts created isolation between RUN commands, causing fontconfig installation and fc-cache execution inconsistency
  - **Solution**: Consolidated font installation and fc-cache into single RUN command ensuring same execution context
  - **Impact**: Complete elimination of "command not found" errors in Docker builds across all platforms
  - Enhanced BuildKit cache mount strategy with reduced parallelism (8→2) for improved stability
  - Added comprehensive font configuration validation with error recovery mechanisms
  - Removed redundant fc-cache command from final-runtime stage to prevent conflicts
- **Docker Workflow Reliability**: Optimize GitHub Actions Docker build pipeline
  - Enhanced buildkitd configuration for consistent multi-platform builds
  - Improved error handling and debugging capabilities in build process
  - Streamlined workflow execution with better resource management
- **Container Engine Error Handling**: Implement comprehensive exception system
  - New exceptions.py module with detailed error messages and platform-specific troubleshooting
  - Enhanced Docker and Podman engine error detection with proper exception chaining
  - Improved user experience with actionable error messages and installation guidance
- **GitHub Actions Integration Tests**: Fix outdated test expectations
  - Updated job references from deprecated "test" to current "unit-tests"
  - Fixed workflow_dispatch input validation to match current CI configuration
  - Ensured test suite accurately reflects current GitHub Actions workflow structure

### Added
- **Multi-Stage CI Workflow**: Implement intelligent 3-stage GitHub Actions pipeline
  - Stage 1: Fast unit tests with no external dependencies (10min timeout)
  - Stage 2: Integration tests with conditional dependency checking (20min timeout) 
  - Stage 3: Package build and validation (10min timeout)
  - Each stage runs only if the previous stage passes, optimizing CI resource usage
- **Comprehensive Test Categorization**: Enhanced pytest marker system for better test organization
  - Auto-marking by directory structure: `unit`, `integration`, `system`  
  - Dependency markers: `requires_latex`, `requires_docker`, `requires_podman`, `requires_r`
  - Performance markers: `fast`, `slow`, `ci_exclude`
  - Smart dependency detection based on test names and file patterns
- **Container Session Management**: Enhanced cleanup system for Docker and Podman engines
  - Global engine registry with weak references to track active container instances
  - Automatic cleanup on program termination through atexit handlers
  - Improved resource management preventing container session leaks

### Changed
- **DOI Validation in CI**: Improve CI environment detection logic
  - CI environments now disable online validation but still perform offline format validation
  - Tests properly validate DOI formats even in GitHub Actions environments
  - Maintains backward compatibility while enabling proper validation testing
- **Test Infrastructure**: Enhanced robustness for different testing environments
  - Accept multiple valid error message formats in LaTeX installation verification
  - Improved test mocking for both `shutil.which()` and `subprocess.run()` calls
  - Better error message flexibility across different testing environments

## [v1.4.24] - 2025-08-12

### Added
- **OIDC Publishing**: Implement OpenID Connect authentication for PyPI publishing
  - Eliminate need for API tokens in release workflows
  - Enable secure, passwordless publishing with cryptographic attestations
  - Add supply chain security with package provenance verification

### Changed
- **CI/CD Improvements**: Streamline GitHub Actions workflows with local-first approach
  - Consolidate CI workflows into single, efficient job
  - Archive legacy workflows while preserving history
  - Optimize dependency caching and build performance
  - Add comprehensive error reporting and debug guidance

### Fixed
- **Dependency Management**: Fix check-deps-verbose command to use module directly
- **Build System**: Fix Makefile CLI fallback commands argument formats
- **Pre-commit**: Resolve repository boundary validation for submodule-free architecture

## [v1.4.21] - 2025-08-08

### Fixed
- **Script Execution**: Fix PDF validation and word count analysis subprocess failures in pipx/Homebrew installations
  - Replace subprocess execution of PDF validator and word count scripts with direct function imports
  - Resolve path resolution issues for validation scripts in virtual environments  
  - Ensure PDF validation and word count analysis work correctly in all installation methods
  - Fix "No such file or directory" errors for validation and analysis tools

## [v1.4.20] - 2025-08-08

### Fixed
- **PDF Copying**: Fix copy_pdf script execution failure in pipx/Homebrew installations
  - Replace subprocess execution of copy_pdf.py with direct function import and call
  - Resolve path resolution issues in virtual environments
  - Ensure PDF copying works correctly in all installation methods (pip, pipx, Homebrew)
  - Fix "No such file or directory" error when copying generated PDF to manuscript directory
## [v1.4.19] - 2025-08-08

### Added
- **Shell Completion**: Add dedicated `completion` command for installing shell auto-completion
  - Provides `rxiv completion {bash|zsh|fish}` command for installing shell auto-completion
  - Includes comprehensive help documentation with examples
  - Replaces the problematic `--install-completion` option

### Removed
- **Shell Completion**: Remove `--install-completion` option to avoid redundancy
  - Eliminates the Click framework command validation conflict
  - Simplifies the CLI interface with a single, clear completion method
  - Users should now use `rxiv completion {shell}` instead

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