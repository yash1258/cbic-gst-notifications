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

from src.gst.circulars.scraper import GstCircularScraper
from src.gst.circulars.organizer import GstCircularOrganizer
from src.gst.circulars.downloader import GstCircularDownloader
from src.gst.circulars.analyzer import GstCircularAnalyzer


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

def run_scrape_circ(args):
    scraper = GstCircularScraper()
    asyncio.run(scraper.run())

def run_organize_circ(args):
    organizer = GstCircularOrganizer()
    organizer.run()

def run_download_circ(args):
    year = args.year
    lang = args.language.upper()
    
    if lang not in ["ENG", "HINDI", "BOTH"]:
        print("Language must be 'ENG', 'HINDI', or 'BOTH'.")
        return
        
    print(f"Beginning PDF extraction for Circulars {year} | Language: {lang}")
    
    def dl_lang(l):
        dl = GstCircularDownloader(year, l)
        asyncio.run(dl.run())
        
    if lang in ["ENG", "BOTH"]:
        dl_lang("ENG")
    if lang in ["HINDI", "BOTH"]:
        dl_lang("HINDI")

def run_analyze_circ(args):
    """Analyzes completeness of the circular data against the DB metadata."""
    analyzer = GstCircularAnalyzer(args.year)
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

    # Circulars
    parser_scrape_circ = subparsers.add_parser("scrape-circ", help="Fetch circular metadata from CBIC APIs")
    parser_scrape_circ.set_defaults(func=run_scrape_circ)

    parser_organize_circ = subparsers.add_parser("organize-circ", help="Sort the raw API data for circulars into Years")
    parser_organize_circ.set_defaults(func=run_organize_circ)

    parser_download_circ = subparsers.add_parser("download-circ", help="Download Circular PDFs by Year")
    parser_download_circ.add_argument("year", type=str, help="Year to download (e.g. 2024)")
    parser_download_circ.add_argument("--language", "-l", type=str, default="BOTH", 
                               help="Language 'ENG', 'HINDI', or 'BOTH' (default)")
    parser_download_circ.set_defaults(func=run_download_circ)

    parser_analyze_circ = subparsers.add_parser("analyze-circ", help="Verify completeness of circular downloads for a Year")
    parser_analyze_circ.add_argument("year", type=str, help="Year to check (e.g. 2024)")
    parser_analyze_circ.set_defaults(func=run_analyze_circ)

    # Future hooks: "forms", "customs" would become their own top-level subparsers here.

    args = parser.parse_args()
    
    try:
        args.func(args)
    except Exception as e:
        print(f"\nExecution Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
