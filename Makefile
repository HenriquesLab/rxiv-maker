# ======================================================================
#  _____  __   __  _  __   __         __  __          _
# |  __ \ \ \ / / (_)\ \ / /         |  \/  |        | |
# | |__) | \ V /   _  \ V /   _____  | \  / |  __ _  | | __  ___  _ __
# |  _  /   > <   | |  > <   |_____| | |\/| | / _` | | |/ / / _ \| '__|
# | | \ \  / . \  | | / . \          | |  | || (_| | |   < |  __/| |
# |_|  \_\/_/ \_\ |_|/_/ \_\         |_|  |_| \__,_| |_|\_\ \___||_|
#
# ======================================================================
# Automated Scientific Article Generation and Publishing System
#
# 🚀 QUICK START:
#   make setup        # Install Python dependencies
#   make pdf          # Generate PDF (requires LaTeX)
#   make help         # Show all available commands
#
# Author: Rxiv-Maker Project
# Documentation: See README.md
# ======================================================================

# ======================================================================
# ⚙️  CONFIGURATION VARIABLES
# ======================================================================

# Export all variables but handle MANUSCRIPT_PATH specially
export
.EXPORT_ALL_VARIABLES:

# ======================================================================
# 🌐 CROSS-PLATFORM COMPATIBILITY
# ======================================================================

# Detect operating system
ifdef MAKEFILE_FORCE_UNIX
    DETECTED_OS := GitHub-Actions-Unix
    SHELL_NULL := /dev/null
    VENV_PYTHON := .venv/bin/python
else ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    SHELL_NULL := nul
    VENV_PYTHON := .venv\Scripts\python.exe
else
    UNAME_S := $(shell uname -s)
    DETECTED_OS := $(if $(findstring Linux,$(UNAME_S)),Linux,$(if $(findstring Darwin,$(UNAME_S)),macOS,Unix))
    SHELL_NULL := /dev/null
    VENV_PYTHON := .venv/bin/python
endif

# Cross-platform Python command selection (prefer uv, then venv, then system python)
ifeq ($(OS),Windows_NT)
    PYTHON_CMD := $(shell where uv >nul 2>&1 && echo uv run python || (if exist "$(VENV_PYTHON)" (echo $(VENV_PYTHON)) else (echo python)))
else
    PYTHON_CMD := $(shell command -v uv >$(SHELL_NULL) 2>&1 && echo "uv run python" || (test -f "$(VENV_PYTHON)" && echo "$(VENV_PYTHON)" || echo python3))
endif

# ======================================================================
# 🐳 ENGINE MODE CONFIGURATION (DOCKER vs LOCAL)
# ======================================================================

# Engine mode: LOCAL (default) or DOCKER
# Override with: make pdf RXIV_ENGINE=DOCKER
RXIV_ENGINE ?= LOCAL

# Docker configuration
# Get rxiv-maker version for Docker image tagging with fallback mechanism
RXIV_VERSION := $(shell python3 -c "import sys; sys.path.insert(0, 'src'); from rxiv_maker.__version__ import __version__; print(__version__)" 2>/dev/null || echo "latest")

# Docker image with fallback: try versioned, then latest, then main
DOCKER_IMAGE_VERSIONED := henriqueslab/rxiv-maker-base:v$(RXIV_VERSION)
DOCKER_IMAGE_FALLBACK := $(shell \
	if docker manifest inspect $(DOCKER_IMAGE_VERSIONED) >/dev/null 2>&1; then \
		echo $(DOCKER_IMAGE_VERSIONED); \
	elif docker manifest inspect henriqueslab/rxiv-maker-base:latest >/dev/null 2>&1; then \
		echo henriqueslab/rxiv-maker-base:latest; \
	else \
		echo henriqueslab/rxiv-maker-base:main; \
	fi)
DOCKER_IMAGE ?= $(DOCKER_IMAGE_FALLBACK)
DOCKER_HUB_REPO ?= henriqueslab/rxiv-maker-base

# Platform detection for Docker
# Multi-architecture support: AMD64 and ARM64 both supported
# Detect host architecture for native execution (no emulation needed)
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_M),arm64)
    DOCKER_PLATFORM := linux/arm64
