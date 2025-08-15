# Packaging Infrastructure

This directory contains all packaging-related files for rxiv-maker, organized for better maintainability.

## Directory Structure

```
packaging/
├── debian/           # Debian package configuration
│   ├── control       # Package dependencies and metadata
│   ├── rules         # Build rules
│   ├── changelog     # Debian changelog
│   └── ...
├── containerfiles/   # Container definitions for packaging
│   └── Containerfile.deb-build
├── scripts/          # Packaging automation scripts
│   ├── build-deb.sh
│   ├── setup-apt-repo.sh
│   ├── validate-apt-repo.sh
│   └── ...
├── tests/            # Packaging-specific tests
│   ├── container/    # Container-based tests
│   └── ...
├── docs/             # Packaging documentation
│   ├── apt-installation.md
│   ├── apt-repository-guide.md
│   └── ...
└── apt-repo/         # APT repository files
    └── ...
```

## Usage

### Build Debian Package

```bash
# Build package using the script
./packaging/scripts/build-deb.sh

# Build with container
podman build -t rxiv-deb-builder -f packaging/containerfiles/Containerfile.deb-build .
podman run --rm -v "$(pwd)":/workspace -w /workspace rxiv-deb-builder dpkg-buildpackage -b -uc -us
```

### Test Package

```bash
# Run packaging tests
python -m pytest packaging/tests/

# Container tests
./packaging/scripts/test-apt-container.sh
```

### Set Up APT Repository

```bash
# Set up local APT repository
./packaging/scripts/setup-apt-repo.sh

# Validate repository
./packaging/scripts/validate-apt-repo.sh
```

## GitHub Actions Integration

The packaging workflows are located in `.github/workflows/`:
- `publish-apt.yml` - Publishes packages to APT repository
- `test-apt-containers.yml` - Tests containerized builds

These workflows automatically reference the packaging files in this directory.

## Development Notes

- All scripts automatically adjust paths to work from any directory
- Container builds use the organized structure
- Tests validate both local and containerized builds
- Documentation is co-located with implementation files