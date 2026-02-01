"""
Processor 1080 - A data processing application for 1080 data files.

This package provides tools for loading, validating, processing,
and exporting 1080 data in various formats.
"""

__version__ = "1.0.0"

from .models import Record1080, ProcessingResult
from .processor import Processor1080
from .file_handler import FileHandler

__all__ = [
    "Record1080",
    "ProcessingResult",
    "Processor1080",
    "FileHandler",
]