else ifeq ($(UNAME_M),aarch64)
    DOCKER_PLATFORM := linux/arm64
else ifeq ($(UNAME_M),x86_64)
    DOCKER_PLATFORM := linux/amd64
else
    DOCKER_PLATFORM := linux/amd64
endif

# Engine-specific command configuration
ifeq ($(RXIV_ENGINE),DOCKER)
    # Docker mode: Run all commands inside containers with platform-specific image
    DOCKER_RUN_CMD = docker run --rm --platform $(DOCKER_PLATFORM) -v $(PWD):/workspace -w /workspace
    # Install package in editable mode and run python command
    PYTHON_CMD = $(DOCKER_RUN_CMD) $(DOCKER_IMAGE) sh -c "pip install -e . >/dev/null 2>&1 && python"
    DOCKER_MODE_ACTIVE = true
    ENGINE_STATUS = 🐳 Docker ($(DOCKER_PLATFORM))
else
    # Local mode: Use local installations (existing behavior)
    DOCKER_MODE_ACTIVE = false
    ENGINE_STATUS = 💻 Local
endif

OUTPUT_DIR := output

# Simple MANUSCRIPT_PATH handling: command line > environment > .env file > default
-include .env
MANUSCRIPT_PATH ?= MANUSCRIPT
export MANUSCRIPT_PATH

ARTICLE_DIR = $(MANUSCRIPT_PATH)
FIGURES_DIR = $(ARTICLE_DIR)/FIGURES
STYLE_DIR := src/tex/style
PYTHON_SCRIPT := src/py/commands/generate_preprint.py
FIGURE_SCRIPT := src/py/commands/generate_figures.py

# Testing configuration
TEMPLATE_FILE := src/tex/template.tex
ARTICLE_MD = $(ARTICLE_DIR)/01_MAIN.md
MANUSCRIPT_CONFIG = $(ARTICLE_DIR)/00_CONFIG.yml
SUPPLEMENTARY_MD = $(ARTICLE_DIR)/02_SUPPLEMENTARY_INFO.md
REFERENCES_BIB = $(ARTICLE_DIR)/03_REFERENCES.bib

# Output file names based on manuscript path
MANUSCRIPT_NAME = $(notdir $(MANUSCRIPT_PATH))
OUTPUT_TEX = $(MANUSCRIPT_NAME).tex
OUTPUT_PDF = $(MANUSCRIPT_NAME).pdf

# ======================================================================
# 📌 DEFAULT AND CONVENIENCE TARGETS
# ======================================================================

# Default target
.PHONY: all
all: pdf

# ======================================================================
# 🚀 QUICK START COMMANDS
# ======================================================================
# Main user-facing commands with simple names

# Install Python dependencies only (cross-platform)
.PHONY: setup
setup:
	@$(PYTHON_CMD) -m pip install -e . || PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.setup_environment

# Reinstall Python dependencies (removes .venv and creates new one) - cross-platform
.PHONY: setup-reinstall
setup-reinstall:
	@$(PYTHON_CMD) -m rxiv_maker.cli setup --reinstall || PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.setup_environment --reinstall

# Test platform detection
.PHONY: test-platform
test-platform:
	@echo "Host machine: $(UNAME_M)"
	@echo "Docker platform: $(DOCKER_PLATFORM)"

# Install system dependencies (LaTeX, Node.js, R, etc.)
.PHONY: install-deps
install-deps:
	@echo "🔧 Installing system dependencies..."
	@$(PYTHON_CMD) -m rxiv_maker.cli install-deps

# Install system dependencies in minimal mode
.PHONY: install-deps-minimal
install-deps-minimal:
	@echo "🔧 Installing system dependencies (minimal mode)..."
	@$(PYTHON_CMD) -m rxiv_maker.cli install-deps --mode=minimal

# Check system dependencies
.PHONY: check-deps
check-deps:
	@echo "🔍 Checking system dependencies..."
	@$(PYTHON_CMD) -m rxiv_maker.cli setup --check-deps-only || PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.setup_environment --check-deps-only

