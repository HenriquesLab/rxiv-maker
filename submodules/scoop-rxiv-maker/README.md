# Scoop Bucket for rxiv-maker

A [Scoop](https://scoop.sh/) bucket for installing [rxiv-maker](https://github.com/henriqueslab/rxiv-maker), an automated LaTeX article generation system.

## Installation

### Prerequisites
- Windows 10/11
- [Scoop](https://scoop.sh/) package manager

### Quick Install
```powershell
# Add the bucket
scoop bucket add henriqueslab https://github.com/henriqueslab/scoop-rxiv-maker.git

# Install rxiv-maker
scoop install rxiv-maker
```

### System Dependencies
rxiv-maker requires additional system dependencies for full functionality:

```powershell
# Install LaTeX distribution (recommended)
scoop bucket add extras
scoop install latex

# Or install MiKTeX
scoop install miktex

# Install Git (if not already available)
scoop install git

# Install Make (for legacy commands)
scoop install make
```

## Usage

After installation, the `rxiv` command will be available in your PATH:

```powershell
# Initialize a new manuscript
rxiv init

# Generate PDF
rxiv pdf

# Show help
rxiv --help

# Check version
rxiv version
```

## Updating

```powershell
# Update the bucket
scoop update

# Update rxiv-maker
scoop update rxiv-maker
```

## Uninstalling

```powershell
# Remove rxiv-maker
scoop uninstall rxiv-maker

# Remove the bucket (optional)
scoop bucket rm henriqueslab
```

## Troubleshooting

### Python Dependencies
rxiv-maker is a Python application and requires Python 3.11+. Scoop will automatically install Python if not present.

### LaTeX Issues
If you encounter LaTeX compilation errors:
1. Ensure a LaTeX distribution is installed (`scoop install latex` or `scoop install miktex`)
2. Check that `pdflatex` is available in your PATH
3. For advanced features, install the full TeX Live distribution

### Permission Issues
If you encounter permission errors:
1. Run PowerShell as Administrator
2. Check Windows execution policy: `Get-ExecutionPolicy`
3. If needed, set policy: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Development

This bucket automatically tracks releases from the [official rxiv-maker PyPI package](https://pypi.org/project/rxiv-maker/).

### Manual Updates
To manually update the manifest:
1. Check the latest version on PyPI
2. Update `bucket/rxiv-maker.json`
3. Verify the SHA256 checksum matches the PyPI release

## Support

- **rxiv-maker Issues**: [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- **Bucket Issues**: [GitHub Issues](https://github.com/henriqueslab/scoop-rxiv-maker/issues)
- **Documentation**: [rxiv-maker README](https://github.com/henriqueslab/rxiv-maker#readme)

## License

This bucket is licensed under the MIT License. See [LICENSE](LICENSE) for details.

The rxiv-maker software is separately licensed. See the [rxiv-maker repository](https://github.com/henriqueslab/rxiv-maker) for its license terms.