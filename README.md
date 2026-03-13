# CBIC Tax Data Extractor

A modular Python pipeline for extracting tax notifications, circulars, orders, instructions, and forms from the [CBIC Tax Information Portal](https://taxinformation.cbic.gov.in).

## What's Extracted

See **[EXTRACTION_STATUS.md](EXTRACTION_STATUS.md)** for the full tracking document.

| Data Type | Documents | Years | Status |
|---|---|---|---|
| GST Notifications | 1,281 | 2017–2025 | ✅ Complete |
| GST Circulars | 271 | 2017–2025 | ✅ Complete |
| GST Orders | 39 | 2017–2022 | ✅ Complete |
| GST Instructions | 42 | 2019–2025 | ✅ Complete |
| GST Forms | 197 | 21 categories | ✅ Complete |
| Customs Notifications | 6,872 | 1935–2026 | 📋 Metadata Only |
| Customs Circulars | 1,760 | 1995–2026 | 📋 Metadata Only |
| Customs Instructions | 393 | 2004–2026 | 📋 Metadata Only |
| Central Excise | — | — | ⬜ Not Started |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

All commands go through the unified CLI entry point `run.py`:

```bash
# GST Notifications
python run.py scrape                                # Scrape metadata from CBIC API
python run.py organize                              # Organize into year JSONs
python run.py download <year> [-l ENG|HINDI|BOTH]   # Download PDFs
python run.py analyze <year>                        # Verify completeness

# GST Circulars
python run.py scrape-circ                           # Scrape metadata
python run.py organize-circ                         # Organize into year JSONs
python run.py download-circ <year> [-l ENG|HINDI|BOTH]  # Download PDFs
python run.py analyze-circ <year>                   # Verify completeness

# GST Orders
python run.py scrape-order                          # Scrape metadata
python run.py organize-order                        # Organize into year JSONs
python run.py download-order <year> [-l ENG|HINDI|BOTH]  # Download PDFs
python run.py analyze-order <year>                  # Verify completeness

# GST Instructions
python run.py scrape-inst                           # Scrape metadata
python run.py organize-inst                         # Organize into year JSONs
python run.py download-inst <year> [-l ENG|HINDI|BOTH]  # Download PDFs
python run.py analyze-inst <year>                   # Verify completeness

# GST Forms
python run.py scrape-forms                          # Fetch all form metadata
python run.py download-forms                        # Download all form PDFs
python run.py analyze-forms                         # Verify completeness

# Customs (metadata pipelines — same pattern as GST)
python run.py scrape-customs                        # Customs Notifications
python run.py scrape-customs-circ                   # Customs Circulars
python run.py scrape-customs-inst                   # Customs Instructions
# organize-customs, download-customs <year>, analyze-customs <year>, etc.
```

## Project Structure

```
cbic-gst-scans/
├── run.py                     # CLI entry point (all commands)
├── src/
│   ├── core/                  # Shared: api_client, config, utils
│   ├── gst/
│   │   ├── notifications/     # scraper, organizer, downloader, analyzer
│   │   ├── circulars/
│   │   ├── orders/
│   │   ├── instructions/
│   │   └── forms/             # scraper, downloader, analyzer (no organizer)
│   └── customs/
│       ├── notifications/
│       ├── circulars/
│       └── instructions/
├── data/                      # All extracted data (gitignored)
├── EXTRACTION_STATUS.md       # Full tracking document
├── API_DOCUMENTATION.md       # CBIC API endpoint reference
└── requirements.txt
```

## API Notes

- **No authentication** required (public endpoints)
- **Self-signed SSL** — verification is disabled in the pipeline
- **Rate limiting** — 5 concurrent connections with batch delays
- See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for full endpoint reference

## License

MIT
