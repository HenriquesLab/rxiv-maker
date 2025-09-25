"""Data updater module for fetching fresh arXiv and preprint server data.

This module provides functions to fetch the latest submission data from:
1. arXiv monthly submissions
2. Preprint servers via PubMed search (bioRxiv, medRxiv, etc.)
"""

import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests


def fetch_arxiv_monthly_data() -> pd.DataFrame:
    """Fetch the latest arXiv monthly submission data.

    Returns:
        DataFrame with columns: year_month, submissions, cumulative_submissions
    """
    try:
        # Fetch CSV data from arXiv
        url = "https://arxiv.org/stats/get_monthly_submissions"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse CSV data
        lines = response.text.strip().split("\n")
        data = []
        cumulative = 0

        for line in lines:
            parts = line.split(",")
            if len(parts) >= 2:
                try:
                    month = parts[0].strip()
                    submissions = int(parts[1].strip())
                    cumulative += submissions

                    data.append({"year_month": month, "submissions": submissions, "cumulative_submissions": cumulative})
                except (ValueError, IndexError):
                    continue

        df = pd.DataFrame(data)
        df["year_month"] = pd.to_datetime(df["year_month"])

        # Verify chronological ordering
        if not df["year_month"].is_monotonic_increasing:
            df = df.sort_values("year_month").reset_index(drop=True)
            # Recalculate cumulative with correct ordering
            df["cumulative_submissions"] = df["submissions"].cumsum()

        print(f"Fetched {len(df)} months of arXiv data from {df['year_month'].min()} to {df['year_month'].max()}")
        return df

    except Exception as e:
        print(f"Error fetching arXiv data: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["year_month", "submissions", "cumulative_submissions"])


def fetch_pubmed_preprint_data(start_year: int = 2020) -> pd.DataFrame:
    """Fetch preprint publication data via PubMed search.

    Args:
        start_year: Starting year for data collection

    Returns:
        DataFrame with columns: year, server, publications
    """
    try:
        # Define search terms for different preprint servers
        search_terms = {
            "biorxiv": "biorxiv[Journal]",
            "medrxiv": "medrxiv[Journal]",
            "arxiv": "arxiv[Journal]",
            "preprint": "preprint[pt]",
        }

        current_year = datetime.now().year
        years = list(range(start_year, current_year + 1))

        all_data = []

        for server, search_term in search_terms.items():
            print(f"Fetching {server} data...")

            for year in years:
                try:
                    # Add year filter to search term
                    year_search = f"{search_term} AND {year}[dp]"

                    # Use NCBI E-utilities to get count
                    count = _get_pubmed_count(year_search)

                    if count is not None:
                        all_data.append({"year": year, "server": server, "publications": count})

                    # Be respectful to NCBI servers
                    time.sleep(0.5)

                except Exception as e:
                    print(f"Error fetching {server} data for {year}: {e}")
                    continue

        df = pd.DataFrame(all_data)
        print(f"Fetched preprint data for {len(df)} server-year combinations")
        return df

    except Exception as e:
        print(f"Error fetching preprint data: {e}")
        return pd.DataFrame(columns=["year", "server", "publications"])


def _get_pubmed_count(search_term: str) -> int:
    """Get publication count from PubMed for a given search term.

    Args:
        search_term: PubMed search query

    Returns:
        Number of publications found, or None if error
    """
    try:
        # NCBI E-utilities esearch endpoint
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

        params = {
            "db": "pubmed",
            "term": search_term,
            "retmode": "xml",
            "retmax": 0,  # We only want the count, not the actual records
            "tool": "rxiv-maker",
            "email": "ricardo.henriques@itqb.unl.pt",
        }

        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.content)
        count_elem = root.find("Count")

        if count_elem is not None:
            return int(count_elem.text)
        else:
            return None

    except Exception as e:
        print(f"Error getting PubMed count for '{search_term}': {e}")
        return None


