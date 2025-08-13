"""DOI validation module."""

from .api_clients import (
    BaseDOIClient,
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
    "BaseDOIClient",
    "CrossRefClient",
    "DataCiteClient",
    "HandleSystemClient",
    "JOSSClient",
    "OpenAlexClient",
    "SemanticScholarClient",
    "DOIResolver",
    "MetadataComparator",
]
