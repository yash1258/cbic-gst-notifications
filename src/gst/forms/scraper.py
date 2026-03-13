"""
Scrapes GST Form metadata from the CBIC bulk-fetch API.
Unlike notifications/circulars, the forms API returns all records in a single call.
"""

import asyncio
from collections import defaultdict
from datetime import datetime

from src.core import config
from src.core.utils import save_json, load_json
from src.core.api_client import CbicApiClient

GST_TAX_ID = 1000001

class GstFormScraper:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("gst", "forms")
        self.raw_file = self.paths["raw_metadata_file"]
        self.summary_file = self.paths["metadata"] / "summary.json"

    async def run(self):
        print("Fetching all GST Forms via bulk API...")
        
        async with CbicApiClient() as client:
            resp = await client.fetch_json(f"/api/cbic-form-msts/fetchForms/{GST_TAX_ID}")
        
        if "error" in resp:
            print(f"ERROR: API returned {resp}")
            return
        
        if not isinstance(resp, list):
            print(f"ERROR: Expected list, got {type(resp)}")
            return

        # Parse each form record
        forms = []
        for record in resp:
            forms.append({
                "id": record.get("id"),
                "formNo": record.get("formNo", ""),
                "formName": record.get("formName", ""),
                "formCategory": record.get("formCategory", ""),
                "contentFileName": record.get("contentFileName", ""),
                "contentFilePath": record.get("contentFilePath", ""),
                "contentFileNameHi": record.get("contentFileNameHi"),
                "contentFilePathHi": record.get("contentFilePathHi"),
                "formNoHi": record.get("formNoHi"),
                "formNameHi": record.get("formNameHi"),
                "formCategoryHi": record.get("formCategoryHi", ""),
                "isAmended": record.get("isAmended", ""),
                "parentId": record.get("parentId"),
                "orderId": record.get("orderId"),
                "createdDt": record.get("createdDt", ""),
            })

        save_json(self.raw_file, forms)
        print(f"Saved {len(forms)} GST form records to raw_metadata.json")
        
        # Generate summary organized by category
        by_category = defaultdict(list)
        for f in forms:
            by_category[f["formCategory"]].append(f)
        
        # Save per-category JSON files (analogous to year JSONs)
        for cat, cat_forms in sorted(by_category.items()):
            cat_slug = cat.replace(" ", "-").replace("/", "-")
            cat_data = {
                "category": cat,
                "tax_type": "GST",
                "document_category": "Forms",
                "count": len(cat_forms),
                "forms": cat_forms
            }
            save_json(self.paths["metadata"] / f"{cat_slug}.json", cat_data)
            print(f"  {cat}: {len(cat_forms)} forms")

        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_forms": len(forms),
            "by_category": {c: len(f) for c, f in sorted(by_category.items(), key=lambda x: -len(x[1]))},
            "id_range": {"min": min(f["id"] for f in forms), "max": max(f["id"] for f in forms)},
            "statistics": {
                "with_hindi": sum(1 for f in forms if f.get("contentFileNameHi")),
                "categories": len(by_category),
            }
        }
        save_json(self.summary_file, summary)
        print(f"\nTotal: {len(forms)} GST forms across {len(by_category)} categories.")
