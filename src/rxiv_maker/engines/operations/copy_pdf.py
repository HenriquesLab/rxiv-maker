"""DEPRECATED: PDF copy functionality moved to BuildManager.

This module is deprecated. The PDF copying functionality has been integrated
directly into the BuildManager class. Use BuildManager.copy_pdf_to_manuscript()
instead.

This module will be removed in a future version.
"""

import warnings

from ...processors.yaml_processor import extract_yaml_metadata
from ...utils import copy_pdf_to_manuscript_folder, find_manuscript_md

# Issue deprecation warning
warnings.warn(
    "copy_pdf module is deprecated. Use BuildManager.copy_pdf_to_manuscript() instead.",
    DeprecationWarning,
    stacklevel=2,
)


def copy_pdf_with_custom_filename(output_dir: str = "output") -> bool:
    """DEPRECATED: Copy PDF to manuscript directory with custom filename.

    Use BuildManager.copy_pdf_to_manuscript() instead.
    """
    warnings.warn(
        "copy_pdf_with_custom_filename() is deprecated. Use BuildManager.copy_pdf_to_manuscript() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    try:
        manuscript_md = find_manuscript_md()
        yaml_metadata = extract_yaml_metadata(manuscript_md)
        result = copy_pdf_to_manuscript_folder(output_dir, yaml_metadata)
        return bool(result)
    except Exception:
        return False
