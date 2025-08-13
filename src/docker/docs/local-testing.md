# Local Docker Testing for rxiv-maker

This directory contains tools for testing the rxiv-maker Docker workflow locally, mirroring the GitHub Actions `build-pdf` workflow.

## Quick Start

### Method 1: Using the Test Script (Recommended)

```bash
# Navigate to the project root
cd /path/to/rxiv-maker

# Make the script executable (one-time setup)
chmod +x src/docker/test-local.sh

# Run test with default settings (uses EXAMPLE_MANUSCRIPT)
./src/docker/test-local.sh

# Run test with custom manuscript
./src/docker/test-local.sh --manuscript MANUSCRIPT

# Run test with debug output
./src/docker/test-local.sh --debug --interactive
```

### Method 2: Using Docker Compose

```bash
# Navigate to the project root
cd /path/to/rxiv-maker

# Run with default settings
docker-compose -f src/docker/docker-compose.test.yml up --build

# Run with custom manuscript
MANUSCRIPT_PATH=MANUSCRIPT docker-compose -f src/docker/docker-compose.test.yml up --build

# Run with debug mode
DEBUG=true docker-compose -f src/docker/docker-compose.test.yml up --build
```

## Available Commands

### Test Script Options

```bash
./src/docker/test-local.sh [OPTIONS] [MANUSCRIPT_PATH]

Options:
  --manuscript PATH     Use specific manuscript directory
  --build-base          Build base Docker image locally
  --interactive         Drop into shell on failure for debugging
  --clean               Clean up all Docker resources
  --debug               Enable verbose debugging output
  --no-cache            Disable dependency caching
  --force-figures       Force regeneration of all figures
  --help                Show help message
```

### Docker Compose Services

```bash
# Main test service
docker-compose -f src/docker/docker-compose.test.yml up --build

# Interactive shell for debugging
docker-compose -f src/docker/docker-compose.test.yml --profile shell up

# Jupyter notebook for development
docker-compose -f src/docker/docker-compose.test.yml --profile jupyter up
```

## Testing Workflow

The local testing mirrors the GitHub Actions workflow:

1. **Environment Setup**: Configure Git, check system resources
2. **Dependency Installation**: Install Python dependencies via `make setup`
3. **Manuscript Validation**: Verify manuscript directory exists and is valid
4. **Figure Generation**: Create figures from Python/R scripts and Mermaid diagrams
5. **PDF Generation**: Convert Markdown to LaTeX and compile to PDF
6. **Result Validation**: Verify PDF was created successfully

## Manuscript Selection

The system automatically selects the manuscript directory in this order:

1. **Command line argument**: `--manuscript PATH`
2. **Environment variable**: `MANUSCRIPT_PATH=PATH`
3. **`.env` file**: `MANUSCRIPT_PATH=PATH`
4. **Default**: `EXAMPLE_MANUSCRIPT`

## Output Location

Generated PDFs are saved to `output/MANUSCRIPT_NAME.pdf` where `MANUSCRIPT_NAME` is the manuscript directory name.

## Debugging

### Interactive Mode

```bash
# Drop into shell on failure
./src/docker/test-local.sh --interactive --debug

# Run shell service directly
docker-compose -f src/docker/docker-compose.test.yml --profile shell up
```

### Debug Information

The test script provides comprehensive debug information:

- System resources (memory, disk space)
- Python and LaTeX versions
- Environment variables
- File listings
- Log file contents

### Common Issues

1. **Base image not found**: Run `./src/docker/test-local.sh --build-base` to build locally
2. **Permission errors**: Ensure Docker daemon is running and user has permissions
3. **Manuscript not found**: Check that the manuscript directory exists and contains required files
4. **LaTeX compilation errors**: Check the log files in the output directory

## Development Workflow

### Live Development

Use Docker Compose with volume mounts for live development:

```bash
# Start container with volume mounts
docker-compose -f src/docker/docker-compose.test.yml --profile shell up

# In another terminal, execute commands
docker-compose -f src/docker/docker-compose.test.yml exec rxiv-maker-test bash

# Inside container, run tests
make pdf
```

### Testing Changes

1. Make changes to source code
2. Run local test to verify changes work
3. Push to GitHub to run full CI/CD pipeline

```bash
# Test changes locally
./src/docker/test-local.sh --debug

# If successful, push to GitHub
git add .
git commit -m "Your changes"
git push
```

## Cleanup

### Clean Docker Resources

```bash
# Clean test resources only
./src/docker/test-local.sh --clean

# Clean all Docker resources
docker system prune -a

# Clean Docker Compose resources
docker-compose -f src/docker/docker-compose.test.yml down -v
```

### Clean Output Files

```bash
# Clean generated files
make clean

# Clean figures
make clean-figures
```

## Performance Tips

1. **Use caching**: Avoid `--no-cache` unless testing dependency changes
2. **Reuse base image**: Pull base image once, then use `--build-base` only when needed
3. **Volume mounts**: Use Docker Compose for development to avoid rebuilding
4. **Parallel testing**: Run multiple tests in parallel with different manuscript directories

## Troubleshooting

### Docker Issues

```bash
# Check Docker status
docker info

# Check Docker daemon
sudo systemctl status docker  # Linux
brew services list | grep docker  # macOS

# Check Docker Compose version
docker-compose --version
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER output/
chmod -R 755 output/

# Check Docker group membership (Linux)
groups $USER
```

### Build Issues

```bash
# Check build context
docker build --dry-run -f src/docker/test-dockerfile .

# Build with verbose output
docker build --progress=plain -f src/docker/test-dockerfile .
```

## Integration with GitHub Actions

The local testing environment is designed to match the GitHub Actions workflow exactly:

- Same base Docker image
- Same environment variables
- Same build steps
- Same validation logic

This ensures that tests that pass locally will also pass in CI/CD.

## Files Overview

- `test-local.sh`: Main test orchestration script
- `test-dockerfile`: Docker image with local source code
- `docker-compose.test.yml`: Docker Compose configuration
- `LOCAL_TESTING.md`: This documentation
- `.dockerignore.test`: Build context optimization for testing