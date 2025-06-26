# ======================================================================
#  _____  __   __  _  __   __         __  __          _
# |  __ \ \ \ / / (_)\ \ / /         |  \/  |        | |
# | |__) | \ V /   _  \ V /   _____  | \  / |  __ _  | | __  ___  _ __
# |  _  /   > <   | |  > <   |_____| | |\/| | / _` | | |/ / / _ \| '__|
# |_| \_\  /_/\_\ |_| /_/\_\         | |  | || (_| | |   < |  __/| |
#                                     |_|  |_| \__,_| |_|\_\ \___||_|
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

# Load environment variables from .env file if it exists
-include .env
export

# Export MANUSCRIPT_PATH explicitly
export MANUSCRIPT_PATH

# Check if .env file exists
ENV_FILE_EXISTS := $(shell [ -f ".env" ] && echo "true" || echo "false")

# Python command selection (use venv if available, otherwise system python)
PYTHON_CMD := $(shell if [ -f ".venv/bin/python" ]; then echo ".venv/bin/python"; else echo "python3"; fi)

OUTPUT_DIR := output
# Get MANUSCRIPT_PATH from environment, default to MANUSCRIPT if not set
MANUSCRIPT_PATH := $(shell echo $${MANUSCRIPT_PATH:-MANUSCRIPT})
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

# Install Python dependencies
.PHONY: setup
setup:
	@echo "Installing Python dependencies..."
	@$(PYTHON_CMD) -m pip install --upgrade pip
	@$(PYTHON_CMD) -m pip install -e ".[dev]"
	@echo "✅ Setup complete! Now you can run 'make pdf' to create your document."
	@echo "Note: You'll also need LaTeX installed on your system."

# Generate PDF with validation (requires LaTeX installation)
.PHONY: pdf
pdf: validate _build_pdf
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) src/py/commands/copy_pdf.py --output-dir $(OUTPUT_DIR)
	@if [ -f "$(OUTPUT_DIR)/$(OUTPUT_PDF)" ]; then \
		echo "✅ PDF compilation complete: $(OUTPUT_DIR)/$(OUTPUT_PDF)"; \
	else \
		echo "❌ Error: PDF file was not created"; \
		echo "💡 Run 'make validate-detailed' for comprehensive error analysis"; \
		exit 1; \
	fi

# Generate PDF without validation (for debugging)
.PHONY: pdf-no-validate
pdf-no-validate: _build_pdf
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) src/py/commands/copy_pdf.py --output-dir $(OUTPUT_DIR)
	@if [ -f "$(OUTPUT_DIR)/$(OUTPUT_PDF)" ]; then \
		echo "✅ PDF compilation complete: $(OUTPUT_DIR)/$(OUTPUT_PDF)"; \
	else \
		echo "❌ Error: PDF file was not created"; \
		echo "💡 Run 'make validate-detailed' for comprehensive error analysis"; \
		exit 1; \
	fi

# Prepare arXiv submission package
.PHONY: arxiv
arxiv: _generate_files
	@echo "Preparing arXiv submission package..."
	@$(PYTHON_CMD) prepare_arxiv.py --output-dir $(OUTPUT_DIR) --arxiv-dir $(OUTPUT_DIR)/arxiv_submission --zip-filename $(OUTPUT_DIR)/for_arxiv.zip --zip
	@echo "✅ arXiv package ready: $(OUTPUT_DIR)/for_arxiv.zip"
	@echo "Copying arXiv package to manuscript directory with naming convention..."
	@YEAR=$$($(PYTHON_CMD) -c "import yaml; import sys; sys.path.insert(0, 'src/py'); config = yaml.safe_load(open('$(MANUSCRIPT_CONFIG)', 'r')); print(config.get('date', '').split('-')[0] if config.get('date') else '$(shell date +%Y)')"); \
	FIRST_AUTHOR=$$($(PYTHON_CMD) -c "import yaml; import sys; sys.path.insert(0, 'src/py'); config = yaml.safe_load(open('$(MANUSCRIPT_CONFIG)', 'r')); authors = config.get('authors', []); name = authors[0]['name'] if authors and len(authors) > 0 else 'Unknown'; print(name.split()[-1] if ' ' in name else name)"); \
	ARXIV_FILENAME="$${YEAR}__$${FIRST_AUTHOR}_et_al__for_arxiv.zip"; \
	cp $(OUTPUT_DIR)/for_arxiv.zip $(MANUSCRIPT_PATH)/$${ARXIV_FILENAME}; \
	echo "✅ arXiv package copied to: $(MANUSCRIPT_PATH)/$${ARXIV_FILENAME}"
	@echo "📤 Upload the renamed file to arXiv for submission"

