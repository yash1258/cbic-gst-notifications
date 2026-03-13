#!/usr/bin/env python3
"""
CLI entry point for CBIC Tax Data Extractor.
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

from src.gst.orders.scraper import GstOrderScraper
from src.gst.orders.organizer import GstOrderOrganizer
from src.gst.orders.downloader import GstOrderDownloader
from src.gst.orders.analyzer import GstOrderAnalyzer

from src.customs.notifications.scraper import CustomsNotificationScraper
from src.customs.notifications.organizer import CustomsNotificationOrganizer
from src.customs.notifications.downloader import CustomsNotificationDownloader
from src.customs.notifications.analyzer import CustomsNotificationAnalyzer

from src.customs.circulars.scraper import CustomsCircularScraper
from src.customs.circulars.organizer import CustomsCircularOrganizer
from src.customs.circulars.downloader import CustomsCircularDownloader
from src.customs.circulars.analyzer import CustomsCircularAnalyzer

from src.gst.instructions.scraper import GstInstructionScraper
from src.gst.instructions.organizer import GstInstructionOrganizer
from src.gst.instructions.downloader import GstInstructionDownloader
from src.gst.instructions.analyzer import GstInstructionAnalyzer

from src.customs.instructions.scraper import CustomsInstructionScraper
from src.customs.instructions.organizer import CustomsInstructionOrganizer
from src.customs.instructions.downloader import CustomsInstructionDownloader
from src.customs.instructions.analyzer import CustomsInstructionAnalyzer

from src.gst.forms.scraper import GstFormScraper
from src.gst.forms.downloader import GstFormDownloader
from src.gst.forms.analyzer import GstFormAnalyzer


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

def run_scrape_order(args):
    scraper = GstOrderScraper()
    asyncio.run(scraper.run())

def run_organize_order(args):
    organizer = GstOrderOrganizer()
    organizer.run()

def run_download_order(args):
    year = args.year
    lang = args.language.upper()
    
    if lang not in ["ENG", "HINDI", "BOTH"]:
        print("Language must be 'ENG', 'HINDI', or 'BOTH'.")
        return
        
    print(f"Beginning PDF extraction for Orders {year} | Language: {lang}")
    
    def dl_lang(l):
        dl = GstOrderDownloader(year, l)
        asyncio.run(dl.run())
        
    if lang in ["ENG", "BOTH"]:
        dl_lang("ENG")
    if lang in ["HINDI", "BOTH"]:
        dl_lang("HINDI")

def run_analyze_order(args):
    """Analyzes completeness of the order data against the DB metadata."""
    analyzer = GstOrderAnalyzer(args.year)
    results = analyzer.run()
    if results:
        print(json.dumps(results, indent=2))

def _dl_customs_notif(args):
    lang = args.language.upper()
    if lang not in ["ENG", "HINDI", "BOTH"]:
        print("Language must be 'ENG', 'HINDI', or 'BOTH'."); return
    if lang in ["ENG", "BOTH"]:
        asyncio.run(CustomsNotificationDownloader(args.year, "ENG").run())
    if lang in ["HINDI", "BOTH"]:
        asyncio.run(CustomsNotificationDownloader(args.year, "HINDI").run())

def _dl_customs_circ(args):
    lang = args.language.upper()
    if lang not in ["ENG", "HINDI", "BOTH"]:
        print("Language must be 'ENG', 'HINDI', or 'BOTH'."); return
    if lang in ["ENG", "BOTH"]:
        asyncio.run(CustomsCircularDownloader(args.year, "ENG").run())
    if lang in ["HINDI", "BOTH"]:
        asyncio.run(CustomsCircularDownloader(args.year, "HINDI").run())

def _dl_inst(args, tax_type):
    lang = args.language.upper()
    if lang not in ["ENG", "HINDI", "BOTH"]:
        print("Language must be 'ENG', 'HINDI', or 'BOTH'."); return
    Cls = GstInstructionDownloader if tax_type == "gst" else CustomsInstructionDownloader
    if lang in ["ENG", "BOTH"]:
        asyncio.run(Cls(args.year, "ENG").run())
    if lang in ["HINDI", "BOTH"]:
        asyncio.run(Cls(args.year, "HINDI").run())

def _analyze_forms():
    results = GstFormAnalyzer().run()
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

    # Orders
    parser_scrape_order = subparsers.add_parser("scrape-order", help="Fetch order metadata from CBIC APIs")
    parser_scrape_order.set_defaults(func=run_scrape_order)

    parser_organize_order = subparsers.add_parser("organize-order", help="Sort the raw API data for orders into Years")
    parser_organize_order.set_defaults(func=run_organize_order)

    parser_download_order = subparsers.add_parser("download-order", help="Download Order PDFs by Year")
    parser_download_order.add_argument("year", type=str, help="Year to download (e.g. 2024)")
    parser_download_order.add_argument("--language", "-l", type=str, default="BOTH", 
                               help="Language 'ENG', 'HINDI', or 'BOTH' (default)")
    parser_download_order.set_defaults(func=run_download_order)

    parser_analyze_order = subparsers.add_parser("analyze-order", help="Verify completeness of order downloads for a Year")
    parser_analyze_order.add_argument("year", type=str, help="Year to check (e.g. 2024)")
    parser_analyze_order.set_defaults(func=run_analyze_order)

    # Customs Notifications
    subparsers.add_parser("scrape-customs", help="Fetch Customs notification metadata").set_defaults(func=lambda a: asyncio.run(CustomsNotificationScraper().run()))
    subparsers.add_parser("organize-customs", help="Sort Customs notification data into Years").set_defaults(func=lambda a: CustomsNotificationOrganizer().run())

    p = subparsers.add_parser("download-customs", help="Download Customs Notification PDFs by Year")
    p.add_argument("year", type=str)
    p.add_argument("--language", "-l", type=str, default="BOTH")
    p.set_defaults(func=lambda a: _dl_customs_notif(a))

    p = subparsers.add_parser("analyze-customs", help="Verify Customs notification downloads")
    p.add_argument("year", type=str)
    p.set_defaults(func=lambda a: print(json.dumps(CustomsNotificationAnalyzer(a.year).run(), indent=2)) if CustomsNotificationAnalyzer(a.year).run() else None)

    # Customs Circulars
    subparsers.add_parser("scrape-customs-circ", help="Fetch Customs circular metadata").set_defaults(func=lambda a: asyncio.run(CustomsCircularScraper().run()))
    subparsers.add_parser("organize-customs-circ", help="Sort Customs circular data into Years").set_defaults(func=lambda a: CustomsCircularOrganizer().run())

    p = subparsers.add_parser("download-customs-circ", help="Download Customs Circular PDFs by Year")
    p.add_argument("year", type=str)
    p.add_argument("--language", "-l", type=str, default="BOTH")
    p.set_defaults(func=lambda a: _dl_customs_circ(a))

    p = subparsers.add_parser("analyze-customs-circ", help="Verify Customs circular downloads")
    p.add_argument("year", type=str)
    p.set_defaults(func=lambda a: print(json.dumps(CustomsCircularAnalyzer(a.year).run(), indent=2)) if CustomsCircularAnalyzer(a.year).run() else None)

    # GST Instructions
    subparsers.add_parser("scrape-inst", help="Fetch GST instruction metadata").set_defaults(func=lambda a: asyncio.run(GstInstructionScraper().run()))
    subparsers.add_parser("organize-inst", help="Sort GST instruction data into Years").set_defaults(func=lambda a: GstInstructionOrganizer().run())

    p = subparsers.add_parser("download-inst", help="Download GST Instruction PDFs by Year")
    p.add_argument("year", type=str)
    p.add_argument("--language", "-l", type=str, default="BOTH")
    p.set_defaults(func=lambda a: _dl_inst(a, "gst"))

    p = subparsers.add_parser("analyze-inst", help="Verify GST instruction downloads")
    p.add_argument("year", type=str)
    p.set_defaults(func=lambda a: print(json.dumps(GstInstructionAnalyzer(a.year).run(), indent=2)) if GstInstructionAnalyzer(a.year).run() else None)

    # Customs Instructions
    subparsers.add_parser("scrape-customs-inst", help="Fetch Customs instruction metadata").set_defaults(func=lambda a: asyncio.run(CustomsInstructionScraper().run()))
    subparsers.add_parser("organize-customs-inst", help="Sort Customs instruction data into Years").set_defaults(func=lambda a: CustomsInstructionOrganizer().run())

    p = subparsers.add_parser("download-customs-inst", help="Download Customs Instruction PDFs by Year")
    p.add_argument("year", type=str)
    p.add_argument("--language", "-l", type=str, default="BOTH")
    p.set_defaults(func=lambda a: _dl_inst(a, "customs"))

    p = subparsers.add_parser("analyze-customs-inst", help="Verify Customs instruction downloads")
    p.add_argument("year", type=str)
    p.set_defaults(func=lambda a: print(json.dumps(CustomsInstructionAnalyzer(a.year).run(), indent=2)) if CustomsInstructionAnalyzer(a.year).run() else None)

    # GST Forms
    subparsers.add_parser("scrape-forms", help="Fetch all GST form metadata (bulk API)").set_defaults(func=lambda a: asyncio.run(GstFormScraper().run()))
    subparsers.add_parser("download-forms", help="Download all GST Form PDFs").set_defaults(func=lambda a: asyncio.run(GstFormDownloader().run()))
    subparsers.add_parser("analyze-forms", help="Verify GST form download completeness").set_defaults(func=lambda a: _analyze_forms())

    # Future hooks: Central Excise, HSNS Cess

    args = parser.parse_args()
    
    try:
        args.func(args)
    except Exception as e:
        print(f"\nExecution Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
