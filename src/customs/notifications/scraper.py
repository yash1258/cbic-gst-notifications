"""
Scrapes metadata from the CBIC Customs Notifications endpoints.
Same API as GST notifications, filtered for Customs tax type (tax.id = 1000002).
"""

import asyncio
from typing import Dict, Any

from src.core import config
from src.core.utils import save_json, load_json
from src.core.api_client import CbicApiClient, logger

CUSTOMS_TAX_ID = 1000002
START_ID = 1000001
END_ID = 1010588

class CustomsNotificationScraper:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("customs", "notifications")
        self.raw_file = self.paths["raw_metadata_file"]
        self.prog_file = self.paths["progress_file"]
        self.err_file = self.paths["error_log_file"]

    def load_progress(self) -> int:
        data = load_json(self.prog_file)
        return data.get("last_id", START_ID - 1)

    def save_progress(self, last_id: int):
        save_json(self.prog_file, {"last_id": last_id})

    def parse_notification(self, record: dict) -> Dict[str, Any]:
        """Extract relevant fields for Customs notifications only."""
        tax_id = record.get("tax", {}).get("id")
        date_str = record.get("notificationDt", "")
        
        if tax_id != CUSTOMS_TAX_ID:
            return None
        
        return {
            "id": record.get("id"),
            "notificationNo": record.get("notificationNo", ""),
            "notificationDt": date_str[:10] if date_str else "",
            "notificationName": record.get("notificationName", ""),
            "notificationCategory": record.get("notificationCategory", ""),
            "notificationNoHi": record.get("notificationNoHi", ""),
            "notificationNameHi": record.get("notificationNameHi", ""),
            "docFileName": record.get("docFileName", ""),
            "docFileNameHi": record.get("docFileNameHi", ""),
            "docFilePath": record.get("docFilePath", ""),
            "isAmended": record.get("isAmended", ""),
            "isOmitted": record.get("isOmitted", ""),
            "parentId": record.get("parentId"),
            "orderId": record.get("orderId"),
        }

    async def fetch_notification(self, client: CbicApiClient, notif_id: int, errors: list) -> Dict[str, Any]:
        endpoint = f"/api/cbic-notification-msts/{notif_id}"
        response = await client.fetch_json(endpoint)
        
        if "error" in response:
            if response["status"] != 404:
                errors.append(client.format_error_log(notif_id, response["error"], response["status"]))
            return None
            
        return self.parse_notification(response)

    async def run(self):
        start_id = self.load_progress() + 1
        existing_records = load_json(self.raw_file, [])
        existing_ids = {n["id"] for n in existing_records}
        
        all_notifications = list(existing_records)
        all_errors = load_json(self.err_file, [])
        
        print(f"Scanning Customs Notification APIs: IDs {start_id:,} to {END_ID:,}")
        
        async with CbicApiClient() as client:
            total_ids = END_ID - start_id + 1
            processed = 0
            
            for batch_start in range(start_id, END_ID + 1, config.BATCH_SIZE):
                batch_end = min(batch_start + config.BATCH_SIZE, END_ID + 1)
                batch_ids = [i for i in range(batch_start, batch_end) if i not in existing_ids]
                
                if not batch_ids:
                    processed += (batch_end - batch_start)
                    continue
                
                tasks = [self.fetch_notification(client, i, all_errors) for i in batch_ids]
                results = await asyncio.gather(*tasks)
                
                for r in filter(None, results):
                    if r["id"] not in existing_ids:
                        all_notifications.append(r)
                        existing_ids.add(r["id"])
                
                processed += len(batch_ids)
                
                if processed % 500 < config.BATCH_SIZE:
                    print(f"Progress: {processed}/{total_ids} ({processed/total_ids*100:.1f}%) | Customs Found: {len(existing_ids)}")
                    
                if processed % 1000 < config.BATCH_SIZE:
                    self.save_progress(batch_end - 1)
                    save_json(self.raw_file, all_notifications)
                    save_json(self.err_file, all_errors)
                
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
                
        self.save_progress(END_ID)
        save_json(self.raw_file, all_notifications)
        save_json(self.err_file, all_errors)
        print(f"API Metadata scrape complete. {len(all_notifications)} Customs notifications found.")
