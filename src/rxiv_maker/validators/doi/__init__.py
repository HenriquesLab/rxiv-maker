"""DOI validation module."""

from .api_clients import (
    CrossRefClient,
    DataCiteClient,
    DOIResolver,
    HandleSystemClient,
    JOSSClient,
    OpenAlexClient,
    SemanticScholarClient,
)
from .metadata_comparator import MetadataComparator

__all__ = [
    "CrossRefClient",
    "DataCiteClient",
    "HandleSystemClient",
    "JOSSClient",
    "OpenAlexClient",
    "SemanticScholarClient",
    "DOIResolver",
    "MetadataComparator",
]
