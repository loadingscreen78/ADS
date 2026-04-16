# File upload module
"""
File Upload System for Batch Data

Provides:
- File upload handling
- Format validation (Parquet, CSV)
- Data preprocessing
- Metadata extraction
"""

from src.upload.file_handler import FileUploadHandler

__all__ = [
    "FileUploadHandler",
]
