# CLI Modernization Changelog

This document tracks the evolution of Rxiv-Maker's command-line interface from traditional Make commands to the modern Click-based CLI.

## Overview

The CLI modernization initiative brings Rxiv-Maker into the modern Python ecosystem with a beautiful, user-friendly command-line interface that works consistently across all platforms.

## Timeline

### Phase 1: Foundation (Completed)
- ✅ Click framework integration
- ✅ Rich terminal output with colors and progress bars
- ✅ Command structure design
- ✅ Core command implementation

### Phase 2: Feature Parity (Completed)
- ✅ All Make commands available in CLI
- ✅ Docker engine support
- ✅ Configuration management
- ✅ Auto-completion support

### Phase 3: Enhanced Features (Completed)
- ✅ Better error messages with suggestions
- ✅ Installation checker with auto-fix
- ✅ Update notifications
- ✅ Detailed version information

### Phase 4: Documentation (Completed)
- ✅ Migration guide for users
- ✅ Complete CLI reference
- ✅ Updated examples throughout docs
- ✅ This changelog

## Key Improvements

### User Experience
- **Intuitive Commands**: `rxiv pdf MY_PAPER/` instead of `MANUSCRIPT_PATH=MY_PAPER make pdf`
- **Rich Output**: Colors, progress bars, and formatted tables
- **Better Errors**: Actionable error messages with specific suggestions
- **Auto-completion**: Tab completion for all shells

### Developer Experience
- **Modern Stack**: Click, Rich, and modern Python patterns
- **Testable**: Comprehensive CLI tests with pytest
- **Extensible**: Easy to add new commands and options
- **Type Safety**: Full type hints throughout

### Cross-Platform Support
- **Windows**: First-class support with proper path handling
- **macOS**: Native experience including Apple Silicon
- **Linux**: Seamless integration with package managers

## Command Mapping

### Simplified Syntax
- Positional arguments: `rxiv pdf MY_PAPER/` vs `MANUSCRIPT_PATH=MY_PAPER make pdf`
- Named options: `rxiv pdf --force-figures` vs `make pdf FORCE_FIGURES=true`
- Subcommands: `rxiv bibliography fix` vs `make fix-bibliography`

### New Commands
- `rxiv check-installation`: System dependency checker
- `rxiv config`: Configuration management
- `rxiv version --detailed`: System information

### Enhanced Commands
- `rxiv validate --detailed`: Rich validation output
- `rxiv pdf --verbose`: Real-time progress tracking
- `rxiv figures --force`: Standalone figure generation

## Technical Details

### Architecture
```
rxiv_maker/
├── cli/
│   ├── main.py           # Entry point
│   ├── commands/         # Command implementations
│   │   ├── pdf.py
│   │   ├── validate.py
│   │   └── ...
│   ├── config.py         # Configuration management
│   └── utils/            # CLI utilities
```

### Dependencies
- `click>=8.0.0`: Command-line framework
- `rich>=13.0.0`: Terminal formatting
- `shellingham`: Shell detection
- `typer-config`: Configuration support

### Entry Points
```python
[project.scripts]
rxiv = "rxiv_maker.cli:main"
```

## Migration Support

### Backward Compatibility
- Make commands remain fully functional
- Both interfaces use the same underlying code
- Seamless interoperability

### Gradual Adoption
- Use CLI and Make commands together
- Environment variables work with both
- Configuration shared between interfaces

## Future Enhancements

### Planned Features
- Interactive mode for guided workflows
- Plugin system for custom commands
- Remote execution support
- Advanced caching strategies

### Under Consideration
- Web UI integration
- Cloud build support
- Collaborative features
- Template marketplace

## Breaking Changes

None. The CLI is purely additive - all existing Make commands continue to work exactly as before.

## Credits

The CLI modernization was inspired by:
- Poetry's elegant command structure
- Black's configuration approach
- Rich's beautiful terminal output
- Typer's intuitive design patterns

## Feedback

We welcome feedback on the new CLI:
- [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues): Bug reports
- [GitHub Discussions](https://github.com/henriqueslab/rxiv-maker/discussions): Feature requests
- [Twitter](https://twitter.com/henriqueslab): Quick feedback

## Version History

### v1.4.0 (Current)
- Full CLI implementation
- Complete feature parity with Make
- Comprehensive documentation
- Auto-completion support

### v1.3.0
- Initial CLI prototype
- Basic commands (pdf, validate)
- Click integration

### Pre-CLI Era
- Make-based interface only
- Platform-specific scripts
- Manual dependency management