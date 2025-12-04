"""Exporters for converting manuscripts to various formats.

This package provides functionality to export rxiv-maker manuscripts to different
file formats for collaborative review and distribution.

Available exporters:
- DocxExporter: Export to Microsoft Word (.docx) format
"""

from .docx_exporter import DocxExporter

__all__ = ["DocxExporter"]
