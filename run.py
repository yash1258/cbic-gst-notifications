#!/usr/bin/env python3
"""
CLI entry point for CBIC GST Modular Extractor.
Run with `--help` for usage information.
"""

import asyncio
import argparse
import sys
import json
from pprint import pprint

from src.gst.notifications.scraper import GstNotificationScraper
from src.gst.notifications.organizer import GstNotificationOrganizer
from src.gst.notifications.downloader import GstNotificationDownloader
from src.gst.notifications.analyzer import GstNotificationAnalyzer


def run_scrape(args):
    """Scrapes raw DB metadata from endpoints."""
    scraper = GstNotificationScraper()
    asyncio.run(scraper.run())

def run_organize(args):
    """Converts raw data into Year JSONs."""
    organizer = GstNotificationOrganizer()
    organizer.run()

def run_download(args):
    """Downloads actual PDFs using explicit Year JSONs."""
    year = args.year
    lang = args.language.upper()
    
    if lang not in ["ENG", "HINDI", "BOTH"]:
        print("Language must be 'ENG', 'HINDI', or 'BOTH'.")
        return
        
    print(f"Beginning PDF extraction for {year} | Language: {lang}")
    
    def dl_lang(l):
        dl = GstNotificationDownloader(year, l)
        asyncio.run(dl.run())
        
    if lang in ["ENG", "BOTH"]:
        dl_lang("ENG")
    if lang in ["HINDI", "BOTH"]:
        dl_lang("HINDI")

def run_analyze(args):
    """Analyzes completeness of the data against the DB metadata."""
    analyzer = GstNotificationAnalyzer(args.year)
    results = analyzer.run()
    if results:
        print(json.dumps(results, indent=2))

def main():
    parser = argparse.ArgumentParser(description="CBIC Tax Metadata Extractor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scraper
    parser_scrape = subparsers.add_parser("scrape", help="Fetch notification metadata from CBIC APIs")
    parser_scrape.set_defaults(func=run_scrape)

    # Organizer
    parser_organizer = subparsers.add_parser("organize", help="Sort the raw API data into Years")
    parser_organizer.set_defaults(func=run_organize)

    # Downloader
    parser_download = subparsers.add_parser("download", help="Download PDFs by Year")
    parser_download.add_argument("year", type=str, help="Year to download (e.g. 2024)")
    parser_download.add_argument("--language", "-l", type=str, default="BOTH", 
                               help="Language 'ENG', 'HINDI', or 'BOTH' (default)")
    parser_download.set_defaults(func=run_download)

    # Analyzer
    parser_analyze = subparsers.add_parser("analyze", help="Verify completeness of downloads for a Year")
    parser_analyze.add_argument("year", type=str, help="Year to check (e.g. 2024)")
    parser_analyze.set_defaults(func=run_analyze)

    # Future hooks: "circulars", "forms", "customs" would become their own top-level subparsers here.

    args = parser.parse_args()
    
    try:
        args.func(args)
    except Exception as e:
        print(f"\nExecution Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
