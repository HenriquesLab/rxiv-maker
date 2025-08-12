# SHA256 Fetcher for Package Managers

This directory contains scripts to reliably fetch SHA256 hashes for rxiv-maker packages from PyPI, fixing the shell variable interpolation issues that were causing package manager update failures.

## Scripts

### `fetch-sha256.sh` (Recommended)
Bash script that provides a robust, easy-to-use interface for package managers.

```bash
# Basic usage - gets sdist SHA256
./fetch-sha256.sh 1.4.8

# Explicit package type
./fetch-sha256.sh 1.4.8 sdist
./fetch-sha256.sh 1.4.8 wheel

# With debug output
DEBUG=1 ./fetch-sha256.sh 1.4.8
```

### `fetch-package-sha256.py`
Pure Python implementation for environments where bash is not available.

```bash
python3 fetch-package-sha256.py 1.4.8
python3 fetch-package-sha256.py 1.4.8 --package-type=wheel
```

## Package Manager Integration

### Homebrew Formula Updates

Replace the problematic SHA256 fetching in Homebrew formula update scripts:

```bash
# OLD (problematic):
SHA256=$(curl -s "https://pypi.org/pypi/rxiv-maker/$TARGET_VERSION/json" | python3 -c "import sys,json; data=json.load(sys.stdin); releases=data.get('releases',{}).get('$TARGET_VERSION',[]); sdist=[f for f in releases if f.get('packagetype')=='sdist']; print(sdist[0]['digests']['sha256'] if sdist else 'error')")

# NEW (fixed):
SHA256=$(./scripts/fetch-sha256.sh "$TARGET_VERSION" sdist)
```

### Scoop Manifest Updates

Replace the problematic SHA256 fetching in Scoop manifest update scripts:

```bash
# OLD (problematic):
SHA256=$(curl -s "https://pypi.org/pypi/rxiv-maker/json" | python3 -c "import sys,json; data=json.load(sys.stdin); releases=data.get('releases',{}).get('$TARGET_VERSION',[]); sdist=[f for f in releases if f.get('packagetype')=='sdist']; print(sdist[0]['digests']['sha256'] if sdist else 'error')")

# NEW (fixed):
SHA256=$(./scripts/fetch-sha256.sh "$TARGET_VERSION" sdist)
```

## Error Handling

The scripts provide proper error handling and exit codes:

- **Exit 0**: Success - SHA256 printed to stdout
- **Exit 1**: Error - Details printed to stderr

Example error handling in package manager scripts:

```bash
if SHA256=$(./scripts/fetch-sha256.sh "$TARGET_VERSION"); then
    echo "✅ SHA256 retrieved: $SHA256"
    # Update package manager manifest with $SHA256
else
    echo "❌ Failed to fetch SHA256 hash"
    exit 1
fi
```

## Features

### Robust Error Handling
- Network error detection and reporting
- JSON parsing error handling
- Missing package/version detection
- SHA256 format validation

### Flexible Package Type Support
- Automatic fallback from wheel to sdist if needed
- Explicit package type specification
- Clear error messages for missing package types

### Debug Support
- Verbose logging with `DEBUG=1`
- Color-coded output (when terminal supports it)
- Step-by-step progress reporting

### Shell-Safe Implementation
- No complex variable interpolation in Python strings
- Proper escaping and quoting
- Here-document usage to avoid shell issues

## Testing

Test the scripts with a known version:

```bash
# Test successful case
./scripts/fetch-sha256.sh 1.4.8
# Should output: a valid 64-character SHA256 hash

# Test error case  
./scripts/fetch-sha256.sh 999.999.999
# Should exit with code 1 and error message

# Test with debug
DEBUG=1 ./scripts/fetch-sha256.sh 1.4.8
# Should show detailed progress information
```

## Troubleshooting

### Common Issues

1. **"Python is required but not found"**
   - Install Python 3.6+ or ensure it's in PATH
   - Script tries `python3` first, then `python`

2. **"HTTP error 404"**
   - Version doesn't exist on PyPI
   - Check version format (should match PyPI releases)

3. **"No SHA256 hash found"**
   - PyPI package is missing digest information
   - Try a different package version

4. **"Invalid SHA256 format"**
   - PyPI returned unexpected data format
   - Enable debug mode to investigate

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
DEBUG=1 ./scripts/fetch-sha256.sh 1.4.8
```

This will show:
- Python command being used
- HTTP requests being made
- Package type fallback decisions
- Validation steps

## Migration Guide

For package manager maintainers migrating from the old approach:

1. **Download the scripts** to your package manager repository
2. **Replace the old Python one-liner** with a call to `./scripts/fetch-sha256.sh`
3. **Test with a known version** to verify functionality
4. **Update error handling** to check exit codes properly
5. **Optional**: Add debug mode support for troubleshooting

The new approach eliminates the shell variable interpolation issues that were causing the "Failed to fetch SHA256 hash" errors in both Homebrew and Scoop workflows.