"""
Splits the large `raw_metadata.json` into isolated year.json files.
"""

from collections import defaultdict
from datetime import datetime

from src.core import config
from src.core.utils import load_json, save_json

class GstNotificationOrganizer:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("gst", "notifications")
        self.raw_file = self.paths["raw_metadata_file"]
        self.summary_file = self.paths["metadata"] / "summary.json"

    def run(self):
        notifications = load_json(self.raw_file, [])
        if not notifications:
            print("No raw_metadata.json found to organize.")
            return

        print(f"Organizing {len(notifications)} records by year...")
        
        by_year = defaultdict(list)
        for n in notifications:
            date_str = n.get("notificationDt", "")
            if date_str:
                by_year[date_str[:4]].append(n)

        # Sort within years
        for year in by_year:
            by_year[year].sort(key=lambda x: x.get("notificationDt", ""))

        categories = defaultdict(int)
        amended = 0
        omitted = 0

        for year in sorted(by_year.keys()):
            for n in by_year[year]:
                categories[n.get("notificationCategory", "Unknown")] += 1
                if n.get("isAmended"): amended += 1
                if n.get("isOmitted"): omitted += 1
                
            year_data = {
                "year": int(year),
                "tax_type": "GST",
                "document_category": "Notifications",
                "count": len(by_year[year]),
                "notifications": by_year[year]
            }
            save_json(self.paths["metadata"] / f"{year}.json", year_data)
            print(f"Saved {year}.json ({len(by_year[year])})")
            
        # Summary
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_notifications": len(notifications),
            "by_year": {y: len(n) for y, n in sorted(by_year.items())},
            "by_category": dict(sorted(categories.items(), key=lambda x: -x[1])),
            "statistics": {
                "amended": amended,
                "omitted": omitted,
                "with_hindi": sum(1 for n in notifications if n.get("docFileNameHi"))
            }
        }
        
        save_json(self.summary_file, summary)
        print("Summary generated successfully.")