# ======================================================================
# 🔍 VALIDATION COMMANDS
# ======================================================================

# Validate manuscript structure and content
.PHONY: validate
validate:
	@echo "🔍 Running manuscript validation..."
	@$(PYTHON_CMD) src/py/scripts/validate_manuscript.py "$(MANUSCRIPT_PATH)" || { \
		echo ""; \
		echo "❌ Validation failed! Please fix the issues above before building PDF."; \
		echo "💡 Run 'make validate --help' for validation options"; \
		echo "💡 Use 'make pdf-no-validate' to skip validation and build anyway."; \
		exit 1; \
	}
	@echo "✅ Validation passed!"
# ======================================================================
# 🔨 INTERNAL BUILD TARGETS
# ======================================================================

# Internal target for building PDF (used by both pdf and local targets)
.PHONY: _build_pdf
_build_pdf: _generate_files
	@echo "Compiling LaTeX to PDF..."
	@COMPILATION_SUCCESS=true; \
	cd $(OUTPUT_DIR) && \
	 pdflatex -interaction=nonstopmode $(OUTPUT_TEX) || COMPILATION_SUCCESS=false; \
	 bibtex $(MANUSCRIPT_NAME) || true; \
	 pdflatex -interaction=nonstopmode $(OUTPUT_TEX) || COMPILATION_SUCCESS=false; \
	 pdflatex -interaction=nonstopmode $(OUTPUT_TEX) || COMPILATION_SUCCESS=false; \
	if [ "$$COMPILATION_SUCCESS" = "false" ] && [ -f "$(OUTPUT_DIR)/$(MANUSCRIPT_NAME).log" ]; then \
		echo ""; \
		echo "⚠️  LaTeX compilation encountered errors. Analyzing..."; \
		$(PYTHON_CMD) src/py/commands/validate.py "$(MANUSCRIPT_PATH)" --no-latex=false --detailed 2>/dev/null || true; \
		echo ""; \
		echo "💡 Run 'make validate-latex' for detailed LaTeX error analysis"; \
	fi
	@echo "PDF compilation complete: $(OUTPUT_DIR)/$(OUTPUT_PDF)"
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) src/py/commands/analyze_word_count.py

