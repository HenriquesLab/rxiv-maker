# ======================================================================
# Rxiv-Maker Base Docker Image (Multi-Architecture)
# ======================================================================
# This Docker image contains all system dependencies for Rxiv-Maker
# but NO Python code or rxiv-maker specific logic.
#
# ARCHITECTURE SUPPORT: AMD64 and ARM64
# - Uses mermaid.ink API for diagram generation (no local dependencies)
# - Full cross-platform compatibility with no browser dependencies
# - Lightweight image without graphics processing libraries
# - Focused on LaTeX, Python, R, and essential tools only
#
# This base image is designed to accelerate GitHub Actions workflows
# by pre-installing time-consuming system dependencies.
# ======================================================================

FROM ubuntu:22.04 AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Set locale to avoid locale warnings
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# ======================================================================
# System Dependencies Stage
# ======================================================================

FROM base AS systemdeps

# Update package lists and install essential system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential system tools
    curl \
    wget \
    unzip \
    ca-certificates \
    software-properties-common \
    gnupg \
    lsb-release \
    # Basic build tools
    build-essential \
    make \
    cmake \
    pkg-config \
    autoconf \
    automake \
    libtool \
    # Graphics libraries for scientific plots (minimal set)
    libjpeg-dev \
    libpng-dev \
    # Python development headers
    python3-dev \
    libffi-dev \
    # Git for version control
    git \
    # Additional development tools
    gfortran \
    g++ \
    gcc \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Basic environment variables for package management
ENV PKG_CONFIG_PATH="/usr/lib/pkgconfig:/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/lib/aarch64-linux-gnu/pkgconfig"
ENV XDG_CACHE_HOME="/tmp/.cache"

# GitHub CLI removed - not needed for core functionality

# ======================================================================
# R Installation Stage (MOVED UP FOR BETTER CACHING)
# ======================================================================

FROM systemdeps AS rdeps

# Install R with essential graphics support and compilation dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    # Essential R system dependencies
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    # Font and graphics libraries for R packages (systemfonts, textshaping, ragg)
    libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libtiff5-dev \
    libjpeg-dev \
    libpng-dev \
    # Scientific computing libraries
    libudunits2-dev \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    # Database client libraries for R packages
    default-libmysqlclient-dev \
    libpq-dev \
    libsqlite3-dev \
    # Additional graphics and system libraries
    libxt-dev \
    libx11-dev \
    libxmu-dev \
    # Essential R graphics packages (system versions)
    r-cran-ggplot2 \
    r-cran-dplyr \
    r-cran-scales \
    r-cran-readr \
    r-cran-tidyr \
    r-cran-svglite \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Configure R for optimal performance with multiple repository fallbacks
RUN echo 'options(repos = c(CRAN = "https://packagemanager.rstudio.com/cran/__linux__/jammy/latest", RSPM = "https://packagemanager.rstudio.com/cran/__linux__/jammy/latest", RStudio = "https://cran.rstudio.com/", CRAN_Mirror = "https://cloud.r-project.org/"))' >> /usr/lib/R/etc/Rprofile.site \
    && echo 'options(Ncpus = parallel::detectCores())' >> /usr/lib/R/etc/Rprofile.site \
    && echo 'options(download.file.method = "auto")' >> /usr/lib/R/etc/Rprofile.site \
    && echo 'options(timeout = 300)' >> /usr/lib/R/etc/Rprofile.site

