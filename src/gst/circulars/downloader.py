"""
Combined downloader script for the CBIC GST Circulars.
Handles downloading both ENGLISH and HINDI PDF versions simultaneously into uniquely keyed folders.
"""

import asyncio
import base64
import os
from typing import Dict, Any, List

from src.core import config
from src.core.utils import save_json, load_json, slugify
from src.core.api_client import CbicApiClient

class GstCircularDownloader:
    def __init__(self, target_year: str, language: str):
        self.year = str(target_year)
        self.language = language.upper()  # Expect either 'ENG' or 'HINDI'
        
        self.paths = config.ensure_namespace_dirs("gst", "circulars")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"
        
        lang_sub = language.lower() # 'eng' or 'hindi'
        self.prog_file = self.paths["logs"] / f"progress_{lang_sub}_{self.year}.json"
        self.err_file = self.paths["logs"] / f"errors_{lang_sub}_{self.year}.json"
        
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Missing organized metadata for year {self.year}. Run 'organize-circ' first.")
            
        self.all_data = load_json(self.metadata_file)
        self.circulars = self.all_data.get("circulars", [])

    def load_progress(self) -> set:
        data = load_json(self.prog_file)
        return set(data.get("downloaded_ids", []))

    def save_progress(self, downloaded_ids: set):
        save_json(self.prog_file, {"downloaded_ids": list(downloaded_ids)})

    def get_destination_folder(self, circular: Dict[str, Any]) -> str:
        """
        Creates structurally flawless directory paths using db 'id'.
        Format: data/gst/circulars/downloads/english/2025/Central-Tax/01_1003310/
        """
        category = circular.get("circularCategory", "Unknown").replace(" ", "-")
        circ_no = circular.get("circularNo", "")
        
        number_part = circ_no.split("/")[0] if "/" in circ_no else "unknown"
        unique_number_part = f"{number_part}_{circular['id']}"
        
        folder_language = "english" if self.language == "ENG" else "hindi"
        path = self.paths["downloads"] / folder_language / self.year / category / unique_number_part
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def write_ai_metadata(self, folder_path: str, circular: Dict[str, Any], has_pdf: bool, error_reason: str = None):
        """Creates a local metadata.json inside the PDF folder so an AI Agent can perfectly parse relationships."""
        circ_no = circular.get("circularNo", "")
        safe_name = slugify(circ_no)
        
        lang_str = "english" if self.language == "ENG" else "hindi"
        
        # If Hindi, the PDF from the CBIC API doesn't have an -eng suffix.
        expected_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        
        # Edge case: Sometimes the CBIC completely re-issues generic IDs without english
        is_hindi_only_corrigendum = (
            not circular.get("docFileName") and 
            circular.get("docFileNameHi") and 
            self.language == "ENG"
        )
        if error_reason is None and not has_pdf and is_hindi_only_corrigendum:
            error_reason = "hindi_only_corrigendum"
            
        metadata = {
            "id": circular["id"],
            "circular_no": circ_no,
            "date": circular.get("circularDt", ""),
            "category": circular.get("circularCategory", ""),
            "subject": circular.get("circularName", ""),
            "language": lang_str,
            "available": has_pdf,
            "files": {
                lang_str: expected_filename if has_pdf else None
            },
            f"{lang_str}_db_id": circular["id"],
            "missing_reason": error_reason
        }
        save_json(os.path.join(folder_path, "metadata.json"), metadata)

    async def download_file(self, client: CbicApiClient, circular: Dict[str, Any], downloaded_ids: set, errors: list) -> bool:
        cid = circular["id"]
        if cid in downloaded_ids:
            return True
            
        # Skip Hindi if no Hindi metadata file is marked
        if self.language == "HINDI" and not circular.get("docFileNameHi"):
            return False

        folder_path = self.get_destination_folder(circular)
        safe_name = slugify(circular.get("circularNo", ""))
        pdf_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        file_path = os.path.join(folder_path, pdf_filename)
        
        endpoint = f"/api/cbic-circular-msts/download/{cid}/{self.language}"
        response = await client.fetch_json(endpoint)
        
        if "error" in response:
            error_msg = response["error"]
            if response["status"] == 500:
                error_msg = "server_error_500"
                
            errors.append(client.format_error_log(cid, error_msg, response["status"]))
            self.write_ai_metadata(folder_path, circular, False, error_msg)
            return False

        if "data" not in response:
            errors.append(client.format_error_log(cid, "No base64 data field found in 200 OK wrapper.", 200))
            self.write_ai_metadata(folder_path, circular, False, "no_data_field")
            return False

        # Physical Save
        pdf_bytes = base64.b64decode(response["data"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        self.write_ai_metadata(folder_path, circular, True)
        return True

    async def run(self):
        downloaded_ids = self.load_progress()
        all_errors = load_json(self.err_file, [])
        
        # Determine genuine pending list
        if self.language == "ENG":
            pending = [c for c in self.circulars if c["id"] not in downloaded_ids]
        else:
            pending = [c for c in self.circulars if c.get("docFileNameHi") and c["id"] not in downloaded_ids]
            
        print(f"Downloading {self.language} PDFs for {self.year}. Remaining to process: {len(pending)}")
        
        if not pending:
            return
            
        async with CbicApiClient() as client:
            successful = 0
            
            for i in range(0, len(pending), config.BATCH_SIZE):
                batch = pending[i:i + config.BATCH_SIZE]
                tasks = [self.download_file(client, c, downloaded_ids, all_errors) for c in batch]
                results = await asyncio.gather(*tasks)
                
                # Check results
                for success, circ in zip(results, batch):
                    if success:
                        successful += 1
                        downloaded_ids.add(circ["id"])
                        
                print(f"  Processed local batch: {i+len(batch)}/{len(pending)}")
                self.save_progress(downloaded_ids)
                save_json(self.err_file, all_errors)
                
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
                
        print(f"Finished. {successful} PDFs stored safely.")
