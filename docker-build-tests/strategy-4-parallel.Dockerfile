# Strategy 4: Parallel Package Installation
# Install packages in parallel groups to maximize CPU utilization

FROM ubuntu:24.04 AS test-base

# Basic setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    build-essential \
    pkg-config \
    libfontconfig1-dev \
    libcairo2-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Parallel R package installation using vector installation
RUN R --slave -e " \
  options(repos = c( \
    'https://packagemanager.rstudio.com/cran/__linux__/jammy/latest', \
    'https://cran.rstudio.com/' \
  )); \
  options(Ncpus = parallel::detectCores()); \
  \
  # Install all packages in parallel vectors (let R handle dependencies) \
  cat('Installing core packages in parallel...\\n'); \
  install.packages(c('cli', 'rlang', 'lifecycle', 'vctrs', 'magrittr'), \
                   dependencies = TRUE, Ncpus = parallel::detectCores()); \
  \
  cat('Installing string and network packages in parallel...\\n'); \
  install.packages(c('stringi', 'stringr', 'httr', 'jsonlite', 'xml2'), \
                   dependencies = TRUE, Ncpus = parallel::detectCores()); \
  \
  cat('Installing graphics packages in parallel...\\n'); \
  install.packages(c('systemfonts', 'textshaping', 'ragg'), \
                   dependencies = TRUE, Ncpus = parallel::detectCores()); \
  \
  cat('Installing data analysis packages in parallel...\\n'); \
  install.packages(c('ggplot2', 'dplyr', 'tidyr'), \
                   dependencies = TRUE, Ncpus = parallel::detectCores()); \
  \
  cat('All packages installed using parallel compilation\\n'); \
"

LABEL strategy="parallel-install" \
      description="Parallel R package installation"
