# Submodule Guardrails Documentation

This document describes the comprehensive guardrails system implemented to protect all submodules from contamination and ensure repository integrity.

## Overview

Each submodule now has its own protection system to prevent contamination from other repositories, ensuring clean separation between:
- **Main rxiv-maker project** (Python-based scientific article generator)
- **Homebrew tap** (macOS/Linux package manager)
- **Scoop bucket** (Windows package manager) 
- **VSCode extension** (development environment integration)

## Implemented Guardrails

### 1. Homebrew Submodule (`submodules/homebrew-rxiv-maker`)

**Protection Against:**
- Main project files (Python, YAML, Makefile)
- Other package managers (Scoop, VSCode)
- Cross-contamination patterns

**Implementation:**
- `.gitignore` - Prevents accidental staging of forbidden files
- `.pre-commit-config.yaml` - Pre-commit hooks for validation
- `scripts/validate-homebrew-integrity.sh` - Comprehensive validation script

**Key Validations:**
- Formula structure (`Formula/rxiv-maker.rb`)
- Ruby class inheritance (`RxivMaker < Formula`)
- Python virtualenv integration
- Absence of contaminating files

### 2. Scoop Submodule (`submodules/scoop-rxiv-maker`)

**Protection Against:**
- Main project files (Python, YAML, Makefile)
- Homebrew files (Formula/, *.rb)
- VSCode extension files

**Implementation:**
- `.gitignore` - Contamination prevention patterns
- `.pre-commit-config.yaml` - PowerShell-based pre-commit validation
- `scripts/validate-scoop-integrity.ps1` - PowerShell validation script

**Key Validations:**
- Manifest structure (`bucket/rxiv-maker.json`)
- JSON validity and required fields
- Python dependency configuration
- PyPI URL validation

### 3. VSCode Extension Submodule (`submodules/vscode-rxiv-maker`)

**Protection Against:**
- Main project files (Python, LaTeX, Docker)
- Package manager files (Homebrew, Scoop)
- Build system contamination

**Implementation:**
- `.gitignore` - Comprehensive file exclusion patterns
- `.pre-commit-config.yaml` - Node.js-based validation hooks
- `scripts/validate-vscode-integrity.js` - JavaScript validation script

**Key Validations:**
- Extension manifest (`package.json`) structure
- VSCode engine requirements
- TypeScript configuration validity
- Contribution definitions (languages, grammars, commands)

## Testing Framework

### Individual Submodule Testing

Each submodule can be tested independently:

```bash
# Homebrew validation
cd submodules/homebrew-rxiv-maker
./scripts/validate-homebrew-integrity.sh

# VSCode validation  
cd submodules/vscode-rxiv-maker
node scripts/validate-vscode-integrity.js

# Scoop validation (requires PowerShell)
cd submodules/scoop-rxiv-maker
powershell.exe -ExecutionPolicy Bypass -File scripts/validate-scoop-integrity.ps1
```

### Comprehensive Testing

From the main repository:

```bash
# Test all submodule guardrails
make test-submodule-guardrails

# Test main repository safeguards
make test-safeguards

# Validate repository integrity
make validate-repo

# Run all validations
make validate-all
```

## Contamination Detection

### Types of Contamination Detected

1. **Forward Contamination**: Main project files in submodules
   - Python files (*.py, pyproject.toml, requirements.txt)
   - Build system files (Makefile, noxfile.py)
   - Docker files (Dockerfile, docker-compose.yml)

2. **Cross Contamination**: Package manager files in wrong submodules
   - Homebrew files in Scoop/VSCode submodules
   - Scoop files in Homebrew/VSCode submodules
   - VSCode files in package manager submodules

3. **Reverse Contamination**: Submodule files in main repository
   - Formula/ directories outside submodules
   - VSCode extension files in main project
   - Package manager manifests in wrong locations

### Detection Methods

1. **File Pattern Matching**: Identify files by extension and name
2. **Content Validation**: Parse and validate configuration files
3. **Structure Analysis**: Verify required directories and files exist
4. **Cross-Reference Checks**: Ensure files are in correct repositories

## Automation and CI Integration

### Pre-commit Hooks

Each submodule has pre-commit hooks configured:
- Automatic validation before commits
- Language-specific linting and formatting
- Repository boundary checking

### GitHub Actions

The main repository includes CI workflows:
- Daily integrity checks
- PR validation
- Deep validation on schedule
- Automated reporting

### Developer Workflow

1. **Development**: Normal development in any submodule
2. **Pre-commit**: Automatic validation prevents contaminated commits
3. **Push**: GitHub Actions provide additional validation
4. **Monitoring**: Daily checks catch any drift or issues

## Troubleshooting

### Common Issues

1. **False Positives**: Some files may trigger warnings
   - Review validation output for context
   - Check if files belong in different locations
   - Update .gitignore patterns if needed

2. **Pre-commit Failures**: Validation catches contamination
   - Check what files were added/modified
   - Move files to correct repository locations
   - Remove files that don't belong

3. **CI Failures**: GitHub Actions detect issues
   - Review workflow logs for specific problems
   - Run local validation: `make validate-repo`
   - Fix issues before pushing changes

### Manual Recovery

If contamination is detected:

1. **Identify Source**: Review validation error messages
2. **Remove Contamination**: Delete or move offending files
3. **Verify Fix**: Run validation again
4. **Commit Clean State**: Ensure all validations pass

## Benefits

### Repository Integrity
- Clean separation between project components
- Prevents accidental file mixing
- Maintains package manager conventions

### Developer Experience  
- Clear error messages guide fixes
- Automated prevention of common mistakes
- Easy testing and validation commands

### Maintenance
- Automated monitoring catches issues early
- Documentation provides clear guidance
- Testing framework ensures reliability

## Files Created/Modified

### Main Repository
- `scripts/test-submodule-guardrails.sh` - Testing framework
- `Makefile` - Added `test-submodule-guardrails` target
- `docs/SUBMODULE_GUARDRAILS.md` - This documentation

### Homebrew Submodule
- `.gitignore` - Enhanced contamination prevention
- `.pre-commit-config.yaml` - Validation hooks
- `scripts/validate-homebrew-integrity.sh` - Validation script

### Scoop Submodule  
- `.gitignore` - Enhanced contamination prevention
- `.pre-commit-config.yaml` - PowerShell validation hooks
- `scripts/validate-scoop-integrity.ps1` - PowerShell validation script

### VSCode Submodule
- `.gitignore` - Created comprehensive exclusion patterns
- `.pre-commit-config.yaml` - Node.js validation hooks  
- `scripts/validate-vscode-integrity.js` - JavaScript validation script
- `tsconfig.json` - Fixed JSON syntax issues

## Conclusion

The submodule guardrails system provides comprehensive protection against repository contamination through:

- **Multi-layer defense**: Prevention, detection, and reporting
- **Automated enforcement**: Pre-commit hooks and CI validation
- **Developer-friendly**: Clear error messages and easy testing
- **Comprehensive coverage**: All contamination types detected
- **Cross-platform support**: Works on Windows, macOS, and Linux

This system ensures the integrity of all repositories in the rxiv-maker ecosystem while maintaining developer productivity and code quality.