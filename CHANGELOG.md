# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [v1.7.8] - 2025-01-16

### Added
- **Underlined Text Formatting**: Support for `__text__` markdown syntax to create underlined text.

## [v1.7.7] - 2025-01-15

### Added
- Comprehensive manuscript improvements and validation enhancements.

## [v1.7.0] - 2025-01-08

### Added
- **Installation Streamlining**: Simplified installation to a single `pip` or `pipx` command.
- **Centralized Data Management**: Introduced `DATA` directories for better dataset organization.

### Fixed
- Improved DOI validation caching for better performance.

## [v1.6.4] - 2025-09-04

### Added
- **Dynamic Version Injection**: Acknowledgment text now includes the `Rxiv-Maker` version.
- **Python Code Execution**: Execute Python code directly within markdown files.
- **Blindtext Command**: Added `{{blindtext}}` and `{{Blindtext}}` commands for placeholder text.
- **Custom Command Framework**: Extensible framework for adding new custom commands.

## [v1.6.0] - 2025-08-20

### Added
- **Documentation Consolidation**: Major overhaul and simplification of the documentation.

## [v1.5.16] - 2025-08-16

### Added
- **E2E Testing Framework**: Added a comprehensive end-to-end testing framework.

### Fixed
- **Figure Placement**: Fixed issues with full-page figure placement.
- **APT Repository**: Completed APT repository integration for Debian-based systems.

## [v1.5.12] - 2025-08-15

### Added
- **APT Repository**: Infrastructure for APT repository for Debian-based systems.

## [v1.5.8] - 2025-08-15

### Fixed
- **Style File Path Resolution**: Fixed issues with locating style files in installed packages.

## [v1.5.7] - 2025-08-15

### Fixed
- **BibTeX Manuscript Name Detection**: Fixed a critical issue with manuscript name handling that caused BibTeX errors.

## [v1.5.5] - 2025-08-15

### Fixed
- **BibTeX Trailing Slash Issue**: Fixed an issue where a trailing slash in the manuscript path would cause BibTeX to fail.

## [v1.5.4] - 2025-08-15

### Fixed
- **BibTeX Error Code 1**: Fixed an issue that caused invalid LaTeX filenames to be generated.

## [v1.5.2] - 2025-08-14

### Fixed
- **Path Resolution**: Fixed path handling issues in the PDF generation workflow.

## [v1.5.0] - 2025-08-13

### Added
- **Foundation Hardening**: Major effort to improve stability and test coverage.

## [v1.4.25] - 2025-08-13

### Added
- **Multi-Stage CI Workflow**: Implemented an intelligent 3-stage GitHub Actions pipeline.
- **Test Categorization**: Enhanced pytest marker system for better test organization.

## [v1.4.24] - 2025-08-12

### Added
- **OIDC Publishing**: Implemented OpenID Connect authentication for PyPI publishing.

## [v1.4.19] - 2025-08-08

### Added
- **Shell Completion**: Added a dedicated `completion` command for installing shell auto-completion.

## [v1.4.16] - 2025-08-06

### Changed
- **Citation**: Migrated from Zenodo to arXiv citation.

## [v1.4.13] - 2025-08-04

### Fixed
- **Security**: Fixed xml2js prototype pollution vulnerability (CVE-2023-0842).

## [v1.4.5] - 2025-07-19

### Fixed
- **CRITICAL**: Fixed an issue where LaTeX template files were missing from the PyPI package.

## [v1.4.0] - 2025-07-18

### Changed
- **Package Installation**: `pip install` no longer installs system dependencies automatically. A new command `rxiv-install-deps` is available for that.

## [v1.3.0] - 2025-07-14

### Added
- **Change Tracking System**: Generate PDFs with highlighted changes between versions using `latexdiff`.
- **Docker-Accelerated Google Colab**: A new Colab notebook that uses Docker for a much faster setup.
- **Docker Engine Mode**: Run all operations within a Docker container.
- **Cross-Platform Compatibility**: Full support for Windows, macOS, and Linux.

## [v1.2.0] - 2025-07-08

### Added
- **VS Code Extension**: Integration with a companion VS Code extension.

## [v1.1.1] - 2025-07-02

### Added
- **Enhanced DOI Validation**: Comprehensive DOI validation with support for multiple registrars.
- **Bibliography Management**: New commands to add and fix bibliography entries.
- **Mermaid CLI Support**: Support for Mermaid CLI for generating diagrams.

## [v1.1.0] - 2025-07-02

### Added
- **R Script Support**: Support for R scripts in the figure generation pipeline.

## [v1.0.2] - 2025-07-02

### Added
- **Automatic Python Figure Generation**: Automatically execute Python scripts in the `FIGURES` directory.

## [v1.0.0] - 2025-06-26

### Added
- **Core Features**: Initial release of `rxiv-maker` with a complete manuscript generation system.
