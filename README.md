# CBIC GST Notification Scraper

A Python-based async scraper for extracting GST notification metadata from the CBIC (Central Board of Indirect Taxes and Customs) website.

## Overview

This tool scrapes public API endpoints from https://taxinformation.cbic.gov.in to collect GST notification metadata published since 2017.

## Features

- **Gentle scraping**: 5 concurrent connections with rate limiting (~18-20 min for 10,588 IDs)
- **Resume capability**: Interrupted scans can be resumed from last position
- **Zero errors**: Retry logic with exponential backoff
- **Organized output**: JSON files grouped by year (2017-2025)
- **Comprehensive logging**: All errors documented for review

## Stats

- **Total notifications found**: 1,281 GST notifications (2017+)
- **Years covered**: 2017-2025
- **Categories**: Central Tax, Integrated Tax, Union Territory Tax, Compensation Cess

## Usage

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run scraper
```bash
python scraper.py
```

### Organize results
```bash
python organize.py
```

## Output Structure

```
data/
├── metadata/
│   ├── raw_metadata.json    # All 1,281 records
│   ├── summary.json         # Statistics
│   ├── 2017.json           # By year
│   ├── 2018.json
│   └── ...
└── errors/
    └── scan_errors.json     # Error log (if any)
```

## Data Fields

Each notification includes:
- `notificationNo` - Official number (e.g., "01/2025-Central Tax")
- `notificationDt` - Issue date
- `notificationName` - Subject/description
- `notificationCategory` - Type (Central Tax, Integrated Tax, etc.)
- `docFileName` / `docFileNameHi` - PDF filenames (English/Hindi)
- `isAmended` / `isOmitted` - History flags

## API Endpoints Used

- `GET /api/cbic-notification-msts/{id}` - Metadata
- `GET /api/cbic-notification-msts/download/{id}/ENG` - PDF download (future phase)

## License

MIT
