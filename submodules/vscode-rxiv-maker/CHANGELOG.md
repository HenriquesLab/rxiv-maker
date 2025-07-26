# Change Log

All notable changes to the "rxiv-maker" VS Code extension will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.0.3] - 2025-01-10

### Added
- **Insert Table Reference command** - Find and insert references to tables with `@table:` or `@stable:` syntax
- **Insert Equation Reference command** - Find and insert references to equations with `@eq:` syntax  
- **Install rxiv-maker framework command** - Automated installation with dependency checking for git, make, python, and LaTeX
- **Cross-platform dependency validation** - Platform-specific installation instructions for Windows, macOS, and Linux
- **Workspace-aware installation** - Smart directory picker showing open workspace folders and common locations
- **Automatic directory creation** - Creates installation directories if they don't exist
- **Enhanced error handling** - Clear guidance when dependencies are missing with platform-specific solutions

### Changed
- **Improved figure reference detection** - Now searches both `01_MAIN.md` and `02_SUPPLEMENTARY_INFO.md` files instead of just current document
- **Enhanced label parsing** - Fixed regex to handle figure labels with additional attributes (e.g., `{#fig:label width="100%" tex_position="t"}`)
- **Corrected file naming** - Fixed search for `02_SUPPLEMENTARY_INFO.md` (was incorrectly looking for `02_SUPPLEMENTARY_INFORMATION.md`)
- **Better reference filtering** - Table and equation references now properly distinguish between regular and supplementary items

### Fixed
- **"No figure labels found" error** - Figure reference command now correctly finds all figures across manuscript files
- **Label attribute parsing** - Fixed regex pattern to handle labels with LaTeX positioning and sizing attributes
- **Cross-document reference detection** - All reference commands now search both main and supplementary files consistently

### Technical Improvements
- **Unified reference detection system** - Single `getDocumentReferences()` function handles all reference types
- **Enhanced command registration** - All new commands properly registered in package.json and extension context
- **Improved search logic** - Robust file discovery with fallback paths for different project structures
- **Better error messaging** - User-friendly error messages with specific guidance for resolution

## [0.0.2] - 2025-01-08

### Added
- Comprehensive README with detailed extension features and usage instructions
- Cross-references to main [Rxiv-Maker](https://github.com/HenriquesLab/rxiv-maker) repository
- Complete documentation of rxiv-markdown syntax support
- Installation and usage guides for different user types (beginners, teams, advanced users)
- Clear citation instructions for academic use with BibTeX and APA formats
- Related projects section linking to main framework and documentation
- Support badges showing extension capabilities (syntax highlighting, IntelliSense, etc.)

### Changed
- Updated package description to "Toolkit for scientific manuscript authoring with rxiv-maker"
- Enhanced README with professional academic styling consistent with main project
- Improved documentation structure with better organization and navigation

### Fixed
- Extension icon now has proper black background, eliminating white edges
- README badges converted from SVG to PNG-compatible format for VS Code marketplace compliance

### Removed
- Color theme functionality (themes directory and theme configuration)
- Unused theme files and related package.json entries

## [0.0.1] - 2025-01-08

### Added
- Initial release of Rxiv-Maker VS Code extension
- Syntax highlighting for rxiv-markdown files (.rxm, 01_MAIN.md, 02_SUPPLEMENTARY_INFO.md)
- Language configuration for rxiv-markdown
- Token colors for subscript, superscript, and document control elements
- IntelliSense support for citations and cross-references
- JSON schema validation for 00_CONFIG.yml files
- Commands for project management:
  - Insert Citation
  - Insert Figure Reference
  - Validate project structure
  - Build PDF
  - Clean build artifacts
  - Add bibliography entry by DOI
- Automatic workspace detection for rxiv-maker projects
- Configuration defaults for word wrapping in rxiv-markdown files

### Technical Details
- Built with TypeScript and esbuild
- Supports VS Code 1.101.0 and later
- MIT License
- Published by HenriquesLab