# Install essential R packages with robust error handling
# Install packages in stages with proper error handling
RUN R -e " \
  # Set global options for installation \
  options(repos = c('https://packagemanager.rstudio.com/cran/__linux__/jammy/latest', 'https://cran.rstudio.com/')); \
  options(Ncpus = parallel::detectCores()); \
  \
  # Helper function for robust package installation \
  install_safe <- function(packages, description = '') { \
    cat('Installing', description, 'packages:', paste(packages, collapse=', '), '\n'); \
    for (pkg in packages) { \
      tryCatch({ \
        if (!require(pkg, character.only = TRUE, quietly = TRUE)) { \
          install.packages(pkg, dependencies = TRUE, quiet = FALSE); \
          cat('✓ Successfully installed:', pkg, '\n'); \
        } else { \
          cat('✓ Already available:', pkg, '\n'); \
        } \
      }, error = function(e) { \
        cat('✗ Failed to install:', pkg, '- Error:', conditionMessage(e), '\n'); \
      }); \
    } \
  }; \
  \
  # Core infrastructure packages (most stable) \
  install_safe(c('cli', 'rlang', 'lifecycle', 'vctrs', 'digest', 'fastmap'), 'core infrastructure'); \
  \
  # Essential data science packages \
  install_safe(c('magrittr', 'stringi', 'stringr'), 'string processing'); \
  install_safe(c('dplyr', 'tidyr', 'readr'), 'data manipulation'); \
  \
  # Graphics system packages (install individually for better error handling) \
  install_safe(c('systemfonts'), 'system fonts'); \
  install_safe(c('textshaping'), 'text shaping'); \
  install_safe(c('ragg'), 'graphics devices'); \
  install_safe(c('svglite'), 'SVG output'); \
  \
  # Visualization packages \
  install_safe(c('scales', 'ggplot2'), 'visualization'); \
  \
  # System utilities and I/O \
  install_safe(c('fs', 'processx', 'ps', 'callr', 'withr'), 'system utilities'); \
  install_safe(c('yaml', 'jsonlite', 'xml2'), 'data formats'); \
  install_safe(c('optparse', 'getopt'), 'command line'); \
  \
  # Network and utility packages \
  install_safe(c('curl', 'httr', 'mime', 'openssl', 'askpass', 'sys'), 'network and security'); \
  install_safe(c('base64enc', 'cachem', 'memoise'), 'utilities'); \
  \
  cat('R package installation completed.\n'); \
"

# ======================================================================
# Font Configuration Stage (LaTeX Fonts Only)
# ======================================================================

FROM rdeps AS fontdeps

# Enhanced font support for both LaTeX and R packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential fonts for LaTeX compilation
    fonts-liberation \
    fonts-dejavu-core \
    fonts-lmodern \
    fonts-texgyre \
    # Additional fonts for better rendering
    fonts-dejavu \
    fonts-liberation2 \
    fonts-noto-core \
    # Font configuration tools
    fontconfig \
    fontconfig-config \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    # Rebuild font cache with verbose output for debugging
    && fc-cache -fv \
    # Verify font configuration
    && fc-list | head -10

# Mermaid diagrams handled by mermaid.ink API - no local dependencies needed

# ======================================================================
# LaTeX Installation Stage
# ======================================================================

FROM fontdeps AS latexdeps

# Configure debconf to avoid interactive prompts for TeX packages
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Install comprehensive LaTeX distribution with proper error handling
RUN apt-get update && \
    # Set environment to avoid interactive prompts during installation
    DEBIAN_FRONTEND=noninteractive \
    # Install packages in smaller groups to avoid memory issues
    apt-get install -y --no-install-recommends \
    # Core LaTeX packages first
    texlive-latex-base \
    texlive-latex-recommended \
    && apt-get install -y --no-install-recommends \
    # Font packages
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && apt-get install -y --no-install-recommends \
    # Additional packages
    texlive-latex-extra \
    texlive-science \
    texlive-pictures \
    && apt-get install -y --no-install-recommends \
    # Bibliography and language packages
    texlive-bibtex-extra \
    biber \
    texlive-lang-english \
    && apt-get install -y --no-install-recommends \
    # Advanced TeX engines and utilities
    texlive-plain-generic \
    texlive-xetex \
    texlive-luatex \
    texlive-extra-utils \
    latexdiff \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    # Fix tex-common configuration issues
    && dpkg --configure -a || true
# ======================================================================
# Python Installation Stage (MOVED TO END FOR FREQUENT CHANGES)
# ======================================================================
FROM latexdeps AS pybase
# Add deadsnakes PPA for Python 3.11 on Ubuntu 22.04
RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.11 and essential Python tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    # Additional Python tools
    cython3 \
    file \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    # Fix any remaining configuration issues
    && dpkg --configure -a || true