def update_arxiv_data_file(output_path: str = "DATA/arxiv_monthly_submissions.csv") -> bool:
    """Update the arXiv monthly submissions CSV file with latest data.

    Args:
        output_path: Path to save the updated CSV file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Fetch fresh data
        df = fetch_arxiv_monthly_data()

        if df.empty:
            print("No arXiv data retrieved")
            return False

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save to CSV
        df.to_csv(output_path, index=False)

        print(f"Updated arXiv data file: {output_path}")
        print(f"Data spans: {df['year_month'].min()} to {df['year_month'].max()}")
        print(f"Total submissions: {df['cumulative_submissions'].iloc[-1]:,}")

        return True

    except Exception as e:
        print(f"Error updating arXiv data file: {e}")
        return False


def update_pubmed_data_file(output_path: str = "DATA/pubmed_by_year.csv", start_year: int = 2020) -> bool:
    """Update the PubMed preprint data CSV file with latest data.

    Args:
        output_path: Path to save the updated CSV file
        start_year: Starting year for data collection

    Returns:
        True if successful, False otherwise
    """
    try:
        # Fetch fresh data
        df = fetch_pubmed_preprint_data(start_year)

        if df.empty:
            print("No preprint data retrieved")
            return False

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save to CSV
        df.to_csv(output_path, index=False)

        print(f"Updated preprint data file: {output_path}")
        print(f"Data spans: {df['year'].min()} to {df['year'].max()}")
        print(f"Servers: {', '.join(df['server'].unique())}")

        return True

    except Exception as e:
        print(f"Error updating preprint data file: {e}")
        return False


def update_all_data_files(force_update: bool = False) -> Dict[str, bool]:
    """Update all data files with latest information.

    Args:
        force_update: If True, always update. If False, check file age first.

    Returns:
        Dictionary with update results for each file
    """
    results = {}

    # Define file paths relative to manuscript root
    # Get the manuscript root directory (2 levels up from src/py)
    manuscript_root = Path(__file__).parent.parent.parent
    arxiv_path = manuscript_root / "DATA" / "arxiv_monthly_submissions.csv"
    pubmed_path = manuscript_root / "DATA" / "pubmed_by_year.csv"

    # Check if update is needed (files older than 1 day)
    def needs_update(file_path: str) -> bool:
        if force_update:
            return True

        if not Path(file_path).exists():
            return True

        # For demonstration purposes, don't automatically update every day
        # In a real scenario, you might want more frequent updates
        file_age = datetime.now().timestamp() - Path(file_path).stat().st_mtime
        return file_age > 7 * 24 * 3600  # 7 days

    try:
        # Update arXiv data if needed
        if needs_update(str(arxiv_path)):
            print("Updating arXiv monthly submissions data...")
            results["arxiv"] = update_arxiv_data_file(str(arxiv_path))
        else:
            print("arXiv data is current")
            results["arxiv"] = True

        # Update preprint data if needed
        if needs_update(str(pubmed_path)):
            print("Updating preprint server data...")
            results["pubmed"] = update_pubmed_data_file(str(pubmed_path))
        else:
            print("Preprint data is current")
            results["pubmed"] = True

    except Exception as e:
        print(f"Update check failed: {e}")
        results["arxiv"] = True
        results["pubmed"] = True

    return results


def get_latest_statistics() -> Dict[str, Any]:
    """Get the latest statistics from updated data files.

    Returns:
        Dictionary with latest statistics
    """
    stats = {}

    try:
        # Load arXiv data
        manuscript_root = Path(__file__).parent.parent.parent
        arxiv_df = pd.read_csv(manuscript_root / "DATA" / "arxiv_monthly_submissions.csv")
        arxiv_df["year_month"] = pd.to_datetime(arxiv_df["year_month"])

        latest_arxiv = arxiv_df.iloc[-1]
        stats["arxiv"] = {
            "latest_month": latest_arxiv["year_month"].strftime("%B %Y"),
            "latest_submissions": int(latest_arxiv["submissions"]),
            "total_submissions": int(latest_arxiv["cumulative_submissions"]),
            "data_through": latest_arxiv["year_month"].strftime("%Y-%m-%d"),
        }

    except Exception as e:
        print(f"Error loading arXiv statistics: {e}")
        stats["arxiv"] = {}

    try:
        # Load preprint data
        pubmed_df = pd.read_csv(manuscript_root / "DATA" / "pubmed_by_year.csv")

        latest_year = pubmed_df["year"].max()
        latest_data = pubmed_df[pubmed_df["year"] == latest_year]

        stats["preprints"] = {
            "latest_year": int(latest_year),
            "servers": latest_data.groupby("server")["publications"].first().to_dict(),
            "total_latest_year": int(latest_data["publications"].sum()),
        }

    except Exception as e:
        print(f"Error loading preprint statistics: {e}")
        stats["preprints"] = {}

    stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return stats
