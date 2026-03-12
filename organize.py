"""
Organize raw metadata into year-based JSON files and generate summary.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

import config


def organize_by_year():
    """Split raw_metadata.json into year-based files."""
    
    # Load raw data
    with open(config.RAW_METADATA_FILE, "r", encoding="utf-8") as f:
        notifications = json.load(f)
    
    # Group by year
    by_year = defaultdict(list)
    for n in notifications:
        date_str = n.get("notificationDt", "")
        if date_str:
            year = date_str[:4]
            by_year[year].append(n)
    
    # Sort each year by date
    for year in by_year:
        by_year[year].sort(key=lambda x: x.get("notificationDt", ""))
    
    # Save each year to separate file
    for year in sorted(by_year.keys()):
        year_data = {
            "year": int(year),
            "tax_type": "GST",
            "generated_at": datetime.now().isoformat(),
            "count": len(by_year[year]),
            "notifications": by_year[year]
        }
        
        filepath = f"{config.DATA_DIR}/{year}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(year_data, f, indent=2, ensure_ascii=False)
        
        print(f"  {year}.json: {len(by_year[year])} notifications")
    
    return by_year


def generate_summary(by_year):
    """Generate summary report."""
    
    # Category breakdown
    categories = defaultdict(int)
    # Amendment stats
    amended = 0
    omitted = 0
    total = 0
    
    for year, notifications in by_year.items():
        for n in notifications:
            total += 1
            # Category
            cat = n.get("notificationCategory", "Unknown")
            categories[cat] += 1
            # Flags
            if n.get("isAmended"):
                amended += 1
            if n.get("isOmitted"):
                omitted += 1
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_notifications": total,
        "date_range": {
            "start": "2017-01-01",
            "end": "2025-12-31"
        },
        "by_year": {
            year: len(notifications) 
            for year, notifications in sorted(by_year.items())
        },
        "by_category": dict(sorted(categories.items(), key=lambda x: -x[1])),
        "statistics": {
            "amended": amended,
            "omitted": omitted,
            "with_hindi": sum(
                1 for year, notifs in by_year.items()
                for n in notifs if n.get("docFileNameHi")
            )
        },
        "files": [f"{year}.json" for year in sorted(by_year.keys())]
    }
    
    with open(config.SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary


def main():
    print("=" * 60)
    print("Organizing CBIC GST Notifications")
    print("=" * 60)
    print()
    
    # Organize by year
    print("Creating year-based JSON files...")
    by_year = organize_by_year()
    print()
    
    # Generate summary
    print("Generating summary report...")
    summary = generate_summary(by_year)
    print()
    
    # Display summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total GST notifications (2017+): {summary['total_notifications']}")
    print()
    print("By Year:")
    for year, count in summary['by_year'].items():
        print(f"  {year}: {count}")
    print()
    print("Top Categories:")
    for cat, count in list(summary['by_category'].items())[:5]:
        print(f"  {cat}: {count}")
    print()
    print("Statistics:")
    print(f"  Amended: {summary['statistics']['amended']}")
    print(f"  Omitted: {summary['statistics']['omitted']}")
    print(f"  With Hindi version: {summary['statistics']['with_hindi']}")
    print()
    print(f"Files saved to: {config.DATA_DIR}/")
    print(f"Summary saved to: {config.SUMMARY_FILE}")


if __name__ == "__main__":
    main()