# Check system dependencies (verbose)
.PHONY: check-deps-verbose
check-deps-verbose:
	@echo "🔍 Checking system dependencies (verbose)..."
	@$(PYTHON_CMD) -m rxiv_maker.cli setup --check-deps-only --verbose || PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.setup_environment --check-deps-only --verbose

# Generate PDF with validation (requires LaTeX installation)
.PHONY: pdf
pdf:
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.cli pdf "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR) $(if $(FORCE_FIGURES),--force-figures) || \
	 PYTHONPATH="$(PWD)/src" MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.commands.build_manager --manuscript-path "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR) --verbose $(if $(FORCE_FIGURES),--force-figures)

# Generate PDF without validation (for debugging)
.PHONY: pdf-no-validate
pdf-no-validate:
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.cli pdf "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR) --skip-validation $(if $(FORCE_FIGURES),--force-figures) || \
	 PYTHONPATH="$(PWD)/src" MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.commands.build_manager --manuscript-path "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR) --skip-validation $(if $(FORCE_FIGURES),--force-figures)

# Generate PDF with change tracking against a git tag
.PHONY: pdf-track-changes
pdf-track-changes:
ifndef TAG
	$(error TAG is required. Usage: make pdf-track-changes TAG=v1.0.0)
endif
	@echo "🔍 Generating PDF with change tracking against tag: $(TAG)"
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.cli track-changes "$(MANUSCRIPT_PATH)" $(TAG) --output-dir $(OUTPUT_DIR) --verbose || \
	 PYTHONPATH="$(PWD)/src" MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.commands.build_manager \
		--manuscript-path "$(MANUSCRIPT_PATH)" \
		--output-dir $(OUTPUT_DIR) \
		--track-changes $(TAG) \
		--verbose $(if $(FORCE_FIGURES),--force-figures)

# Prepare arXiv submission package
.PHONY: arxiv
arxiv: pdf
	@echo "Preparing arXiv submission package..."
	@$(PYTHON_CMD) -m rxiv_maker.cli arxiv "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR) || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.prepare_arxiv --output-dir $(OUTPUT_DIR) --arxiv-dir $(OUTPUT_DIR)/arxiv_submission --zip-filename $(OUTPUT_DIR)/for_arxiv.zip --manuscript-path "$(MANUSCRIPT_PATH)" --zip
	@echo "✅ arXiv package ready: $(OUTPUT_DIR)/for_arxiv.zip"
	@echo "Copying arXiv package to manuscript directory with naming convention..."
	@YEAR=$$($(PYTHON_CMD) -c "import yaml; config = yaml.safe_load(open('$(MANUSCRIPT_CONFIG)', 'r')); print(config.get('date', '').split('-')[0] if config.get('date') else '$(shell date +%Y)')"); \
	FIRST_AUTHOR=$$($(PYTHON_CMD) -c "import yaml; config = yaml.safe_load(open('$(MANUSCRIPT_CONFIG)', 'r')); authors = config.get('authors', []); name = authors[0]['name'] if authors and len(authors) > 0 else 'Unknown'; print(name.split()[-1] if ' ' in name else name)"); \
	ARXIV_FILENAME="$${YEAR}__$${FIRST_AUTHOR}_et_al__for_arxiv.zip"; \
	cp $(OUTPUT_DIR)/for_arxiv.zip $(MANUSCRIPT_PATH)/$${ARXIV_FILENAME}; \
	echo "✅ arXiv package copied to: $(MANUSCRIPT_PATH)/$${ARXIV_FILENAME}"
	@echo "📤 Upload the renamed file to arXiv for submission"

# ======================================================================
# 🔍 VALIDATION COMMANDS
# ======================================================================

# Validate manuscript structure and content (with detailed report)
.PHONY: validate
validate:
	@echo "🔍 Running manuscript validation..."
	@# Use command line variable or make variable with detailed and verbose output
	@$(PYTHON_CMD) -m rxiv_maker.cli validate "$(MANUSCRIPT_PATH)" --detailed || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.validate "$(MANUSCRIPT_PATH)" --detailed || { \
		echo ""; \
		echo "❌ Validation failed! Please fix the issues above before building PDF."; \
		echo "💡 Run 'make validate --help' for validation options"; \
		echo "💡 Use 'make pdf-no-validate' to skip validation and build anyway."; \
		exit 1; \
	}
	@echo "✅ Validation passed!"

