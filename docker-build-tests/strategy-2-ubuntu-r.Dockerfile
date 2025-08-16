# Strategy 2: Ubuntu R Packages
# Use Ubuntu's pre-compiled R packages instead of CRAN compilation

FROM ubuntu:24.04 AS test-base

# Basic setup
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages using Ubuntu's repository (pre-compiled)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core R packages from Ubuntu
    r-cran-cli \
    r-cran-rlang \
    r-cran-lifecycle \
    r-cran-vctrs \
    r-cran-magrittr \
    r-cran-stringi \
    r-cran-stringr \
    r-cran-httr \
    r-cran-jsonlite \
    r-cran-xml2 \
    r-cran-ggplot2 \
    r-cran-dplyr \
    r-cran-tidyr \
    # Graphics system packages (if available)
    r-cran-systemfonts \
    r-cran-ragg \
    && rm -rf /var/lib/apt/lists/*

# Install any missing packages from CRAN as fallback
RUN R --slave -e " \
  required_packages <- c('textshaping'); \
  missing_packages <- required_packages[!require(required_packages, character.only = TRUE, quietly = TRUE)]; \
  if (length(missing_packages) > 0) { \
    cat('Installing missing packages from CRAN:', paste(missing_packages, collapse=', '), '\\n'); \
    options(repos = 'https://cran.rstudio.com/'); \
    install.packages(missing_packages, dependencies = TRUE); \
  } else { \
    cat('All packages already available from Ubuntu repository\\n'); \
  } \
"

LABEL strategy="ubuntu-packages" \
      description="Use Ubuntu's pre-compiled R packages"
