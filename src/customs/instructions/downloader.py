"""Customs Instructions downloader (placeholder — metadata-only for now)."""

import asyncio
import base64
import os
from typing import Dict, Any

from src.core import config
from src.core.utils import save_json, load_json, slugify
from src.core.api_client import CbicApiClient

class CustomsInstructionDownloader:
    def __init__(self, target_year: str, language: str):
        self.year = str(target_year)
        self.language = language.upper()
        self.paths = config.ensure_namespace_dirs("customs", "instructions")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"
        lang_sub = language.lower()
        self.prog_file = self.paths["logs"] / f"progress_{lang_sub}_{self.year}.json"
        self.err_file = self.paths["logs"] / f"errors_{lang_sub}_{self.year}.json"
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Missing organized metadata for year {self.year}.")
        self.all_data = load_json(self.metadata_file)
        self.instructions = self.all_data.get("instructions", [])

    def load_progress(self) -> set:
        return set(load_json(self.prog_file).get("downloaded_ids", []))

    def save_progress(self, downloaded_ids: set):
        save_json(self.prog_file, {"downloaded_ids": list(downloaded_ids)})

    def get_destination_folder(self, inst):
        cat = (inst.get("instructionCategory") or "Uncategorized").replace(" ", "-")
        inst_no = inst.get("instructionNo", "")
        number_part = inst_no.split("/")[0] if "/" in inst_no else slugify(inst_no)[:30] if inst_no else "unknown"
        unique = f"{number_part}_{inst['id']}"
        folder_language = "english" if self.language == "ENG" else "hindi"
        path = self.paths["downloads"] / folder_language / self.year / cat / unique
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def write_ai_metadata(self, folder_path, inst, has_pdf, error_reason=None):
        inst_no = inst.get("instructionNo", "")
        safe_name = slugify(inst_no)
        lang_str = "english" if self.language == "ENG" else "hindi"
        expected_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        save_json(os.path.join(folder_path, "metadata.json"), {
            "id": inst["id"], "instruction_no": inst_no,
            "date": inst.get("instructionDt", ""), "category": inst.get("instructionCategory", ""),
            "subject": inst.get("instructionName", ""), "language": lang_str,
            "available": has_pdf, "files": {lang_str: expected_filename if has_pdf else None},
            f"{lang_str}_db_id": inst["id"], "missing_reason": error_reason
        })

    async def download_file(self, client, inst, downloaded_ids, errors):
        iid = inst["id"]
        if iid in downloaded_ids: return True
        if self.language == "HINDI" and not inst.get("docFileNameHi"): return False
        folder_path = self.get_destination_folder(inst)
        safe_name = slugify(inst.get("instructionNo", ""))
        pdf_filename = f"{safe_name}-eng.pdf" if self.language == "ENG" else f"{safe_name}.pdf"
        file_path = os.path.join(folder_path, pdf_filename)
        endpoint = f"/api/cbic-instruction-msts/download/{iid}/{self.language}"
        response = await client.fetch_json(endpoint)
        if "error" in response:
            error_msg = "server_error_500" if response["status"] == 500 else response["error"]
            errors.append(client.format_error_log(iid, error_msg, response["status"]))
            self.write_ai_metadata(folder_path, inst, False, error_msg)
            return False
        if "data" not in response:
            errors.append(client.format_error_log(iid, "No base64 data field.", 200))
            self.write_ai_metadata(folder_path, inst, False, "no_data_field")
            return False
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(response["data"]))
        self.write_ai_metadata(folder_path, inst, True)
        return True

    async def run(self):
        downloaded_ids = self.load_progress()
        all_errors = load_json(self.err_file, [])
        if self.language == "ENG":
            pending = [i for i in self.instructions if i["id"] not in downloaded_ids]
        else:
            pending = [i for i in self.instructions if i.get("docFileNameHi") and i["id"] not in downloaded_ids]
        print(f"Downloading {self.language} PDFs for Customs Instructions {self.year}. Remaining: {len(pending)}")
        if not pending: return
        async with CbicApiClient() as client:
            successful = 0
            for i in range(0, len(pending), config.BATCH_SIZE):
                batch = pending[i:i + config.BATCH_SIZE]
                tasks = [self.download_file(client, inst, downloaded_ids, all_errors) for inst in batch]
                results = await asyncio.gather(*tasks)
                for success, inst in zip(results, batch):
                    if success: successful += 1; downloaded_ids.add(inst["id"])
                print(f"  Processed batch: {i+len(batch)}/{len(pending)}")
                self.save_progress(downloaded_ids)
                save_json(self.err_file, all_errors)
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
        print(f"Finished. {successful} PDFs stored safely.")
