"""Configuration for CBIC GST Notification Scraper"""

# API Configuration
BASE_URL = "https://taxinformation.cbic.gov.in"
METADATA_ENDPOINT = "/api/cbic-notification-msts/{id}"

# ID Range (discovered from API exploration)
ID_START = 1000001
ID_END = 1010588

# Filters
GST_TAX_ID = 1000001
MIN_DATE = "2017-01-01"  # CGST Act came into effect July 2017

# Concurrency - Very gentle settings
MAX_CONCURRENT = 5
BATCH_SIZE = 100
BATCH_DELAY_SECONDS = 1.0  # Delay between batches
REQUEST_TIMEOUT_SECONDS = 30

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # Exponential backoff base

# Paths
DATA_DIR = "data/metadata"
ERROR_DIR = "data/errors"
RAW_METADATA_FILE = "data/metadata/raw_metadata.json"
SUMMARY_FILE = "data/metadata/summary.json"
ERROR_LOG_FILE = "data/errors/scan_errors.json"
PROGRESS_FILE = "data/metadata/progress.json"

# SSL - CBIC has certificate issues
VERIFY_SSL = False
