"""
Downloads GST Form PDFs from the CBIC API.
Forms use a simpler download endpoint: /api/cbic-form-msts/download/{id}
No language parameter — forms are single-language (English only).
"""

import asyncio
import base64
import os

from src.core import config
from src.core.utils import save_json, load_json, slugify
from src.core.api_client import CbicApiClient

class GstFormDownloader:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("gst", "forms")
        self.raw_file = self.paths["raw_metadata_file"]
        self.prog_file = self.paths["logs"] / "progress_downloads.json"
        self.err_file = self.paths["logs"] / "errors_downloads.json"
        
        self.forms = load_json(self.raw_file, [])
        if not self.forms:
            raise FileNotFoundError("No raw_metadata.json found. Run 'scrape-forms' first.")

    def load_progress(self) -> set:
        return set(load_json(self.prog_file).get("downloaded_ids", []))

    def save_progress(self, downloaded_ids: set):
        save_json(self.prog_file, {"downloaded_ids": list(downloaded_ids)})

    def get_destination_folder(self, form: dict) -> str:
        cat = (form.get("formCategory") or "Uncategorized").replace(" ", "-").replace("/", "-")
        unique = str(form['id'])
        
        path = self.paths["downloads"] / cat / unique
        os.makedirs(str(path), exist_ok=True)
        return str(path)

    async def download_file(self, client: CbicApiClient, form: dict, downloaded_ids: set, errors: list) -> bool:
        fid = form["id"]
        if fid in downloaded_ids:
            return True

        folder_path = self.get_destination_folder(form)
        
        # Download PDF
        endpoint = f"/api/cbic-form-msts/download/{fid}"
        response = await client.fetch_json(endpoint)
        
        if "error" in response:
            error_msg = "server_error_500" if response["status"] == 500 else response["error"]
            errors.append({"id": fid, "form": form.get("formNo", ""), "error": error_msg, "status": response["status"]})
            save_json(os.path.join(folder_path, "metadata.json"), {
                "id": fid, "form_no": form.get("formNo", ""), "form_name": form.get("formName", ""),
                "category": form.get("formCategory", ""), "available": False, "missing_reason": error_msg
            })
            return False

        # The download endpoint returns {data: base64, fileName: "..."}
        if "data" not in response:
            errors.append({"id": fid, "form": form.get("formNo", ""), "error": "no_data_field"})
            save_json(os.path.join(folder_path, "metadata.json"), {
                "id": fid, "form_no": form.get("formNo", ""), "form_name": form.get("formName", ""),
                "category": form.get("formCategory", ""), "available": False, "missing_reason": "no_data_field"
            })
            return False

        filename = response.get("fileName", "")
        if not filename:
            # Some forms (e.g., GST Amnesty Scheme) return empty fileName
            safe = slugify(form.get("formNo", "")) or f"form_{fid}"
            filename = f"{safe}.pdf"
        file_path = os.path.join(folder_path, filename)
        
        pdf_bytes = base64.b64decode(response["data"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        save_json(os.path.join(folder_path, "metadata.json"), {
            "id": fid, "form_no": form.get("formNo", ""), "form_name": form.get("formName", ""),
            "category": form.get("formCategory", ""), "available": True,
            "file": filename, "size_bytes": len(pdf_bytes)
        })
        return True

    async def run(self):
        downloaded_ids = self.load_progress()
        all_errors = load_json(self.err_file, [])
        
        pending = [f for f in self.forms if f["id"] not in downloaded_ids]
        print(f"Downloading GST Form PDFs. Remaining: {len(pending)}/{len(self.forms)}")
        
        if not pending:
            print("All forms already downloaded.")
            return
            
        async with CbicApiClient() as client:
            successful = 0
            
            for i in range(0, len(pending), config.BATCH_SIZE):
                batch = pending[i:i + config.BATCH_SIZE]
                tasks = [self.download_file(client, f, downloaded_ids, all_errors) for f in batch]
                results = await asyncio.gather(*tasks)
                
                for success, form in zip(results, batch):
                    if success:
                        successful += 1
                        downloaded_ids.add(form["id"])
                        
                print(f"  Batch {i+len(batch)}/{len(pending)} | Success: {successful}")
                self.save_progress(downloaded_ids)
                save_json(self.err_file, all_errors)
                
                await asyncio.sleep(config.BATCH_DELAY_SECONDS)
                
        print(f"Finished. {successful}/{len(pending)} PDFs downloaded.")
