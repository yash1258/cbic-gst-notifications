import json
import os
from src.core import config
from src.core.utils import load_json, slugify

class GstFormAnalyzer:
    def __init__(self):
        self.paths = config.ensure_namespace_dirs("gst", "forms")
        self.raw_file = self.paths["raw_metadata_file"]
        
    def run(self):
        print(f"\n=====================================")
        print(f"ANALYZE GST Forms (Strict Validation)")
        print(f"=====================================")
        
        forms = load_json(self.raw_file, [])
        if not forms:
            print("No raw_metadata.json found.")
            return None
            
        report = {
            "expected": len(forms),
            "available": 0,
            "missing": 0,
            "missing_reasons": {},
            "by_category": {},
            "missing_list": []
        }
        
        for form in forms:
            fid = form["id"]
            form_no = form.get("formNo", "")
            cat = (form.get("formCategory") or "Uncategorized").replace(" ", "-").replace("/", "-")
            unique = str(fid)
            
            meta_path = self.paths["downloads"] / cat / unique / "metadata.json"
            
            if cat not in report["by_category"]:
                report["by_category"][cat] = {"expected": 0, "available": 0, "missing": 0}
            report["by_category"][cat]["expected"] += 1
            
            if meta_path.exists():
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                if meta.get("available"):
                    report["available"] += 1
                    report["by_category"][cat]["available"] += 1
                else:
                    reason = meta.get("missing_reason", "unknown")
                    report["missing"] += 1
                    report["missing_reasons"][reason] = report["missing_reasons"].get(reason, 0) + 1
                    report["by_category"][cat]["missing"] += 1
                    report["missing_list"].append({"id": fid, "form": form_no, "reason": reason})
            else:
                report["missing"] += 1
                report["missing_reasons"]["not_downloaded"] = report["missing_reasons"].get("not_downloaded", 0) + 1
                report["by_category"][cat]["missing"] += 1
                report["missing_list"].append({"id": fid, "form": form_no, "reason": "not_downloaded"})
                    
        return report
