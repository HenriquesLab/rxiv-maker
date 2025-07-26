# Homebrew Tap for rxiv-maker

A [Homebrew](https://brew.sh/) tap for installing [rxiv-maker](https://github.com/henriqueslab/rxiv-maker), an automated LaTeX article generation system.

## Installation

### Prerequisites
- macOS 10.15+ or Linux
- [Homebrew](https://brew.sh/) package manager

### Quick Install
```bash
# Add the tap
brew tap henriqueslab/rxiv-maker

# Install rxiv-maker
brew install rxiv-maker
```

### System Dependencies
rxiv-maker requires additional system dependencies for full functionality:

#### macOS
```bash
# Install LaTeX distribution (recommended)
brew install --cask mactex

# Or minimal LaTeX installation
brew install --cask basictex

# Git is usually pre-installed with Xcode Command Line Tools
# If not available:
xcode-select --install
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install texlive-full git make

# Fedora/CentOS/RHEL
sudo dnf install texlive-scheme-full git make

# Arch Linux
sudo pacman -S texlive-most git make
```

## Usage

After installation, the `rxiv` command will be available in your PATH:

```bash
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

```bash
# Update Homebrew and all packages
brew update && brew upgrade

# Update only rxiv-maker
brew upgrade rxiv-maker
```

## Uninstalling

```bash
# Remove rxiv-maker
brew uninstall rxiv-maker

# Remove the tap (optional)
brew untap henriqueslab/rxiv-maker
```

## Troubleshooting

### Python Environment
rxiv-maker is installed in an isolated Python virtual environment to avoid conflicts with system Python packages. This follows Python PEP 668 best practices.

### LaTeX Issues
If you encounter LaTeX compilation errors:

#### macOS
1. Ensure MacTeX or BasicTeX is installed
2. Add LaTeX to PATH: `echo 'export PATH="/usr/local/texlive/2023/bin/universal-darwin:$PATH"' >> ~/.zshrc`
3. Reload shell: `source ~/.zshrc`
4. Verify: `which pdflatex`

#### Linux
1. Install full TeXLive distribution for best compatibility
2. Verify LaTeX installation: `pdflatex --version`
3. For Ubuntu/Debian: `sudo apt-get install texlive-latex-extra texlive-fonts-recommended`

### Permission Issues
If you encounter permission errors:
```bash
# Fix Homebrew permissions
sudo chown -R $(whoami) $(brew --prefix)/*

# Or reinstall Homebrew (if issues persist)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### PATH Issues
If `rxiv` command is not found:
```bash
# Check if Homebrew bin is in PATH
echo $PATH | grep $(brew --prefix)/bin

# Add to PATH if missing (zsh)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Add to PATH if missing (bash)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

## Development

This tap automatically tracks releases from the [official rxiv-maker PyPI package](https://pypi.org/project/rxiv-maker/).

### Manual Updates
To manually update the formula:
1. Check the latest version on PyPI
2. Update `Formula/rxiv-maker.rb`
3. Calculate new SHA256: `brew fetch --build-from-source rxiv-maker`
4. Test the formula: `brew install --build-from-source rxiv-maker`

### Testing
```bash
# Test formula syntax
brew audit --strict rxiv-maker

# Test installation
brew install --verbose --debug rxiv-maker

# Test functionality
rxiv --help
```

## Support

- **rxiv-maker Issues**: [GitHub Issues](https://github.com/henriqueslab/rxiv-maker/issues)
- **Tap Issues**: [GitHub Issues](https://github.com/henriqueslab/homebrew-rxiv-maker/issues)
- **Documentation**: [rxiv-maker README](https://github.com/henriqueslab/rxiv-maker#readme)
- **Homebrew Docs**: [Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)

## License

This tap is licensed under the MIT License. See [LICENSE](LICENSE) for details.

The rxiv-maker software is separately licensed. See the [rxiv-maker repository](https://github.com/henriqueslab/rxiv-maker) for its license terms.