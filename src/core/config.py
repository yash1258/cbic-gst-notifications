"""
Core configuration for the CBIC Tax Information Scraper.
Provides shared settings and structured paths for all namespaces (GST/Customs/etc).
"""

import os
from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"

# Unified API Configuration
BASE_URL = "https://taxinformation.cbic.gov.in"

# HTTP Client Settings (Designed for Gentle Scraping of fragile CBIC servers)
MAX_CONCURRENT_REQUESTS = 5
DEFAULT_REQUEST_TIMEOUT = 60  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff base
BATCH_SIZE = 20
BATCH_DELAY_SECONDS = 1.0


def get_namespace_paths(tax_type: str, document_category: str):
    """
    Generates standardized paths for any tax_type + document_category combination.
    E.g. ('gst', 'notifications') outputs paths mapped to data/gst/notifications/
    This strict namespacing is critical for AI-agent traversal without collisions.
    """
    base = DATA_DIR / tax_type.lower() / document_category.lower()
    
    return {
        "base": base,
        "metadata": base / "metadata",          # Contains raw_metadata.json, year.json
        "downloads": base / "downloads",        # Contains the actual PDF files and local metadata
        "logs": base / "logs",                 # Contains scraping errors and download logs
        
        # Commonly accessed specific files
        "raw_metadata_file": base / "metadata" / "raw_metadata.json",
        "progress_file": base / "logs" / "progress.json",
        "error_log_file": base / "logs" / "errors.json"
    }

def ensure_namespace_dirs(tax_type: str, document_category: str):
    """Creates the standard directory structure for a namespace."""
    paths = get_namespace_paths(tax_type, document_category)
    for key in ["base", "metadata", "downloads", "logs"]:
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths
