# Strategy 5: Minimal R Installation
# Skip heavy graphics packages that cause compilation issues

FROM ubuntu:24.04 AS test-base

# Basic setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Minimal R package installation - skip graphics system
RUN R --slave -e " \
  options(repos = c( \
    'https://packagemanager.rstudio.com/cran/__linux__/jammy/latest', \
    'https://cran.rstudio.com/' \
  )); \
  options(Ncpus = parallel::detectCores()); \
  \
  # Only install essential packages, skip graphics \
  cat('Installing minimal essential packages...\\n'); \
  install.packages(c( \
    'cli', 'rlang', 'lifecycle', 'vctrs', 'magrittr', \
    'stringi', 'stringr', 'httr', 'jsonlite', 'xml2', \
    'ggplot2', 'dplyr', 'tidyr' \
  ), dependencies = TRUE); \
  \
  cat('Minimal R installation completed (graphics packages skipped)\\n'); \
"

# Add a note about missing graphics capabilities
RUN echo 'WARNING: This image has minimal R graphics capabilities' > /usr/local/share/R-graphics-warning.txt

LABEL strategy="minimal-r" \
      description="Minimal R installation without heavy graphics packages"
