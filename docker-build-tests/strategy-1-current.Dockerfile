# Strategy 1: Current Approach (Baseline)
# This is a simplified version of the current Dockerfile focusing on the R installation part
# for timing comparison

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

# Current R package installation approach
RUN R --slave -e " \
  arch <- if (Sys.info()['machine'] == 'aarch64') 'arm64' else 'amd64'; \
  cat('Architecture detected in R:', arch, '\\n'); \
  options(repos = c( \
    paste0('https://cran.devxy.io/', arch, '/jammy/latest'), \
    'https://packagemanager.rstudio.com/cran/__linux__/jammy/latest', \
    'https://cran.rstudio.com/' \
  )); \
  options(Ncpus = parallel::detectCores()); \
  timeout_val <- if (Sys.info()['machine'] == 'aarch64') 1200 else 300; \
  options(timeout = timeout_val); \
  \
  install_safe <- function(packages, description = '', optional = FALSE) { \
    cat('Installing', description, 'packages:', paste(packages, collapse=', '), '\\n'); \
    for (pkg in packages) { \
      tryCatch({ \
        if (!require(pkg, character.only = TRUE, quietly = TRUE)) { \
          install.packages(pkg, dependencies = TRUE, quiet = FALSE); \
          cat('✓ Successfully installed:', pkg, '\\n'); \
        } else { \
          cat('✓ Already available:', pkg, '\\n'); \
        } \
      }, error = function(e) { \
        msg <- paste('✗ Failed to install:', pkg, '- Error:', conditionMessage(e)); \
        cat(msg, '\\n'); \
        if (!optional) { \
          cat('Package', pkg, 'is required, continuing anyway...\\n'); \
        } \
      }); \
    } \
  }; \
  \
  install_safe(c('cli', 'rlang', 'lifecycle', 'vctrs'), 'core infrastructure'); \
  install_safe(c('magrittr', 'stringi', 'stringr'), 'string processing'); \
  install_safe(c('httr', 'jsonlite', 'xml2'), 'network and data'); \
  install_safe(c('systemfonts', 'textshaping', 'ragg'), 'graphics system', optional = TRUE); \
  install_safe(c('ggplot2', 'dplyr', 'tidyr'), 'data analysis'); \
"

LABEL strategy="current-baseline" \
      description="Current R package installation approach"
