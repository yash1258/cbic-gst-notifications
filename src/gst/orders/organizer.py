"""
Splits the large `raw_metadata.json` into isolated year.json files for Orders.
"""

from collections import defaultdict
from datetime import datetime

from src.core import config
from src.core.utils import load_json, save_json

class GstOrderOrganizer:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("gst", "orders")
        self.raw_file = self.paths["raw_metadata_file"]
        self.summary_file = self.paths["metadata"] / "summary.json"

    def run(self):
        orders = load_json(self.raw_file, [])
        if not orders:
            print("No raw_metadata.json found to organize.")
            return

        print(f"Organizing {len(orders)} records by year...")
        
        by_year = defaultdict(list)
        for o in orders:
            date_str = o.get("orderDt", "")
            if date_str:
                by_year[date_str[:4]].append(o)

        # Sort within years
        for year in by_year:
            by_year[year].sort(key=lambda x: x.get("orderDt", ""))

        categories = defaultdict(int)
        amended = 0
        omitted = 0

        for year in sorted(by_year.keys()):
            for o in by_year[year]:
                categories[o.get("orderCategory", "Unknown")] += 1
                if o.get("isAmended"): amended += 1
                if o.get("isOmitted"): omitted += 1
                
            year_data = {
                "year": int(year),
                "tax_type": "GST",
                "document_category": "Orders",
                "count": len(by_year[year]),
                "orders": by_year[year]
            }
            save_json(self.paths["metadata"] / f"{year}.json", year_data)
            print(f"Saved {year}.json ({len(by_year[year])})")
            
        # Summary
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_orders": len(orders),
            "by_year": {y: len(o) for y, o in sorted(by_year.items())},
            "by_category": dict(sorted(categories.items(), key=lambda x: -x[1])),
            "statistics": {
                "amended": amended,
                "omitted": omitted,
                "with_hindi": sum(1 for o in orders if o.get("docFileNameHi"))
            }
        }
        
        save_json(self.summary_file, summary)
        print("Summary generated successfully.")
