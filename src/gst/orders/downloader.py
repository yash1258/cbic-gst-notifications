"""
Combined downloader script for the CBIC GST Orders.
Handles downloading both ENGLISH and HINDI PDF versions into uniquely keyed folders.
"""

import asyncio
import base64
import os
from typing import Dict, Any, List

from src.core import config
from src.core.utils import save_json, load_json, slugify
from src.core.api_client import CbicApiClient

class GstOrderDownloader:
    def __init__(self, target_year: str, language: str):
        self.year = str(target_year)
        self.language = language.upper()  # Expect either 'ENG' or 'HINDI'
        
        self.paths = config.ensure_namespace_dirs("gst", "orders")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"
        
        lang_sub = language.lower() # 'eng' or 'hindi'
        self.prog_file = self.paths["logs"] / f"progress_{lang_sub}_{self.year}.json"
        self.err_file = self.paths["logs"] / f"errors_{lang_sub}_{self.year}.json"
        
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Missing organized metadata for year {self.year}. Run 'organize-order' first.")
            
        self.all_data = load_json(self.metadata_file)
        self.orders = self.all_data.get("orders", [])

    def load_progress(self) -> set:
        data = load_json(self.prog_file)
        return set(data.get("downloaded_ids", []))

    def save_progress(self, downloaded_ids: set):
        save_json(self.prog_file, {"downloaded_ids": list(downloaded_ids)})

    def get_destination_folder(self, order: Dict[str, Any]) -> str:
        """
        Creates structurally flawless directory paths using db 'id'.
        Format: data/gst/orders/downloads/english/2020/Order-CGST/01_1000001/
        """
        category = order.get("orderCategory", "Unknown").replace(" ", "-")
        order_no = order.get("orderNo", "")
        
        number_part = order_no.split("/")[0] if "/" in order_no else "unknown"
        unique_number_part = f"{number_part}_{order['id']}"
        
        folder_language = "english" if self.language == "ENG" else "hindi"
        path = self.paths["downloads"] / folder_language / self.year / category / unique_number_part
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def write_ai_metadata(self, folder_path: str, order: Dict[str, Any], has_pdf: bool, error_reason: str = None):
        """Creates a local metadata.json inside the PDF folder so an AI Agent can perfectly parse relationships."""
        order_no = order.get("orderNo", "")
        safe_name = slugify(order_no)
        
        lang_str = "english" if self.language == "ENG" else "hindi"
        
        expected_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        
        # Edge case: Hindi-only corrigendum
        is_hindi_only_corrigendum = (
            not order.get("docFileName") and 
            order.get("docFileNameHi") and 
            self.language == "ENG"
        )
        if error_reason is None and not has_pdf and is_hindi_only_corrigendum:
            error_reason = "hindi_only_corrigendum"
            
        metadata = {
            "id": order["id"],
            "order_no": order_no,
            "date": order.get("orderDt", ""),
            "category": order.get("orderCategory", ""),
            "subject": order.get("orderName", ""),
            "language": lang_str,
            "available": has_pdf,
            "files": {
                lang_str: expected_filename if has_pdf else None
            },
            f"{lang_str}_db_id": order["id"],
            "missing_reason": error_reason
        }
        save_json(os.path.join(folder_path, "metadata.json"), metadata)

    async def download_file(self, client: CbicApiClient, order: Dict[str, Any], downloaded_ids: set, errors: list) -> bool:
        oid = order["id"]
        if oid in downloaded_ids:
            return True
            
        # Skip Hindi if no Hindi metadata file is marked
        if self.language == "HINDI" and not order.get("docFileNameHi"):
            return False

        folder_path = self.get_destination_folder(order)
        safe_name = slugify(order.get("orderNo", ""))
        pdf_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        file_path = os.path.join(folder_path, pdf_filename)
        
        endpoint = f"/api/cbic-order-msts/download/{oid}/{self.language}"
        response = await client.fetch_json(endpoint)
        
        if "error" in response:
            error_msg = response["error"]
            if response["status"] == 500:
                error_msg = "server_error_500"
                
            errors.append(client.format_error_log(oid, error_msg, response["status"]))
            self.write_ai_metadata(folder_path, order, False, error_msg)
            return False

        if "data" not in response:
            errors.append(client.format_error_log(oid, "No base64 data field found in 200 OK wrapper.", 200))
            self.write_ai_metadata(folder_path, order, False, "no_data_field")
            return False

        # Physical Save
        pdf_bytes = base64.b64decode(response["data"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        self.write_ai_metadata(folder_path, order, True)
        return True

    async def run(self):
        downloaded_ids = self.load_progress()
        all_errors = load_json(self.err_file, [])
        
        # Determine genuine pending list
        if self.language == "ENG":
            pending = [o for o in self.orders if o["id"] not in downloaded_ids]
        else:
            pending = [o for o in self.orders if o.get("docFileNameHi") and o["id"] not in downloaded_ids]
            
        print(f"Downloading {self.language} PDFs for {self.year}. Remaining to process: {len(pending)}")
        
        if not pending:
            return
            
        async with CbicApiClient() as client:
            successful = 0
            
            for i in range(0, len(pending), config.BATCH_SIZE):
                batch = pending[i:i + config.BATCH_SIZE]
                tasks = [self.download_file(client, o, downloaded_ids, all_errors) for o in batch]
                results = await asyncio.gather(*tasks)
                
                # Check results
                for success, order in zip(results, batch):
                    if success:
                        successful += 1
                        downloaded_ids.add(order["id"])
                        
                print(f"  Processed local batch: {i+len(batch)}/{len(pending)}")
                self.save_progress(downloaded_ids)
                save_json(self.err_file, all_errors)
                
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
                
        print(f"Finished. {successful} PDFs stored safely.")
