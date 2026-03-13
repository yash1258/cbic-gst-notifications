"""
Splits raw_metadata.json into isolated year.json files for Customs Instructions.
"""

from collections import defaultdict
from datetime import datetime

from src.core import config
from src.core.utils import load_json, save_json

class CustomsInstructionOrganizer:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("customs", "instructions")
        self.raw_file = self.paths["raw_metadata_file"]
        self.summary_file = self.paths["metadata"] / "summary.json"

    def run(self):
        instructions = load_json(self.raw_file, [])
        if not instructions:
            print("No raw_metadata.json found to organize.")
            return

        print(f"Organizing {len(instructions)} Customs instruction records by year...")
        
        by_year = defaultdict(list)
        for inst in instructions:
            date_str = inst.get("instructionDt", "")
            if date_str:
                by_year[date_str[:4]].append(inst)

        for year in by_year:
            by_year[year].sort(key=lambda x: x.get("instructionDt", ""))

        categories = defaultdict(int)
        for year in sorted(by_year.keys()):
            for inst in by_year[year]:
                cat = inst.get("instructionCategory") or "Uncategorized"
                categories[cat] += 1
            year_data = {
                "year": int(year),
                "tax_type": "Customs",
                "document_category": "Instructions",
                "count": len(by_year[year]),
                "instructions": by_year[year]
            }
            save_json(self.paths["metadata"] / f"{year}.json", year_data)
            print(f"Saved {year}.json ({len(by_year[year])})")

        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_instructions": len(instructions),
            "by_year": {y: len(i) for y, i in sorted(by_year.items())},
            "by_category": dict(sorted(categories.items(), key=lambda x: -x[1])),
            "statistics": {
                "with_hindi": sum(1 for i in instructions if i.get("docFileNameHi"))
            }
        }
        save_json(self.summary_file, summary)
        print("Summary generated successfully.")
