# Package Management System Documentation

## Overview

This document describes the enhanced package management automation system for rxiv-maker. The system uses a template-based approach to ensure robust, reliable, and maintainable package manager updates.

## Architecture

### Components

1. **Template Files**: Standardized templates with placeholders for dynamic values
2. **Validation Scripts**: Scripts to validate template integrity and generated files
3. **Update Scripts**: Scripts to generate package files from templates
4. **Orchestration Scripts**: Scripts to coordinate updates across multiple package managers
5. **Enhanced Workflows**: GitHub Actions workflows with improved error handling and rollback capabilities

### File Structure

```
rxiv-maker/
├── scripts/
│   ├── validate-package-templates.py     # Template validation
│   ├── update-package-templates.py       # Template processing
│   ├── orchestrate-release.py           # Release orchestration
│   └── test-package-system.py           # System testing
├── submodules/
│   ├── homebrew-rxiv-maker/
│   │   ├── Formula/
│   │   │   ├── rxiv-maker.rb.template   # Homebrew template
│   │   │   └── rxiv-maker.rb            # Generated formula
│   │   └── .github/workflows/
│   │       └── update-formula.yml       # Enhanced workflow
│   └── scoop-rxiv-maker/
│       ├── bucket/
│       │   ├── rxiv-maker.json.template # Scoop template
│       │   └── rxiv-maker.json          # Generated manifest
│       └── .github/workflows/
│           └── update-manifest.yml      # Enhanced workflow
└── .github/workflows/
    └── release.yml                      # Main release workflow
```

## Template System

### Placeholder Format

All templates use double curly brace placeholders: `{{PLACEHOLDER_NAME}}`

### Homebrew Template Placeholders

- `{{VERSION}}`: Full version string (e.g., "v1.4.8")
- `{{MACOS_ARM64_SHA256}}`: SHA256 hash for macOS ARM64 binary
- `{{MACOS_X64_SHA256}}`: SHA256 hash for macOS x64 binary
- `{{LINUX_X64_SHA256}}`: SHA256 hash for Linux x64 binary

### Scoop Template Placeholders

- `{{VERSION}}`: Full version string (e.g., "v1.4.8")
- `{{VERSION_NUM}}`: Version number without 'v' prefix (e.g., "1.4.8")
- `{{WINDOWS_X64_SHA256}}`: SHA256 hash for Windows x64 binary

## Scripts

### validate-package-templates.py

Validates template integrity and generated files.

**Usage:**
```bash
python validate-package-templates.py validate-templates
python validate-package-templates.py validate-checksum <file> <expected_hash>
```

**Features:**
- Template structure validation
- Placeholder verification
- Ruby syntax checking (Homebrew)
- JSON structure validation (Scoop)
- Checksum verification

### update-package-templates.py

Generates package files from templates with downloaded binaries and calculated checksums.

**Usage:**
```bash
python update-package-templates.py <command> <version> [--dry-run]
```

**Commands:**
- `homebrew <version>`: Update Homebrew formula
- `scoop <version>`: Update Scoop manifest
- `all <version>`: Update all package managers

**Features:**
- Automatic binary downloading with retry logic
- SHA256 checksum calculation
- Template processing with validation
- Dry-run mode for testing
- Comprehensive error handling

### orchestrate-release.py

Orchestrates package manager updates across multiple repositories.

**Usage:**
```bash
python orchestrate-release.py <command> <version> [options]
```

**Commands:**
- `orchestrate <version>`: Full release orchestration
- `test <version>`: Test release readiness
- `validate <version>`: Validate release exists

**Options:**
- `--dry-run`: Show what would be done without making changes
- `--token <token>`: GitHub token (or use GITHUB_TOKEN env var)

**Features:**
- Release readiness validation
- Asset availability checking
- Workflow triggering via repository dispatch
- Status monitoring and reporting
- Comprehensive logging

### test-package-system.py

Comprehensive testing suite for the package management system.

**Usage:**
```bash
python test-package-system.py [test-name]
```

**Available Tests:**
- `dependencies`: Test script dependencies
- `permissions`: Test file permissions  
- `templates`: Test template integrity
- `validation`: Test template validation
- `updates`: Test template updates (dry run)
- `orchestration`: Test orchestration script
- `workflows`: Test workflow files
- `all` (default): Run all tests

## Enhanced Workflows

### Homebrew Workflow (update-formula.yml)

**Improvements:**
- Python-based template processing
- Comprehensive validation steps
- Automatic backup and rollback
- Dry-run support
- Enhanced error handling
- Detailed status reporting