# Internal target for generating all necessary files
.PHONY: _generate_files
_generate_files:
	@echo "Setting up output directory..."
	@mkdir -p $(OUTPUT_DIR)
	@mkdir -p $(OUTPUT_DIR)/Figures

	@echo "Checking if figures need to be generated..."
	@NEED_FIGURES=false; \
	for mmd_file in $(FIGURES_DIR)/*.mmd; do \
		if [ -f "$$mmd_file" ]; then \
			base_name=$$(basename "$$mmd_file" .mmd); \
			if [ ! -f "$(FIGURES_DIR)/$$base_name/$$base_name.pdf" ]; then \
				NEED_FIGURES=true; \
				break; \
			fi; \
		fi; \
	done; \
	if [ "$$NEED_FIGURES" = "true" ] || [ "$(FORCE_FIGURES)" = "true" ]; then \
		echo "Generating figures from $(FIGURES_DIR)..."; \
		MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) $(FIGURE_SCRIPT) --figures-dir $(FIGURES_DIR) --output-dir $(FIGURES_DIR) --format pdf; \
	fi

	@echo "Generating $(OUTPUT_TEX) from $(ARTICLE_MD)..."
	@MANUSCRIPT_PATH="$(MANUSCRIPT_PATH)" $(PYTHON_CMD) $(PYTHON_SCRIPT) --output-dir $(OUTPUT_DIR)

	@echo "Copying necessary files to $(OUTPUT_DIR)..."
	@cp $(STYLE_DIR)/*.cls $(OUTPUT_DIR)/ 2>/dev/null || echo "No .cls files found"
	@cp $(STYLE_DIR)/*.bst $(OUTPUT_DIR)/ 2>/dev/null || echo "No .bst files found"
	@cp $(STYLE_DIR)/*.sty $(OUTPUT_DIR)/ 2>/dev/null || echo "No .sty files found"

	@if [ -f $(REFERENCES_BIB) ]; then \
		cp $(REFERENCES_BIB) $(OUTPUT_DIR)/; \
	fi

	@if [ -d $(FIGURES_DIR) ]; then \
		mkdir -p $(OUTPUT_DIR)/Figures; \
		cp -r $(FIGURES_DIR)/* $(OUTPUT_DIR)/Figures/ 2>/dev/null || true; \
	fi

	@find src/tex -name "*.tex" -not -name "template.tex" -exec cp {} $(OUTPUT_DIR)/ \; 2>/dev/null || true
	@find src/tex -name "*.cls" -exec cp {} $(OUTPUT_DIR)/ \; 2>/dev/null || true
	@find src/tex -name "*.sty" -exec cp {} $(OUTPUT_DIR)/ \; 2>/dev/null || true

# ======================================================================
# 🧹 MAINTENANCE
# ======================================================================

# Clean output directory
.PHONY: clean
clean:
	@echo "Cleaning output directory..."
	@rm -rf $(OUTPUT_DIR)
	@echo "Cleaning generated figures..."
	@if [ -d "$(FIGURES_DIR)" ]; then \
		find "$(FIGURES_DIR)" -name "*.pdf" -o -name "*.png" -o -name "*.svg" -o -name "*.eps" | xargs rm -f 2>/dev/null || true; \
	fi
	@echo "Cleaning any leftover arXiv files..."
	@rm -f for_arxiv.zip arxiv_submission 2>/dev/null || true
	@echo "Clean complete"

# Show help
.PHONY: help
help:
	@VERSION=$$($(PYTHON_CMD) -c "import sys; sys.path.insert(0, 'src/py'); from src.py import __version__; print(__version__)" 2>/dev/null || echo "unknown"); \
	echo "====================================="; \
	echo "Rxiv-Maker v$$VERSION - Makefile Commands"; \
	echo "====================================="; \
	echo ""; \
	echo "🚀 ESSENTIAL COMMANDS:"; \
	echo "  make setup          - Install Python dependencies"; \
	echo "  make pdf            - Generate PDF with validation (requires LaTeX)"; \
	echo "  make validate       - Check manuscript for issues"; \
	echo "  make arxiv          - Prepare arXiv submission package"; \
	echo "  make clean          - Remove output directory"; \
	echo "  make help           - Show this help message"; \
	echo ""; \
	echo "📁 DIRECTORIES:"; \
	echo "  - Manuscript files: $(ARTICLE_DIR)/"; \
	echo "  - Figures:          $(FIGURES_DIR)/"; \
	echo "  - Output:           $(OUTPUT_DIR)/"; \
	echo ""; \
	echo "💡 TIP: New to Rxiv-Maker?"; \
	echo "   1. Install LaTeX on your system"; \
	echo "   2. Run 'make setup' to install Python dependencies"; \
	echo "   3. Run 'make pdf' to generate your first PDF"; \
	echo "   4. Edit files in $(ARTICLE_DIR)/ and re-run 'make pdf'"; \
	echo ""; \
	echo "💡 ADVANCED OPTIONS:"; \
	echo "   - Skip validation: make pdf-no-validate"; \
	echo "   - Force figure regeneration: make pdf FORCE_FIGURES=true"; \
	echo "   - Use different manuscript folder: make pdf MANUSCRIPT_PATH=path/to/folder"; \
	echo "   - Validation options: python3 src/py/scripts/validate_manuscript.py --help"; \
	echo "   - arXiv files created in: $(OUTPUT_DIR)/arxiv_submission/"; \
	echo "   - arXiv ZIP file: $(OUTPUT_DIR)/for_arxiv.zip"
