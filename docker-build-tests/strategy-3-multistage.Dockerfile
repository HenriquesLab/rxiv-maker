# Strategy 3: Multi-stage Build with R Pre-compilation
# Pre-compile heavy packages in a separate stage to enable better caching

FROM ubuntu:24.04 AS r-builder

# Install build dependencies
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

# Pre-compile heavy graphics packages in builder stage
RUN R --slave -e " \
  options(repos = c( \
    'https://packagemanager.rstudio.com/cran/__linux__/jammy/latest', \
    'https://cran.rstudio.com/' \
  )); \
  options(Ncpus = parallel::detectCores()); \
  \
  # Install heavy graphics packages first \
  cat('Pre-compiling graphics packages...\\n'); \
  install.packages(c('systemfonts', 'textshaping', 'ragg'), dependencies = TRUE); \
  \
  # Create a package library snapshot \
  cat('Graphics packages pre-compiled successfully\\n'); \
"

# Final stage - copy pre-compiled packages
FROM ubuntu:24.04 AS test-base

# Install runtime R
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    libfontconfig1 \
    libcairo2 \
    libfreetype6 \
    libpng16-16 \
    libtiff6 \
    libjpeg-turbo8 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled R packages from builder
COPY --from=r-builder /usr/local/lib/R/site-library /usr/local/lib/R/site-library

# Install remaining packages quickly
RUN R --slave -e " \
  options(repos = c( \
    'https://packagemanager.rstudio.com/cran/__linux__/jammy/latest', \
    'https://cran.rstudio.com/' \
  )); \
  \
  # Quick install of lighter packages \
  install.packages(c('cli', 'rlang', 'lifecycle', 'vctrs', 'magrittr', \
                     'stringi', 'stringr', 'httr', 'jsonlite', 'xml2', \
                     'ggplot2', 'dplyr', 'tidyr'), dependencies = TRUE); \
"

LABEL strategy="multistage-precompile" \
      description="Multi-stage build with R package pre-compilation"
