import os
import json
from src.core import config
from src.core.utils import slugify

class GstOrderAnalyzer:
    def __init__(self, target_year: str):
        self.year = str(target_year)
        self.paths = config.ensure_namespace_dirs("gst", "orders")
        self.metadata_file = self.paths["metadata"] / f"{self.year}.json"
        
    def run(self):
        print(f"\n=====================================")
        print(f"ANALYZE YEAR {self.year} Orders (Strict Validation)")
        print(f"=====================================")
        
        if not self.metadata_file.exists():
            print(f"Metadata file {self.metadata_file} not found.")
            return None
            
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            orders = data.get("orders", [])
            
        report = {
            "expected": len(orders),
            "english": {"available": 0, "missing": 0, "missing_reasons": {}, "list": []},
            "hindi": {"expected": sum(1 for o in orders if o.get("docFileNameHi")), "available": 0, "missing": 0, "missing_reasons": {}, "list": []}
        }
        
        for o in orders:
            order_no = o.get("orderNo", "")
            if not order_no:
                self._record_error(report, "english", o, "empty_order_no", order_no)
                if o.get("docFileNameHi"):
                    self._record_error(report, "hindi", o, "empty_order_no", order_no)
                continue
                
            category = o.get("orderCategory", "Unknown").replace(" ", "-")
            number_part = order_no.split("/")[0] if "/" in order_no else "unknown"
            unique_number_part = f"{number_part}_{o.get('id')}"
            
            # Check English Path
            eng_meta_path = self.paths["downloads"] / "english" / self.year / category / unique_number_part / "metadata.json"
            self._validate_path(report, "english", eng_meta_path, o, order_no)

            # Check Hindi Path
            if bool(o.get("docFileNameHi")):
                hin_meta_path = self.paths["downloads"] / "hindi" / self.year / category / unique_number_part / "metadata.json"
                self._validate_path(report, "hindi", hin_meta_path, o, order_no)
                    
        return report

    def _validate_path(self, report, lang, meta_path, o, order_no):
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
            # Cross-verify ID matching correctly
            db_id_key = "english_db_id" if lang == "english" else "hindi_db_id"
            target_id = meta.get('id') or meta.get(db_id_key)
            
            if str(target_id) == str(o.get('id')):
                if meta.get('available'):
                    report[lang]["available"] += 1
                else:
                    reason = meta.get('missing_reason', 'missing_no_reason')
                    self._record_error(report, lang, o, reason, order_no)
            else:
                self._record_error(report, lang, o, "overwritten_by_duplicate", order_no, meta.get('id'))
        else:
            self._record_error(report, lang, o, "directory_not_found", order_no)

    def _record_error(self, report, lang, o, reason, order_no, overwritten_by=None):
        report[lang]["missing"] += 1
        report[lang]["missing_reasons"][reason] = report[lang]["missing_reasons"].get(reason, 0) + 1
        
        err = {"id": o.get("id"), "notif": order_no, "reason": reason}
        if overwritten_by:
            err["overwritten_by"] = overwritten_by
        report[lang]["list"].append(err)
