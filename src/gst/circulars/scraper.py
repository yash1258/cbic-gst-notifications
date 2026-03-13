"""
Scrapes metadata from the CBIC GST Circulars endpoints.
"""

import asyncio
import time
from typing import List, Dict, Any

from src.core import config
from src.core.utils import save_json, load_json
from src.core.api_client import CbicApiClient, logger

# The exact numeric ID code for GST tax documents on CBIC
GST_TAX_ID = 1000001
# ID Boundaries based on CBIC database
START_ID = 1000001
END_ID = 1005000

class GstCircularScraper:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("gst", "circulars")
        self.raw_file = self.paths["raw_metadata_file"]
        self.prog_file = self.paths["progress_file"]
        self.err_file = self.paths["error_log_file"]

    def load_progress(self) -> int:
        data = load_json(self.prog_file)
        return data.get("last_id", START_ID - 1)

    def save_progress(self, last_id: int):
        save_json(self.prog_file, {"last_id": last_id})

    def parse_circular(self, record: dict) -> Dict[str, Any]:
        """Extract relevant fields, explicitly rejecting non-GST and Pre-2017 records."""
        tax_id = record.get("tax", {}).get("id")
        date_str = record.get("circularDt", "")
        
        if tax_id != GST_TAX_ID:
            return None
        if date_str and date_str[:10] < "2017-01-01":
            return None
        
        return {
            "id": record.get("id"),
            "circularNo": record.get("circularNo", ""),
            "circularDt": date_str[:10] if date_str else "",
            "circularName": record.get("circularName", ""),
            "circularCategory": record.get("circularCategory", ""),
            "circularNoHi": record.get("circularNoHi", ""),
            "circularNameHi": record.get("circularNameHi", ""),
            "docFileName": record.get("docFileName", ""),
            "docFileNameHi": record.get("docFileNameHi", ""),
            "docFilePath": record.get("docFilePath", ""),
            "isAmended": record.get("isAmended", ""),
            "isOmitted": record.get("isOmitted", ""),
            "parentId": record.get("parentId"),
            "orderId": record.get("orderId"),
        }

    async def fetch_circular(self, client: CbicApiClient, circ_id: int, errors: list) -> Dict[str, Any]:
        endpoint = f"/api/cbic-circular-msts/{circ_id}"
        response = await client.fetch_json(endpoint)
        
        if "error" in response:
            if response["status"] != 404:  # Silently skip 404s, they simply don't exist
                errors.append(client.format_error_log(circ_id, response["error"], response["status"]))
            return None
            
        return self.parse_circular(response)

    async def run(self):
        start_id = self.load_progress() + 1
        existing_records = load_json(self.raw_file, [])
        existing_ids = {n["id"] for n in existing_records}
        
        all_circulars = list(existing_records)
        all_errors = load_json(self.err_file, [])
        
        print(f"Scanning GST Circular APIs: IDs {start_id:,} to {END_ID:,}")
        
        async with CbicApiClient() as client:
            total_ids = END_ID - start_id + 1
            processed = 0
            
            for batch_start in range(start_id, END_ID + 1, config.BATCH_SIZE):
                batch_end = min(batch_start + config.BATCH_SIZE, END_ID + 1)
                batch_ids = [i for i in range(batch_start, batch_end) if i not in existing_ids]
                
                if not batch_ids:
                    processed += (batch_end - batch_start)
                    continue
                
                tasks = [self.fetch_circular(client, i, all_errors) for i in batch_ids]
                results = await asyncio.gather(*tasks)
                
                for r in filter(None, results):
                    if r["id"] not in existing_ids:
                        all_circulars.append(r)
                        existing_ids.add(r["id"])
                
                processed += len(batch_ids)
                
                if processed % 500 < config.BATCH_SIZE:
                    print(f"Progress: {processed}/{total_ids} ({processed/total_ids*100:.1f}%) | GST Found: {len(existing_ids)}")
                    
                if processed % 1000 < config.BATCH_SIZE:
                    self.save_progress(batch_end - 1)
                    save_json(self.raw_file, all_circulars)
                    save_json(self.err_file, all_errors)
                
                # Gentile delay
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
                
        # Final save
        self.save_progress(END_ID)
        save_json(self.raw_file, all_circulars)
        save_json(self.err_file, all_errors)
        print("API Metadata scrape complete.")
