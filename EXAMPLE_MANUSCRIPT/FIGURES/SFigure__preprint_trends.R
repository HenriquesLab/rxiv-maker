#!/usr/bin/env Rscript
# SFigure__preprint_trends: Preprint Submission Trends Across Multiple Servers
#
# Publication-ready plot showing the growth of arXiv submissions from 1991 to 2025.
# Optimized for single-column format in academic preprints.
# Runs in headless mode by default (no display window).
# Data source: https://arxiv.org/stats/monthly_submissions.
#
# Usage:
#   Rscript SFigure__preprint_trends.R           # Headless mode (save files only)
#   Rscript SFigure__preprint_trends.R --show    # Display plot and save files
#   Rscript SFigure__preprint_trends.R --help    # Show help message

# Function to check and install required packages with error handling
check_and_install_packages <- function(packages) {
  for (pkg in packages) {
    if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
      message(paste("Installing package:", pkg))
      tryCatch({
        install.packages(pkg, repos = "https://cloud.r-project.org/", dependencies = TRUE)
        library(pkg, character.only = TRUE)
        message(paste("Successfully installed and loaded:", pkg))
      }, error = function(e) {
        stop(paste("Failed to install package", pkg, ":", e$message))
      })
    }
  }
}

# List of required packages
required_packages <- c("ggplot2", "scales", "readr", "dplyr", "optparse", "svglite", "tidyr")
check_and_install_packages(required_packages)

# Ensure svglite is loaded
if (!requireNamespace("svglite", quietly = TRUE)) {
  stop("The 'svglite' package is required for SVG output but is not installed. Please install it with install.packages('svglite').")
} else {
  library(svglite)  # Explicitly load svglite to ensure it is recognized
}

library(ggplot2)
library(scales)
library(readr)
library(dplyr)
library(optparse)
library(tidyr)

# Parse command-line arguments
option_list <- list(
  make_option(c("--show"), action = "store_true", default = FALSE, help = "Display plot"),
  make_option(c("--help"), action = "store_true", default = FALSE, help = "Show help message")
)
opt <- parse_args(OptionParser(option_list = option_list))

if (opt$help) {
  cat("Usage: Rscript SFigure__preprint_trends.R [--show] [--help]\n")
  cat("  --show: Display plot (default is headless mode)\n")
  cat("  --help: Show this help message\n")
  quit(status = 0)
}

# Load and process data
load_and_process_data <- function() {
  # Get the directory of the current script
  script_args <- commandArgs(trailingOnly = FALSE)
  script_path <- normalizePath(sub("--file=", "", script_args[grep("--file=", script_args)]))
  script_dir <- dirname(script_path)

  # Define the path to the data file
  data_path <- file.path(script_dir, "DATA", "SFigure__preprint_trends", "pubmed_by_year.csv")

  # Check if the file exists
  if (!file.exists(data_path)) {
    stop(paste("Error: Data file not found at", data_path))
  }

  # Load and process the data
  df <- read_csv(data_path, show_col_types = FALSE)  # Suppress column type messages
  df <- df %>%
    pivot_longer(cols = c(preprint, medrxiv, biorxiv, arxiv), names_to = "source", values_to = "submissions") %>%
    mutate(date = as.Date(paste0(Year, "-01-01"), format = "%Y-%m-%d")) %>%  # Convert year to Date
    arrange(date, source)  # Ensure proper ordering
  return(df)
}

# Create the figure with modern styling
create_figure <- function(df) {
  # Define a modern color palette
  colors <- c("#1f77b4", "#ff7f0e", "#2ca02c", "#d62728")

  p <- ggplot(df, aes(x = date, y = submissions, color = source, fill = source)) +
    geom_line(size = 1.2, alpha = 0.9) +
    geom_area(alpha = 0.15, position = "identity") +
    labs(
      title = "Preprint Submissions by Year and Source",
      x = "Year",
      y = "Annual Submissions",
      color = "Source",
      fill = "Source"
    ) +
    scale_x_date(
      date_breaks = "1 year",
      date_labels = "%Y"
    ) +
    scale_y_continuous(
      labels = scales::comma_format(),
      expand = expansion(mult = c(0, 0.05))
    ) +
    scale_color_manual(values = colors) +
    scale_fill_manual(values = colors) +
    theme_minimal(base_size = 9) +
    theme(
      axis.title = element_text(face = "bold", color = "#333333"),
      plot.title = element_text(face = "bold", size = 11, hjust = 0.5, color = "#333333"),
      panel.grid.minor = element_line(size = 0.25, color = "#E0E0E0"),
      panel.grid.major = element_line(size = 0.4, color = "#D0D0D0"),
      axis.text.x = element_text(angle = 45, hjust = 1, color = "#333333"),
      axis.text.y = element_text(color = "#333333"),
      legend.position = "bottom",
      legend.title = element_text(face = "bold"),
      panel.background = element_rect(fill = "#FAFAFA", color = NA),
      plot.background = element_rect(fill = "white", color = NA)
    )
  return(p)
}

# Save the figure
save_figure <- function(p, output_path = NULL) {
  # Use environment variable if set, otherwise current working directory
  if (is.null(output_path)) {
    env_output_dir <- Sys.getenv("RXIV_FIGURE_OUTPUT_DIR", unset = "")
    if (env_output_dir != "") {
      output_path <- env_output_dir
    } else {
      output_path <- getwd()
    }
  }

  # Ensure the output directory exists
  if (!dir.exists(output_path)) {
    dir.create(output_path, recursive = TRUE)
  }

  # Save the figure in multiple formats
  ggsave(file.path(output_path, "SFigure__preprint_trends.pdf"), plot = p, width = 3.5, height = 4, dpi = 300)
  ggsave(file.path(output_path, "SFigure__preprint_trends.png"), plot = p, width = 3.5, height = 4, dpi = 300)

  # Use svglite for SVG output
  ggsave(file.path(output_path, "SFigure__preprint_trends.svg"), plot = p, width = 3.5, height = 4, device = svglite::svglite)

  cat("Figure saved to:\n")
  cat(paste0("  - ", file.path(output_path, "SFigure__preprint_trends.pdf"), "\n"))
  cat(paste0("  - ", file.path(output_path, "SFigure__preprint_trends.png"), "\n"))
  cat(paste0("  - ", file.path(output_path, "SFigure__preprint_trends.svg"), "\n"))
}

# Main function
main <- function() {
  df <- load_and_process_data()
  p <- create_figure(df)
  save_figure(p)
  if (opt$show) {
    print(p)
  }
}

main()