# Internal validation target for PDF build (quiet mode)
.PHONY: _validate_quiet
_validate_quiet:
	@echo "🔍 Validating manuscript: $(MANUSCRIPT_PATH)"
	@$(PYTHON_CMD) -m rxiv_maker.cli validate "$(MANUSCRIPT_PATH)" || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.validate "$(MANUSCRIPT_PATH)" || { \
		echo ""; \
		echo "❌ Validation failed! Please fix the issues above before building PDF."; \
		echo "💡 Run 'make validate' for detailed error analysis"; \
		echo "💡 Use 'make pdf-no-validate' to skip validation and build anyway."; \
		exit 1; \
	}

# ======================================================================
# 🧪 TESTING AND CODE QUALITY
# ======================================================================

# Run all tests
.PHONY: test
test:
	@echo "🧪 Running all tests..."
	@$(PYTHON_CMD) -m pytest tests/ -v

# Run unit tests only
.PHONY: test-unit
test-unit:
	@echo "🧪 Running unit tests..."
	@$(PYTHON_CMD) -m pytest tests/unit/ -v

# Run integration tests only
.PHONY: test-integration
test-integration:
	@echo "🧪 Running integration tests..."
	@$(PYTHON_CMD) -m pytest tests/integration/ -v

# Lint code
.PHONY: lint
lint:
	@echo "🔍 Linting code..."
	@$(PYTHON_CMD) -m ruff check src/

# Format code
.PHONY: format
format:
	@echo "🎨 Formatting code..."
	@$(PYTHON_CMD) -m ruff format src/

# Type checking
.PHONY: typecheck
typecheck:
	@echo "🔍 Running type checking..."
	@$(PYTHON_CMD) -m mypy src/

# Run all code quality checks
.PHONY: check
check: lint typecheck
	@echo "✅ All code quality checks passed!"

# ======================================================================
# 📚 BIBLIOGRAPHY MANAGEMENT
# ======================================================================

# Fix bibliography issues automatically by searching CrossRef
.PHONY: fix-bibliography
fix-bibliography:
	@echo "🔧 Attempting to fix bibliography issues..."
	@$(PYTHON_CMD) -m rxiv_maker.cli bibliography fix "$(MANUSCRIPT_PATH)" || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.fix_bibliography "$(MANUSCRIPT_PATH)" || { \
		echo ""; \
		echo "❌ Bibliography fixing failed!"; \
		echo "💡 Run with --dry-run to see potential fixes first"; \
		echo "💡 Use --verbose for detailed logging"; \
		exit 1; \
	}

# Preview bibliography fixes without applying them
.PHONY: fix-bibliography-dry-run
fix-bibliography-dry-run:
	@echo "🔍 Checking potential bibliography fixes..."
	@$(PYTHON_CMD) -m rxiv_maker.cli bibliography fix "$(MANUSCRIPT_PATH)" --dry-run || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.fix_bibliography "$(MANUSCRIPT_PATH)" --dry-run

# Add bibliography entries from DOI
.PHONY: add-bibliography
add-bibliography:
	@# Extract DOI arguments from command line
	@DOI_ARGS=""; \
	for arg in $(MAKECMDGOALS); do \
		if echo "$$arg" | grep -E '^10\.[0-9]{4}.*' >/dev/null 2>&1; then \
			DOI_ARGS="$$DOI_ARGS $$arg"; \
		fi; \
	done; \
	if [ -z "$$DOI_ARGS" ]; then \
		echo "❌ Error: No DOI(s) provided"; \
		echo "💡 Usage: make add-bibliography 10.1000/example"; \
		echo "💡 Multiple: make add-bibliography 10.1000/ex1 10.1000/ex2"; \
		exit 1; \
	fi; \
	echo "📚 Adding bibliography entries from DOI(s):$$DOI_ARGS"; \
	$(PYTHON_CMD) -m rxiv_maker.cli bibliography add "$(MANUSCRIPT_PATH)" $$DOI_ARGS $(if $(OVERWRITE),--overwrite) $(if $(VERBOSE),--verbose) || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.add_bibliography "$(MANUSCRIPT_PATH)" $$DOI_ARGS $(if $(OVERWRITE),--overwrite) $(if $(VERBOSE),--verbose); \
	exit 0

