"""
Downloads GST Instruction PDFs from the CBIC API.
"""

import asyncio
import base64
import os
from typing import Dict, Any

from src.core import config
from src.core.utils import save_json, load_json, slugify
from src.core.api_client import CbicApiClient

class GstInstructionDownloader:
    def __init__(self, target_year: str, language: str):
        self.year = str(target_year)
        self.language = language.upper()
        
        self.paths = config.ensure_namespace_dirs("gst", "instructions")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"
        
        lang_sub = language.lower()
        self.prog_file = self.paths["logs"] / f"progress_{lang_sub}_{self.year}.json"
        self.err_file = self.paths["logs"] / f"errors_{lang_sub}_{self.year}.json"
        
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Missing organized metadata for year {self.year}. Run 'organize-inst' first.")
            
        self.all_data = load_json(self.metadata_file)
        self.instructions = self.all_data.get("instructions", [])

    def load_progress(self) -> set:
        data = load_json(self.prog_file)
        return set(data.get("downloaded_ids", []))

    def save_progress(self, downloaded_ids: set):
        save_json(self.prog_file, {"downloaded_ids": list(downloaded_ids)})

    def get_destination_folder(self, instruction: Dict[str, Any]) -> str:
        cat = (instruction.get("instructionCategory") or "Uncategorized").replace(" ", "-")
        inst_no = instruction.get("instructionNo", "")
        
        number_part = inst_no.split("/")[0] if "/" in inst_no else slugify(inst_no)[:30] if inst_no else "unknown"
        unique_number_part = f"{number_part}_{instruction['id']}"
        
        folder_language = "english" if self.language == "ENG" else "hindi"
        path = self.paths["downloads"] / folder_language / self.year / cat / unique_number_part
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def write_ai_metadata(self, folder_path: str, instruction: Dict[str, Any], has_pdf: bool, error_reason: str = None):
        inst_no = instruction.get("instructionNo", "")
        safe_name = slugify(inst_no)
        
        lang_str = "english" if self.language == "ENG" else "hindi"
        expected_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        
        is_hindi_only = (
            not instruction.get("docFileName") and 
            instruction.get("docFileNameHi") and 
            self.language == "ENG"
        )
        if error_reason is None and not has_pdf and is_hindi_only:
            error_reason = "hindi_only"
            
        metadata = {
            "id": instruction["id"],
            "instruction_no": inst_no,
            "date": instruction.get("instructionDt", ""),
            "category": instruction.get("instructionCategory", ""),
            "subject": instruction.get("instructionName", ""),
            "language": lang_str,
            "available": has_pdf,
            "files": {lang_str: expected_filename if has_pdf else None},
            f"{lang_str}_db_id": instruction["id"],
            "missing_reason": error_reason
        }
        save_json(os.path.join(folder_path, "metadata.json"), metadata)

    async def download_file(self, client: CbicApiClient, instruction: Dict[str, Any], downloaded_ids: set, errors: list) -> bool:
        iid = instruction["id"]
        if iid in downloaded_ids:
            return True
            
        if self.language == "HINDI" and not instruction.get("docFileNameHi"):
            return False

        folder_path = self.get_destination_folder(instruction)
        safe_name = slugify(instruction.get("instructionNo", ""))
        pdf_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        file_path = os.path.join(folder_path, pdf_filename)
        
        endpoint = f"/api/cbic-instruction-msts/download/{iid}/{self.language}"
        response = await client.fetch_json(endpoint)
        
        if "error" in response:
            error_msg = response["error"]
            if response["status"] == 500:
                error_msg = "server_error_500"
            errors.append(client.format_error_log(iid, error_msg, response["status"]))
            self.write_ai_metadata(folder_path, instruction, False, error_msg)
            return False

        if "data" not in response:
            errors.append(client.format_error_log(iid, "No base64 data field found.", 200))
            self.write_ai_metadata(folder_path, instruction, False, "no_data_field")
            return False

        pdf_bytes = base64.b64decode(response["data"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        self.write_ai_metadata(folder_path, instruction, True)
        return True

    async def run(self):
        downloaded_ids = self.load_progress()
        all_errors = load_json(self.err_file, [])
        
        if self.language == "ENG":
            pending = [i for i in self.instructions if i["id"] not in downloaded_ids]
        else:
            pending = [i for i in self.instructions if i.get("docFileNameHi") and i["id"] not in downloaded_ids]
            
        print(f"Downloading {self.language} PDFs for GST Instructions {self.year}. Remaining: {len(pending)}")
        
        if not pending:
            return
            
        async with CbicApiClient() as client:
            successful = 0
            
            for i in range(0, len(pending), config.BATCH_SIZE):
                batch = pending[i:i + config.BATCH_SIZE]
                tasks = [self.download_file(client, inst, downloaded_ids, all_errors) for inst in batch]
                results = await asyncio.gather(*tasks)
                
                for success, inst in zip(results, batch):
                    if success:
                        successful += 1
                        downloaded_ids.add(inst["id"])
                        
                print(f"  Processed batch: {i+len(batch)}/{len(pending)}")
                self.save_progress(downloaded_ids)
                save_json(self.err_file, all_errors)
                
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
                
        print(f"Finished. {successful} PDFs stored safely.")
