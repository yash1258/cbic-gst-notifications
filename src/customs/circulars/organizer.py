"""
Splits raw_metadata.json into isolated year.json files for Customs Circulars.
"""

from collections import defaultdict
from datetime import datetime

from src.core import config
from src.core.utils import load_json, save_json

class CustomsCircularOrganizer:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("customs", "circulars")
        self.raw_file = self.paths["raw_metadata_file"]
        self.summary_file = self.paths["metadata"] / "summary.json"

    def run(self):
        circulars = load_json(self.raw_file, [])
        if not circulars:
            print("No raw_metadata.json found to organize.")
            return

        print(f"Organizing {len(circulars)} Customs circular records by year...")
        
        by_year = defaultdict(list)
        for c in circulars:
            date_str = c.get("circularDt", "")
            if date_str:
                by_year[date_str[:4]].append(c)

        for year in by_year:
            by_year[year].sort(key=lambda x: x.get("circularDt", ""))

        categories = defaultdict(int)
        amended = 0
        omitted = 0

        for year in sorted(by_year.keys()):
            for c in by_year[year]:
                categories[c.get("circularCategory", "Unknown")] += 1
                if c.get("isAmended"): amended += 1
                if c.get("isOmitted"): omitted += 1
                
            year_data = {
                "year": int(year),
                "tax_type": "Customs",
                "document_category": "Circulars",
                "count": len(by_year[year]),
                "circulars": by_year[year]
            }
            save_json(self.paths["metadata"] / f"{year}.json", year_data)
            print(f"Saved {year}.json ({len(by_year[year])})")
            
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_circulars": len(circulars),
            "by_year": {y: len(c) for y, c in sorted(by_year.items())},
            "by_category": dict(sorted(categories.items(), key=lambda x: -x[1])),
            "statistics": {
                "amended": amended,
                "omitted": omitted,
                "with_hindi": sum(1 for c in circulars if c.get("docFileNameHi"))
            }
        }
        
        save_json(self.summary_file, summary)
        print("Summary generated successfully.")