# Allow DOI patterns as pseudo-targets
.PHONY: $(shell echo 10.*)
10.%: ;
	@# DOI patterns are handled by add-bibliography target

# ======================================================================
# 🔨 INTERNAL BUILD TARGETS (Deprecated - now handled by Python)
# ======================================================================
# These targets are kept for compatibility but delegate to Python commands

# ======================================================================
# 🧹 MAINTENANCE
# ======================================================================

# Clean output directory (cross-platform)
.PHONY: clean
clean:
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.cli clean "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR) || \
	 PYTHONPATH="$(PWD)/src" MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.commands.cleanup --manuscript-path "$(MANUSCRIPT_PATH)" --output-dir $(OUTPUT_DIR)

# Clean only output directory
.PHONY: clean-output
clean-output:
	@$(PYTHON_CMD) -m rxiv_maker.cli clean --output-only --output-dir $(OUTPUT_DIR) || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.cleanup --output-only --output-dir $(OUTPUT_DIR)

# Clean only generated figures
.PHONY: clean-figures
clean-figures:
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.cli clean "$(MANUSCRIPT_PATH)" --figures-only || \
	 PYTHONPATH="$(PWD)/src" MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) -m rxiv_maker.commands.cleanup --figures-only --manuscript-path "$(MANUSCRIPT_PATH)"

# Clean only arXiv files
.PHONY: clean-arxiv
clean-arxiv:
	@$(PYTHON_CMD) -m rxiv_maker.cli clean --arxiv-only || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.cleanup --arxiv-only

# Clean only temporary files
.PHONY: clean-temp
clean-temp:
	@$(PYTHON_CMD) -m rxiv_maker.cli clean --temp-only || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.cleanup --temp-only

# Clean only cache files
.PHONY: clean-cache
clean-cache:
	@$(PYTHON_CMD) -m rxiv_maker.cli clean --cache-only || \
	 PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -m rxiv_maker.commands.cleanup --cache-only

# ======================================================================
# 🐳 DOCKER ENGINE MODE
# ======================================================================

# Note: Docker image management commands are in src/docker/images/base/Makefile for maintainers.
# End users can use RXIV_ENGINE=DOCKER with any command for containerized execution.

# Show help
.PHONY: help
help:
	@VERSION=$$(PYTHONPATH="$(PWD)/src" $(PYTHON_CMD) -c "from rxiv_maker import __version__; print(__version__)" 2>/dev/null || echo "unknown"); \
	echo "Rxiv-Maker v$$VERSION ($(DETECTED_OS))"; \
	echo ""; \
	echo "Essential Commands:"; \
	echo "  make setup      - Install Python dependencies only"; \
	echo "  make install-deps - Install system dependencies (LaTeX, etc.)"; \
	echo "  make pdf        - Generate PDF with validation"; \
	echo "  make validate   - Check manuscript for issues"; \
	echo "  make clean      - Remove output files"; \
	echo "  make arxiv      - Prepare arXiv submission"; \
	echo ""; \
	echo "Docker Mode:"; \
	echo "  make pdf RXIV_ENGINE=DOCKER      - Generate PDF in container"; \
	echo "  make validate RXIV_ENGINE=DOCKER - Validate in container"; \
	echo ""; \
	echo "Advanced Options:"; \
	echo "  make pdf FORCE_FIGURES=true      - Force figure regeneration"; \
	echo "  make pdf MANUSCRIPT_PATH=MY_PAPER - Use custom manuscript"; \
	echo "  make pdf-track-changes TAG=v1.0.0 - Track changes vs git tag"; \
	echo ""; \
	echo "Directories: $(ARTICLE_DIR)/ → $(OUTPUT_DIR)/"; \
	echo "Quick Start: make setup && make pdf"