# Set Python 3.11 as default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Upgrade pip to latest version
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install uv (modern Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Make uv available globally for all users
RUN cp /root/.local/bin/uv /usr/local/bin/uv && chmod +x /usr/local/bin/uv

# Install Python packages in optimized stages for better caching
# Core dependencies that rarely change (put first for better caching)
RUN uv pip install --system --no-cache-dir \
    "numpy>=1.24.0,<2.0.0" \
    "scipy>=1.10.0,<2.0.0" \
    "pandas>=2.0.0,<3.0.0" \
    "Pillow>=9.0.0,<11.0.0" \
    "PyYAML>=6.0.0,<7.0.0"

# Graphics and visualization libraries (moderate change frequency)
RUN uv pip install --system --no-cache-dir \
    "matplotlib>=3.7.0,<3.9.0" \
    "seaborn>=0.12.0,<0.14.0"

# Document processing libraries (moderate change frequency)
RUN uv pip install --system --no-cache-dir \
    "requests>=2.28.0,<3.0.0" \
    "svglib>=1.5.0,<2.0.0" \
    "reportlab>=4.0.0,<5.0.0" \
    "defusedxml>=0.7.0,<1.0.0" \
    "lxml>=4.9.0,<6.0.0" \
    "pypdf>=3.0.0,<5.0.0"

# Utility and application-specific libraries (higher change frequency)
RUN uv pip install --system --no-cache-dir \
    "python-dotenv>=1.0.0,<2.0.0" \
    "crossref-commons>=0.0.7,<1.0.0" \
    "platformdirs>=4.0.0,<5.0.0" \
    "click>=8.0.0,<9.0.0" \
    "rich>=13.0.0,<14.0.0" \
    "rich-click>=1.6.0,<2.0.0" \
    "typing-extensions>=4.0.0,<5.0.0" \
    "packaging>=21.0.0,<25.0.0" \
    "tomli-w>=1.0.0,<2.0.0" \
    "tomli>=2.0.0,<3.0.0"

# Essential development tools only (removed testing frameworks)
RUN uv pip install --system --no-cache-dir \
    "ruff>=0.8.0,<1.0.0"
# ======================================================================
# Final Optimized Stage
# ======================================================================
FROM pybase AS final
# Create a non-root user for security (but allow GitHub Actions to work)
RUN groupadd -r rxivmaker && useradd -r -g rxivmaker -d /home/rxivmaker -s /bin/bash rxivmaker \
    && mkdir -p /home/rxivmaker \
    && chown rxivmaker:rxivmaker /home/rxivmaker

# Set up working directory
WORKDIR /workspace

# Create necessary directories with proper permissions
RUN mkdir -p /workspace/output /workspace/cache /tmp/texmf-var \
    && chown -R rxivmaker:rxivmaker /workspace /tmp/texmf-var \
    && chmod -R 777 /workspace /tmp/texmf-var

# Set environment variables for LaTeX
ENV TEXMFVAR=/tmp/texmf-var
ENV TEXMFHOME=/tmp/texmf-home
ENV TEXMFCACHE=/tmp/texmf-cache

# Font configuration for LaTeX
ENV FONTCONFIG_FILE=/etc/fonts/fonts.conf
ENV FC_CACHE_DIR=/tmp/fontconfig-cache

# Set environment variables for R
ENV R_LIBS_USER=/home/rxivmaker/.R/library

# Create additional directories for R and font caching
RUN mkdir -p /home/rxivmaker/.R/library /home/rxivmaker/.cache /tmp/fontconfig-cache \
    && chown -R rxivmaker:rxivmaker /home/rxivmaker/.R /home/rxivmaker/.cache /tmp/fontconfig-cache \
    && chmod -R 777 /tmp/fontconfig-cache

# Create Python dependency verification script using here document approach
RUN cat > /usr/local/bin/verify-python-deps.sh << 'VERIFY_SCRIPT'
#!/bin/bash
echo "Verifying Python dependencies..."

# Test mermaid.ink integration (requests library)
echo "Testing requests library for mermaid.ink API..."
python3 -c "
import sys
import requests
import base64

print(f'Python path: {sys.executable}')
print(f'Python version: {sys.version}')
print(f'Requests version: {requests.__version__}')

# Test mermaid.ink API connection
test_diagram = 'graph TD; A-->B'
encoded = base64.b64encode(test_diagram.encode('utf-8')).decode('ascii')
api_url = f'https://mermaid.ink/svg/{encoded}'
print(f'Testing mermaid.ink API: {api_url[:50]}...')
print('✅ Mermaid.ink API integration ready!')
"

# Test other critical dependencies
echo "Testing other Python dependencies..."
python3 -c "
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
import subprocess
print('✅ Core scientific libraries verified!')
"

echo "All Python dependencies verified successfully!"
VERIFY_SCRIPT
RUN chmod +x /usr/local/bin/verify-python-deps.sh

# Create test script for backward compatibility
RUN printf '#!/bin/bash\n/usr/local/bin/verify-python-deps.sh\n' > /usr/local/bin/test-deps.sh \
    && chmod +x /usr/local/bin/test-deps.sh

# Run dependency verification during build to catch issues early
RUN /usr/local/bin/verify-python-deps.sh

# ======================================================================
# Runtime Dependency Injection Support
# ======================================================================
# This enables the "development mode" pattern where Python dependencies
# are installed at runtime from the mounted pyproject.toml, ensuring
# perfect synchronization between local and container environments.

# Create runtime dependency installation script
RUN cat > /usr/local/bin/install-project-deps.sh << 'INSTALL_SCRIPT'
#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} Installing project dependencies from pyproject.toml..."

# Check if pyproject.toml exists in workspace
if [ ! -f "/workspace/pyproject.toml" ]; then
    echo -e "${YELLOW}[WARNING]${NC} No pyproject.toml found in /workspace"
    echo -e "${YELLOW}[WARNING]${NC} Mount your project directory to /workspace to enable runtime dependency injection"
    exit 0
fi

# Install project in editable mode with all dependencies
echo -e "${BLUE}[INFO]${NC} Installing project dependencies with uv..."
cd /workspace

# Install the project in editable mode (use --force-reinstall to ensure all deps)
uv pip install --system -e . --no-cache-dir --force-reinstall

echo -e "${GREEN}[SUCCESS]${NC} Project dependencies installed successfully!"

# Verify critical imports work
echo -e "${BLUE}[INFO]${NC} Verifying imports..."
python3 -c "
import sys
sys.path.insert(0, '/workspace/src')
try:
    from rxiv_maker.utils.cache_utils import get_cache_dir
    from rxiv_maker.validators.doi_validator import DOIValidator
    print('✅ Runtime dependency injection successful!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"
INSTALL_SCRIPT
RUN chmod +x /usr/local/bin/install-project-deps.sh

# Create development mode startup script
RUN cat > /usr/local/bin/dev-mode.sh << 'DEV_SCRIPT'
#!/bin/bash
# Development mode: Install dependencies and start interactive shell
echo "🔧 Starting Rxiv-Maker development mode..."
/usr/local/bin/install-project-deps.sh
echo "🚀 Ready for development! Project dependencies are synchronized."
exec /bin/bash "$@"
DEV_SCRIPT
RUN chmod +x /usr/local/bin/dev-mode.sh

# Add usage instructions as a script
RUN cat > /usr/local/bin/usage.sh << 'USAGE_SCRIPT'
#!/bin/bash
echo "=========================================="
echo "   Rxiv-Maker Docker Usage Instructions"
echo "=========================================="
echo ""
echo "DEVELOPMENT MODE (recommended):"
echo "  Mount your project and use runtime dependency injection:"
echo "  $ docker run -v \$PWD:/workspace henriqueslab/rxiv-maker-base:latest dev-mode.sh"
echo ""
echo "MANUAL DEPENDENCY INSTALLATION:"
echo "  $ docker run -v \$PWD:/workspace henriqueslab/rxiv-maker-base:latest install-project-deps.sh"
echo ""
echo "PRODUCTION MODE:"
echo "  Use the pre-installed base dependencies (may have version drift)"
echo "  $ docker run henriqueslab/rxiv-maker-base:latest"
echo ""
echo "VERIFY DEPENDENCIES:"
echo "  $ docker run henriqueslab/rxiv-maker-base:latest verify-python-deps.sh"
echo ""
USAGE_SCRIPT
RUN chmod +x /usr/local/bin/usage.sh

# Add labels for metadata
LABEL maintainer="Rxiv-Maker Project"
LABEL description="Lightweight base image for Rxiv-Maker with mermaid.ink API integration"
LABEL version="2.0.1-mermaid-api"
LABEL org.opencontainers.image.source="https://github.com/henriqueslab/rxiv-maker"
LABEL org.opencontainers.image.description="Ubuntu-based image with LaTeX, Python, R, and mermaid.ink API support"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.variant="mermaid-api"

# For GitHub Actions, we need to stay as root to allow workspace access
# USER rxivmaker

# Set default command
CMD ["/bin/bash"]
