"""
Utility functions for the application.
"""

import uuid
import hashlib
import os
from pathlib import Path
from typing import Optional


def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())


def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()