**Trigger Methods:**
- Repository dispatch from main release workflow
- Manual workflow dispatch with dry-run option

### Scoop Workflow (update-manifest.yml)

**Improvements:**
- Python-based template processing
- JSON validation with PowerShell
- Scoop installation testing
- Automatic backup and rollback
- Cross-platform shell scripting
- Enhanced error reporting

**Trigger Methods:**
- Repository dispatch from main release workflow
- Manual workflow dispatch with dry-run option

### Main Release Workflow Integration

The main release workflow now includes:
1. Release readiness validation
2. Package manager readiness testing
3. Coordinated update orchestration
4. Comprehensive status reporting
5. Graceful failure handling

## Error Handling and Rollback

### Automatic Rollback

Both package manager workflows include automatic rollback mechanisms:

1. **Backup Creation**: Current files are backed up before updates
2. **Validation Failure Detection**: Multiple validation steps catch errors
3. **Automatic Restoration**: Failed updates trigger automatic rollback
4. **Commit Rollback**: Rollback changes are committed if necessary

### Error Scenarios

- **Network Failures**: Retry logic with exponential backoff
- **Invalid Checksums**: Validation prevents deployment of corrupted files
- **Template Errors**: Pre-processing validation catches template issues
- **Syntax Errors**: Language-specific validation prevents broken packages
- **Missing Assets**: Release validation ensures all required files exist

## Testing

### Manual Testing

```bash
# Test template validation
python scripts/validate-package-templates.py validate-templates

# Test template updates (dry run)
python scripts/update-package-templates.py all v1.0.0-test --dry-run

# Test orchestration (requires GitHub token)
export GITHUB_TOKEN="your-token"
python scripts/orchestrate-release.py test v1.0.0-test

# Run comprehensive test suite
python scripts/test-package-system.py
```

### Automated Testing

The system includes comprehensive automated testing:
- Template integrity validation
- Script dependency checking
- Dry-run functionality testing
- Workflow structure validation
- Permission verification

## Best Practices

### Version Management

1. Always use semantic versioning (e.g., v1.4.8)
2. Ensure GitHub releases include all required binary assets
3. Test updates with dry-run mode before actual deployment

### Security

1. Use dedicated GitHub tokens with minimal required permissions
2. Validate all downloaded files with checksum verification
3. Never commit secrets or tokens to repositories

### Maintenance

1. Regularly test the system with `test-package-system.py`
2. Monitor workflow logs for any warnings or issues
3. Keep templates synchronized with package manager requirements
4. Update dependencies and tools as needed

## Troubleshooting

### Common Issues

**Template Validation Failures:**
- Check template syntax and required placeholders
- Verify Ruby/JSON structure is valid
- Ensure all required sections are present

**Update Script Failures:**
- Verify network connectivity for binary downloads
- Check GitHub release exists and contains required assets
- Validate version format (must start with 'v')

**Workflow Failures:**
- Check GitHub token permissions
- Verify repository dispatch configuration
- Review workflow logs for specific error messages

**Orchestration Issues:**
- Ensure release assets are accessible
- Check package manager repository permissions
- Verify workflow triggers are configured correctly

### Debug Commands

```bash
# Validate specific template
python scripts/validate-package-templates.py validate-templates

# Test update with verbose output
python scripts/update-package-templates.py all v1.0.0-test --dry-run

# Check release readiness
python scripts/orchestrate-release.py validate v1.4.8

# Run specific tests
python scripts/test-package-system.py templates
```

## Migration from Legacy System

The new system is designed to be backward compatible while providing enhanced functionality:

1. **Template Creation**: Existing package files are used as basis for templates
2. **Placeholder Replacement**: Hard-coded values are replaced with placeholders
3. **Workflow Enhancement**: Existing workflows are enhanced with new features
4. **Gradual Rollout**: New system can be tested alongside existing system

## Future Enhancements

Potential improvements for the system:

1. **Additional Package Managers**: Support for Conda, Snap, AppImage
2. **Automated Testing**: Integration with package manager testing frameworks
3. **Monitoring**: Real-time monitoring of package availability
4. **Analytics**: Usage tracking and update success metrics
5. **Notification System**: Slack/email notifications for update status

## Contributing

When contributing to the package management system:

1. Test all changes with the comprehensive test suite
2. Update templates when adding new functionality
3. Maintain backward compatibility where possible
4. Document any new placeholders or configuration options
5. Test both successful and failure scenarios